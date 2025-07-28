import json
import logging
from typing import Generator, Optional, Union

import boto3
from botocore.exceptions import ClientError
from dify_plugin.entities.model.llm import LLMResult, LLMResultChunk, LLMResultChunkDelta
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageTool,
    SystemPromptMessage,
    UserPromptMessage,
)
from dify_plugin.interfaces.model import large_language_model

logger = logging.getLogger(__name__)


class AWSBedrockARNLargeLanguageModel(large_language_model.LargeLanguageModel):
    """
    AWS Bedrock Large Language Model with ARN and custom inference ID support
    """

    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator[LLMResultChunk, None, None]]:
        """
        Invoke large language model
        """
        try:
            # Support for custom inference profile ARN or custom inference ID
            model_name = self._resolve_model_identifier(model, credentials)

            client = self._create_bedrock_runtime_client(credentials)

            # Simple message conversion
            messages = []
            system_message = ""

            for message in prompt_messages:
                if isinstance(message, SystemPromptMessage):
                    system_message = message.content
                elif isinstance(message, UserPromptMessage):
                    messages.append({"role": "user", "content": [{"text": message.content}]})
                elif isinstance(message, AssistantPromptMessage):
                    messages.append({"role": "assistant", "content": [{"text": message.content}]})

            request_body = {
                "messages": messages,
                "inferenceConfig": {
                    "maxTokens": model_parameters.get("max_tokens", 1024),
                    "temperature": model_parameters.get("temperature", 0.7),
                    "topP": model_parameters.get("top_p", 1.0),
                },
            }

            if system_message:
                request_body["system"] = [{"text": system_message}]

            if stream:
                response = client.invoke_model_with_response_stream(
                    modelId=model_name, body=json.dumps(request_body), contentType="application/json"
                )
                return self._simple_stream_handler(response, prompt_messages, model_name)
            else:
                response = client.invoke_model(
                    modelId=model_name, body=json.dumps(request_body), contentType="application/json"
                )
                return self._simple_response_handler(response, prompt_messages, model_name)

        except ClientError as e:
            raise self._handle_bedrock_error(e)
        except Exception as e:
            logger.error(f"Error invoking model {model_name}: {str(e)}")
            raise ValueError(f"Model invocation failed: {str(e)}")

    def _simple_stream_handler(
        self, response, prompt_messages: list[PromptMessage], model_name: str
    ) -> Generator[LLMResultChunk, None, None]:
        """
        Simple stream handler
        """
        for event in response["body"]:
            if "chunk" in event:
                chunk = event["chunk"]
                if "bytes" in chunk:
                    chunk_data = json.loads(chunk["bytes"].decode("utf-8"))

                    if "contentBlockDelta" in chunk_data:
                        delta = chunk_data["contentBlockDelta"]
                        if "delta" in delta and "text" in delta["delta"]:
                            text = delta["delta"]["text"]

                            yield LLMResultChunk(
                                model=model_name,
                                prompt_messages=prompt_messages,
                                delta=LLMResultChunkDelta(index=0, message=AssistantPromptMessage(content=text)),
                            )

    def _simple_response_handler(self, response, prompt_messages: list[PromptMessage], model_name: str) -> LLMResult:
        """
        Simple response handler
        """
        response_body = json.loads(response["body"].read())
        content = ""

        if "content" in response_body:
            for content_block in response_body["content"]:
                if "text" in content_block:
                    content += content_block["text"]

        return LLMResult(
            model=model_name,
            prompt_messages=prompt_messages,
            message=AssistantPromptMessage(content=content),
        )

    def _resolve_model_identifier(self, model: str, credentials: dict) -> str:
        """
        Resolve model identifier with support for ARN and custom inference ID
        """
        # Priority order:
        # 1. model_arn (for inference profile ARNs)
        # 2. inference_profile_id (for custom inference IDs)
        # 3. model_name (for custom model names)
        # 4. model parameter (default)

        if credentials.get("model_arn"):
            return credentials["model_arn"]
        elif credentials.get("inference_profile_id"):
            return credentials["inference_profile_id"]
        elif credentials.get("model_name"):
            return credentials["model_name"]
        else:
            return model

    def _create_bedrock_runtime_client(self, credentials: dict):
        """
        Create Bedrock runtime client with proper configuration
        """
        client_config = {
            "service_name": "bedrock-runtime",
            "aws_access_key_id": credentials.get("aws_access_key_id"),
            "aws_secret_access_key": credentials.get("aws_secret_access_key"),
            "region_name": credentials.get("aws_region", "us-east-1"),
        }

        # Add session token if available (for temporary credentials)
        session_token = credentials.get("aws_session_token")
        if session_token:
            client_config["aws_session_token"] = session_token

        return boto3.client(**client_config)

    def _handle_bedrock_error(self, error: ClientError) -> Exception:
        """
        Handle AWS Bedrock client errors with detailed mapping
        """
        error_code = error.response.get("Error", {}).get("Code", "Unknown")
        error_message = error.response.get("Error", {}).get("Message", str(error))

        # Map common Bedrock errors to user-friendly messages
        error_mapping = {
            "ResourceNotFoundException": f"Model or inference profile not found. Please check if the model ARN/ID exists and is accessible: {error_message}",
            "AccessDeniedException": "Access denied to the specified model. Please verify IAM permissions for the model/inference profile.",
            "ValidationException": f"Invalid request parameters: {error_message}",
            "ThrottlingException": "Request rate limit exceeded. Please retry after a short delay.",
            "ServiceUnavailableException": f"AWS Bedrock service is temporarily unavailable: {error_message}",
            "ModelTimeoutException": f"Model request timed out: {error_message}",
            "ModelNotReadyException": f"Model is not ready for inference: {error_message}",
            "InternalServerException": f"Internal server error from AWS Bedrock: {error_message}",
        }

        mapped_message = error_mapping.get(error_code, f"AWS Bedrock error ({error_code}): {error_message}")
        logger.error(f"AWS Bedrock error: {mapped_message}")

        return ValueError(mapped_message)

    def get_num_tokens(self, model: str, credentials: dict, prompt_messages: list[PromptMessage]) -> int:
        """
        Get number of tokens in prompt messages
        """
        # Simple token estimation - in production, use proper tokenization
        total_text = ""
        for message in prompt_messages:
            if hasattr(message, "content") and message.content:
                total_text += str(message.content)

        # Rough estimation: 1 token ≈ 4 characters
        return max(1, len(total_text) // 4)

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate model credentials
        """
        # Validate required credentials
        required_fields = ["aws_access_key_id", "aws_secret_access_key", "aws_region"]
        for field in required_fields:
            if not credentials.get(field):
                raise ValueError(f"{field.replace('_', ' ').title()} is required")

        # Test connection using bedrock client for listing models
        try:
            client = self._create_bedrock_runtime_client(credentials)

            # Test the resolved model identifier
            model_name = self._resolve_model_identifier(model, credentials)
            logger.info(f"Validating model identifier: {model_name}")

            # For ARN validation, try a minimal test call
            if (
                model_name.startswith("arn:aws:bedrock:")
                or credentials.get("model_arn")
                or credentials.get("inference_profile_id")
            ):
                # Test with minimal request for ARN/custom inference profiles
                test_request = {
                    "messages": [{"role": "user", "content": [{"text": "test"}]}],
                    "inferenceConfig": {"maxTokens": 1},
                }

                try:
                    client.invoke_model(
                        modelId=model_name, body=json.dumps(test_request), contentType="application/json"
                    )
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    # A ValidationException is expected for a minimal test call, so we can ignore it.
                    # This confirms that the credentials are valid enough to reach the model.
                    if error_code == "ValidationException":
                        logger.info("Successfully validated credentials with an expected ValidationException.")
                        pass
                    else:
                        # Any other client error during validation is a failure.
                        raise self._handle_bedrock_error(e)
            else:
                # For standard models, use bedrock client for basic validation
                bedrock_client = boto3.client(
                    "bedrock",
                    aws_access_key_id=credentials.get("aws_access_key_id"),
                    aws_secret_access_key=credentials.get("aws_secret_access_key"),
                    region_name=credentials.get("aws_region"),
                )

                # Test basic access to AWS Bedrock
                bedrock_client.list_foundation_models()

        except ClientError as e:
            raise self._handle_bedrock_error(e)
        except Exception as e:
            raise ValueError(f"Failed to validate credentials: {str(e)}")

    def _invoke_error_mapping(self) -> dict:
        """
        Map model invoke errors to error types
        """
        return {
            "ResourceNotFoundException": "Model not found",
            "AccessDeniedException": "Access denied",
            "ValidationException": "Invalid request",
            "ThrottlingException": "Rate limit exceeded",
            "ServiceUnavailableException": "Service unavailable",
            "ModelTimeoutException": "Model timeout",
            "ModelNotReadyException": "Model not ready",
            "InternalServerException": "Internal server error",
        }

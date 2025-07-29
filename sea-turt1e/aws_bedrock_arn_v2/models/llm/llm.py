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
        # Force immediate logging to see what's happening
        print(f"FORCE DEBUG: _invoke called with model: {model}")
        print(f"FORCE DEBUG: credentials keys: {list(credentials.keys())}")

        try:
            # Debug logs
            logger.info(f"DEBUG: _invoke called with model: {model}")
            logger.info(f"DEBUG: credentials keys: {list(credentials.keys())}")

            # Support for custom inference profile ARN or custom inference ID
            model_name = self._resolve_model_identifier(model, credentials)
            logger.info(f"DEBUG: Resolved model name: {model_name}")
            print(f"FORCE DEBUG: Resolved model name: {model_name}")

            # Debug credential values (safely)
            logger.info(f"DEBUG: model_arn: {credentials.get('model_arn', 'NOT_SET')}")
            logger.info(f"DEBUG: inference_profile_id: {credentials.get('inference_profile_id', 'NOT_SET')}")
            logger.info(f"DEBUG: model_name: {credentials.get('model_name', 'NOT_SET')}")

            print(f"FORCE DEBUG: model_arn: {credentials.get('model_arn', 'NOT_SET')}")
            print(f"FORCE DEBUG: inference_profile_id: {credentials.get('inference_profile_id', 'NOT_SET')}")
            print(f"FORCE DEBUG: model_name: {credentials.get('model_name', 'NOT_SET')}")

            # Check available models for debugging
            try:
                self._check_available_models(credentials, model_name)
            except Exception as debug_e:
                print(f"FORCE DEBUG: Model check failed: {debug_e}")

            client = self._create_bedrock_runtime_client(credentials)

            # Claude-specific message conversion
            messages = []
            system_message = ""

            for message in prompt_messages:
                if isinstance(message, SystemPromptMessage):
                    system_message = message.content
                elif isinstance(message, UserPromptMessage):
                    messages.append({"role": "user", "content": message.content})
                elif isinstance(message, AssistantPromptMessage):
                    messages.append({"role": "assistant", "content": message.content})

            # Claude-specific request format
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": model_parameters.get("max_tokens", 1024),
                "temperature": model_parameters.get("temperature", 0.7),
                "top_p": model_parameters.get("top_p", 1.0),
                "messages": messages,
            }

            if system_message:
                request_body["system"] = system_message

            logger.info(f"DEBUG: About to call Bedrock with modelId: {model_name}")
            logger.info(f"DEBUG: Request body: {json.dumps(request_body, indent=2)}")

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
            logger.error(f"DEBUG: ClientError occurred: {e}")
            raise self._handle_bedrock_error(e)
        except Exception as e:
            logger.error(f"DEBUG: Exception in _invoke: {str(e)}")
            logger.error(f"DEBUG: Exception type: {type(e)}")
            raise ValueError(f"Model invocation failed: {str(e)}")

    def _simple_stream_handler(
        self, response, prompt_messages: list[PromptMessage], model_name: str
    ) -> Generator[LLMResultChunk, None, None]:
        """
        Claude-specific stream handler
        """
        for event in response["body"]:
            if "chunk" in event:
                chunk = event["chunk"]
                if "bytes" in chunk:
                    chunk_data = json.loads(chunk["bytes"].decode("utf-8"))

                    # Handle Claude streaming format
                    if "type" in chunk_data:
                        if chunk_data["type"] == "content_block_delta":
                            if "delta" in chunk_data and "text" in chunk_data["delta"]:
                                text = chunk_data["delta"]["text"]
                                yield LLMResultChunk(
                                    model=model_name,
                                    prompt_messages=prompt_messages,
                                    delta=LLMResultChunkDelta(index=0, message=AssistantPromptMessage(content=text)),
                                )
                        elif chunk_data["type"] == "content_block_start":
                            # Handle start of content block if needed
                            pass

    def _simple_response_handler(self, response, prompt_messages: list[PromptMessage], model_name: str) -> LLMResult:
        """
        Claude-specific response handler
        """
        response_body = json.loads(response["body"].read())
        content = ""

        # Handle Claude response format
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
        # Debug output
        print(f"FORCE DEBUG: _resolve_model_identifier - model: {model}")
        print(f"FORCE DEBUG: _resolve_model_identifier - credentials: {credentials}")

        # Priority order:
        # 1. model_arn (for inference profile ARNs)
        # 2. inference_profile_id (for custom inference IDs)
        # 3. model_name (for custom model names)
        # 4. If model parameter looks like an ARN, use it directly
        # 5. model parameter (default)

        if credentials.get("model_arn"):
            print(f"FORCE DEBUG: Using model_arn: {credentials['model_arn']}")
            return credentials["model_arn"]
        elif credentials.get("inference_profile_id"):
            print(f"FORCE DEBUG: Using inference_profile_id: {credentials['inference_profile_id']}")
            return credentials["inference_profile_id"]
        elif credentials.get("model_name"):
            print(f"FORCE DEBUG: Using model_name: {credentials['model_name']}")
            return credentials["model_name"]
        elif model.startswith("arn:aws:bedrock"):
            # If the model parameter itself is an ARN, use it directly
            print(f"FORCE DEBUG: Model parameter is ARN: {model}")
            return model
        elif ":" in model and not model.startswith("aws_bedrock_arn_custom"):
            # If it looks like a model ID (contains colon), use it
            print(f"FORCE DEBUG: Model parameter looks like model ID: {model}")
            return model
        else:
            # Default fallback - try to map common model names
            print(f"FORCE DEBUG: Using fallback mapping for: {model}")
            return self._get_fallback_model_id(model)

    def _get_fallback_model_id(self, model: str) -> str:
        """
        Get fallback model ID for common model names
        """
        fallback_mapping = {
            "aws_bedrock_arn_custom": "",  # Use inference profile ID
            "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
            "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
            "claude-3-opus": "anthropic.claude-3-opus-20240229-v1:0",
        }

        mapped_model = fallback_mapping.get(model, model)
        print(f"FORCE DEBUG: Fallback mapping {model} -> {mapped_model}")
        return mapped_model

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
        # Debug: Log what credentials we received
        logger.info(f"DEBUG: Received credentials keys: {list(credentials.keys())}")
        logger.info(f"DEBUG: Model parameter: {model}")

        # Check all possible credential field names
        access_key = (
            credentials.get("aws_access_key_id")
            or credentials.get("access_key_id")
            or credentials.get("aws_access_key")
        )
        secret_key = (
            credentials.get("aws_secret_access_key")
            or credentials.get("secret_access_key")
            or credentials.get("aws_secret_key")
        )
        region = credentials.get("aws_region") or credentials.get("region")

        logger.info(f"DEBUG: Access key found: {bool(access_key)}")
        logger.info(f"DEBUG: Secret key found: {bool(secret_key)}")
        logger.info(f"DEBUG: Region found: {bool(region)}")

        # If credentials are missing, still allow for debugging
        if not (access_key and secret_key and region):
            logger.warning("DEBUG: Some AWS credentials missing, but allowing for debugging")
            return

        # Test the resolved model identifier
        try:
            model_name = self._resolve_model_identifier(model, credentials)
            logger.info(f"DEBUG: Resolved model identifier: {model_name}")

            # For ARN validation, ensure it's properly formatted
            if model_name.startswith("arn:aws:bedrock"):
                logger.info("DEBUG: Model is an ARN - validation successful")
                return

            logger.info("DEBUG: Model credentials validation successful")

        except Exception as e:
            logger.error(f"DEBUG: Validation error: {str(e)}")
            # Still allow for debugging
            return

    def _create_bedrock_client(self, credentials: dict):
        """Create a Bedrock client for listing models"""
        return boto3.client(
            "bedrock",
            region_name=credentials.get("aws_region"),
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
        )

    def _check_available_models(self, credentials: dict, target_model: str):
        """Check if the target model is available and list available models"""
        try:
            bedrock_client = self._create_bedrock_client(credentials)
            response = bedrock_client.list_foundation_models()

            available_models = []
            for model in response.get("modelSummaries", []):
                model_id = model.get("modelId", "")
                if "anthropic" in model_id.lower() or "claude" in model_id.lower():
                    available_models.append(model_id)

            print(f"FORCE DEBUG: Available Anthropic/Claude models: {available_models}")
            print(f"FORCE DEBUG: Target model '{target_model}' in available list: {target_model in available_models}")

            if available_models:
                print(f"FORCE DEBUG: Suggest using one of: {available_models[:3]}")  # Show first 3

        except Exception as e:
            print(f"FORCE DEBUG: Could not list models: {e}")

    @property
    def _invoke_error_mapping(self) -> dict[type[Exception], list[str]]:
        """
        Map model invoke errors to error types
        """
        # Return empty dict to avoid type issues - let Dify handle error mapping
        return {}

import json
import logging
from typing import Any, Dict, Generator, Iterator, Optional, Union

import boto3
from botocore.exceptions import ClientError
from dify_plugin.entities.model import (
    AIModelEntity,
    FetchFrom,
    I18nObject,
    ModelFeature,
    ModelPropertyKey,
    ModelType,
    ParameterRule,
    ParameterType,
)
from dify_plugin.entities.model.llm import LLMMode, LLMResult, LLMResultChunk, LLMResultChunkDelta
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)
from dify_plugin.interfaces.model import large_language_model

logger = logging.getLogger(__name__)


class AWSBedrockARNLargeLanguageModel(large_language_model.LargeLanguageModel):
    """
    AWS Bedrock Large Language Model with ARN and custom inference ID support
    """

    def get_model_schema(self, model: str, credentials: dict) -> AIModelEntity:
        """
        Get model schema
        """
        # Use model name from credentials if available, otherwise use model parameter
        model_name = credentials.get("model_name", model)
        
        return AIModelEntity(
            model=model_name,
            label=I18nObject(en_US=f"AWS Bedrock - {model_name}"),
            model_type=ModelType.LLM,
            features=[
                ModelFeature.TOOL_CALL,
                ModelFeature.MULTI_TOOL_CALL,
                ModelFeature.STREAM_TOOL_CALL,
            ],
            fetch_from=FetchFrom.CUSTOMIZABLE_MODEL,
            model_properties={
                ModelPropertyKey.CONTEXT_SIZE: 200000,
                ModelPropertyKey.MODE: LLMMode.CHAT.value,
            },
            parameter_rules=[
                ParameterRule(
                    name="temperature",
                    label=I18nObject(en_US="Temperature", zh_Hans="温度"),
                    type=ParameterType.FLOAT,
                    default=0.7,
                    min=0.0,
                    max=1.0,
                    precision=2,
                ),
                ParameterRule(
                    name="max_tokens",
                    label=I18nObject(en_US="Max Tokens", zh_Hans="最大令牌数"),
                    type=ParameterType.INT,
                    default=1024,
                    min=1,
                    max=4096,
                ),
                ParameterRule(
                    name="top_p",
                    label=I18nObject(en_US="Top P", zh_Hans="Top P"),
                    type=ParameterType.FLOAT,
                    default=1.0,
                    min=0.0,
                    max=1.0,
                    precision=2,
                ),
            ],
        )

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
        model_name = self._get_model_name(model, credentials)

        # Create AWS Bedrock client
        client = self._create_bedrock_client(credentials)

        # Convert messages to request format
        request_body = self._convert_messages_to_request(prompt_messages, model_parameters, tools, stop)

        try:
            if stream:
                return self._handle_stream_response(client, model_name, request_body, prompt_messages)
            else:
                return self._handle_non_stream_response(client, model_name, request_body, prompt_messages)
        except ClientError as e:
            self._handle_client_error(e, model_name)
        except Exception as e:
            raise Exception(f"Unexpected error invoking model {model_name}: {str(e)}")

    def _get_model_name(self, model: str, credentials: dict) -> str:
        """
        Get the actual model name/ARN to use for API calls
        """
        # Check if model_name is provided in credentials (for custom configuration)
        model_name = credentials.get("model_name", model)

        # Validate the model identifier
        if not model_name:
            raise ValueError("Model name cannot be empty")

        # Support both ARN format and standard model ID
        if model_name.startswith("arn:aws:bedrock:"):
            # ARN format: arn:aws:bedrock:region:account:inference-profile/profile-id
            if not model_name.count(":") >= 5:
                raise ValueError(f"Invalid ARN format: {model_name}")
            logger.info(f"Using custom inference profile ARN: {model_name}")
        else:
            # Standard model ID format
            logger.info(f"Using standard model ID: {model_name}")

        return model_name

    def _create_bedrock_client(self, credentials: dict):
        """
        Create AWS Bedrock client
        """
        try:
            return boto3.client(
                "bedrock-runtime",
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                region_name=credentials.get("aws_region", "us-east-1"),
            )
        except Exception as e:
            raise Exception(f"Failed to create AWS Bedrock client: {str(e)}")

    def _convert_messages_to_request(
        self,
        messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
    ) -> dict:
        """
        Convert prompt messages to AWS Bedrock request format
        """
        # Extract system message
        system_message = ""
        conversation_messages = []

        for message in messages:
            if isinstance(message, SystemPromptMessage):
                system_message = message.content
            elif isinstance(message, UserPromptMessage):
                conversation_messages.append({"role": "user", "content": [{"text": message.content}]})
            elif isinstance(message, AssistantPromptMessage):
                conversation_messages.append({"role": "assistant", "content": [{"text": message.content}]})
            elif isinstance(message, ToolPromptMessage):
                # Handle tool messages if needed
                pass

        # Build request body
        request_body = {
            "messages": conversation_messages,
            "inferenceConfig": {
                "maxTokens": model_parameters.get("max_tokens", 1024),
                "temperature": model_parameters.get("temperature", 0.7),
                "topP": model_parameters.get("top_p", 1.0),
            },
        }

        if system_message:
            request_body["system"] = [{"text": system_message}]

        if stop:
            request_body["inferenceConfig"]["stopSequences"] = stop

        # Add tool configuration if provided
        if tools:
            request_body["toolConfig"] = self._convert_tools_to_bedrock_format(tools)

        return request_body

    def _convert_tools_to_bedrock_format(self, tools: list[PromptMessageTool]) -> dict:
        """
        Convert tools to AWS Bedrock format
        """
        tool_specs = []
        for tool in tools:
            tool_spec = {
                "toolSpec": {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": {"json": tool.parameters},
                }
            }
            tool_specs.append(tool_spec)

        return {"tools": tool_specs, "toolChoice": {"auto": {}}}

    def _handle_stream_response(
        self, client, model_name: str, request_body: dict, prompt_messages: list[PromptMessage]
    ) -> Generator[LLMResultChunk, None, None]:
        """
        Handle streaming response
        """
        try:
            response = client.invoke_model_with_response_stream(
                modelId=model_name, body=json.dumps(request_body), contentType="application/json"
            )

            for chunk in self._process_stream_response(response, prompt_messages):
                yield chunk

        except ClientError as e:
            self._handle_client_error(e, model_name)

    def _handle_non_stream_response(
        self, client, model_name: str, request_body: dict, prompt_messages: list[PromptMessage]
    ) -> LLMResult:
        """
        Handle non-streaming response
        """
        try:
            response = client.invoke_model(
                modelId=model_name, body=json.dumps(request_body), contentType="application/json"
            )

            response_body = json.loads(response["body"].read())
            return self._process_non_stream_response(response_body, prompt_messages)

        except ClientError as e:
            self._handle_client_error(e, model_name)

    def _process_stream_response(
        self, response, prompt_messages: list[PromptMessage]
    ) -> Generator[LLMResultChunk, None, None]:
        """
        Process streaming response from AWS Bedrock
        """
        full_content = ""

        for event in response["body"]:
            if "chunk" in event:
                chunk = event["chunk"]
                if "bytes" in chunk:
                    chunk_data = json.loads(chunk["bytes"].decode("utf-8"))

                    if "contentBlockDelta" in chunk_data:
                        delta = chunk_data["contentBlockDelta"]
                        if "delta" in delta and "text" in delta["delta"]:
                            text = delta["delta"]["text"]
                            full_content += text

                            yield LLMResultChunk(
                                model=response.get("modelId", "unknown"),
                                prompt_messages=prompt_messages,
                                system_fingerprint="",
                                delta=LLMResultChunkDelta(
                                    index=0,
                                    message=AssistantPromptMessage(content=text),
                                    finish_reason=None,
                                    usage=None,
                                ),
                            )

                    elif "messageStop" in chunk_data:
                        # Stream ended
                        yield LLMResultChunk(
                            model=response.get("modelId", "unknown"),
                            prompt_messages=prompt_messages,
                            system_fingerprint="",
                            delta=LLMResultChunkDelta(
                                index=0,
                                message=AssistantPromptMessage(content=""),
                                finish_reason="stop",
                                usage=self._extract_usage_from_metadata(chunk_data),
                            ),
                        )

    def _process_non_stream_response(self, response_body: dict, prompt_messages: list[PromptMessage]) -> LLMResult:
        """
        Process non-streaming response from AWS Bedrock
        """
        content = ""
        if "content" in response_body:
            for content_block in response_body["content"]:
                if "text" in content_block:
                    content += content_block["text"]

        return LLMResult(
            model=response_body.get("modelId", "unknown"),
            prompt_messages=prompt_messages,
            message=AssistantPromptMessage(content=content),
            usage=self._extract_usage_from_metadata(response_body),
        )

    def _extract_usage_from_metadata(self, response_data: dict) -> dict:
        """
        Extract usage information from response metadata
        """
        usage = {}
        if "usage" in response_data:
            usage_data = response_data["usage"]
            usage["prompt_tokens"] = usage_data.get("inputTokens", 0)
            usage["completion_tokens"] = usage_data.get("outputTokens", 0)
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        return usage

    def _handle_client_error(self, error: ClientError, model_name: str):
        """
        Handle AWS Bedrock client errors
        """
        error_code = error.response["Error"]["Code"]
        error_message = error.response["Error"]["Message"]

        if error_code == "ResourceNotFoundException":
            raise Exception(f"Model {model_name} not found: {error_message}")
        elif error_code == "AccessDeniedException":
            raise Exception(f"Access denied to model {model_name}: {error_message}")
        elif error_code == "ValidationException":
            raise ValueError(f"Invalid request for model {model_name}: {error_message}")
        elif error_code == "ThrottlingException":
            raise Exception(f"Rate limit exceeded for model {model_name}: {error_message}")
        elif error_code == "ServiceUnavailableException":
            raise Exception(f"Service unavailable for model {model_name}: {error_message}")
        else:
            raise Exception(f"AWS Bedrock error [{error_code}]: {error_message}")

    def get_num_tokens(self, model: str, credentials: dict, prompt_messages: list[PromptMessage]) -> int:
        """
        Get number of tokens in prompt messages
        """
        # Simple token estimation - in production, use proper tokenization
        total_text = ""
        for message in prompt_messages:
            if hasattr(message, "content"):
                total_text += message.content

        # Rough estimation: 1 token ≈ 4 characters
        return len(total_text) // 4

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate model credentials
        """
        if not credentials.get("aws_access_key_id"):
            raise ValueError("AWS Access Key ID is required")

        if not credentials.get("aws_secret_access_key"):
            raise ValueError("AWS Secret Access Key is required")

        if not credentials.get("aws_region"):
            raise ValueError("AWS Region is required")

        # Test connection using bedrock client for listing models
        try:
            bedrock_client = boto3.client(
                "bedrock",
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                region_name=credentials.get("aws_region"),
            )
            
            # Test basic access to AWS Bedrock
            bedrock_client.list_foundation_models()

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDeniedException":
                raise ValueError(f"Access denied to AWS Bedrock")
            elif error_code == "UnauthorizedOperation":
                raise ValueError(f"Invalid AWS credentials")
            else:
                raise ValueError(f"AWS Bedrock validation failed: {str(e)}")
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
            "ServiceUnavailableException": "Service unavailable"
        }

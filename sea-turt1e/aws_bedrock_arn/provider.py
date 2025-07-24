import logging
import re
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from core.model_runtime.entities.model_entities import ModelType
from core.model_runtime.entities.provider_entities import ProviderRuntime, ProviderRuntimeType
from core.model_runtime.errors.invoke import (
    InvokeAuthorizationError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)
from core.model_runtime.model_providers.__base.model_provider import ModelProvider

logger = logging.getLogger(__name__)


class AWSBedrockARNProvider(ModelProvider):
    """
    AWS Bedrock model provider with ARN and custom inference ID support
    """

    def get_provider_runtime(self) -> ProviderRuntime:
        """
        Get provider runtime
        """
        return ProviderRuntime(
            type=ProviderRuntimeType.REMOTE,
            name="aws_bedrock_arn",
            description={
                "en_US": "AWS Bedrock with ARN and custom inference ID support",
                "zh_Hans": "支持ARN和自定义推理ID的AWS Bedrock",
            },
            icon_small={"en_US": "bedrock.svg", "zh_Hans": "bedrock.svg"},
            icon_large={"en_US": "bedrock.svg", "zh_Hans": "bedrock.svg"},
            help={
                "en_US": {
                    "title": "AWS Bedrock ARN Provider",
                    "description": "Supports both standard model IDs and custom inference profile ARNs for cost allocation tags",
                    "link": "https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html",
                },
                "zh_Hans": {
                    "title": "AWS Bedrock ARN 提供商",
                    "description": "支持标准模型ID和自定义推理配置文件ARN以实现成本分配标签",
                    "link": "https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html",
                },
            },
            supported_model_types=[ModelType.LLM],
            configurate_methods=["customizable-model"],
            provider_credential_schema=None,
            model_credential_schema=None,
        )

    def validate_provider_credentials(self, credentials: dict) -> None:
        """
        Validate provider credentials
        """
        try:
            client = boto3.client(
                "bedrock-runtime",
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                region_name=credentials.get("aws_region"),
            )

            # Test connection by listing foundation models
            try:
                client.list_foundation_models()
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "UnauthorizedOperation":
                    raise InvokeAuthorizationError("Invalid AWS credentials")
                elif error_code == "AccessDenied":
                    raise InvokeAuthorizationError("Access denied to AWS Bedrock")
                else:
                    raise InvokeConnectionError(f"AWS Bedrock connection error: {str(e)}")

        except NoCredentialsError:
            raise InvokeAuthorizationError("AWS credentials not found")
        except Exception as e:
            raise InvokeConnectionError(f"Failed to connect to AWS Bedrock: {str(e)}")

    def validate_model_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate model credentials
        """
        model_name = credentials.get("model_name", model)

        # Validate model name or ARN format
        if not self._is_valid_model_identifier(model_name):
            raise InvokeError(f"Invalid model identifier: {model_name}")

        # Validate AWS credentials
        self.validate_provider_credentials(credentials)

        # Test model access
        try:
            client = boto3.client(
                "bedrock-runtime",
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                region_name=credentials.get("aws_region"),
            )

            # Try to get model info (this will fail if model doesn't exist or no access)
            response = client.invoke_model(
                modelId=model_name, body='{"prompt": "test", "maxTokens": 1}', contentType="application/json"
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                raise InvokeError(f"Model not found: {model_name}")
            elif error_code == "AccessDeniedException":
                raise InvokeAuthorizationError(f"Access denied to model: {model_name}")
            elif error_code == "ValidationException":
                # This is expected for test call with invalid body
                pass
            else:
                raise InvokeError(f"Model validation error: {str(e)}")
        except Exception as e:
            raise InvokeError(f"Failed to validate model: {str(e)}")

    def _is_valid_model_identifier(self, identifier: str) -> bool:
        """
        Check if the identifier is a valid model ID or ARN
        """
        if not identifier:
            return False

        # Check for ARN format first
        arn_pattern = r"^arn:aws:bedrock:[^:]+:\d{12}:inference-profile/[^/]+$"
        if re.match(arn_pattern, identifier):
            return True

        # If it starts with 'arn:' but doesn't match the full pattern, it's invalid
        if identifier.startswith("arn:"):
            return False

        # Check for standard model ID format (includes colons for version numbers)
        model_id_pattern = r"^[a-zA-Z0-9\-\._:]+$"
        if re.match(model_id_pattern, identifier):
            return True

        return False

    def get_model_instance(self, model_type: ModelType):
        """
        Get model instance
        """
        if model_type == ModelType.LLM:
            from .models.llm import AWSBedrockARNLargeLanguageModel

            return AWSBedrockARNLargeLanguageModel()
        else:
            raise NotImplementedError(f"Model type {model_type} is not supported")

    def get_customizable_model_schema(self, model: str, credentials: dict) -> dict:
        """
        Get customizable model schema
        """
        return {
            "model": model,
            "label": {"en_US": model, "zh_Hans": model},
            "model_type": ModelType.LLM,
            "features": ["stream", "non-stream"],
            "model_properties": {"context_size": 200000, "max_chunks": 1},
            "parameter_rules": [
                {
                    "name": "temperature",
                    "label": {"en_US": "Temperature", "zh_Hans": "温度"},
                    "type": "float",
                    "default": 0.7,
                    "min": 0.0,
                    "max": 1.0,
                    "precision": 2,
                },
                {
                    "name": "max_tokens",
                    "label": {"en_US": "Max Tokens", "zh_Hans": "最大令牌数"},
                    "type": "int",
                    "default": 1024,
                    "min": 1,
                    "max": 4096,
                },
                {
                    "name": "top_p",
                    "label": {"en_US": "Top P", "zh_Hans": "Top P"},
                    "type": "float",
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "precision": 2,
                },
            ],
        }

import logging
import re
from collections.abc import Mapping

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dify_plugin import ModelProvider
from dify_plugin.entities.model import ModelType
from dify_plugin.errors.model import CredentialsValidateFailedError

logger = logging.getLogger(__name__)


class AwsPluginV2ModelProvider(ModelProvider):
    def validate_provider_credentials(self, credentials: Mapping) -> None:
        """
        Validate provider credentials
        if validate failed, raise exception

        :param credentials: provider credentials, credentials form defined in `provider_credential_schema`.
        """
        try:
            # Use bedrock client for listing models (not bedrock-runtime)
            bedrock_client = boto3.client(
                "bedrock",
                aws_access_key_id=credentials.get("aws_access_key_id"),
                aws_secret_access_key=credentials.get("aws_secret_access_key"),
                region_name=credentials.get("aws_region"),
            )

            # Test connection by listing foundation models
            try:
                bedrock_client.list_foundation_models()
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "UnauthorizedOperation":
                    raise CredentialsValidateFailedError("Invalid AWS credentials")
                elif error_code == "AccessDenied":
                    raise CredentialsValidateFailedError("Access denied to AWS Bedrock")
                else:
                    raise CredentialsValidateFailedError(f"AWS Bedrock connection error: {str(e)}")

        except NoCredentialsError:
            raise CredentialsValidateFailedError("AWS credentials not found")
        except CredentialsValidateFailedError as ex:
            raise ex
        except Exception as ex:
            logger.exception(
                f"{self.get_provider_schema().provider} credentials validate failed"
            )
            raise CredentialsValidateFailedError(f"Failed to connect to AWS Bedrock: {str(ex)}")

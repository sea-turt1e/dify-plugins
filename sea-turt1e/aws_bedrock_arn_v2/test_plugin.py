#!/usr/bin/env python3
"""
Test script for AWS Bedrock ARN plugin
This script helps verify the functionality of the AWS Bedrock ARN plugin.
"""

import json
import sys

from dify_plugin.entities.model.message import UserPromptMessage
from models.llm.llm import AWSBedrockARNLargeLanguageModel


def test_model_with_arn():
    """Test the model with ARN support"""

    # Initialize the model
    model = AWSBedrockARNLargeLanguageModel()

    # Example credentials for testing
    # Note: Replace with your actual credentials
    test_credentials = {
        "aws_access_key_id": "your_access_key_id",
        "aws_secret_access_key": "your_secret_access_key",
        "aws_region": "ap-northeast-1",
        # Option 1: Use standard model name
        "model_name": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        # Option 2: Use custom inference profile ARN
        # "model_arn": "arn:aws:bedrock:ap-northeast-1:123456789012:application-inference-profile/ps********",
        # Option 3: Use custom inference profile ID
        # "inference_profile_id": "ps********"
    }

    # Test messages
    test_messages = [UserPromptMessage(content="Hello, can you respond with a simple greeting?")]

    # Test model parameters
    test_parameters = {"max_tokens": 100, "temperature": 0.7, "top_p": 1.0}

    try:
        print("Testing credential validation...")
        model.validate_credentials("test-model", test_credentials)
        print("✅ Credentials validation passed")

        print("\nTesting model invocation...")
        result = model._invoke(
            model="test-model",
            credentials=test_credentials,
            prompt_messages=test_messages,
            model_parameters=test_parameters,
            stream=False,
        )

        print(f"✅ Model invocation successful")
        print(f"Response: {result.message.content}")

        print("\nTesting token counting...")
        token_count = model.get_num_tokens("test-model", test_credentials, test_messages)
        print(f"✅ Token count: {token_count}")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

    return True


def demonstrate_arn_usage():
    """Demonstrate different ways to use the plugin"""

    print("=== AWS Bedrock ARN Plugin Usage Examples ===\n")

    print("1. Standard Model Usage:")
    print("   Set model_name: 'anthropic.claude-3-5-sonnet-20240620-v1:0'\n")

    print("2. Custom Inference Profile ARN Usage:")
    print("   Set model_arn: 'arn:aws:bedrock:ap-northeast-1:123456789012:application-inference-profile/ps********'\n")

    print("3. Custom Inference Profile ID Usage:")
    print("   Set inference_profile_id: 'ps********'\n")

    print("Priority Order:")
    print("   1. model_arn (highest priority)")
    print("   2. inference_profile_id")
    print("   3. model_name")
    print("   4. model parameter (lowest priority)\n")

    print("To create a custom inference profile with cost allocation tags:")
    print("aws bedrock create-inference-profile --region 'ap-northeast-1' \\")
    print("  --inference-profile-name 'sample-profile-name' \\")
    print("  --description 'sample-profile-name' \\")
    print(
        '  --model-source \'{"copyFrom": "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"}\' \\'
    )
    print('  --tags \'[{"key": "CostAllocateTag","value": "sample"}]\'')


if __name__ == "__main__":
    print("AWS Bedrock ARN Plugin Test\n")

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demonstrate_arn_usage()
    else:
        print("Note: Update credentials in the script before running actual tests.")
        print("Run with 'demo' argument to see usage examples.")
        # Uncomment the line below to run actual tests (after setting credentials)
        # test_model_with_arn()

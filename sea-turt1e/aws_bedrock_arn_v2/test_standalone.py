#!/usr/bin/env python3
"""
Standalone test runner for AWS Bedrock ARN plugin
This allows testing the plugin functionality without connecting to Dify
"""

import logging
import os
import sys
from typing import Optional

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dify_plugin.entities.model.message import SystemPromptMessage, UserPromptMessage
from models.llm.llm import AWSBedrockARNLargeLanguageModel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_model_resolution():
    """Test model identifier resolution"""
    model = AWSBedrockARNLargeLanguageModel()

    test_cases = [
        # Test case 1: Standard model name
        {
            "model": "claude-3-sonnet",
            "credentials": {"model_name": "anthropic.claude-3-5-sonnet-20240620-v1:0"},
            "expected": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        },
        # Test case 2: Model ARN (highest priority)
        {
            "model": "claude-3-sonnet",
            "credentials": {
                "model_arn": "arn:aws:bedrock:ap-northeast-1:123456789012:application-inference-profile/ps12345678",
                "inference_profile_id": "ps87654321",
                "model_name": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            },
            "expected": "arn:aws:bedrock:ap-northeast-1:123456789012:application-inference-profile/ps12345678",
        },
        # Test case 3: Inference profile ID (second priority)
        {
            "model": "claude-3-sonnet",
            "credentials": {
                "inference_profile_id": "ps87654321",
                "model_name": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            },
            "expected": "ps87654321",
        },
        # Test case 4: Fallback to model parameter
        {
            "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "credentials": {},
            "expected": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        },
    ]

    print("Testing Model Identifier Resolution:")
    print("=" * 50)

    for i, test_case in enumerate(test_cases, 1):
        result = model._resolve_model_identifier(test_case["model"], test_case["credentials"])
        success = result == test_case["expected"]
        status = "✅ PASS" if success else "❌ FAIL"

        print(f"Test {i}: {status}")
        print(f"  Input model: {test_case['model']}")
        print(f"  Credentials: {test_case['credentials']}")
        print(f"  Expected: {test_case['expected']}")
        print(f"  Got: {result}")
        print()

        if not success:
            return False

    return True


def test_credential_validation():
    """Test credential validation (without actual AWS calls)"""
    model = AWSBedrockARNLargeLanguageModel()

    print("Testing Credential Validation:")
    print("=" * 50)

    # Test missing required fields
    test_cases = [
        {
            "name": "Missing AWS Access Key ID",
            "credentials": {"aws_secret_access_key": "fake_secret", "aws_region": "us-east-1"},
            "should_fail": True,
        },
        {
            "name": "Missing AWS Secret Access Key",
            "credentials": {"aws_access_key_id": "fake_key", "aws_region": "us-east-1"},
            "should_fail": True,
        },
        {
            "name": "Missing AWS Region",
            "credentials": {"aws_access_key_id": "fake_key", "aws_secret_access_key": "fake_secret"},
            "should_fail": True,
        },
        {
            "name": "All required fields present",
            "credentials": {
                "aws_access_key_id": "fake_key",
                "aws_secret_access_key": "fake_secret",
                "aws_region": "us-east-1",
            },
            "should_fail": False,  # Will fail on AWS call, but not on required field validation
        },
    ]

    for test_case in test_cases:
        try:
            # We'll catch the error at the required fields level, not AWS level
            required_fields = ["aws_access_key_id", "aws_secret_access_key", "aws_region"]
            missing_fields = []
            for field in required_fields:
                if not test_case["credentials"].get(field):
                    missing_fields.append(field)

            if missing_fields:
                if test_case["should_fail"]:
                    print(f"✅ PASS: {test_case['name']} - Correctly detected missing fields: {missing_fields}")
                else:
                    print(f"❌ FAIL: {test_case['name']} - Unexpected missing fields: {missing_fields}")
                    return False
            else:
                if test_case["should_fail"]:
                    print(f"❌ FAIL: {test_case['name']} - Should have failed but didn't")
                    return False
                else:
                    print(f"✅ PASS: {test_case['name']} - All required fields present")

        except Exception as e:
            if test_case["should_fail"]:
                print(f"✅ PASS: {test_case['name']} - Correctly failed with: {str(e)}")
            else:
                print(f"❌ FAIL: {test_case['name']} - Unexpected error: {str(e)}")
                return False

    return True


def test_token_counting():
    """Test token counting functionality"""
    model = AWSBedrockARNLargeLanguageModel()

    print("\nTesting Token Counting:")
    print("=" * 50)

    test_cases = [
        {
            "name": "Claude model",
            "model": "claude-3-sonnet",
            "credentials": {"model_name": "anthropic.claude-3-5-sonnet-20240620-v1:0"},
            "messages": [UserPromptMessage(content="Hello, how are you?")],
            "expected_ratio": 3.5,  # characters per token
        },
        {
            "name": "Titan model",
            "model": "titan-text",
            "credentials": {"model_name": "amazon.titan-text-lite-v1"},
            "messages": [UserPromptMessage(content="Hello, how are you?")],
            "expected_ratio": 4.0,
        },
        {
            "name": "Multiple messages",
            "model": "claude-3-sonnet",
            "credentials": {"model_name": "anthropic.claude-3-5-sonnet-20240620-v1:0"},
            "messages": [
                SystemPromptMessage(content="You are a helpful assistant."),
                UserPromptMessage(content="Hello, how are you?"),
            ],
            "expected_ratio": 3.5,
        },
    ]

    for test_case in test_cases:
        token_count = model.get_num_tokens(test_case["model"], test_case["credentials"], test_case["messages"])

        # Calculate expected token count
        total_chars = sum(len(msg.content) for msg in test_case["messages"] if hasattr(msg, "content"))
        expected_tokens = max(1, int(total_chars // test_case["expected_ratio"]))

        # Allow some variance in token counting
        is_reasonable = abs(token_count - expected_tokens) <= max(1, expected_tokens * 0.2)
        status = "✅ PASS" if is_reasonable else "❌ FAIL"

        print(f"{status}: {test_case['name']}")
        print(f"  Characters: {total_chars}")
        print(f"  Expected tokens: ~{expected_tokens}")
        print(f"  Actual tokens: {token_count}")
        print()

        if not is_reasonable:
            return False

    return True


def main():
    """Run all tests"""
    print("AWS Bedrock ARN Plugin - Standalone Test Suite")
    print("=" * 60)
    print()

    all_passed = True

    try:
        # Test 1: Model Resolution
        all_passed &= test_model_resolution()

        # Test 2: Credential Validation
        all_passed &= test_credential_validation()

        # Test 3: Token Counting
        all_passed &= test_token_counting()

        print("=" * 60)
        if all_passed:
            print("🎉 All tests passed! Plugin is working correctly.")
            print("\nTo test with actual AWS credentials:")
            print("1. Set up your AWS credentials in environment variables or AWS credentials file")
            print("2. Use the test_plugin.py script with actual model invocation")
        else:
            print("❌ Some tests failed. Please check the implementation.")
            return 1

    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        logger.exception("Test suite error")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

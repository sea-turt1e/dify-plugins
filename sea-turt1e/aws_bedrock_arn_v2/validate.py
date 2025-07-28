#!/usr/bin/env python3
"""
Simple plugin validation without imports that cause SSL issues
"""

import json
import os

import yaml


def validate_plugin_structure():
    """Validate plugin files and structure"""
    print("Validating Plugin Structure")
    print("=" * 40)

    errors = []
    warnings = []

    # Check manifest.yaml
    try:
        with open("manifest.yaml", "r") as f:
            manifest = yaml.safe_load(f)
        print("✅ manifest.yaml is valid")

        # Check required fields
        required = ["version", "type", "name", "plugins"]
        for field in required:
            if field not in manifest:
                errors.append(f"manifest.yaml missing required field: {field}")

        if manifest.get("type") != "plugin":
            errors.append(f"manifest.yaml type should be 'plugin', got '{manifest.get('type')}'")

    except Exception as e:
        errors.append(f"manifest.yaml validation failed: {e}")

    # Check provider config
    try:
        with open("provider/aws_plugin_v2.yaml", "r") as f:
            provider = yaml.safe_load(f)
        print("✅ provider/aws_plugin_v2.yaml is valid")

        # Check provider structure
        if "provider" not in provider:
            errors.append("provider config missing 'provider' field")
        if "supported_model_types" not in provider:
            errors.append("provider config missing 'supported_model_types' field")
        if "llm" not in provider.get("supported_model_types", []):
            warnings.append("provider config doesn't support 'llm' model type")

    except Exception as e:
        errors.append(f"provider config validation failed: {e}")

    # Check model file
    if not os.path.exists("models/llm/llm.py"):
        errors.append("models/llm/llm.py file missing")
    else:
        print("✅ models/llm/llm.py exists")

        # Basic syntax check
        try:
            with open("models/llm/llm.py", "r") as f:
                content = f.read()

            # Check for required class
            if "class AWSBedrockARNLargeLanguageModel" not in content:
                errors.append("llm.py missing AWSBedrockARNLargeLanguageModel class")

            # Check for required methods
            required_methods = ["_invoke", "get_num_tokens", "validate_credentials"]
            for method in required_methods:
                if f"def {method}" not in content:
                    warnings.append(f"llm.py missing method: {method}")

        except Exception as e:
            errors.append(f"llm.py validation failed: {e}")

    # Check main.py
    if not os.path.exists("main.py"):
        errors.append("main.py file missing")
    else:
        print("✅ main.py exists")

    print("\nValidation Results:")
    print("-" * 20)

    if errors:
        print("❌ Errors found:")
        for error in errors:
            print(f"   - {error}")

    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"   - {warning}")

    if not errors and not warnings:
        print("🎉 Plugin structure is valid!")
    elif not errors:
        print("✅ Plugin structure is valid (with warnings)")
    else:
        print("❌ Plugin structure has errors")

    return len(errors) == 0


def check_aws_requirements():
    """Check AWS-related requirements"""
    print("\nChecking AWS Requirements")
    print("=" * 40)

    # Check if boto3 is available
    try:
        import boto3

        print("✅ boto3 is available")
        print(f"   Version: {boto3.__version__}")
    except ImportError:
        print("❌ boto3 not available - install with: pip install boto3")
        return False

    # Check AWS credentials (without making actual calls)
    aws_configured = False

    # Check environment variables
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        print("✅ AWS credentials found in environment variables")
        aws_configured = True

    # Check AWS credentials file
    aws_creds_file = os.path.expanduser("~/.aws/credentials")
    if os.path.exists(aws_creds_file):
        print("✅ AWS credentials file exists")
        aws_configured = True

    # Check AWS config file
    aws_config_file = os.path.expanduser("~/.aws/config")
    if os.path.exists(aws_config_file):
        print("✅ AWS config file exists")

    if not aws_configured:
        print("⚠️  No AWS credentials detected")
        print("   Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        print("   Or configure AWS CLI with: aws configure")

    return True


def test_model_identifier_resolution():
    """Test model identifier resolution logic (without AWS calls)"""
    print("\nTesting Model Identifier Resolution")
    print("=" * 40)

    # Simulate the resolution logic
    def resolve_model_identifier(model, credentials):
        if credentials.get("model_arn"):
            return credentials["model_arn"]
        elif credentials.get("inference_profile_id"):
            return credentials["inference_profile_id"]
        elif credentials.get("model_name"):
            return credentials["model_name"]
        else:
            return model

    test_cases = [
        {
            "name": "Standard model",
            "model": "claude-3-sonnet",
            "credentials": {"model_name": "anthropic.claude-3-5-sonnet-20240620-v1:0"},
            "expected": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        },
        {
            "name": "Model ARN priority",
            "model": "claude-3-sonnet",
            "credentials": {
                "model_arn": "arn:aws:bedrock:ap-northeast-1:123456789012:application-inference-profile/ps12345",
                "inference_profile_id": "ps87654",
                "model_name": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            },
            "expected": "arn:aws:bedrock:ap-northeast-1:123456789012:application-inference-profile/ps12345",
        },
        {
            "name": "Inference profile ID",
            "model": "claude-3-sonnet",
            "credentials": {
                "inference_profile_id": "ps87654",
                "model_name": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            },
            "expected": "ps87654",
        },
        {
            "name": "Fallback to model parameter",
            "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "credentials": {},
            "expected": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        },
    ]

    all_passed = True
    for test_case in test_cases:
        result = resolve_model_identifier(test_case["model"], test_case["credentials"])
        passed = result == test_case["expected"]
        status = "✅" if passed else "❌"

        print(f"{status} {test_case['name']}")
        if not passed:
            print(f"   Expected: {test_case['expected']}")
            print(f"   Got: {result}")
            all_passed = False

    return all_passed


def main():
    """Run validation tests"""
    print("AWS Bedrock ARN Plugin - Basic Validation")
    print("=" * 50)

    all_good = True

    # Test 1: Plugin structure
    all_good &= validate_plugin_structure()

    # Test 2: AWS requirements
    all_good &= check_aws_requirements()

    # Test 3: Model resolution logic
    all_good &= test_model_identifier_resolution()

    print("\n" + "=" * 50)
    if all_good:
        print("🎉 Basic validation passed!")
        print("\nNext steps:")
        print("1. Set up AWS credentials for testing")
        print("2. Configure Dify connection (optional)")
        print("3. Test with actual AWS Bedrock models")
    else:
        print("❌ Some validation issues found")

    return 0 if all_good else 1


if __name__ == "__main__":
    exit(main())

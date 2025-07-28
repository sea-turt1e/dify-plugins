# AWS Bedrock ARN Plugin for Dify

**Author:** sea-turt1e  
**Version:** 0.0.1  
**Type:** Model Provider  

## Description

This plugin extends Dify's AWS Bedrock model provider to support **custom inference profile ARNs** and **inference profile IDs** for cost allocation and advanced model management, addressing GitHub issue [#13710](https://github.com/langgenius/dify/issues/13710).

## Features

- ✅ **ARN Support**: Use custom inference profile ARNs for cost allocation
- ✅ **Inference Profile ID Support**: Use custom inference profile IDs  
- ✅ **Standard Model IDs**: Backward compatibility with standard Bedrock model identifiers
- ✅ **Cost Allocation Tags**: Track costs by team, project, or environment through custom inference profiles
- ✅ **Enhanced Error Handling**: Detailed AWS Bedrock error messages
- ✅ **Multiple Regions**: Support for all AWS Bedrock regions
- ✅ **Streaming Support**: Both streaming and non-streaming responses

## Setup and Usage

### 1. AWS Credentials Configuration

Configure your AWS credentials in the model provider settings:

- **Access Key ID**: Your AWS access key ID
- **Secret Access Key**: Your AWS secret access key  
- **AWS Region**: The region where your models/inference profiles are located

### 2. Model Configuration Options

Choose one of the following when configuring a model:

#### Option A: Standard Model Name
```
Model Name/ID: anthropic.claude-3-5-sonnet-20240620-v1:0
```

#### Option B: Custom Inference Profile ARN
```
Model ARN: arn:aws:bedrock:ap-northeast-1:123456789012:application-inference-profile/ps********
```

#### Option C: Custom Inference Profile ID
```
Inference Profile ID: ps********
```

### 3. Priority Order

The plugin resolves model identifiers in this priority order:
1. **model_arn** (highest priority)
2. **inference_profile_id**  
3. **model_name**
4. **model parameter** (lowest priority)

## Creating Custom Inference Profiles

To create a custom inference profile with cost allocation tags:

```bash
# Create custom inference profile
aws bedrock create-inference-profile --region 'ap-northeast-1' \
  --inference-profile-name 'your-profile-name' \
  --description 'Description for your profile' \
  --model-source '{"copyFrom": "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"}' \
  --tags '[{"key": "CostAllocateTag","value": "your-tag-value"}]'

# List custom inference profiles  
aws bedrock list-inference-profiles --region 'ap-northeast-1' --type-equals 'APPLICATION'

# Test inference
aws bedrock-runtime converse --region ap-northeast-1 \
  --model-id "arn:aws:bedrock:ap-northeast-1:123456789012:application-inference-profile/ps********" \
  --messages '[{"role": "user", "content": [{"text": "Hello"}]}]'
```

## IAM Permissions

Ensure your AWS credentials have these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream", 
                "bedrock:ListFoundationModels",
                "bedrock:ListInferenceProfiles"
            ],
            "Resource": "*"
        }
    ]
}
```

## Troubleshooting

### Internal Server Error Solutions

1. **Verify ARN format**: Ensure ARNs are complete and valid
2. **Check IAM permissions**: Verify access to the specified model/inference profile  
3. **Confirm region settings**: Ensure region matches inference profile location
4. **Validate model existence**: Confirm the model/inference profile exists and is active

## Requirements

- Valid AWS credentials with Bedrock access
- boto3 Python library
- Dify plugin environment




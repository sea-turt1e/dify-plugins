# AWS Bedrock ARN Plugin

This plugin provides AWS Bedrock model provider support with ARN (Amazon Resource Name) and custom inference ID capabilities, addressing GitHub issue [#13710](https://github.com/langgenius/dify/issues/13710).

## Features

### ARN Support
- **Custom Inference Profiles**: Support for custom inference profile ARNs
- **Cost Allocation Tags**: Enable cost tracking and allocation through custom profiles
- **Standard Model IDs**: Backward compatibility with standard Bedrock model identifiers

### Model Identifier Formats

#### Standard Model ID
```
anthropic.claude-3-5-sonnet-20240620-v1:0
amazon.titan-text-lite-v1
```

#### Custom Inference Profile ARN
```
arn:aws:bedrock:us-east-1:123456789012:inference-profile/my-custom-profile
arn:aws:bedrock:ap-northeast-1:123456789012:inference-profile/sample-profile-name
```

## Configuration

### Provider Credentials
- **AWS Access Key ID**: Your AWS access key
- **AWS Secret Access Key**: Your AWS secret key
- **AWS Region**: AWS region where your models are deployed

### Model Configuration
- **Model Name/ARN**: Either a standard model ID or a custom inference profile ARN
- **Model Parameters**: Temperature, max tokens, top-p settings

## Usage Example

### Creating a Custom Inference Profile

Using AWS CLI to create a custom inference profile with cost allocation tags:

```bash
aws bedrock create-inference-profile \
  --region 'ap-northeast-1' \
  --inference-profile-name 'my-custom-profile' \
  --model-source '{"copyFrom": "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"}' \
  --tags '{"team": "ai-research", "project": "chatbot", "environment": "production"}'
```

### Using the Custom Profile in Dify

1. Install this plugin in your Dify instance
2. Configure the AWS Bedrock ARN provider with your credentials
3. Set the model name to your custom inference profile ARN:
   ```
   arn:aws:bedrock:ap-northeast-1:123456789012:inference-profile/my-custom-profile
   ```

## Benefits

### Cost Allocation
- **Detailed Billing**: Track costs per custom inference profile
- **Tag-based Reporting**: Use AWS Cost Explorer with your custom tags
- **Team/Project Allocation**: Separate costs by team, project, or environment

### Flexibility
- **Standard Models**: Use existing foundation models without changes
- **Custom Profiles**: Create specialized profiles for different use cases
- **Mixed Usage**: Use both standard and custom models in the same Dify instance

## Technical Implementation

### ARN Validation
The plugin validates ARN format to ensure proper structure:
```
arn:aws:bedrock:[region]:[account-id]:inference-profile/[profile-name]
```

### Error Handling
- **Model Not Found**: Clear error messages for invalid ARNs or model IDs
- **Access Denied**: Proper handling of IAM permission issues
- **Region Mismatch**: Validation of region consistency

### Security
- **Credential Validation**: Secure AWS credential handling
- **IAM Permissions**: Proper permission checks for model access
- **Error Sanitization**: No sensitive information in error messages

## Installation

1. Copy the plugin files to your Dify plugins directory
2. Install required dependencies:
   ```bash
   pip install boto3
   ```
3. Configure the plugin in Dify's model provider settings
4. Add your AWS credentials and select models/ARNs

## Requirements

- Python 3.8+
- boto3
- Valid AWS credentials with Bedrock access
- Dify plugin system support

## License

This plugin is provided under the same license as the Dify project.

## Privacy Policy

This plugin processes data according to the following privacy policy:

### Data Collection
- The plugin collects AWS credentials (Access Key ID, Secret Access Key) for authentication
- Model interaction data is processed through AWS Bedrock services
- No personal data is stored persistently by the plugin

### Data Usage
- Credentials are used solely for AWS Bedrock API authentication
- Model interactions are processed according to AWS Bedrock's privacy policy
- No data is shared with third parties beyond AWS services

### Data Security
- All credentials are handled securely and not logged
- Communication with AWS Bedrock uses encrypted connections
- No sensitive information is exposed in error messages

### User Rights
- Users can revoke access by removing their AWS credentials
- All data processing stops immediately upon credential removal

## Support

For issues related to this plugin, please refer to the original GitHub issue [#13710](https://github.com/langgenius/dify/issues/13710) or create a new issue in the Dify repository.
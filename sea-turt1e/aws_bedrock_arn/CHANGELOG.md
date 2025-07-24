# Changelog

## [0.1.0] - 2025-01-16

### Added
- Initial release of AWS Bedrock ARN plugin
- Support for both standard model IDs and custom inference profile ARNs
- Cost allocation tags capability through custom inference profiles
- ARN format validation with proper error handling
- Streaming and non-streaming response support
- Comprehensive test coverage

### Features
- **ARN Support**: Full support for `arn:aws:bedrock:region:account:inference-profile/profile-id` format
- **Backward Compatibility**: Maintains support for standard model IDs like `anthropic.claude-3-5-sonnet-20240620-v1:0`
- **Cost Allocation**: Enables AWS cost allocation tags for better billing tracking
- **Error Handling**: Proper validation and error messages for invalid identifiers
- **Security**: Secure credential handling with IAM permission validation

### Technical Details
- Model identifier validation with regex patterns
- AWS Bedrock API integration with boto3
- Streaming response processing
- Token usage tracking
- Region-aware configuration

### Addresses
- GitHub Issue #13710: Support for ARN and custom inference ID in AWS Bedrock provider
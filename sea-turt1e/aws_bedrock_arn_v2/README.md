## AWS Bedrock ARN Plugin

**Author:** sea-turt1e
**Version:** 0.0.1
**Type:** model

### Description

This plugin provides AWS Bedrock model provider support with ARN (Amazon Resource Name) and custom inference ID capabilities, addressing GitHub issue [#13710](https://github.com/langgenius/dify/issues/13710).

### Features

- **ARN Support**: Use custom inference profile ARNs for cost allocation
- **Standard Model IDs**: Backward compatibility with standard Bedrock model identifiers
- **Cost Allocation Tags**: Track costs by team, project, or environment
- **Multiple Regions**: Support for all AWS Bedrock regions

### Usage

1. Configure your AWS credentials in the provider settings
2. Use either standard model IDs or custom inference profile ARNs:
   - Standard: `anthropic.claude-3-5-sonnet-20240620-v1:0`
   - ARN: `arn:aws:bedrock:us-east-1:123456789012:inference-profile/my-profile`

### Requirements

- Valid AWS credentials with Bedrock access
- boto3 Python library




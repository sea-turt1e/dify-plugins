#!/bin/bash

# AWS Bedrock ARN Plugin - Development Scripts

show_help() {
    echo "AWS Bedrock ARN Plugin Development Helper"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  test         Run standalone tests (no AWS connection required)"
    echo "  run          Run the plugin in standalone mode"
    echo "  check        Check plugin configuration and dependencies"
    echo "  validate     Validate plugin structure"
    echo "  help         Show this help message"
    echo ""
    echo "Environment Setup:"
    echo "  Copy .env.example to .env and configure your settings"
    echo "  For Dify connection: set DIFY_API_KEY, DIFY_HOST, DIFY_PORT"
    echo "  For AWS testing: set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION"
}

run_tests() {
    echo "Running standalone tests..."
    python test_standalone.py
}

run_plugin() {
    echo "Running plugin..."
    if [ -f ".env" ]; then
        echo "Loading environment from .env file..."
        export $(cat .env | grep -v '^#' | xargs)
    fi
    python -m main
}

check_setup() {
    echo "Checking plugin setup..."
    echo ""
    
    # Check Python dependencies
    echo "Checking Python dependencies:"
    python -c "import boto3; print('✅ boto3 available')" 2>/dev/null || echo "❌ boto3 not available - run: pip install boto3"
    python -c "import dify_plugin; print('✅ dify_plugin available')" 2>/dev/null || echo "❌ dify_plugin not available"
    
    echo ""
    
    # Check configuration files
    echo "Checking configuration files:"
    [ -f "manifest.yaml" ] && echo "✅ manifest.yaml exists" || echo "❌ manifest.yaml missing"
    [ -f "provider/aws_plugin_v2.yaml" ] && echo "✅ provider config exists" || echo "❌ provider config missing"
    [ -f "models/llm/llm.py" ] && echo "✅ LLM model exists" || echo "❌ LLM model missing"
    [ -f ".env" ] && echo "✅ .env file exists" || echo "ℹ️  .env file not found (optional)"
    
    echo ""
    
    # Check environment variables
    echo "Checking environment variables:"
    [ -n "$DIFY_API_KEY" ] && echo "✅ DIFY_API_KEY set" || echo "ℹ️  DIFY_API_KEY not set (plugin will run in standalone mode)"
    [ -n "$AWS_ACCESS_KEY_ID" ] && echo "✅ AWS_ACCESS_KEY_ID set" || echo "ℹ️  AWS_ACCESS_KEY_ID not set (needed for AWS testing)"
    [ -n "$AWS_SECRET_ACCESS_KEY" ] && echo "✅ AWS_SECRET_ACCESS_KEY set" || echo "ℹ️  AWS_SECRET_ACCESS_KEY not set (needed for AWS testing)"
    [ -n "$AWS_DEFAULT_REGION" ] && echo "✅ AWS_DEFAULT_REGION set" || echo "ℹ️  AWS_DEFAULT_REGION not set (will use us-east-1 as default)"
}

validate_plugin() {
    echo "Validating plugin structure..."
    python -c "
import yaml
import json
import os

try:
    # Validate manifest.yaml
    with open('manifest.yaml', 'r') as f:
        manifest = yaml.safe_load(f)
    print('✅ manifest.yaml is valid YAML')
    
    # Check required fields
    required_fields = ['version', 'type', 'name', 'plugins']
    missing = [field for field in required_fields if field not in manifest]
    if missing:
        print(f'❌ manifest.yaml missing required fields: {missing}')
    else:
        print('✅ manifest.yaml has all required fields')
    
    # Validate provider config
    with open('provider/aws_plugin_v2.yaml', 'r') as f:
        provider = yaml.safe_load(f)
    print('✅ provider config is valid YAML')
    
    print('✅ Plugin structure validation passed')
    
except Exception as e:
    print(f'❌ Validation failed: {e}')
    "
}

case "$1" in
    "test")
        run_tests
        ;;
    "run")
        run_plugin
        ;;
    "check")
        check_setup
        ;;
    "validate")
        validate_plugin
        ;;
    "help"|"--help"|"-h"|"")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac

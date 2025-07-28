#!/bin/bash

# AWS Bedrock ARN Plugin - Dify Connection Setup

echo "Setting up Dify connection for AWS Bedrock ARN Plugin"
echo "=================================================="

echo ""
echo "Current plugin status: Running in standalone mode"
echo ""

echo "To connect to Dify, you need to:"
echo "1. Get a valid Dify API key from your Dify instance"
echo "2. Set the environment variables below"
echo "3. Restart the plugin"
echo ""

echo "Set these environment variables:"
echo "export DIFY_API_KEY=\"your_actual_api_key_here\""
echo "export DIFY_HOST=\"localhost\"  # or your Dify host"
echo "export DIFY_PORT=\"5001\"       # or your Dify port"
echo ""

echo "Or update the .env file:"
echo "DIFY_API_KEY=your_actual_api_key_here"
echo "DIFY_HOST=localhost"
echo "DIFY_PORT=5001"
echo ""

echo "Where to get your Dify API key:"
echo "- For local Dify: Check your Dify instance settings/admin panel"
echo "- For Dify Cloud: Check your account API settings"
echo "- For self-hosted: Check your deployment configuration"
echo ""

echo "Note: The plugin is working correctly in standalone mode!"
echo "The heartbeat messages indicate healthy operation."

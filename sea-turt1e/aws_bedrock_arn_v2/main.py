import os

from dify_plugin import DifyPluginEnv, Plugin

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment variables

# Create plugin with configuration from environment variables
# For development without Dify connection, don't set DIFY_API_KEY
plugin_env_config = {}

# Only add Dify connection config if API key is available
if os.getenv("DIFY_API_KEY"):
    plugin_env_config.update(
        {
            "DIFY_API_KEY": os.getenv("DIFY_API_KEY"),
            "DIFY_HOST": os.getenv("DIFY_HOST", "localhost"),
            "DIFY_PORT": int(os.getenv("DIFY_PORT", "5001")),
        }
    )

# Add timeout configuration
if os.getenv("MAX_REQUEST_TIMEOUT"):
    plugin_env_config["MAX_REQUEST_TIMEOUT"] = int(os.getenv("MAX_REQUEST_TIMEOUT", "120"))

plugin = Plugin(DifyPluginEnv(**plugin_env_config))

if __name__ == "__main__":
    print("Starting AWS Bedrock ARN Plugin...")
    if not os.getenv("DIFY_API_KEY"):
        print("Running in standalone mode (no Dify connection)")
        print("To connect to Dify, set DIFY_API_KEY environment variable")
    plugin.run()

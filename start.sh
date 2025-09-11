#!/bin/bash

# Render start script for MCP Hotel Assistant
echo "🚀 Starting MCP Hotel Assistant on Render..."

# Set Python path
export PYTHONPATH="${PYTHONPATH}:/opt/render/project/src"

# Start the Chainlit app
exec chainlit run mcp_chainlit_app.py --port $PORT --host 0.0.0.0

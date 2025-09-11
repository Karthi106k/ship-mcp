#!/bin/bash

# Start MCP server script
echo "Starting OHIP MCP Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo "Please edit .env file with your API keys before running the server."
    exit 1
fi

# Start MCP server
echo "Starting MCP server..."
python -m ohip_mcp.server mcp

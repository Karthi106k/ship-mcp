#!/bin/bash

# Start Chainlit app script
echo "Starting OHIP Chainlit App..."

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
    echo "Please edit .env file with your API keys before running the app."
    exit 1
fi

# Start Chainlit app
echo "Starting Chainlit app..."
python -m ohip_mcp.server chainlit

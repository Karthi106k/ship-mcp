# OHIP MCP Server Setup Guide

This guide will walk you through setting up the OHIP MCP Server step by step.

## 📋 Prerequisites Checklist

- [ ] Python 3.9 or higher installed
- [ ] Git installed
- [ ] Gemini API key obtained from Google AI Studio
- [ ] OHIP API credentials (base URL and API key)
- [ ] Postman collection exported as JSON (optional)

## 🚀 Step-by-Step Setup

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd ohip-mcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor
```

**Required environment variables:**
```env
# Gemini API Configuration
GEMINI_API_KEY=your_actual_gemini_api_key_here

# OHIP API Configuration
OHIP_BASE_URL=https://your-ohip-api-domain.com/api/v1
OHIP_API_KEY=your_actual_ohip_api_key_here

# Optional: Chainlit Configuration
CHAINLIT_HOST=0.0.0.0
CHAINLIT_PORT=8000
```

### 3. Postman Collection Integration (Optional)

If you have a Postman collection with your OHIP endpoints:

```bash
# Export your Postman collection as JSON
# Then run the converter
python scripts/postman_converter.py path/to/your/collection.json

# Review generated files
ls generated/
# - mcp_tools.json (MCP tool definitions)
# - client_methods.py (Python client methods)

# Integrate the generated code into your project
# (Manual step - copy methods to appropriate files)
```

### 4. Testing the Setup

```bash
# Test MCP server only
python -m ohip_mcp.server mcp

# Test Chainlit interface only  
python -m ohip_mcp.server chainlit

# Test complete application
./scripts/start_chainlit.sh
```

### 5. Verification

1. **MCP Server Test**: The MCP server should start without errors and display available tools
2. **Chainlit Interface Test**: Open `http://localhost:8000` and see the chat interface
3. **End-to-End Test**: Try sending a message like "Search for patient John Doe"

## 🔧 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**2. API Connection Errors**
- Verify your API keys in `.env`
- Check API base URLs
- Test API connectivity manually

**3. Port Already in Use**
```bash
# Change port in .env file
CHAINLIT_PORT=8001

# Or kill existing process
lsof -ti:8000 | xargs kill
```

**4. Gemini API Errors**
- Ensure you have a valid Gemini API key
- Check your Google AI Studio quota
- Verify the model name in the code

### Log Files

Check the log file for detailed error information:
```bash
tail -f ohip_mcp.log
```

## 🎯 Next Steps

After successful setup:

1. **Customize for Your API**: Update the OHIP client methods to match your actual API endpoints
2. **Add Authentication**: Implement proper authentication for your OHIP API
3. **Enhance Workflows**: Customize LangGraph workflows for your specific use cases
4. **UI Customization**: Modify the Chainlit interface for your branding
5. **Security Review**: Implement proper security measures for production use

## 🔐 Security Considerations

- Never commit `.env` files to version control
- Use environment-specific configurations
- Implement proper authentication and authorization
- Follow healthcare data privacy regulations
- Use HTTPS in production
- Regularly rotate API keys

## 📞 Getting Help

If you encounter issues:

1. Check the logs (`ohip_mcp.log`)
2. Verify your configuration (`.env` file)
3. Test individual components separately
4. Review the main README.md for additional information
5. Check the generated documentation in `docs/`

## 🔄 Development Workflow

For ongoing development:

```bash
# Start development server with auto-reload
python -m ohip_mcp.server chainlit

# Run tests (when available)
pytest tests/

# Code formatting
black src/
isort src/

# Type checking
mypy src/
```
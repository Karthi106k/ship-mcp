# OHIP MCP Server

A Model Context Protocol (MCP) server that wraps OHIP (Ontario Health Insurance Plan) API endpoints, integrating MCP → LangGraph → Chainlit → Gemini API for a complete healthcare assistant solution.

## 🏗️ Architecture

```
User Interface (Chainlit) 
    ↓
Gemini API (Chat & NLP)
    ↓  
LangGraph (Workflow Orchestration)
    ↓
MCP Server (Tool Interface)
    ↓
OHIP API (Healthcare Data)
```

## 🚀 Features

- **MCP Server**: Exposes OHIP endpoints as MCP tools
- **LangGraph Workflows**: Orchestrates complex healthcare operations
- **Chainlit Interface**: Modern chat UI for user interactions
- **Gemini Integration**: AI-powered conversation and intent analysis
- **OHIP Operations**:
  - Patient search and lookup
  - Claims history retrieval
  - New claim submission
  - Healthcare provider management

## 📋 Prerequisites

- Python 3.9+
- Gemini API key
- OHIP API access credentials
- Postman collection with OHIP endpoints

## 🛠️ Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd ohip-mcp
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your API keys:
   # - GEMINI_API_KEY=your_gemini_api_key
   # - OHIP_API_KEY=your_ohip_api_key  
   # - OHIP_BASE_URL=your_ohip_base_url
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `HOSTNAME` | API base hostname | Yes |
| `CLIENT_ID` | OAuth client ID | Yes |
| `CLIENT_SECRET` | OAuth client secret | Yes |
| `ENTERPRISE_ID` | Enterprise identifier | No (default: PSALES) |
| `APP_KEY` | Application key for API access | Yes |
| `CHAINLIT_HOST` | Chainlit server host | No (default: 0.0.0.0) |
| `CHAINLIT_PORT` | Chainlit server port | No (default: 8000) |
| `MCP_SERVER_PORT` | MCP server port | No (default: 3001) |

### Postman Collection Integration

To integrate your Postman collection:

1. **Export your collection** as JSON
2. **Update the OHIP client** (`src/ohip_mcp/api_clients/ohip_client.py`) with your actual endpoints:
   - Replace placeholder URLs with real endpoints
   - Update authentication methods
   - Modify request/response handling

3. **Update MCP tools** (`src/ohip_mcp/mcp_server/server.py`) to match your API:
   - Add/remove tools based on your endpoints
   - Update input schemas to match your API parameters
   - Modify tool descriptions

## 🚀 Usage

### Start the Complete Application

```bash
# Start both MCP server and Chainlit interface
./scripts/start_chainlit.sh
```

### Start Components Separately

```bash
# Test OAuth authentication first
python test_oauth.py

# Start only MCP server
./scripts/start_mcp.sh

# Or start only Chainlit interface
python -m ohip_mcp.server chainlit
```

### Using the Chat Interface

1. Open your browser to `http://localhost:8000`
2. Start chatting with the OHIP assistant
3. Example queries:
   - "Search for patient John Doe"
   - "Get claims history for patient ID 12345"
   - "Submit a new claim for service code A001"

## 🔌 MCP Tools

The server exposes these MCP tools:

### `test_oauth_token`
Test OAuth token endpoint and authentication.

**Parameters**: None

### `test_api_connection`
Test full API connection including OAuth authentication.

**Parameters**: None

### `ohip_search_patient`
Search for patients in the OHIP system.

**Parameters**:
- `health_card_number` (optional): Patient's health card number
- `first_name` (optional): Patient's first name  
- `last_name` (optional): Patient's last name
- `date_of_birth` (optional): Patient's date of birth (YYYY-MM-DD)

### `ohip_get_patient_claims`
Retrieve claims history for a patient.

**Parameters**:
- `patient_id` (required): Patient ID from OHIP system
- `start_date` (optional): Start date for claims search (YYYY-MM-DD)
- `end_date` (optional): End date for claims search (YYYY-MM-DD)

### `ohip_submit_claim`
Submit a new claim to OHIP.

**Parameters**:
- `patient_id` (required): Patient ID from OHIP system
- `provider_id` (required): Healthcare provider ID
- `service_code` (required): OHIP service code
- `service_date` (required): Date service was provided (YYYY-MM-DD)
- `amount` (required): Claim amount

## 🔄 LangGraph Workflows

The system uses LangGraph to orchestrate complex operations:

1. **Request Analysis**: Determines the type of operation needed
2. **Parameter Extraction**: Extracts relevant parameters from user input
3. **API Execution**: Calls appropriate OHIP endpoints
4. **Response Formatting**: Formats results for user consumption
5. **Error Handling**: Manages errors and provides helpful feedback

## 🛡️ Security Considerations

- Store API keys securely in environment variables
- Implement proper authentication and authorization
- Validate all input parameters
- Log access and operations for audit trails
- Follow healthcare data privacy regulations (PIPEDA, PHIPA)

## 🧪 Development

### Project Structure

```
src/ohip_mcp/
├── __init__.py
├── config.py                 # Configuration management
├── server.py                 # Main server entry point
├── api_clients/              # API client implementations
│   ├── __init__.py
│   └── ohip_client.py       # OHIP API client
├── chainlit_app/            # Chainlit chat interface
│   ├── __init__.py
│   ├── app.py              # Main Chainlit app
│   └── gemini_client.py    # Gemini API client
├── langraph_workflows/      # LangGraph workflow definitions
│   ├── __init__.py
│   └── ohip_workflow.py    # OHIP operations workflow
└── mcp_server/             # MCP server implementation
    ├── __init__.py
    └── server.py           # MCP server core
```

### Adding New Endpoints

1. **Update OHIP Client**: Add new methods to `ohip_client.py`
2. **Add MCP Tool**: Define new tool in `mcp_server/server.py`
3. **Update Workflow**: Add workflow steps in `ohip_workflow.py`
4. **Test Integration**: Verify end-to-end functionality

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=ohip_mcp tests/
```

## 📝 Customizing for Your Postman Collection

To adapt this for your specific Postman collection:

1. **Analyze your collection**: Identify the endpoints, parameters, and authentication
2. **Update the OHIP client**: Modify `ohip_client.py` methods to match your API
3. **Adjust MCP tools**: Update tool definitions in the MCP server
4. **Customize workflows**: Modify LangGraph workflows for your use cases
5. **Update UI prompts**: Adjust Chainlit interface for your domain

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🆘 Support

For issues and questions:
- Check the logs in `ohip_mcp.log`
- Review configuration in `.env`
- Verify API connectivity
- Check Postman collection export format

## 🔗 Links

- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Chainlit Documentation](https://docs.chainlit.io/)
- [Gemini API Documentation](https://ai.google.dev/docs)

"""MCP Server implementation for OHIP endpoints."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)
from pydantic import BaseModel

from ..api_clients.ohip_client import APIClient
from ..config import get_settings

logger = logging.getLogger(__name__)


class OHIPMCPServer:
    """MCP Server for OAuth-protected API endpoints."""
    
    def __init__(self):
        self.server = Server("ohip-mcp")
        self.api_client = APIClient()
        self.settings = get_settings()
        
        # Register handlers
        self.server.list_tools = self.list_tools
        self.server.call_tool = self.call_tool
    
    async def list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """List available tools (API endpoints)."""
        tools = [
            Tool(
                name="test_oauth_token",
                description="Test OAuth token endpoint and authentication",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="test_api_connection",
                description="Test full API connection including OAuth authentication",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="ohip_search_patient",
                description="Search for patients in OHIP system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "health_card_number": {
                            "type": "string",
                            "description": "Patient's health card number"
                        },
                        "first_name": {
                            "type": "string", 
                            "description": "Patient's first name"
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Patient's last name"
                        },
                        "date_of_birth": {
                            "type": "string",
                            "description": "Patient's date of birth (YYYY-MM-DD)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="ohip_get_patient_claims",
                description="Get claims history for a patient",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "Patient ID from OHIP system"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date for claims search (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string", 
                            "description": "End date for claims search (YYYY-MM-DD)"
                        }
                    },
                    "required": ["patient_id"]
                }
            ),
            Tool(
                name="ohip_submit_claim",
                description="Submit a new claim to OHIP",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "Patient ID from OHIP system"
                        },
                        "provider_id": {
                            "type": "string",
                            "description": "Healthcare provider ID"
                        },
                        "service_code": {
                            "type": "string",
                            "description": "OHIP service code"
                        },
                        "service_date": {
                            "type": "string",
                            "description": "Date service was provided (YYYY-MM-DD)"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Claim amount"
                        }
                    },
                    "required": ["patient_id", "provider_id", "service_code", "service_date", "amount"]
                }
            ),
            Tool(
                name="get_reservation",
                description="Get hotel reservation details by reservation ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hotel_id": {
                            "type": "string",
                            "description": "Hotel ID"
                        },
                        "reservation_id": {
                            "type": "string",
                            "description": "Reservation ID to retrieve"
                        },
                        "fetch_instructions": {
                            "type": "string",
                            "description": "Fetch instructions for the reservation data",
                            "default": "Reservation"
                        }
                    },
                    "required": ["hotel_id", "reservation_id"]
                }
            )
        ]
        
        return ListToolsResult(tools=tools)
    
    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool calls to API endpoints."""
        try:
            if request.params.name == "test_oauth_token":
                result = await self.api_client.test_oauth_token()
            elif request.params.name == "test_api_connection":
                result = await self.api_client.test_api_connection()
            elif request.params.name == "ohip_search_patient":
                result = await self.api_client.search_patient(request.params.arguments)
            elif request.params.name == "ohip_get_patient_claims":
                result = await self.api_client.get_patient_claims(request.params.arguments)
            elif request.params.name == "ohip_submit_claim":
                result = await self.api_client.submit_claim(request.params.arguments)
            elif request.params.name == "get_reservation":
                result = await self.api_client.get_reservation(request.params.arguments)
            else:
                raise ValueError(f"Unknown tool: {request.params.name}")
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            )
        
        except Exception as e:
            logger.error(f"Error calling tool {request.params.name}: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", 
                        text=f"Error: {str(e)}"
                    )
                ],
                isError=True
            )
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point for the MCP server."""
    logging.basicConfig(level=logging.INFO)
    server = OHIPMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

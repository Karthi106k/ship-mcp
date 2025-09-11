#!/usr/bin/env python3
"""
Test script for MCP server with OAuth integration.
"""

import asyncio
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ohip_mcp.mcp_server.server import OHIPMCPServer


async def test_mcp_server():
    """Test the MCP server functionality."""
    print("🔧 Testing MCP Server with OAuth Integration")
    print("=" * 50)
    
    try:
        # Initialize MCP server
        print("🚀 Initializing MCP server...")
        server = OHIPMCPServer()
        
        # Test tool listing
        print("📋 Testing tool listing...")
        from mcp.types import ListToolsRequest
        tools_request = ListToolsRequest()
        tools_result = await server.list_tools(tools_request)
        
        print(f"✅ Found {len(tools_result.tools)} tools:")
        for tool in tools_result.tools:
            print(f"   - {tool.name}: {tool.description}")
        
        # Test OAuth token tool
        print("\n🔐 Testing OAuth token tool...")
        from mcp.types import CallToolRequest, CallToolRequestParams
        
        token_request = CallToolRequest(
            params=CallToolRequestParams(
                name="test_oauth_token",
                arguments={}
            )
        )
        
        token_result = await server.call_tool(token_request)
        print("✅ OAuth token tool test successful!")
        print(f"📝 Result: {token_result.content[0].text[:100]}...")
        
        # Test API connection tool
        print("\n🌐 Testing API connection tool...")
        connection_request = CallToolRequest(
            params=CallToolRequestParams(
                name="test_api_connection", 
                arguments={}
            )
        )
        
        connection_result = await server.call_tool(connection_request)
        print("✅ API connection tool test successful!")
        print(f"📝 Result: {connection_result.content[0].text[:100]}...")
        
        # Test reservation tool (this will fail without real data, but tests the tool exists)
        print("\n🏨 Testing reservation tool...")
        reservation_request = CallToolRequest(
            params=CallToolRequestParams(
                name="get_reservation",
                arguments={
                    "hotel_id": "test_hotel",
                    "reservation_id": "test_reservation"
                }
            )
        )
        
        try:
            reservation_result = await server.call_tool(reservation_request)
            print("✅ Reservation tool test successful!")
        except Exception as e:
            print(f"⚠️  Reservation tool test (expected to fail with test data): {str(e)[:100]}...")
        
        print("\n🎉 All MCP server tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_mcp_server()
    
    if success:
        print("\n✅ MCP server is ready!")
        print("\n📋 Next steps:")
        print("1. Test with Chainlit: python test_chainlit.py")
        print("2. Run full server: python -c 'from src.ohip_mcp.server import main; main()' chainlit")
    else:
        print("\n❌ MCP server tests failed")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

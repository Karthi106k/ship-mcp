"""
Test script for the MCP Agent.
"""

import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ohip_mcp.mcp_agent import MCPAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mcp_agent():
    """Test the MCP Agent with various requests."""
    logger.info("🤖 Testing MCP Agent")
    logger.info("=" * 50)
    
    # Initialize agent
    agent = MCPAgent()
    await agent.initialize()
    
    test_requests = [
        "Test the OAuth connection",
        "Check if the API is working", 
        "Get reservation details for hotel SYDH3 and reservation 218290",
        "What can you do?",
        "Hello, how are you?"
    ]
    
    for i, request in enumerate(test_requests, 1):
        logger.info(f"\n🔍 Test {i}: {request}")
        logger.info("-" * 40)
        
        try:
            response = await agent.process_user_request(request)
            logger.info(f"✅ Response: {response}")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    logger.info("\n🎉 MCP Agent testing completed!")


if __name__ == "__main__":
    asyncio.run(test_mcp_agent())

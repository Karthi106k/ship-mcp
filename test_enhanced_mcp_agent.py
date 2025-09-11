"""
Test script for the enhanced MCP Agent with natural language formatting.
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


async def test_enhanced_mcp_agent():
    """Test the enhanced MCP Agent with natural language reservation formatting."""
    logger.info("🤖 Testing Enhanced MCP Agent with Natural Language Formatting")
    logger.info("=" * 70)
    
    # Initialize agent
    agent = MCPAgent()
    await agent.initialize()
    
    # Test reservation request that should trigger natural language formatting
    test_request = "Get reservation details for hotel SYDH3 and reservation 218290"
    
    logger.info(f"🎯 Test Request: {test_request}")
    logger.info("-" * 50)
    
    try:
        response = await agent.process_user_request(test_request)
        logger.info("✅ SUCCESS! Enhanced MCP Agent Response:")
        logger.info("=" * 50)
        print(response)
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

    logger.info("\n🎉 Enhanced MCP Agent test completed!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_mcp_agent())

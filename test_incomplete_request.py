"""
Test script to see how MCP Agent handles incomplete reservation requests.
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


async def test_incomplete_requests():
    """Test MCP Agent with incomplete reservation requests."""
    logger.info("🧪 Testing MCP Agent with Incomplete Requests")
    logger.info("=" * 60)
    
    # Initialize agent
    agent = MCPAgent()
    await agent.initialize()
    
    test_cases = [
        "Get reservation details for 218290",  # Missing hotel_id
        "Show me reservation for hotel SYDH3",  # Missing reservation_id
        "Get reservation details",  # Missing both
        "Get reservation details for hotel SYDH3 and reservation 218290",  # Complete (for comparison)
    ]
    
    for i, test_request in enumerate(test_cases, 1):
        logger.info(f"\n🎯 Test {i}: {test_request}")
        logger.info("-" * 40)
        
        try:
            response = await agent.process_user_request(test_request)
            logger.info("✅ Response:")
            print(f"   {response}")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")

    logger.info("\n🎉 Incomplete request test completed!")


if __name__ == "__main__":
    asyncio.run(test_incomplete_requests())

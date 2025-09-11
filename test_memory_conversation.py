"""
Test script for MCP Agent with conversation memory.
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


async def test_memory_conversation():
    """Test MCP Agent with conversation memory."""
    logger.info("🧠 Testing MCP Agent with Conversation Memory")
    logger.info("=" * 60)
    
    # Initialize agent
    agent = MCPAgent()
    await agent.initialize()
    
    # Simulate a conversation with memory
    conversation_history = []
    
    conversation_flow = [
        "Get reservation details for 218290",  # Missing hotel ID
        "SYDH3",  # Providing the hotel ID in follow-up
        "Show me another reservation for the same hotel",  # Referring to previous context
        "What was the guest name from that first reservation?",  # Asking about previous result
    ]
    
    for i, user_message in enumerate(conversation_flow, 1):
        logger.info(f"\n🔄 Turn {i}: {user_message}")
        logger.info("-" * 50)
        
        try:
            # Get response with conversation history
            response = await agent.get_conversation_response(
                user_message, 
                conversation_history=conversation_history
            )
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "assistant", "content": response})
            
            logger.info("✅ Response:")
            print(f"   {response}")
            logger.info(f"📚 History length: {len(conversation_history)} messages")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")

    logger.info("\n🎉 Memory conversation test completed!")
    logger.info(f"📊 Final conversation history: {len(conversation_history)} messages")


if __name__ == "__main__":
    asyncio.run(test_memory_conversation())

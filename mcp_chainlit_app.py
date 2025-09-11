"""
True MCP-powered Chainlit application where Gemini 2.5 Flash intelligently calls MCP tools.
"""

import chainlit as cl
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ohip_mcp.mcp_agent import MCPAgent

logger = logging.getLogger(__name__)

# Initialize MCP Agent
mcp_agent = MCPAgent()


@cl.on_chat_start
async def start():
    """Initialize the MCP agent and welcome the user."""
    try:
        logger.info("Initializing MCP Agent...")
        await mcp_agent.initialize()
        
        # Initialize conversation memory in session
        cl.user_session.set("conversation_history", [])
        logger.info("Initialized conversation memory")
        
        await cl.Message(
            content="""🤖 **Welcome to the MCP-Powered Hotel Assistant!**

I'm an AI agent that uses **Gemini 2.5 Flash** to intelligently call **MCP (Model Context Protocol) tools** to help you with hotel operations.

**🛠️ Available MCP Tools:**
- 🔐 **test_oauth_token** - Test OAuth authentication
- 🌐 **test_api_connection** - Test full API connectivity  
- 🏨 **get_reservation** - Get detailed hotel reservation information

**🤖 How I Work:**
1. You tell me what you want to do in natural language
2. I use Gemini 2.5 Flash to understand your request
3. I intelligently decide which MCP tools to call
4. I execute the tools and format the results for you

**💬 Try asking:**
- "Test the OAuth connection"
- "Check if the API is working"
- "Get reservation details for hotel SYDH3 and reservation 218290"
- "Show me reservation information"

**✨ I'm powered by true MCP architecture - the AI decides what tools to use!**

How can I help you today?"""
        ).send()
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP agent: {e}")
        await cl.Message(
            content=f"❌ **Initialization Error**: Failed to start MCP agent: {str(e)}"
        ).send()


@cl.on_message
async def main(message: cl.Message):
    """Process user message through the MCP agent with conversation memory."""
    
    # Get conversation history from session
    conversation_history = cl.user_session.get("conversation_history", [])
    
    with cl.Step(name="🤖 MCP Agent Processing", type="llm") as step:
        step.output = "Gemini 2.5 Flash is analyzing your request and deciding which MCP tools to call..."
        
        try:
            # Get response from MCP agent with conversation history
            response = await mcp_agent.get_conversation_response(
                message.content, 
                conversation_history=conversation_history
            )
            step.output = "✅ MCP tools executed successfully!"
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": message.content})
            conversation_history.append({"role": "assistant", "content": response})
            
            # Keep only last 10 exchanges (20 messages) to prevent memory overflow
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
            
            # Save updated history back to session
            cl.user_session.set("conversation_history", conversation_history)
            logger.info(f"Updated conversation history: {len(conversation_history)} messages")
            
        except Exception as e:
            logger.error(f"Error in MCP agent: {e}")
            response = f"❌ **MCP Agent Error**: {str(e)}"
            step.output = f"❌ Error in MCP processing: {str(e)}"
    
    await cl.Message(content=response).send()


@cl.on_stop
async def on_stop():
    """Handle chat session stop."""
    logger.info("MCP-powered chat session stopped")


if __name__ == "__main__":
    # This allows running the app directly but chainlit run is preferred
    pass

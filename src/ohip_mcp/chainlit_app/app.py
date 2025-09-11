"""Chainlit chat application for OHIP MCP Server."""

import asyncio
import json
import logging
from typing import Any, Dict, List

import chainlit as cl
import google.generativeai as genai

from ..config import get_settings
from ..langraph_workflows.ohip_workflow import OHIPWorkflow
from .gemini_client import GeminiClient

logger = logging.getLogger(__name__)

# Initialize settings and clients
settings = get_settings()
gemini_client = GeminiClient()
ohip_workflow = OHIPWorkflow()


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    await cl.Message(
        content="🏥 Welcome to the OHIP Assistant! I can help you with:\n\n"
                "• 🔍 **Search for patients** - Find patient information in the OHIP system\n"
                "• 📋 **View claims history** - Get claims data for specific patients\n"
                "• ➕ **Submit new claims** - Create and submit new claims to OHIP\n\n"
                "How can I assist you today?"
    ).send()
    
    # Initialize session state
    cl.user_session.set("messages", [])
    cl.user_session.set("workflow_active", False)


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    try:
        # Get current message history
        messages = cl.user_session.get("messages", [])
        
        # Add user message to history
        user_message = {
            "role": "user",
            "content": message.content
        }
        messages.append(user_message)
        
        # Show typing indicator
        async with cl.Step(name="Processing", type="run") as step:
            step.output = "Analyzing your request..."
            
            # Check if this is an OHIP-related request
            if await _is_ohip_request(message.content):
                # Use LangGraph workflow for OHIP operations
                step.output = "Executing OHIP workflow..."
                
                workflow_result = await ohip_workflow.run(messages)
                
                if workflow_result.get("error"):
                    response_content = f"❌ Error: {workflow_result['error']}"
                else:
                    response_content = _format_ohip_response(workflow_result)
                
            else:
                # Use Gemini for general conversation
                step.output = "Generating response with Gemini..."
                
                response_content = await gemini_client.generate_response(
                    messages, 
                    system_prompt=_get_system_prompt()
                )
        
        # Send response
        await cl.Message(content=response_content).send()
        
        # Update message history
        assistant_message = {
            "role": "assistant", 
            "content": response_content
        }
        messages.append(assistant_message)
        cl.user_session.set("messages", messages)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await cl.Message(
            content=f"❌ I encountered an error: {str(e)}. Please try again."
        ).send()


async def _is_ohip_request(content: str) -> bool:
    """Determine if the message is an OHIP-related request."""
    ohip_keywords = [
        "patient", "claim", "ohip", "health card", "medical", "provider",
        "search patient", "submit claim", "claims history", "billing"
    ]
    
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in ohip_keywords)


def _format_ohip_response(workflow_result: Dict[str, Any]) -> str:
    """Format the workflow result into a user-friendly response."""
    if not workflow_result.get("result"):
        return "❌ No results found."
    
    result = workflow_result["result"]
    status = result.get("status", "unknown")
    message = result.get("message", "Operation completed")
    data = result.get("data", {})
    
    if status == "success":
        response = f"✅ **{message}**\n\n"
        
        if data:
            if isinstance(data, dict):
                response += "📊 **Results:**\n"
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        response += f"• **{key}**: {json.dumps(value, indent=2)}\n"
                    else:
                        response += f"• **{key}**: {value}\n"
            elif isinstance(data, list):
                response += f"📊 **Found {len(data)} results:**\n"
                for i, item in enumerate(data[:5], 1):  # Limit to first 5 results
                    response += f"{i}. {json.dumps(item, indent=2)}\n"
                if len(data) > 5:
                    response += f"... and {len(data) - 5} more results\n"
        
        return response
    else:
        return f"❌ **Error**: {message}"


def _get_system_prompt() -> str:
    """Get the system prompt for Gemini."""
    return """You are an OHIP (Ontario Health Insurance Plan) Assistant. You help users with:

1. Patient searches in the OHIP system
2. Claims history retrieval  
3. New claim submissions
4. General OHIP-related questions

You are knowledgeable about:
- OHIP billing codes and procedures
- Patient privacy and healthcare regulations
- Medical terminology and healthcare processes
- Ontario healthcare system

Always be helpful, professional, and ensure patient privacy is maintained. When users ask about OHIP operations, guide them on what information is needed and explain the process clearly.

If a user asks about something outside of OHIP/healthcare, politely redirect them back to OHIP-related topics."""


@cl.on_stop
async def on_stop():
    """Handle chat session stop."""
    logger.info("Chat session stopped")


if __name__ == "__main__":
    # This allows running the app directly
    pass

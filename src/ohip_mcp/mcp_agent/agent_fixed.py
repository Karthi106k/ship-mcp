"""
MCP Agent that uses Gemini 2.5 Flash to intelligently call MCP tools.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import google.generativeai as genai

from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest
from ..mcp_server.server import OHIPMCPServer
from ..config import get_settings

logger = logging.getLogger(__name__)


class MCPAgent:
    """Agent that uses Gemini 2.5 Flash to call MCP tools intelligently."""
    
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.mcp_server = OHIPMCPServer()
        self.available_tools = []
        logger.info("MCPAgent initialized with Gemini 2.5 Flash")
    
    async def initialize(self):
        """Initialize the MCP agent and load available tools."""
        try:
            # Get available tools from MCP server
            tools_request = ListToolsRequest(params={})
            tools_response = await self.mcp_server.list_tools(tools_request)
            
            self.available_tools = tools_response.tools
            logger.info(f"Loaded {len(self.available_tools)} MCP tools")
            for tool in self.available_tools:
                logger.info(f"  - {tool.name}: {tool.description}")
                
        except Exception as e:
            logger.error(f"Failed to initialize MCP agent: {e}")
            raise
    
    async def process_user_request(self, user_message: str) -> str:
        """Process a user request and decide which MCP tools to call."""
        try:
            # Create system prompt for Gemini
            system_prompt = f"""You are an intelligent MCP (Model Context Protocol) agent powered by Gemini 2.5 Flash.

Available MCP Tools:
{self._format_tools_list()}

Your job is to:
1. Understand what the user wants to do
2. Decide which MCP tools to call (if any)
3. Call the tools in the right order
4. Present the results in a helpful way

User Request: "{user_message}"

If you need to call MCP tools, respond with a JSON object in this format:
{{
    "action": "call_tools",
    "tools_to_call": [
        {{
            "tool_name": "tool_name",
            "parameters": {{"param1": "value1", "param2": "value2"}}
        }}
    ],
    "explanation": "Why you're calling these tools"
}}

If you don't need to call any tools, respond with:
{{
    "action": "respond_directly",
    "response": "Your direct response to the user"
}}

Be intelligent about tool selection:
- For "test oauth" or "check connection" → use test_oauth_token or test_api_connection
- For "get reservation" or "reservation details" → use get_reservation (need hotel_id and reservation_id)
- For general questions → respond_directly

IMPORTANT: If a user asks for reservation details but doesn't provide both hotel_id and reservation_id, respond with "respond_directly" and ask for the missing information instead of calling the tool with incomplete parameters.
"""

            # Get Gemini's decision
            response = await self.model.generate_content_async(system_prompt)
            decision_text = response.text.strip()
            
            logger.info(f"Gemini decision: {decision_text}")
            
            # Parse Gemini's decision
            try:
                # Clean up response if it has markdown code blocks
                if decision_text.startswith("```json"):
                    decision_text = decision_text.replace("```json", "").replace("```", "").strip()
                elif decision_text.startswith("```"):
                    decision_text = decision_text.replace("```", "").strip()
                
                decision = json.loads(decision_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini decision: {e}")
                return f"I had trouble understanding how to help you. Could you please rephrase your request?"
            
            # Execute the decision
            if decision.get("action") == "call_tools":
                return await self._execute_tools(decision["tools_to_call"], decision.get("explanation", ""))
            elif decision.get("action") == "respond_directly":
                return decision["response"]
            else:
                return "I'm not sure how to help with that request. Could you please be more specific?"
                
        except Exception as e:
            logger.error(f"Error processing user request: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    async def _execute_tools(self, tools_to_call: List[Dict[str, Any]], explanation: str) -> str:
        """Execute the MCP tools that Gemini decided to call."""
        results = []
        
        if explanation:
            results.append(f"🤖 **AI Decision**: {explanation}\n")
        
        for tool_call in tools_to_call:
            tool_name = tool_call["tool_name"]
            parameters = tool_call.get("parameters", {})
            
            try:
                logger.info(f"Calling MCP tool: {tool_name} with params: {parameters}")
                
                # Create MCP tool call request
                request = CallToolRequest(
                    params=CallToolRequestParams(
                        name=tool_name,
                        arguments=parameters
                    )
                )
                
                # Call the MCP tool
                tool_response = await self.mcp_server.call_tool(request)
                
                # Format the response
                if tool_response.content:
                    content = tool_response.content[0]
                    if hasattr(content, 'text'):
                        tool_result = content.text
                    else:
                        tool_result = str(content)
                    
                    # Special handling for reservation data - format it naturally
                    if tool_name == "get_reservation" and "reservations" in tool_result.lower():
                        formatted_result = await self._format_reservation_response(tool_result)
                        results.append(f"🏨 **Reservation Details**:\n\n{formatted_result}")
                    else:
                        results.append(f"✅ **{tool_name}**: {tool_result}")
                else:
                    results.append(f"✅ **{tool_name}**: Tool executed successfully")
                    
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                results.append(f"❌ **{tool_name}**: Error - {str(e)}")
        
        return "\n\n".join(results)
    
    async def _format_reservation_response(self, raw_json_response: str) -> str:
        """Use Gemini 2.5 Flash to format reservation JSON into natural language."""
        try:
            formatting_prompt = f"""You are a hotel concierge assistant. Convert this reservation API response into a friendly, natural language summary for hotel staff.

Focus on the most important details that hotel staff need:
- Guest name and contact information
- Check-in and check-out dates
- Room type and number of guests (adults/children)
- Reservation status and confirmation numbers
- Any special requests or notes

Make it conversational and professional, as if you're briefing the front desk staff.

API Response:
{raw_json_response}

Format your response as a natural, friendly summary. Don't include technical JSON details - just the human-readable information that matters for hotel operations.
"""
            
            response = await self.model.generate_content_async(formatting_prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error formatting reservation response: {e}")
            # Fallback to raw response if formatting fails
            return f"Here's the reservation data (formatting error occurred):\n\n{raw_json_response[:500]}..."
    
    async def get_conversation_response(self, user_message: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """Get a conversational response with conversation memory, potentially calling MCP tools."""
        try:
            # Use conversation history for better context understanding
            return await self.process_user_request_with_context(user_message, conversation_history)
        except Exception as e:
            logger.error(f"Error in conversation response: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    async def process_user_request_with_context(self, user_message: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """Process user request with conversation context for better understanding."""
        try:
            # Build context-aware prompt
            context_info = ""
            if conversation_history and len(conversation_history) > 0:
                # Extract relevant context from recent conversation
                context_info = "\n\nRecent conversation context:\n"
                for msg in conversation_history[-6:]:  # Last 3 exchanges
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")[:200]  # Limit length
                    context_info += f"{role.title()}: {content}\n"
            
            # Enhanced system prompt with conversation context
            system_prompt = f"""You are an intelligent MCP (Model Context Protocol) agent powered by Gemini 2.5 Flash.

Available MCP Tools:
{self._format_tools_list()}

Your job is to:
1. Understand what the user wants to do (considering conversation context)
2. Decide which MCP tools to call (if any)
3. Call the tools in the right order
4. Present the results in a helpful way

User Request: "{user_message}"{context_info}

IMPORTANT CONTEXT AWARENESS:
- If the user refers to "it", "that", "the reservation", etc., check the conversation history for what they're referring to
- If they provide missing information (like hotel ID after you asked for it), combine it with previous requests
- Remember what you've already told them to avoid repetition

If you need to call MCP tools, respond with a JSON object in this format:
{{
    "action": "call_tools",
    "tools_to_call": [
        {{
            "tool_name": "tool_name",
            "parameters": {{"param1": "value1", "param2": "value2"}}
        }}
    ],
    "explanation": "Why you're calling these tools"
}}

If you don't need to call any tools, respond with:
{{
    "action": "respond_directly",
    "response": "Your direct response to the user"
}}

Be intelligent about tool selection:
- For "test oauth" or "check connection" → use test_oauth_token or test_api_connection
- For "get reservation" or "reservation details" → use get_reservation (need hotel_id and reservation_id)
- For general questions → respond_directly

IMPORTANT: If a user asks for reservation details but doesn't provide both hotel_id and reservation_id, respond with "respond_directly" and ask for the missing information instead of calling the tool with incomplete parameters.

CONTEXT AWARENESS: If the user provides missing information in response to your previous request, intelligently combine it with the previous context.
"""

            # Get Gemini's decision
            response = await self.model.generate_content_async(system_prompt)
            decision_text = response.text.strip()
            
            logger.info(f"Gemini decision with context: {decision_text}")
            
            # Parse Gemini's decision
            try:
                # Clean up response if it has markdown code blocks
                if decision_text.startswith("```json"):
                    decision_text = decision_text.replace("```json", "").replace("```", "").strip()
                elif decision_text.startswith("```"):
                    decision_text = decision_text.replace("```", "").strip()
                
                decision = json.loads(decision_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini decision: {e}")
                return f"I had trouble understanding how to help you. Could you please rephrase your request?"
            
            # Execute the decision
            if decision.get("action") == "call_tools":
                return await self._execute_tools(decision["tools_to_call"], decision.get("explanation", ""))
            elif decision.get("action") == "respond_directly":
                return decision["response"]
            else:
                return "I'm not sure how to help with that request. Could you please be more specific?"
                
        except Exception as e:
            logger.error(f"Error processing user request with context: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    def _format_tools_list(self) -> str:
        """Format the available tools list for the system prompt."""
        if not self.available_tools:
            return "No tools available"
        
        tools_text = ""
        for tool in self.available_tools:
            tools_text += f"- {tool.name}: {tool.description}\n"
        
        return tools_text.strip()

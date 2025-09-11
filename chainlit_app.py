"""
Standalone Chainlit chat application for OHIP MCP Server with OAuth integration.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import chainlit as cl
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ohip_mcp.api_clients.oauth_client import OAuthClient
from ohip_mcp.api_clients.ohip_client import APIClient
from ohip_mcp.config import get_settings

logger = logging.getLogger(__name__)

# Initialize settings and clients
settings = get_settings()
api_client = APIClient()


class GeminiClient:
    """Client for interacting with Google's Gemini API."""
    
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def generate_response(
        self, 
        prompt: str, 
        messages: List[Dict[str, Any]] = None
    ) -> str:
        """Generate a response using Gemini API - FIXED VERSION."""
        try:
            logger.info("GeminiClient: Generating response with FIXED implementation")
            
            # For simple prompt-based generation, use the prompt directly
            if messages and len(messages) > 0 and isinstance(messages, list):
                # Convert messages to Gemini format with system prompt
                gemini_prompt = self._convert_messages(messages, prompt)
                logger.info("GeminiClient: Using conversation format")
            else:
                # Just use the prompt directly for extraction tasks
                gemini_prompt = prompt
                logger.info("GeminiClient: Using direct prompt format")
            
            # Generate response
            response = await self.model.generate_content_async(gemini_prompt)
            
            result = response.text
            logger.info(f"GeminiClient: Response generated successfully, length: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."
    
    def _convert_messages(
        self, 
        messages: List[Dict[str, Any]], 
        system_prompt: str = None
    ) -> str:
        """Convert message history to Gemini prompt format - FIXED VERSION."""
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}\n")
        
        # Enhanced validation and error handling
        if messages and isinstance(messages, list):
            for message in messages:
                if isinstance(message, dict) and "role" in message and "content" in message:
                    role = message.get("role", "user")
                    content = message.get("content", "")
                    
                    if role == "user":
                        prompt_parts.append(f"Human: {content}")
                    elif role == "assistant":
                        prompt_parts.append(f"Assistant: {content}")
                else:
                    logger.warning(f"Invalid message format: {message}")
        
        # Add the current prompt
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)


# Initialize Gemini client
gemini_client = GeminiClient()


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    # Force refresh OAuth token on chat start
    try:
        logger.info("Refreshing OAuth token on chat start...")
        await api_client.oauth_client.get_access_token(force_refresh=True)
        token_status = "✅ Fresh OAuth token obtained"
    except Exception as e:
        logger.error(f"Failed to refresh token on startup: {e}")
        token_status = "⚠️ Using existing token (refresh failed)"
    
    await cl.Message(
        content=f"🏨 **Welcome to the Hotel Reservation Assistant!** \n\n"
                f"{token_status}\n\n"
                "I can help you with:\n\n"
                "• 🔍 **Test OAuth Connection** - Verify API authentication\n"
                "• 🔐 **Check API Status** - Test full API connectivity\n"
                "• 🏨 **Hotel Reservations** - Get reservation details\n"
                "• 🔧 **OHIP Operations** - Search patients, view claims, submit claims\n\n"
                "Try asking:\n"
                "- 'Refresh token' - Get a fresh OAuth token\n"
                "- 'Test OAuth connection'\n"
                "- 'Check API status'\n"
                "- 'Get reservation details for hotel SYDH3 and reservation 218290'\n"
                "- 'Search for patient information'\n\n"
                "🤖 **New Feature**: I now use Gemini 2.5 Flash to understand your requests naturally!\n"
                "🔧 **Debug Info**: Gemini client loaded successfully with fixes applied.\n"
                "How can I assist you today?"
    ).send()
    
    # Initialize session state
    cl.user_session.set("messages", [])


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
            
            # Check if this is an OHIP API test request
            content_lower = message.content.lower()
            
            if "refresh token" in content_lower or "new token" in content_lower:
                step.output = "Refreshing OAuth token..."
                
                try:
                    # Force refresh the token
                    await api_client.oauth_client.get_access_token(force_refresh=True)
                    response_content = "✅ **Token Refreshed Successfully**\n\nA new OAuth token has been requested and cached for future API calls."
                except Exception as e:
                    response_content = f"❌ **Token Refresh Failed**: {str(e)}"
                    
            elif "test oauth" in content_lower or "oauth connection" in content_lower:
                step.output = "Testing OAuth authentication..."
                
                try:
                    result = await api_client.test_oauth_token()
                    response_content = _format_api_response(result, "🔐 OAuth Test")
                except Exception as e:
                    response_content = f"❌ **OAuth Test Failed**: {str(e)}"
                    
            elif "api status" in content_lower or "check api" in content_lower or "test api" in content_lower:
                step.output = "Testing full API connection..."
                
                try:
                    result = await api_client.test_api_connection()
                    response_content = _format_api_response(result, "🌐 API Connection Test")
                except Exception as e:
                    response_content = f"❌ **API Connection Test Failed**: {str(e)}"
                    
            elif "reservation" in content_lower or "hotel" in content_lower:
                step.output = "🤖 Using Gemini 2.5 Flash to extract hotel and reservation details..."
                
                # Use Gemini 2.5 Flash to intelligently extract hotel_id and reservation_id
                extraction_prompt = f"""
Extract the hotel ID and reservation ID from this user message:
"{message.content}"

Return ONLY a JSON object with this exact format:
{{"hotel_id": "EXTRACTED_HOTEL_ID", "reservation_id": "EXTRACTED_RESERVATION_ID"}}

Rules:
- hotel_id should be the hotel identifier (e.g., "SYDH3", "SAND01", "ABC123")
- reservation_id should be the reservation number (e.g., "218290", "123456", "12345")
- Keep original case/format when possible
- If you cannot find both values, return: {{"error": "Could not extract both hotel_id and reservation_id"}}
- Return ONLY the JSON, no other text
- Be flexible with different phrasings and formats

Examples of valid extractions:
- "Get reservation details for hotel SYDH3 and reservation 218290" → {{"hotel_id": "SYDH3", "reservation_id": "218290"}}
- "Find reservation 12345 at hotel ABC123" → {{"hotel_id": "ABC123", "reservation_id": "12345"}}
- "Look up hotel XYZ, reservation number 98765" → {{"hotel_id": "XYZ", "reservation_id": "98765"}}
"""
                
                try:
                    extraction_result = await gemini_client.generate_response(extraction_prompt, [])
                    logger.info(f"Gemini 2.5 Flash extraction result: {extraction_result}")
                    
                    # Parse the JSON response (handle markdown code blocks)
                    import json
                    import re
                    
                    # Remove markdown code blocks if present
                    clean_result = extraction_result.strip()
                    if clean_result.startswith("```json"):
                        clean_result = re.sub(r'^```json\s*\n?', '', clean_result)
                        clean_result = re.sub(r'\n?```$', '', clean_result)
                    elif clean_result.startswith("```"):
                        clean_result = re.sub(r'^```\s*\n?', '', clean_result)
                        clean_result = re.sub(r'\n?```$', '', clean_result)
                    
                    extracted_data = json.loads(clean_result.strip())
                    
                    if "error" in extracted_data:
                        response_content = f"""
❌ **AI Extraction Failed**: {extracted_data['error']}

Please specify both hotel ID and reservation ID clearly. Examples:
- "Get reservation details for hotel SYDH3 and reservation 218290"
- "Find reservation 12345 at hotel ABC123"
- "Look up hotel XYZ, reservation number 98765"
"""
                    elif "hotel_id" in extracted_data and "reservation_id" in extracted_data:
                        hotel_id = extracted_data["hotel_id"]
                        reservation_id = extracted_data["reservation_id"]
                        
                        step.output = f"✅ Gemini 2.5 Flash Extracted: Hotel {hotel_id}, Reservation {reservation_id}"
                        
                        try:
                            result = await api_client.get_reservation({
                                "hotel_id": hotel_id,
                                "reservation_id": reservation_id,
                                "fetch_instructions": "Reservation"
                            })
                            
                            # Send the full API response to Gemini 2.5 Flash for intelligent formatting
                            if result.get("status") == "success" and result.get("data"):
                                step.output = "🤖 Using Gemini 2.5 Flash to format comprehensive reservation details..."
                                
                                formatting_prompt = f"""
Analyze this hotel reservation API response and format it into a comprehensive, well-organized summary for hotel staff. Show ALL important details in a professional, easy-to-read format.

API Response:
{result.get("data")}

Please format this into a detailed summary including:

1. **RESERVATION OVERVIEW**
   - Reservation ID(s) and confirmation numbers
   - Hotel name and ID
   - Current status
   - Create/modify dates

2. **GUEST INFORMATION**
   - Guest name(s) and titles
   - Contact information (phone, email)
   - Address
   - VIP status and membership details
   - Any special notes

3. **STAY DETAILS**
   - Check-in and check-out dates/times
   - Room type, class, and room number (if assigned)
   - Number of guests (adults/children)
   - Rate plan and nightly rate
   - Total nights and estimated total cost

4. **BOOKING INFORMATION**
   - Booking channel and source
   - Market code and guarantee type
   - Payment method
   - Any special requests or packages

5. **ADDITIONAL DETAILS**
   - Company/group affiliations
   - Reservation indicators/flags
   - Any other relevant information from the API

Format this professionally with clear headings, bullet points, and emojis for easy reading. If there are multiple reservations, show them separately. Include any important operational notes that hotel staff should know.

Make it comprehensive - don't leave out important details from the JSON response.
"""
                                
                                try:
                                    formatted_response = await gemini_client.generate_response(formatting_prompt, [])
                                    response_content = f"✅ **🏨 Reservation Details - Success**\n\n📝 **Message**: Reservation {reservation_id} retrieved successfully\n\n{formatted_response}"
                                except Exception as format_error:
                                    logger.error(f"LLM formatting error: {format_error}")
                                    response_content = _format_api_response(result, "🏨 Reservation Details")
                            else:
                                response_content = _format_api_response(result, "🏨 Reservation Details")
                        except Exception as e:
                            response_content = f"❌ **Reservation Lookup Failed**: {str(e)}"
                    else:
                        response_content = "❌ **Invalid AI Response**: Could not extract hotel ID and reservation ID. Please try again with a clearer format."
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {e}, Raw response: {extraction_result}")
                    response_content = f"""
❌ **Parsing Error**: Could not parse the AI extraction result.

Raw AI response: {extraction_result[:200]}...

Please try rephrasing your request more clearly.
"""
                except Exception as e:
                    logger.error(f"Extraction error: {e}")
                    response_content = f"❌ **Extraction Error**: {str(e)}. Please try again."
                    
            elif any(keyword in content_lower for keyword in ["patient", "search", "claim", "ohip"]):
                step.output = "Processing OHIP request..."
                
                response_content = """
🏥 **OHIP Operations Available:**

**🔍 Patient Search:**
- Search by health card number
- Search by name and date of birth
- Patient information lookup

**📋 Claims Management:**
- View claims history
- Submit new claims
- Check claim status

**⚙️ System Operations:**
- Test API connectivity
- Check authentication status
- Verify system health

To get started, try: "Test OAuth connection" or "Check API status"
"""
            else:
                # Use Gemini for general conversation
                step.output = "Generating response with Gemini..."
                
                system_prompt = """You are an OHIP (Ontario Health Insurance Plan) Assistant. You help users with:
1. OAuth authentication testing
2. API connectivity checks  
3. Patient searches in the OHIP system
4. Claims history retrieval
5. New claim submissions
6. General OHIP-related questions

Always be helpful, professional, and ensure patient privacy is maintained. When users ask about OHIP operations, guide them on what information is needed and explain the process clearly.

If a user asks about something outside of OHIP/healthcare, politely redirect them back to OHIP-related topics."""
                
                response_content = await gemini_client.generate_response(messages, system_prompt)
        
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


def _format_api_response(result: Dict[str, Any], title: str) -> str:
    """Format API response for display."""
    if result.get("status") == "success":
        response = f"✅ **{title} - Success**\n\n"
        response += f"📝 **Message**: {result.get('message', 'Operation completed')}\n\n"
        
        data = result.get("data", {})
        if data:
            response += "📊 **Details**:\n"
            if isinstance(data, dict):
                # Special formatting for reservation data
                if "reservations" in data:
                    response += _format_reservation_data(data)
                else:
                    # Standard formatting for other data
                    for key, value in data.items():
                        if key == "token_preview":
                            response += f"• **Token**: {value}\n"
                        elif key == "token_length":
                            response += f"• **Token Length**: {value} characters\n"
                        elif key == "expires_at":
                            response += f"• **Expires**: {value}\n"
                        elif key == "base_url":
                            response += f"• **API URL**: {value}\n"
                        elif key == "enterprise_id":
                            response += f"• **Enterprise**: {value}\n"
                        else:
                            response += f"• **{key}**: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}\n"
        
        return response
    else:
        return f"❌ **{title} - Failed**: {result.get('message', 'Unknown error')}"


def _format_reservation_data(data: Dict[str, Any]) -> str:
    """Format reservation data for better display."""
    response = ""
    
    reservations = data.get("reservations", {})
    if isinstance(reservations, dict) and "reservation" in reservations:
        reservation_list = reservations["reservation"]
        if isinstance(reservation_list, list) and len(reservation_list) > 0:
            reservation = reservation_list[0]  # Get first reservation
            
            response += "🏨 **Reservation Information**:\n"
            
            # Extract key information
            if "reservationIdList" in reservation:
                ids = reservation["reservationIdList"]
                for id_info in ids:
                    if isinstance(id_info, dict):
                        response += f"• **{id_info.get('type', 'ID')}**: {id_info.get('id', 'N/A')}\n"
            
            # Guest information
            if "roomStay" in reservation:
                room_stays = reservation["roomStay"]
                if isinstance(room_stays, list) and len(room_stays) > 0:
                    room_stay = room_stays[0]
                    
                    if "guestCounts" in room_stay:
                        guest_counts = room_stay["guestCounts"]
                        response += f"• **Guests**: {guest_counts.get('adults', 0)} adults"
                        if guest_counts.get('children', 0) > 0:
                            response += f", {guest_counts['children']} children"
                        response += "\n"
                    
                    if "timeSpan" in room_stay:
                        time_span = room_stay["timeSpan"]
                        response += f"• **Check-in**: {time_span.get('startDate', 'N/A')}\n"
                        response += f"• **Check-out**: {time_span.get('endDate', 'N/A')}\n"
                    
                    if "roomTypes" in room_stay:
                        room_types = room_stay["roomTypes"]
                        if isinstance(room_types, list) and len(room_types) > 0:
                            room_type = room_types[0]
                            response += f"• **Room Type**: {room_type.get('roomTypeCode', 'N/A')}\n"
            
            # Guest names
            if "resGuests" in reservation:
                guests = reservation["resGuests"]
                if isinstance(guests, list) and len(guests) > 0:
                    guest = guests[0]
                    if "profileInfo" in guest and "profile" in guest["profileInfo"]:
                        profile = guest["profileInfo"]["profile"]
                        if "customer" in profile and "personName" in profile["customer"]:
                            person_name = profile["customer"]["personName"]
                            name_parts = []
                            if "givenName" in person_name:
                                name_parts.append(person_name["givenName"])
                            if "surname" in person_name:
                                name_parts.append(person_name["surname"])
                            if name_parts:
                                response += f"• **Guest Name**: {' '.join(name_parts)}\n"
            
            # Reservation status
            if "reservationStatus" in reservation:
                response += f"• **Status**: {reservation['reservationStatus']}\n"
    
    # Show available data keys for debugging
    response += f"\n📋 **Available Data**: {', '.join(data.keys())}\n"
    
    return response


@cl.on_stop
async def on_stop():
    """Handle chat session stop."""
    logger.info("Chat session stopped")


if __name__ == "__main__":
    # This allows running the app directly but chainlit run is preferred
    pass

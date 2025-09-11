#!/usr/bin/env python3
"""
Chainlit application with LLM-based parameter extraction for hotel reservations.
This version uses Gemini LLM to intelligently parse user requests instead of regex.
"""

import chainlit as cl
import logging
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ohip_mcp.api_clients.ohip_client import APIClient
from ohip_mcp.chainlit_app.gemini_client import GeminiClient
from ohip_mcp.langraph_workflows.ohip_workflow import OHIPWorkflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
api_client = APIClient()
gemini_client = GeminiClient()
ohip_workflow = OHIPWorkflow()


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
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
                "• 🏨 **Hotel Reservations** - Get reservation details using AI extraction\n"
                "• 🔧 **OHIP Operations** - Search patients, view claims, submit claims\n\n"
                "Try asking:\n"
                "- 'Refresh token' - Get a fresh OAuth token\n"
                "- 'Test OAuth connection'\n"
                "- 'Check API status'\n"
                "- 'Get reservation details for hotel SYDH3 and reservation 218290'\n"
                "- 'Find reservation 12345 at hotel ABC123'\n"
                "- 'Search for patient information'\n\n"
                "🤖 **New Feature**: I now use AI to understand your requests naturally!\n"
                "How can I assist you today?"
    ).send()
    cl.user_session.set("messages", [])


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    try:
        # Get message history
        messages = cl.user_session.get("messages", [])
        messages.append({"role": "user", "content": message.content})
        
        content_lower = message.content.lower()
        
        async with cl.Step(name="Processing", type="run") as step:
            if "refresh token" in content_lower or "new token" in content_lower:
                step.output = "Requesting fresh OAuth token..."
                try:
                    await api_client.oauth_client.get_access_token(force_refresh=True)
                    response_content = "✅ **Token Refreshed Successfully!**\n\nA fresh OAuth token has been obtained and cached for future requests."
                except Exception as e:
                    response_content = f"❌ **Token Refresh Failed**: {str(e)}"
                    
            elif "test oauth" in content_lower or "oauth connection" in content_lower:
                step.output = "Testing OAuth connection..."
                try:
                    result = await api_client.test_oauth_token()
                    response_content = _format_api_response(result, "OAuth Connection Test")
                except Exception as e:
                    response_content = f"❌ **OAuth Connection Test Failed**: {str(e)}"
                    
            elif "test api" in content_lower or "api status" in content_lower or "check api" in content_lower:
                step.output = "Testing full API connection..."
                try:
                    result = await api_client.test_api_connection()
                    response_content = _format_api_response(result, "API Connection Test")
                except Exception as e:
                    response_content = f"❌ **API Connection Test Failed**: {str(e)}"
                    
            elif "reservation" in content_lower or "hotel" in content_lower:
                step.output = "🤖 Using AI to extract hotel and reservation details..."
                
                # Use Gemini LLM to intelligently extract hotel_id and reservation_id
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
                    logger.info(f"LLM extraction result: {extraction_result}")
                    
                    # Parse the JSON response
                    extracted_data = json.loads(extraction_result.strip())
                    
                    if "error" in extracted_data:
                        response_content = f"""
❌ **Extraction Failed**: {extracted_data['error']}

Please specify both hotel ID and reservation ID clearly. Examples:
- "Get reservation details for hotel SYDH3 and reservation 218290"
- "Find reservation 12345 at hotel ABC123"
- "Look up hotel XYZ, reservation number 98765"
"""
                    elif "hotel_id" in extracted_data and "reservation_id" in extracted_data:
                        hotel_id = extracted_data["hotel_id"]
                        reservation_id = extracted_data["reservation_id"]
                        
                        step.output = f"✅ AI Extracted: Hotel {hotel_id}, Reservation {reservation_id}"
                        
                        try:
                            result = await api_client.get_reservation({
                                "hotel_id": hotel_id,
                                "reservation_id": reservation_id,
                                "fetch_instructions": "Reservation"
                            })
                            response_content = _format_api_response(result, "🏨 Reservation Details")
                        except Exception as e:
                            response_content = f"❌ **Reservation Lookup Failed**: {str(e)}"
                    else:
                        response_content = "❌ **Invalid Response**: Could not extract hotel ID and reservation ID. Please try again with a clearer format."
                        
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
                    
            else:
                # Use Gemini for general conversation
                step.output = "Generating response..."
                try:
                    response_content = await gemini_client.generate_response(message.content, messages)
                except Exception as e:
                    logger.error(f"Gemini error: {e}")
                    response_content = f"❌ I encountered an error: {str(e)}. Please try again."

        # Send the response
        await cl.Message(content=response_content).send()
        
        # Update message history
        messages.append({"role": "assistant", "content": response_content})
        cl.user_session.set("messages", messages)
        
    except Exception as e:
        logger.error(f"Error in main handler: {e}")
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
    # This won't be called when using chainlit run, but useful for debugging
    logger.info("Chainlit app initialized with LLM-based extraction")

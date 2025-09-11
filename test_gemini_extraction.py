#!/usr/bin/env python3
"""
Test script for Gemini 2.5 Flash-based parameter extraction
"""

import asyncio
import sys
import json
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ohip_mcp.chainlit_app.gemini_client import GeminiClient


async def test_gemini_extraction():
    """Test Gemini 2.5 Flash extraction with various inputs."""
    print("🤖 Testing Gemini 2.5 Flash Extraction")
    print("=" * 50)
    
    gemini_client = GeminiClient()
    
    test_messages = [
        "Get reservation details for hotel SYDH3 and reservation 218290",
        "Find reservation 12345 at hotel ABC123",
        "Look up hotel XYZ, reservation number 98765",
        "I need info for SYDH3 hotel and booking 218290",
        "Show me reservation 218290 from hotel SYDH3",
        "Can you get details for hotel invalid?",  # Should fail
    ]
    
    extraction_prompt_template = """
Extract the hotel ID and reservation ID from this user message:
"{message}"

Return ONLY a JSON object with this exact format:
{{"hotel_id": "EXTRACTED_HOTEL_ID", "reservation_id": "EXTRACTED_RESERVATION_ID"}}

Rules:
- hotel_id should be the hotel identifier (e.g., "SYDH3", "SAND01", "ABC123")
- reservation_id should be the reservation number (e.g., "218290", "123456", "12345")
- Keep original case/format when possible
- If you cannot find both values, return: {{"error": "Could not extract both hotel_id and reservation_id"}}
- Return ONLY the JSON, no other text
- Be flexible with different phrasings and formats
"""
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🔍 Test {i}: {message}")
        print("-" * 40)
        
        try:
            extraction_prompt = extraction_prompt_template.format(message=message)
            result = await gemini_client.generate_response(extraction_prompt, [])
            
            print(f"📤 Raw Response: {result}")
            
            # Try to parse JSON
            try:
                parsed = json.loads(result.strip())
                if "error" in parsed:
                    print(f"❌ Extraction Failed: {parsed['error']}")
                elif "hotel_id" in parsed and "reservation_id" in parsed:
                    print(f"✅ Success!")
                    print(f"   Hotel ID: {parsed['hotel_id']}")
                    print(f"   Reservation ID: {parsed['reservation_id']}")
                else:
                    print(f"⚠️  Unexpected format: {parsed}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎉 Gemini 2.5 Flash extraction test completed!")


if __name__ == "__main__":
    asyncio.run(test_gemini_extraction())

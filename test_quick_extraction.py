#!/usr/bin/env python3
"""
Quick test for the fixed Gemini 2.5 Flash extraction
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


async def test_quick_extraction():
    """Quick test of the fixed extraction."""
    print("🚀 Quick Test: Gemini 2.5 Flash Extraction")
    print("=" * 45)
    
    gemini_client = GeminiClient()
    
    test_message = "Get reservation details for hotel SYDH3 and reservation 218290"
    
    extraction_prompt = f"""
Extract the hotel ID and reservation ID from this user message:
"{test_message}"

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
    
    print(f"📝 Test Message: {test_message}")
    print("-" * 45)
    
    try:
        # This should call the fixed generate_response method
        result = await gemini_client.generate_response(extraction_prompt, [])
        
        print(f"📤 Raw Response: {result}")
        
        # Test the same parsing logic as in Chainlit
        import re
        clean_result = result.strip()
        if clean_result.startswith("```json"):
            clean_result = re.sub(r'^```json\s*\n?', '', clean_result)
            clean_result = re.sub(r'\n?```$', '', clean_result)
        elif clean_result.startswith("```"):
            clean_result = re.sub(r'^```\s*\n?', '', clean_result)
            clean_result = re.sub(r'\n?```$', '', clean_result)
        
        print(f"🧹 Cleaned Response: {clean_result}")
        
        try:
            parsed = json.loads(clean_result.strip())
            if "error" in parsed:
                print(f"❌ Extraction Failed: {parsed['error']}")
            elif "hotel_id" in parsed and "reservation_id" in parsed:
                print(f"✅ SUCCESS!")
                print(f"   🏨 Hotel ID: {parsed['hotel_id']}")
                print(f"   🎫 Reservation ID: {parsed['reservation_id']}")
            else:
                print(f"⚠️  Unexpected format: {parsed}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n🎯 Test completed!")


if __name__ == "__main__":
    asyncio.run(test_quick_extraction())

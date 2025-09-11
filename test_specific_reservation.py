#!/usr/bin/env python3
"""
Test script for specific hotel reservation: SYDH3 and reservation 218290
"""

import asyncio
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ohip_mcp.api_clients.ohip_client import APIClient


async def test_specific_reservation():
    """Test the specific reservation: SYDH3 and 218290."""
    print("🏨 Testing Specific Reservation")
    print("=" * 40)
    print("Hotel: SYDH3")
    print("Reservation: 218290")
    print()
    
    try:
        api_client = APIClient()
        
        # Test the exact request
        print("🔄 Making API request...")
        result = await api_client.get_reservation({
            "hotel_id": "SYDH3",
            "reservation_id": "218290",
            "fetch_instructions": "Reservation"
        })
        
        print("✅ Success!")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        
        data = result.get('data', {})
        if data:
            print("\n📊 Reservation Data:")
            print(f"Keys in response: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Show first few fields
            if isinstance(data, dict):
                for key, value in list(data.items())[:5]:
                    print(f"  {key}: {str(value)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Let's also test just the OAuth to make sure that's working
        print("\n🔐 Testing OAuth separately...")
        try:
            token_result = await api_client.test_oauth_token()
            print(f"OAuth Status: {token_result.get('status')}")
        except Exception as oauth_e:
            print(f"OAuth Error: {oauth_e}")
        
        return False


async def main():
    """Main function."""
    success = await test_specific_reservation()
    
    if success:
        print("\n🎉 Reservation lookup successful!")
    else:
        print("\n💡 Troubleshooting tips:")
        print("1. Check if hotel SYDH3 exists in your system")
        print("2. Verify reservation 218290 is valid")
        print("3. Ensure your OAuth credentials have access to this hotel")
        print("4. Check if the hotel ID should be lowercase: 'sydh3'")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

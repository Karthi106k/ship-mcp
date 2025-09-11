#!/usr/bin/env python3
"""
Test script for OAuth token endpoint integration.
Run this to test the OAuth authentication flow with your credentials.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ohip_mcp.api_clients.oauth_client import OAuthClient
from ohip_mcp.api_clients.ohip_client import APIClient
from ohip_mcp.config import get_settings


async def test_oauth_flow():
    """Test the complete OAuth flow."""
    print("🔐 Testing OAuth Authentication Flow")
    print("=" * 50)
    
    try:
        # Initialize OAuth client
        oauth_client = OAuthClient()
        
        print(f"📡 Target URL: {oauth_client.hostname}/oauth/v1/tokens")
        print(f"🏢 Enterprise ID: {oauth_client.enterprise_id}")
        print(f"🔑 Client ID: {oauth_client.client_id}")
        print(f"🗝️  App Key: {oauth_client.app_key[:10]}...")
        print()
        
        # Test token request
        print("🚀 Requesting OAuth token...")
        access_token = await oauth_client.get_access_token()
        
        print(f"✅ Token obtained successfully!")
        print(f"📝 Token preview: {access_token[:30]}...")
        print(f"📏 Token length: {len(access_token)} characters")
        
        if oauth_client._token_expires_at:
            print(f"⏰ Expires at: {oauth_client._token_expires_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth test failed: {e}")
        return False


async def test_api_client():
    """Test the API client with OAuth authentication."""
    print("\n🔧 Testing API Client")
    print("=" * 30)
    
    try:
        api_client = APIClient()
        
        # Test OAuth token
        print("🧪 Testing OAuth token method...")
        result = await api_client.test_oauth_token()
        
        print(f"✅ {result['message']}")
        print(f"📊 Token info: {result['data']}")
        
        # Test full connection
        print("\n🌐 Testing full API connection...")
        connection_result = await api_client.test_api_connection()
        
        print(f"✅ {connection_result['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ API client test failed: {e}")
        return False


def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking Environment Configuration")
    print("=" * 40)
    
    required_vars = [
        'HOSTNAME',
        'CLIENT_ID', 
        'CLIENT_SECRET',
        'ENTERPRISE_ID',
        'APP_KEY'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing_vars.append(var)
            print(f"❌ {var}: Not set or placeholder value")
        else:
            # Show partial value for security
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"\n⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print("📝 Please update your .env file with actual values")
        return False
    
    print("✅ All required environment variables are set")
    return True


async def main():
    """Main test function."""
    print("🏥 OAuth Token Endpoint Test")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix configuration before testing.")
        return False
    
    print()
    
    # Test OAuth flow
    oauth_success = await test_oauth_flow()
    
    if oauth_success:
        # Test API client
        api_success = await test_api_client()
        
        if api_success:
            print("\n🎉 All tests passed! Your OAuth integration is working correctly.")
            print("\n📋 Next steps:")
            print("1. Add more API endpoints to the client")
            print("2. Test with the MCP server: python -m ohip_mcp.server mcp")
            print("3. Test with Chainlit: python -m ohip_mcp.server chainlit")
            return True
        else:
            print("\n⚠️  OAuth works but API client has issues")
            return False
    else:
        print("\n❌ OAuth authentication failed")
        print("\n🔧 Troubleshooting:")
        print("- Check your credentials in .env file")
        print("- Verify network connectivity")
        print("- Check if the API endpoint is accessible")
        print("- Review logs for detailed error information")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

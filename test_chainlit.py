#!/usr/bin/env python3
"""
Test script for Chainlit app with OAuth integration.
"""

import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("🔧 Testing Chainlit App with OAuth Integration")
print("=" * 50)

try:
    # Test imports
    print("📦 Testing imports...")
    import chainlit as cl
    from ohip_mcp.chainlit_app.app import start, main
    from ohip_mcp.chainlit_app.gemini_client import GeminiClient
    from ohip_mcp.langraph_workflows.ohip_workflow import OHIPWorkflow
    print("✅ All imports successful!")
    
    # Test Gemini client
    print("\n🤖 Testing Gemini client...")
    gemini_client = GeminiClient()
    print("✅ Gemini client initialized!")
    
    # Test LangGraph workflow
    print("\n🔄 Testing LangGraph workflow...")
    workflow = OHIPWorkflow()
    print("✅ LangGraph workflow initialized!")
    
    print("\n🎉 All Chainlit tests passed!")
    print("\n🚀 Ready to start Chainlit app!")
    print("\n📋 To start the app:")
    print("   source venv311/bin/activate")
    print("   chainlit run src/ohip_mcp/chainlit_app/app.py")
    print("\n🌐 Then open: http://localhost:8000")
    
except Exception as e:
    print(f"❌ Chainlit test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

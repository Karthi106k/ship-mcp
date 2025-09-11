#!/usr/bin/env python3
"""
Quick start script for OHIP MCP Server
Run this to verify your setup and get started quickly.
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required. Current version:", sys.version)
        return False
    print("✅ Python version:", sys.version.split()[0])
    return True


def check_virtual_env():
    """Check if virtual environment is active."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is active")
        return True
    print("⚠️  Virtual environment not detected. Consider activating one.")
    return False


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['mcp', 'langgraph', 'chainlit', 'google-generativeai', 'httpx', 'pydantic']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False
    return True


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        print("📝 Create .env file:")
        print("cp env.example .env")
        return False
    
    print("✅ .env file exists")
    
    # Check for required variables
    required_vars = ['GEMINI_API_KEY', 'HOSTNAME', 'CLIENT_ID', 'CLIENT_SECRET', 'APP_KEY']
    missing_vars = []
    
    with open(env_path, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=your_" in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Please set these variables in .env:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Required environment variables are set")
    return True


def show_next_steps():
    """Show next steps to get started."""
    print("\n🚀 Next Steps:")
    print("1. Start the Chainlit interface:")
    print("   ./scripts/start_chainlit.sh")
    print("   OR")
    print("   python -m ohip_mcp.server chainlit")
    print("")
    print("2. Open your browser to: http://localhost:8000")
    print("")
    print("3. Test with sample queries:")
    print("   - 'Search for patient John Doe'")
    print("   - 'Get claims for patient 12345'")
    print("   - 'Submit a new claim'")
    print("")
    print("4. If you have a Postman collection:")
    print("   python scripts/postman_converter.py your_collection.json")


def main():
    """Main function to run all checks."""
    print("🏥 OHIP MCP Server - Quick Start Check")
    print("=" * 40)
    
    checks = [
        check_python_version(),
        check_virtual_env(),
        check_dependencies(),
        check_env_file()
    ]
    
    if all(checks):
        print("\n🎉 All checks passed! You're ready to go.")
        show_next_steps()
    else:
        print("\n❌ Some checks failed. Please fix the issues above before proceeding.")
        print("\n📚 For detailed setup instructions, see:")
        print("   - README.md")
        print("   - docs/SETUP_GUIDE.md")


if __name__ == "__main__":
    main()

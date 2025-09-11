"""Main server entry point for OHIP MCP Server."""

import asyncio
import logging
import sys
from pathlib import Path

from .config import get_settings


def setup_logging():
    """Set up logging configuration."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('ohip_mcp.log')
        ]
    )


async def run_mcp_server():
    """Run the MCP server."""
    from .mcp_server.server import main as mcp_main
    await mcp_main()


def run_chainlit_app():
    """Run the Chainlit chat application."""
    import chainlit as cl
    from .chainlit_app.app import main  # Import to register handlers
    
    settings = get_settings()
    
    # Run Chainlit app
    cl.run(
        host=settings.chainlit_host,
        port=settings.chainlit_port,
        headless=False,
        watch=True
    )


def main():
    """Main entry point - choose which component to run."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OHIP MCP Server")
    parser.add_argument(
        "component",
        choices=["mcp", "chainlit", "both"],
        help="Which component to run"
    )
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if args.component == "mcp":
        logger.info("Starting MCP server...")
        asyncio.run(run_mcp_server())
    elif args.component == "chainlit":
        logger.info("Starting Chainlit app...")
        run_chainlit_app()
    elif args.component == "both":
        logger.info("Starting both MCP server and Chainlit app...")
        # In a production setup, you'd run these in separate processes
        # For now, we'll just run Chainlit (which includes the workflow)
        run_chainlit_app()


if __name__ == "__main__":
    main()

"""Configuration management for OHIP MCP Server."""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Gemini API Configuration
    gemini_api_key: str
    
    # OAuth API Configuration  
    hostname: str
    client_id: str
    client_secret: str
    enterprise_id: str = "PSALES"
    app_key: str
    
    # Chainlit Configuration
    chainlit_host: str = "0.0.0.0"
    chainlit_port: int = 8000
    
    # MCP Server Configuration
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 3001
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()

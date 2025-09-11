"""OAuth client for handling token authentication."""

import asyncio
import base64
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from ..config import get_settings

logger = logging.getLogger(__name__)


class TokenResponse(BaseModel):
    """OAuth token response model."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: Optional[str] = None


class OAuthClient:
    """OAuth client for token management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.hostname = self.settings.hostname
        self.client_id = self.settings.client_id
        self.client_secret = self.settings.client_secret
        self.enterprise_id = self.settings.enterprise_id
        self.app_key = self.settings.app_key
        
        # Token caching
        self._cached_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def get_access_token(self, force_refresh: bool = False) -> str:
        """Get a valid access token, refreshing if necessary."""
        # Check if we should force a refresh or if we have a cached token that's still valid
        if (not force_refresh and 
            self._cached_token and 
            self._token_expires_at and 
            datetime.now() < self._token_expires_at - timedelta(minutes=5)):  # 5 min buffer
            logger.info("Using cached access token")
            return self._cached_token
        
        # Get new token
        logger.info("Requesting new access token" + (" (forced refresh)" if force_refresh else ""))
        token_response = await self._request_token()
        
        # Cache the token
        self._cached_token = token_response.access_token
        self._token_expires_at = datetime.now() + timedelta(seconds=token_response.expires_in)
        
        return self._cached_token
    
    async def _request_token(self) -> TokenResponse:
        """Request a new OAuth token."""
        url = f"{self.hostname}/oauth/v1/tokens"
        
        # Prepare headers based on your Postman configuration
        headers = {
            "Authorization": self._create_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
            "User-Agent": "PostmanRuntime/7.46.0",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "x-app-key": self.app_key,
            "enterpriseId": self.enterprise_id
        }
        
        # Prepare form data
        form_data = {
            "grant_type": "client_credentials",
            "scope": "urn:opc:hgbu:ws:__myscopes__"
        }
        
        # Add hashed app key (based on your Postman script)
        hashed_app_key = await self._create_hashed_app_key()
        headers["HashedAppKey"] = hashed_app_key
        
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Making OAuth token request to: {url}")
                response = await client.post(
                    url,
                    headers=headers,
                    data=form_data,
                    timeout=30.0
                )
                
                response.raise_for_status()
                token_data = response.json()
                
                logger.info("Successfully obtained OAuth token")
                return TokenResponse(**token_data)
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise Exception(f"OAuth token request failed: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Token request error: {e}")
                raise Exception(f"Failed to get OAuth token: {str(e)}")
    
    def _create_basic_auth_header(self) -> str:
        """Create Basic Auth header from client credentials."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    async def _create_hashed_app_key(self) -> str:
        """Create hashed app key based on your Postman script logic."""
        # This mimics the JavaScript crypto logic from your Postman script
        app_key_bytes = self.app_key.encode('utf-8')
        
        # Create SHA-256 hash
        hash_object = hashlib.sha256(app_key_bytes)
        hash_hex = hash_object.hexdigest()
        
        logger.debug(f"Created hashed app key: {hash_hex[:10]}...")
        return hash_hex
    
    async def get_authenticated_headers(self, force_refresh: bool = False) -> Dict[str, str]:
        """Get headers with valid authentication for API requests."""
        access_token = await self.get_access_token(force_refresh=force_refresh)
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-app-key": self.app_key,
            "enterpriseId": self.enterprise_id,
            "HashedAppKey": await self._create_hashed_app_key()
        }
    
    def clear_token_cache(self):
        """Clear cached token (force refresh on next request)."""
        self._cached_token = None
        self._token_expires_at = None
        logger.info("Token cache cleared")

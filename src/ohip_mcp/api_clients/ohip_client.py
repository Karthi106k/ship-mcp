"""API client for making requests to OAuth-protected endpoints."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from ..config import get_settings
from .oauth_client import OAuthClient

logger = logging.getLogger(__name__)


class APIClient:
    """Client for interacting with OAuth-protected API endpoints."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.hostname
        self.oauth_client = OAuthClient()
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Get authenticated headers from OAuth client
        headers = await self.oauth_client.get_authenticated_headers()
        
        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                # If unauthorized, clear token cache and retry once
                if e.response.status_code == 401:
                    logger.info("Received 401, clearing token cache and retrying...")
                    self.oauth_client.clear_token_cache()
                    # Could implement retry logic here
                raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Request error: {e}")
                raise Exception(f"Failed to make request to API: {str(e)}")
    
    async def search_patient(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for patients in the OHIP system."""
        # Filter out None values
        search_params = {k: v for k, v in params.items() if v is not None}
        
        logger.info(f"Searching for patient with params: {search_params}")
        
        # This would map to your actual OHIP API endpoint from Postman
        result = await self._make_request("GET", "/patients/search", params=search_params)
        
        return {
            "status": "success",
            "message": "Patient search completed",
            "data": result
        }
    
    async def get_patient_claims(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get claims history for a patient."""
        patient_id = params.get("patient_id")
        if not patient_id:
            raise ValueError("patient_id is required")
        
        query_params = {}
        if params.get("start_date"):
            query_params["start_date"] = params["start_date"]
        if params.get("end_date"):
            query_params["end_date"] = params["end_date"]
        
        logger.info(f"Getting claims for patient {patient_id} with params: {query_params}")
        
        # This would map to your actual OHIP API endpoint from Postman
        result = await self._make_request("GET", f"/patients/{patient_id}/claims", params=query_params)
        
        return {
            "status": "success",
            "message": f"Claims retrieved for patient {patient_id}",
            "data": result
        }
    
    async def submit_claim(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a new claim to OHIP."""
        required_fields = ["patient_id", "provider_id", "service_code", "service_date", "amount"]
        
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Required field '{field}' is missing")
        
        claim_data = {
            "patient_id": params["patient_id"],
            "provider_id": params["provider_id"],
            "service_code": params["service_code"],
            "service_date": params["service_date"],
            "amount": params["amount"]
        }
        
        logger.info(f"Submitting claim: {claim_data}")
        
        # This would map to your actual OHIP API endpoint from Postman
        result = await self._make_request("POST", "/claims", data=claim_data)
        
        return {
            "status": "success",
            "message": "Claim submitted successfully",
            "data": result
        }
    
    async def test_oauth_token(self) -> Dict[str, Any]:
        """Test OAuth token endpoint and return token information."""
        try:
            logger.info("Testing OAuth token endpoint")
            
            # Get access token (this will test the full OAuth flow)
            access_token = await self.oauth_client.get_access_token()
            
            # Get token info (you could decode JWT if needed)
            token_info = {
                "token_preview": access_token[:20] + "..." if len(access_token) > 20 else access_token,
                "token_length": len(access_token),
                "expires_at": self.oauth_client._token_expires_at.isoformat() if self.oauth_client._token_expires_at else None
            }
            
            return {
                "status": "success",
                "message": "OAuth token obtained successfully",
                "data": token_info
            }
            
        except Exception as e:
            logger.error(f"OAuth token test failed: {e}")
            raise Exception(f"OAuth token test failed: {str(e)}")
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """Test API connection with authentication."""
        try:
            logger.info("Testing API connection")
            
            # First test OAuth
            oauth_result = await self.test_oauth_token()
            
            # You can add more endpoint tests here once you have more endpoints
            
            return {
                "status": "success",
                "message": "API connection test successful",
                "data": {
                    "oauth_test": oauth_result,
                    "base_url": self.base_url,
                    "enterprise_id": self.settings.enterprise_id
                }
            }
            
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            raise Exception(f"API connection test failed: {str(e)}")
    
    async def get_reservation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get hotel reservation details."""
        hotel_id = params.get("hotel_id")
        reservation_id = params.get("reservation_id")
        fetch_instructions = params.get("fetch_instructions", "Reservation")
        
        if not hotel_id:
            raise ValueError("hotel_id is required")
        if not reservation_id:
            raise ValueError("reservation_id is required")
        
        logger.info(f"Getting reservation {reservation_id} for hotel {hotel_id}")
        
        # Build the endpoint URL
        endpoint = f"/rsv/v1/hotels/{hotel_id}/reservations/{reservation_id}"
        
        # Add query parameters
        query_params = {
            "fetchInstructions": fetch_instructions
        }
        
        try:
            # Get authenticated headers and add hotel-specific headers
            headers = await self.oauth_client.get_authenticated_headers()
            headers["x-hotelid"] = str(hotel_id)  # Add hotel ID header
            
            # Make the request
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            # Log the exact request details for debugging
            logger.info(f"Making request to: {url}")
            logger.info(f"Query params: {query_params}")
            logger.info(f"Hotel ID header: {hotel_id}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    headers=headers, 
                    params=query_params,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                return {
                    "status": "success",
                    "message": f"Reservation {reservation_id} retrieved successfully",
                    "data": result
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            if e.response.status_code == 401:
                logger.info("Received 401, clearing token cache and retrying...")
                self.oauth_client.clear_token_cache()
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise Exception(f"Failed to get reservation: {str(e)}")

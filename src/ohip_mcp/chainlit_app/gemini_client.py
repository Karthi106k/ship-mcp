"""Gemini API client for chat functionality."""

import logging
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from ..config import get_settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google's Gemini API."""
    
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def generate_response(
        self, 
        prompt: str, 
        messages: List[Dict[str, Any]] = None
    ) -> str:
        """Generate a response using Gemini API."""
        try:
            # For simple prompt-based generation, use the prompt directly
            if messages and len(messages) > 0:
                # Convert messages to Gemini format with system prompt
                gemini_prompt = self._convert_messages(messages, prompt)
            else:
                # Just use the prompt directly for extraction tasks
                gemini_prompt = prompt
            
            # Generate response
            response = await self.model.generate_content_async(gemini_prompt)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."
    
    def _convert_messages(
        self, 
        messages: List[Dict[str, Any]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Convert message history to Gemini prompt format."""
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}\n")
        
        if messages and isinstance(messages, list):
            for message in messages:
                if isinstance(message, dict):
                    role = message.get("role", "user")
                    content = message.get("content", "")
                    
                    if role == "user":
                        prompt_parts.append(f"Human: {content}")
                    elif role == "assistant":
                        prompt_parts.append(f"Assistant: {content}")
        
        # Add the current prompt
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent for OHIP operations."""
        intent_prompt = f"""
        Analyze the following message and determine if it's related to OHIP operations.
        
        Message: "{message}"
        
        Respond with JSON containing:
        - is_ohip_related: boolean
        - intent: one of "search_patient", "get_claims", "submit_claim", "general_question"
        - confidence: float between 0 and 1
        - extracted_params: object with any parameters you can extract
        
        Examples of OHIP operations:
        - "Search for patient John Doe" -> search_patient
        - "Get claims for patient ID 12345" -> get_claims  
        - "Submit a new claim for service A001" -> submit_claim
        """
        
        try:
            response = await self.model.generate_content_async(intent_prompt)
            # Parse JSON response (in a real implementation, you'd add proper JSON parsing)
            return {
                "is_ohip_related": True,  # Simplified for now
                "intent": "search_patient",
                "confidence": 0.8,
                "extracted_params": {}
            }
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {
                "is_ohip_related": False,
                "intent": "general_question", 
                "confidence": 0.0,
                "extracted_params": {}
            }

"""LangGraph workflow for OHIP operations."""

import json
import logging
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END

from ..api_clients.ohip_client import APIClient

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State for the OHIP workflow."""
    messages: List[Dict[str, Any]]
    current_step: str
    patient_data: Optional[Dict[str, Any]]
    claims_data: Optional[List[Dict[str, Any]]]
    error: Optional[str]
    result: Optional[Dict[str, Any]]


class OHIPWorkflow:
    """LangGraph workflow for OHIP operations."""
    
    def __init__(self):
        self.api_client = APIClient()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("analyze_request", self._analyze_request)
        workflow.add_node("search_patient", self._search_patient)
        workflow.add_node("get_claims", self._get_claims)
        workflow.add_node("submit_claim", self._submit_claim)
        workflow.add_node("format_response", self._format_response)
        workflow.add_node("handle_error", self._handle_error)
        
        # Add edges
        workflow.set_entry_point("analyze_request")
        
        workflow.add_conditional_edges(
            "analyze_request",
            self._route_request,
            {
                "search_patient": "search_patient",
                "get_claims": "get_claims", 
                "submit_claim": "submit_claim",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("search_patient", "format_response")
        workflow.add_edge("get_claims", "format_response")
        workflow.add_edge("submit_claim", "format_response")
        workflow.add_edge("format_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def _analyze_request(self, state: WorkflowState) -> WorkflowState:
        """Analyze the incoming request to determine the operation."""
        logger.info("Analyzing request")
        
        if not state.get("messages"):
            state["error"] = "No messages provided"
            state["current_step"] = "error"
            return state
        
        last_message = state["messages"][-1]
        content = last_message.get("content", "").lower()
        
        # Simple intent classification
        if "search" in content or "find patient" in content:
            state["current_step"] = "search_patient"
        elif "claims" in content or "claim history" in content:
            state["current_step"] = "get_claims"
        elif "submit" in content or "new claim" in content:
            state["current_step"] = "submit_claim"
        else:
            state["current_step"] = "search_patient"  # Default
        
        logger.info(f"Determined operation: {state['current_step']}")
        return state
    
    def _route_request(self, state: WorkflowState) -> str:
        """Route the request based on analysis."""
        return state.get("current_step", "error")
    
    async def _search_patient(self, state: WorkflowState) -> WorkflowState:
        """Search for a patient."""
        logger.info("Executing patient search")
        
        try:
            # Extract search parameters from the message
            # In a real implementation, you'd use NLP to extract these
            search_params = self._extract_patient_params(state["messages"][-1])
            
            result = await self.api_client.search_patient(search_params)
            state["patient_data"] = result
            state["result"] = result
            state["current_step"] = "format_response"
            
        except Exception as e:
            logger.error(f"Error searching patient: {e}")
            state["error"] = str(e)
            state["current_step"] = "error"
        
        return state
    
    async def _get_claims(self, state: WorkflowState) -> WorkflowState:
        """Get patient claims."""
        logger.info("Executing claims retrieval")
        
        try:
            # Extract claims parameters from the message
            claims_params = self._extract_claims_params(state["messages"][-1])
            
            result = await self.api_client.get_patient_claims(claims_params)
            state["claims_data"] = result.get("data", [])
            state["result"] = result
            state["current_step"] = "format_response"
            
        except Exception as e:
            logger.error(f"Error getting claims: {e}")
            state["error"] = str(e)
            state["current_step"] = "error"
        
        return state
    
    async def _submit_claim(self, state: WorkflowState) -> WorkflowState:
        """Submit a new claim."""
        logger.info("Executing claim submission")
        
        try:
            # Extract claim parameters from the message
            claim_params = self._extract_claim_params(state["messages"][-1])
            
            result = await self.api_client.submit_claim(claim_params)
            state["result"] = result
            state["current_step"] = "format_response"
            
        except Exception as e:
            logger.error(f"Error submitting claim: {e}")
            state["error"] = str(e)
            state["current_step"] = "error"
        
        return state
    
    async def _format_response(self, state: WorkflowState) -> WorkflowState:
        """Format the response for the user."""
        logger.info("Formatting response")
        
        if state.get("result"):
            # Create a user-friendly response
            result = state["result"]
            formatted_message = {
                "role": "assistant",
                "content": f"Operation completed successfully. Result: {json.dumps(result, indent=2)}"
            }
            state["messages"].append(formatted_message)
        
        return state
    
    async def _handle_error(self, state: WorkflowState) -> WorkflowState:
        """Handle errors in the workflow."""
        logger.info("Handling error")
        
        error_message = {
            "role": "assistant",
            "content": f"I encountered an error: {state.get('error', 'Unknown error')}"
        }
        state["messages"].append(error_message)
        
        return state
    
    def _extract_patient_params(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient search parameters from message."""
        # This is a simplified implementation
        # In practice, you'd use NLP to extract these parameters
        content = message.get("content", "")
        
        # For now, return empty dict - this would be enhanced with actual parameter extraction
        return {}
    
    def _extract_claims_params(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Extract claims parameters from message."""
        # Simplified implementation
        content = message.get("content", "")
        
        # For now, return basic params - this would be enhanced with actual parameter extraction
        return {"patient_id": "example_patient_id"}
    
    def _extract_claim_params(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Extract claim submission parameters from message."""
        # Simplified implementation
        content = message.get("content", "")
        
        # For now, return basic params - this would be enhanced with actual parameter extraction
        return {
            "patient_id": "example_patient_id",
            "provider_id": "example_provider_id", 
            "service_code": "A001",
            "service_date": "2025-09-11",
            "amount": 100.0
        }
    
    async def run(self, messages: List[Dict[str, Any]]) -> WorkflowState:
        """Run the workflow with the given messages."""
        initial_state = WorkflowState(
            messages=messages,
            current_step="analyze_request",
            patient_data=None,
            claims_data=None,
            error=None,
            result=None
        )
        
        result = await self.workflow.ainvoke(initial_state)
        return result

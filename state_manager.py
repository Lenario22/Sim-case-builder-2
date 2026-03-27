"""
State Manager Module
Handles robust Streamlit session state management for medical simulation cases.
Ensures data persists across reruns and branching logic is applied consistently.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import json


class SimulationStateManager:
    """
    Manages the lifecycle of a simulation case through session state.
    
    Attributes:
        STATE_KEY_CASE: Key for the main case data dictionary
        STATE_KEY_VALIDATION: Key for validation results
        STATE_KEY_GENERATION_LOG: Key for generation event tracking
    """
    
    STATE_KEY_CASE = "sim_case_data"
    STATE_KEY_VALIDATION = "case_validation"
    STATE_KEY_GENERATION_LOG = "generation_log"
    STATE_KEY_UI_STAGE = "ui_stage"  # "input", "generating", "generated", "exported"
    
    def __init__(self):
        """Initialize state manager and ensure session state dict exists."""
        self._initialize_session()
    
    def _initialize_session(self) -> None:
        """Ensure all required session state keys are initialized."""
        if self.STATE_KEY_CASE not in st.session_state:
            st.session_state[self.STATE_KEY_CASE] = {}
        if self.STATE_KEY_VALIDATION not in st.session_state:
            st.session_state[self.STATE_KEY_VALIDATION] = {}
        if self.STATE_KEY_GENERATION_LOG not in st.session_state:
            st.session_state[self.STATE_KEY_GENERATION_LOG] = []
        if self.STATE_KEY_UI_STAGE not in st.session_state:
            st.session_state[self.STATE_KEY_UI_STAGE] = "input"
    
    def set_case_data(self, case_data: Dict[str, Any]) -> None:
        """
        Store case data in session state with validation.
        
        Args:
            case_data: Dictionary containing the complete case structure
            
        Raises:
            TypeError: If case_data is not a dictionary
        """
        if not isinstance(case_data, dict):
            raise TypeError(f"Expected dict, got {type(case_data).__name__}")
        st.session_state[self.STATE_KEY_CASE] = case_data
        self._log_generation_event("Case data persisted to session")
    
    def get_case_data(self) -> Dict[str, Any]:
        """
        Retrieve case data from session state.
        
        Returns:
            Dictionary containing case data, or empty dict if not set
        """
        return st.session_state.get(self.STATE_KEY_CASE, {})
    
    def set_validation_result(self, field: str, is_valid: bool, 
                            message: str = "") -> None:
        """
        Store validation result for a specific case field.
        
        Args:
            field: Name of the field being validated
            is_valid: Boolean indicating validation success
            message: Optional error/warning message
        """
        if self.STATE_KEY_VALIDATION not in st.session_state:
            st.session_state[self.STATE_KEY_VALIDATION] = {}
        
        st.session_state[self.STATE_KEY_VALIDATION][field] = {
            "is_valid": is_valid,
            "message": message
        }
    
    def get_validation_results(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all validation results.
        
        Returns:
            Dictionary mapping field names to validation results
        """
        return st.session_state.get(self.STATE_KEY_VALIDATION, {})
    
    def is_all_valid(self) -> bool:
        """
        Check if all fields have passed validation.
        
        Returns:
            True if no validation failures exist
        """
        validations = self.get_validation_results()
        return all(v.get("is_valid", False) for v in validations.values())
    
    def set_case_field(self, field_name: str, value: Any) -> None:
        """
        Update a single field in the case data.
        Useful for incremental updates during scenario branching.
        
        Args:
            field_name: Name of the field to update
            value: New value for the field
        """
        case_data = self.get_case_data()
        case_data[field_name] = value
        st.session_state[self.STATE_KEY_CASE] = case_data
    
    def get_case_field(self, field_name: str, default: Any = None) -> Any:
        """
        Retrieve a single field from case data.
        
        Args:
            field_name: Name of the field
            default: Value to return if field doesn't exist
            
        Returns:
            Field value or default
        """
        case_data = self.get_case_data()
        return case_data.get(field_name, default)
    
    def apply_state_transition(self, from_state: str, to_state: str,
                              action_description: str) -> bool:
        """
        Apply a state transition and log it.
        Used for tracking UI progression (input → generating → generated).
        
        Args:
            from_state: Expected current state
            to_state: Target state
            action_description: Human-readable action description
            
        Returns:
            True if transition was valid, False otherwise
        """
        current_state = st.session_state.get(self.STATE_KEY_UI_STAGE, "input")
        
        if current_state != from_state:
            self._log_generation_event(
                f"Invalid state transition: {current_state} → {to_state}"
            )
            return False
        
        st.session_state[self.STATE_KEY_UI_STAGE] = to_state
        self._log_generation_event(
            f"State transition: {from_state} → {to_state} ({action_description})"
        )
        return True
    
    def get_current_state(self) -> str:
        """Get the current UI stage state."""
        return st.session_state.get(self.STATE_KEY_UI_STAGE, "input")
    
    def _log_generation_event(self, event_message: str) -> None:
        """
        Internal method to track generation events for debugging.
        
        Args:
            event_message: Description of the event
        """
        from datetime import datetime
        
        if self.STATE_KEY_GENERATION_LOG not in st.session_state:
            st.session_state[self.STATE_KEY_GENERATION_LOG] = []
        
        timestamp = datetime.now().isoformat()
        st.session_state[self.STATE_KEY_GENERATION_LOG].append({
            "timestamp": timestamp,
            "message": event_message
        })
    
    def get_generation_log(self) -> List[Dict[str, str]]:
        """
        Retrieve the complete generation event log.
        Useful for debugging during development.
        
        Returns:
            List of event dictionaries
        """
        return st.session_state.get(self.STATE_KEY_GENERATION_LOG, [])
    
    def clear_case(self) -> None:
        """Reset all case data and return to input state."""
        st.session_state[self.STATE_KEY_CASE] = {}
        st.session_state[self.STATE_KEY_VALIDATION] = {}
        st.session_state[self.STATE_KEY_UI_STAGE] = "input"
        self._log_generation_event("Case cleared by user")
    
    def export_case_snapshot(self) -> str:
        """
        Export current case state as JSON for backup/debugging.
        
        Returns:
            JSON string representation of case data
        """
        return json.dumps(self.get_case_data(), indent=2, default=str)

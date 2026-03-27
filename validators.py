"""
Validators Module
Implements validation rules for medical simulation cases.
Ensures that cases are logically complete and clinically appropriate.
"""

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    field_name: str
    message: str
    severity: str  # "error", "warning", "info"
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class CaseValidator:
    """
    Comprehensive validation engine for medical simulation cases.
    
    Validates:
    - Case structure completeness
    - Clinical appropriateness
    - Logical branching integrity
    - Data type correctness
    """
    
    # Minimum requirements for a complete case
    REQUIRED_CASE_FIELDS = {
        "case_name": "Case name/title",
        "diagnosis": "Primary diagnosis",
        "target_learner": "Target learner level",
        "difficulty": "Scenario difficulty",
        "age": "Patient age",
        "gender": "Patient gender",
        "chief_complaint": "Chief complaint",
        "hpi": "History of present illness",
        "vital_signs": "Initial vital signs",
    }
    
    # Minimum requirements for each scenario state
    REQUIRED_STATE_FIELDS = {
        "name": "State name",
        "vital_signs": "Vital signs",
        "pe": "Physical exam findings",
        "actions": "Expected clinical actions",
        "progression_logic": "Logic for next state"
    }
    
    # Valid values for categorical fields
    VALID_DIFFICULTIES = ["Basic", "Intermediate", "Advanced", "Nightmare"]
    VALID_LEARNERS = ["Medical Students", "Residents", "Registered Nurses (RNs)", "Interprofessional Team"]
    VALID_GENDERS = ["Male", "Female", "Non-binary", "Unspecified"]
    
    # Vital sign ranges (reasonable clinical bounds)
    VITAL_RANGES = {
        "heart_rate": (40, 180),
        "systolic_bp": (50, 220),
        "diastolic_bp": (30, 140),
        "respiratory_rate": (8, 50),
        "temperature_f": (95.0, 107.0),
        "o2_saturation": (50, 100),
        "glucose": (40, 600),
    }
    
    def __init__(self):
        """Initialize validator."""
        self.validation_results: List[ValidationResult] = []
    
    def validate_complete_case(self, case_data: Dict[str, Any]) -> Tuple[bool, List[ValidationResult]]:
        """
        Perform comprehensive validation of a complete case.
        
        Args:
            case_data: Complete case dictionary
            
        Returns:
            Tuple of (is_valid, list of ValidationResult objects)
        """
        self.validation_results = []
        
        # Validate basic structure
        self._validate_case_structure(case_data)
        
        # Validate specific fields
        self._validate_case_fields(case_data)
        
        # Validate state progression
        self._validate_state_progression(case_data)
        
        # Validate clinical logic
        self._validate_clinical_logic(case_data)
        
        # Check for completeness
        self._validate_completeness(case_data)
        
        is_valid = all(r.severity != "error" for r in self.validation_results)
        return is_valid, self.validation_results
    
    def _validate_case_structure(self, case_data: Dict[str, Any]) -> None:
        """Validate that all required top-level fields exist."""
        missing_fields = [
            field for field in self.REQUIRED_CASE_FIELDS
            if field not in case_data or not case_data[field]
        ]
        
        # Detailed check for each critical field
        for field_name, field_label in self.REQUIRED_CASE_FIELDS.items():
            if field_name not in case_data:
                self.validation_results.append(ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    message=f"Missing field: {field_label}",
                    severity="error",
                    suggestions=[f"Ensure {field_label} is populated"]
                ))
            elif not case_data[field_name]:
                self.validation_results.append(ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    message=f"Field is empty: {field_label}",
                    severity="error",
                    suggestions=[f"Populate {field_label} with relevant clinical information"]
                ))
            else:
                # Field exists and is non-empty, log as success
                self.validation_results.append(ValidationResult(
                    is_valid=True,
                    field_name=field_name,
                    message=f"✓ {field_label} populated",
                    severity="info"
                ))
        
        if missing_fields:
            self.validation_results.append(ValidationResult(
                is_valid=False,
                field_name="critical_fields_summary",
                message=f"Missing or empty required fields: {', '.join(missing_fields)}",
                severity="error",
                suggestions=[
                    "All 9 critical fields must be populated",
                    "Check: case_name, diagnosis, target_learner, difficulty, age, gender, chief_complaint, hpi, vital_signs"
                ]
            ))
    
    def _validate_case_fields(self, case_data: Dict[str, Any]) -> None:
        """Validate individual case fields for correctness."""
        # Validate difficulty
        if case_data.get("difficulty") not in self.VALID_DIFFICULTIES:
            self.validation_results.append(ValidationResult(
                is_valid=False,
                field_name="difficulty",
                message=f"Invalid difficulty: {case_data.get('difficulty')}",
                severity="error",
                suggestions=[f"Choose from: {', '.join(self.VALID_DIFFICULTIES)}"]
            ))
        
        # Validate target learner
        if case_data.get("target_learner") not in self.VALID_LEARNERS:
            self.validation_results.append(ValidationResult(
                is_valid=False,
                field_name="target_learner",
                message=f"Invalid learner type: {case_data.get('target_learner')}",
                severity="error",
                suggestions=[f"Choose from: {', '.join(self.VALID_LEARNERS)}"]
            ))
        
        # Validate gender
        if case_data.get("gender") not in self.VALID_GENDERS:
            self.validation_results.append(ValidationResult(
                is_valid=False,
                field_name="gender",
                message=f"Invalid gender: {case_data.get('gender')}",
                severity="warning",
                suggestions=[f"Choose from: {', '.join(self.VALID_GENDERS)}"]
            ))
        
        # Validate patient age
        age = case_data.get("age")
        if age is not None:
            try:
                age_int = int(age)
                if not (0 <= age_int <= 120):
                    self.validation_results.append(ValidationResult(
                        is_valid=False,
                        field_name="age",
                        message=f"Age {age_int} is out of realistic range (0-120)",
                        severity="warning",
                        suggestions=["Verify patient age is reasonable"]
                    ))
            except (ValueError, TypeError):
                self.validation_results.append(ValidationResult(
                    is_valid=False,
                    field_name="age",
                    message=f"Age must be a number, got {age}",
                    severity="error"
                ))
        
        # Validate vital signs (initial state)
        vitals = case_data.get("vital_signs", {})
        if isinstance(vitals, dict):
            for vital_name, (min_val, max_val) in self.VITAL_RANGES.items():
                if vital_name in vitals:
                    try:
                        vital_value = float(vitals[vital_name])
                        if not (min_val <= vital_value <= max_val):
                            self.validation_results.append(ValidationResult(
                                is_valid=False,
                                field_name=f"vital_signs.{vital_name}",
                                message=f"{vital_name} {vital_value} outside normal range ({min_val}-{max_val})",
                                severity="warning",
                                suggestions=[f"Verify {vital_name} is appropriate for {case_data.get('diagnosis')}"]
                            ))
                    except (ValueError, TypeError):
                        self.validation_results.append(ValidationResult(
                            is_valid=False,
                            field_name=f"vital_signs.{vital_name}",
                            message=f"{vital_name} must be numeric",
                            severity="error"
                        ))
    
    def _validate_state_progression(self, case_data: Dict[str, Any]) -> None:
        """Validate that all 5 scenario states are properly defined."""
        states_present = []
        
        for state_num in range(1, 6):
            state_key = f"s{state_num}_name"
            if state_key in case_data and case_data[state_key]:
                states_present.append(state_num)
        
        if len(states_present) < 2:
            self.validation_results.append(ValidationResult(
                is_valid=False,
                field_name="state_progression",
                message=f"Only {len(states_present)} states defined. Need at least 2 for branching.",
                severity="error",
                suggestions=[
                    "Define at least 2 scenario states (initial + one progression)",
                    "Ideally define all 5 states for complete branching logic"
                ]
            ))
        elif len(states_present) < 5:
            self.validation_results.append(ValidationResult(
                is_valid=True,
                field_name="state_progression",
                message=f"{len(states_present)} states defined (5 recommended for full branching)",
                severity="warning",
                suggestions=["Add remaining states for richer scenario branching"]
            ))
        
        # Validate that states are sequential
        if states_present != list(range(1, max(states_present) + 1)):
            self.validation_results.append(ValidationResult(
                is_valid=False,
                field_name="state_sequence",
                message="States are not sequential (e.g., State 1, 2, 3, missing 4)",
                severity="warning",
                suggestions=["Ensure states are numbered consecutively"]
            ))
    
    def _validate_clinical_logic(self, case_data: Dict[str, Any]) -> None:
        """Validate clinical appropriateness and logic."""
        diagnosis = case_data.get("diagnosis", "").lower()
        
        # Check if diagnosis is reasonable
        common_diagnoses = ["sepsis", "myocardial infarction", "anaphylaxis", 
                          "pulmonary embolism", "dka", "asthma exacerbation"]
        
        if not any(diag in diagnosis for diag in common_diagnoses):
            self.validation_results.append(ValidationResult(
                is_valid=True,
                field_name="diagnosis",
                message=f"Diagnosis '{diagnosis}' is not in common templates",
                severity="info",
                suggestions=["Check if custom diagnosis is appropriate for learner level"]
            ))
        
        # Validate critical actions exist
        critical_actions = case_data.get("critical_actions", [])
        if not critical_actions or len(critical_actions) < 2:
            self.validation_results.append(ValidationResult(
                is_valid=False,
                field_name="critical_actions",
                message="Less than 2 critical actions defined",
                severity="warning",
                suggestions=[
                    "Define at least 2 time-critical actions that learners must perform",
                    "Example: 'Administer antibiotics within 1 hour', 'Obtain IV access'"
                ]
            ))
        
        # Validate debrief questions exist
        debrief_questions = case_data.get("debrief_questions", [])
        if not debrief_questions or len(debrief_questions) < 2:
            self.validation_results.append(ValidationResult(
                is_valid=False,
                field_name="debrief_questions",
                message="Less than 2 debrief questions defined",
                severity="warning",
                suggestions=[
                    "Define at least 2 debrief questions for reflection",
                    "Example: 'What was the critical intervention you missed?', 'How did you prioritize?'"
                ]
            ))
    
    def _validate_completeness(self, case_data: Dict[str, Any]) -> None:
        """Validate that case has a clear start, progression, and end."""
        has_initial_state = case_data.get("s1_name") and case_data.get("s1_vitals")
        has_progressions = any(
            case_data.get(f"s{i}_name") for i in range(2, 6)
        )
        has_end_state = case_data.get("s5_name") or case_data.get("s4_name")
        
        if has_initial_state and has_progressions and has_end_state:
            self.validation_results.append(ValidationResult(
                is_valid=True,
                field_name="case_completeness",
                message="Case has complete start-progression-end structure",
                severity="info"
            ))
        else:
            missing = []
            if not has_initial_state:
                missing.append("Initial state (State 1)")
            if not has_progressions:
                missing.append("Progression states (States 2-4)")
            if not has_end_state:
                missing.append("End state (State 4-5)")
            
            self.validation_results.append(ValidationResult(
                is_valid=False,
                field_name="case_completeness",
                message=f"Case missing: {', '.join(missing)}",
                severity="error",
                suggestions=[
                    "Ensure case has: initial presentation → progression → resolution/complication",
                    "This creates the branching decision points"
                ]
            ))
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of validation results.
        
        Returns:
            Dictionary with counts and details
        """
        errors = [r for r in self.validation_results if r.severity == "error"]
        warnings = [r for r in self.validation_results if r.severity == "warning"]
        info = [r for r in self.validation_results if r.severity == "info"]
        
        return {
            "total_checks": len(self.validation_results),
            "errors": len(errors),
            "warnings": len(warnings),
            "info": len(info),
            "is_valid": len(errors) == 0,
            "error_details": [
                {"field": r.field_name, "message": r.message, "suggestions": r.suggestions}
                for r in errors
            ],
            "warning_details": [
                {"field": r.field_name, "message": r.message, "suggestions": r.suggestions}
                for r in warnings
            ]
        }

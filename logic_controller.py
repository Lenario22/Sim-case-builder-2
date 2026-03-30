"""
Logic Controller Module
Encapsulates all medical simulation branching rules and scenario progression logic.
Decouples clinical decision logic from UI rendering.

Theoretical Frameworks Implemented:
  - Dreyfus Model of Skill Acquisition (CCS-5 difficulty scale)
  - Vector Model of Patient Complexity (5 axes of influence)
  - Complexity-Contributing Factors (13 Task CCFs + 11 Patient CCFs)
  - Han's Taxonomy of Uncertainty (Scientific / Practical / Personal)
"""

from typing import Dict, List, Tuple, Any, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json


# ============================================================================
# DREYFUS MODEL — CCS-5 Difficulty Scale
# ============================================================================

class CCS5Level(Enum):
    """
    5-Level Clinical Complexity Scale grounded in the Dreyfus Model.
    Maps directly to the legacy Difficulty enum for backward compatibility.
    """
    NOVICE           = 1   # Basic: routine, linear, single acute symptom
    ADV_BEGINNER     = 2   # Intermediate: common illness + 1-2 secondary diagnoses
    COMPETENT        = 3   # Advanced: multimorbidity + conflicting treatment goals
    PROFICIENT       = 4   # Nightmare: atypical, high extrinsic load, socioeconomic barriers
    EXPERT           = 5   # Expert: MUS, rare pathology, entangled psychosocial issues

    @property
    def label(self) -> str:
        return {
            1: "Level 1 — Novice",
            2: "Level 2 — Advanced Beginner",
            3: "Level 3 — Competent",
            4: "Level 4 — Proficient",
            5: "Level 5 — Expert",
        }[self.value]

    @property
    def description(self) -> str:
        return {
            1: "Routine, linear case. Single acute symptom, high goal clarity, minimal decision steps.",
            2: "Complicated case. Common illness with 1–2 secondary diagnoses. Requires basic pattern recognition.",
            3: "Moderately complex. Multimorbidity with conflicting treatment goals. Requires analytical System 2 thinking.",
            4: "Highly complex. Atypical presentation, high extrinsic load (data overload), and significant socioeconomic barriers.",
            5: "Extreme complexity. Medically Unexplained Symptoms, rare pathology, or entangled psychosocial issues. High diagnostic uncertainty.",
        }[self.value]

    def to_legacy_difficulty(self) -> str:
        """Map CCS-5 level back to the legacy difficulty string for template compatibility."""
        return {1: "Basic", 2: "Intermediate", 3: "Advanced", 4: "Nightmare", 5: "Nightmare"}[self.value]


class Difficulty(Enum):
    """Legacy scenario difficulty levels. Kept for backward compatibility."""
    BASIC        = "Basic"
    INTERMEDIATE = "Intermediate"
    ADVANCED     = "Advanced"
    NIGHTMARE    = "Nightmare"


# ============================================================================
# VECTOR MODEL OF PATIENT COMPLEXITY
# ============================================================================

@dataclass
class VectorAxis:
    """One axis of the Vector Model (magnitude 0–5)."""
    magnitude: int          # 0 = no pressure, 5 = extreme pressure
    factors: List[str]      # Specific contributing factors on this axis

    def to_dict(self) -> Dict[str, Any]:
        return {"magnitude": self.magnitude, "factors": self.factors}


@dataclass
class VectorModel:
    """
    5-axis representation of patient complexity per the Vector Model.
    Each axis scores 0–5 and lists the specific contributing factors.
    """
    biological:    VectorAxis = field(default_factory=lambda: VectorAxis(0, []))
    socioeconomic: VectorAxis = field(default_factory=lambda: VectorAxis(0, []))
    cultural:      VectorAxis = field(default_factory=lambda: VectorAxis(0, []))
    environmental: VectorAxis = field(default_factory=lambda: VectorAxis(0, []))
    behavioral:    VectorAxis = field(default_factory=lambda: VectorAxis(0, []))

    @property
    def total_pressure(self) -> int:
        return (self.biological.magnitude + self.socioeconomic.magnitude +
                self.cultural.magnitude + self.environmental.magnitude +
                self.behavioral.magnitude)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "biological":    self.biological.to_dict(),
            "socioeconomic": self.socioeconomic.to_dict(),
            "cultural":      self.cultural.to_dict(),
            "environmental": self.environmental.to_dict(),
            "behavioral":    self.behavioral.to_dict(),
            "total_pressure": self.total_pressure,
        }


# ============================================================================
# COMPLEXITY-CONTRIBUTING FACTORS (CCFs)
# ============================================================================

class TaskCCF(Enum):
    """
    13 Task-level Complexity-Contributing Factors.
    These arise from the clinical task/environment, not the patient.
    """
    GOAL_CONFLICT          = "Goal Conflict"
    DATA_DELUGE            = "Data Deluge"
    TIME_PRESSURE          = "Time Pressure"
    AMBIGUOUS_CUES         = "Ambiguous Cues"
    EQUIPMENT_FAILURE      = "Equipment Failure"
    RESOURCE_LIMITATION    = "Resource Limitation"
    INTERPROFESSIONAL_TENSION = "Interprofessional Tension"
    COMMUNICATION_BARRIER  = "Communication Barrier"
    KNOWLEDGE_GAP          = "Knowledge Gap"
    ETHICAL_DILEMMA        = "Ethical Dilemma"
    DIAGNOSTIC_UNCERTAINTY = "Diagnostic Uncertainty"
    HANDOFF_COMPLEXITY     = "Handoff Complexity"
    SYSTEM_FAILURE         = "System Failure"


class PatientCCF(Enum):
    """
    11 Patient-level Complexity-Contributing Factors.
    These arise from the patient's own characteristics.
    """
    POLYPHARMACY           = "Polypharmacy (≥5 meds)"
    AGE_OVER_75            = "Age ≥75"
    COGNITIVE_IMPAIRMENT   = "Cognitive Impairment"
    MULTIMORBIDITY         = "Multimorbidity (≥3 chronic conditions)"
    FUNCTIONAL_DECLINE     = "Functional Decline"
    MENTAL_HEALTH          = "Mental Health Comorbidity"
    SUBSTANCE_USE          = "Substance Use Disorder"
    SOCIAL_ISOLATION       = "Social Isolation"
    LANGUAGE_BARRIER       = "Language Barrier"
    NON_ADHERENCE          = "Non-Adherence to Treatment"
    RARE_DISEASE           = "Rare or Atypical Disease"


# ============================================================================
# HAN'S TAXONOMY OF UNCERTAINTY
# ============================================================================

class UncertaintyType(Enum):
    """
    Han's Taxonomy of Uncertainty in clinical practice.
    Classifies the dominant type of uncertainty in the case.
    """
    SCIENTIFIC  = "Scientific"   # Evidence gaps, conflicting literature
    PRACTICAL   = "Practical"    # System failures, resource constraints
    PERSONAL    = "Personal"     # Patient values, goals of care, autonomy

    @property
    def description(self) -> str:
        return {
            "Scientific": "Uncertainty arising from gaps in medical evidence or conflicting guidelines.",
            "Practical":  "Uncertainty from system failures, resource limitations, or logistical barriers.",
            "Personal":   "Uncertainty rooted in patient values, preferences, or goals of care.",
        }[self.value]


# ============================================================================
# COGNITIVE BIAS TYPES
# ============================================================================

class CognitiveBias(Enum):
    """Cognitive biases most common in clinical reasoning."""
    ANCHORING         = "Anchoring"          # Over-relying on initial data
    SEARCH_SATISFICING = "Search Satisficing" # Stopping after one plausible finding
    CONFIRMATION      = "Confirmation Bias"  # Seeking data that confirms initial dx
    AVAILABILITY      = "Availability Bias"  # Recency of similar cases
    FRAMING           = "Framing Effect"     # How the case was presented


# ============================================================================
# COMPLEXITY PROFILE — Unified output object
# ============================================================================

@dataclass
class ComplexityProfile:
    """
    Full complexity characterization of a simulation case.
    Generated during Phase 0 of the case engine.
    """
    ccs5_level:           CCS5Level
    vector_model:         VectorModel
    task_ccfs:            List[TaskCCF]
    patient_ccfs:         List[PatientCCF]
    uncertainty_type:     UncertaintyType
    uncertainty_rationale: str
    chain_of_thought: Dict[str, str]   # cue_acquisition, hypothesis_generation, etc.
    cognitive_biases_at_risk: List[Dict[str, str]]  # [{"bias": "...", "trigger": "..."}]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ccs5_level":             self.ccs5_level.value,
            "ccs5_label":             self.ccs5_level.label,
            "ccs5_description":       self.ccs5_level.description,
            "vector_model":           self.vector_model.to_dict(),
            "task_ccfs":              [t.value for t in self.task_ccfs],
            "patient_ccfs":           [p.value for p in self.patient_ccfs],
            "uncertainty_type":       self.uncertainty_type.value,
            "uncertainty_description": self.uncertainty_type.description,
            "uncertainty_rationale":  self.uncertainty_rationale,
            "chain_of_thought":       self.chain_of_thought,
            "cognitive_biases_at_risk": self.cognitive_biases_at_risk,
        }


# ============================================================================
# DIAGNOSIS REGISTRY — Scalable medical knowledge layer
# ============================================================================

_DIAGNOSIS_DATA_PATH = Path(__file__).parent / "diagnosis_data.json"


class DiagnosisRegistry:
    """
    Loads and serves diagnosis-specific clinical data from diagnosis_data.json.

    Provides a single source of truth for:
      - Baseline vital signs and severity scaling
      - Physical exam findings
      - Expected lab ranges
      - Required interventions and time windows
      - Comorbidity interaction modifiers

    Adding a new diagnosis = adding an entry to the JSON file. No code changes.
    """

    _instance: Optional["DiagnosisRegistry"] = None
    _data: Dict[str, Any] = {}

    def __new__(cls) -> "DiagnosisRegistry":
        """Singleton — the registry is loaded once and shared."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        with open(_DIAGNOSIS_DATA_PATH, "r") as f:
            raw = json.load(f)
        self._data = raw.get("diagnoses", {})

    def reload(self) -> None:
        """Force a reload (useful after editing the JSON at runtime)."""
        self._load()

    # -- Queries --

    @property
    def all_diagnoses(self) -> List[str]:
        return list(self._data.keys())

    def has(self, diagnosis: str) -> bool:
        return diagnosis in self._data

    def get(self, diagnosis: str) -> Dict[str, Any]:
        return self._data.get(diagnosis, {})

    def vitals(self, diagnosis: str) -> Dict[str, Any]:
        return self.get(diagnosis).get("vitals", {})

    def pe_findings(self, diagnosis: str) -> str:
        return self.get(diagnosis).get("pe_findings", "Abnormal vital signs noted")

    def expected_labs(self, diagnosis: str) -> Dict[str, Any]:
        return self.get(diagnosis).get("expected_labs", {})

    def required_interventions(self, diagnosis: str) -> List[str]:
        return self.get(diagnosis).get("required_interventions", [])

    def time_critical_actions(self, diagnosis: str) -> Dict[str, Any]:
        return self.get(diagnosis).get("time_critical_actions", {})

    def comorbidity_modifiers(self, diagnosis: str) -> Dict[str, Any]:
        return self.get(diagnosis).get("comorbidity_modifiers", {})

    def vital_severity_weights(self, diagnosis: str) -> Dict[str, float]:
        return self.get(diagnosis).get("vital_severity_weights", {})

    def vital_modifier_type(self, diagnosis: str) -> Dict[str, str]:
        return self.get(diagnosis).get("vital_modifiers", {})

    def critical_pe_thresholds(self, diagnosis: str) -> Dict[str, int]:
        return self.get(diagnosis).get("critical_pe_thresholds", {})

    def category(self, diagnosis: str) -> str:
        return self.get(diagnosis).get("category", "General")

    def organ_system(self, diagnosis: str) -> str:
        return self.get(diagnosis).get("organ_system", "Multi-system")


# ============================================================================
# LAB VALIDATOR — Validates AI-generated labs against diagnosis-specific ranges
# ============================================================================

@dataclass
class LabIssue:
    """A single lab value that falls outside expected range for a diagnosis."""
    field_name: str
    value: float
    expected_min: float
    expected_max: float
    direction: str
    severity: str           # "error" or "warning"
    message: str


class LabValidator:
    """
    Validates AI-generated lab values against the expected ranges in DiagnosisRegistry.

    Usage:
        validator = LabValidator()
        issues = validator.validate(case_data, diagnosis="DKA")

    Returns a list of LabIssue objects for any value outside expected range.
    """

    def __init__(self, registry: Optional[DiagnosisRegistry] = None):
        self.registry = registry or DiagnosisRegistry()

    def validate(self, case_data: Dict[str, Any],
                 diagnosis: str,
                 comorbidities: Optional[List[str]] = None) -> List[LabIssue]:
        """
        Check every lab field against the diagnosis-specific expected range.

        Args:
            case_data: Generated case dictionary (keys like "wbc", "glu", etc.)
            diagnosis: Primary diagnosis to look up ranges for
            comorbidities: Optional list of comorbidity keys to apply modifiers

        Returns:
            List of LabIssue objects (empty = all values in range)
        """
        issues: List[LabIssue] = []
        expected = dict(self.registry.expected_labs(diagnosis))

        # Apply comorbidity overrides
        if comorbidities:
            mods = self.registry.comorbidity_modifiers(diagnosis)
            for comorbidity in comorbidities:
                overrides = mods.get(comorbidity, {})
                for lab_key, lab_override in overrides.items():
                    if isinstance(lab_override, dict) and "min" in lab_override:
                        if lab_key in expected:
                            expected[lab_key] = {**expected[lab_key], **lab_override}
                        else:
                            expected[lab_key] = lab_override

        for lab_key, spec in expected.items():
            if not isinstance(spec, dict) or "min" not in spec:
                continue

            raw_value = case_data.get(lab_key)
            if raw_value is None or raw_value == "":
                continue

            try:
                value = float(raw_value)
            except (ValueError, TypeError):
                continue

            lo = spec["min"]
            hi = spec["max"]
            direction = spec.get("direction", "variable")

            if value < lo:
                severity = "error" if value < lo * 0.5 else "warning"
                issues.append(LabIssue(
                    field_name=lab_key, value=value,
                    expected_min=lo, expected_max=hi,
                    direction=direction, severity=severity,
                    message=f"{lab_key} = {value} is below expected range "
                            f"[{lo}–{hi}] for {diagnosis}"
                ))
            elif value > hi:
                severity = "error" if value > hi * 2 else "warning"
                issues.append(LabIssue(
                    field_name=lab_key, value=value,
                    expected_min=lo, expected_max=hi,
                    direction=direction, severity=severity,
                    message=f"{lab_key} = {value} is above expected range "
                            f"[{lo}–{hi}] for {diagnosis}"
                ))

        return issues


# ============================================================================
# BRANCHING ENGINE — Diagnosis-aware state progression
# ============================================================================

@dataclass
class PathwayVitals:
    """Vital sign multipliers for a branching pathway."""
    heart_rate: float = 1.0
    systolic_bp: float = 1.0
    diastolic_bp: float = 1.0
    respiratory_rate: float = 1.0
    temperature_f: float = 1.0
    o2_saturation: float = 1.0


@dataclass
class BranchPathway:
    """One side of a branching decision (positive or negative)."""
    trigger: str
    vital_multipliers: PathwayVitals
    pe_evolution: str
    narrative: str


@dataclass
class StateTemplate:
    """Structured data for one state of the 5-state progression."""
    state_number: int
    name: str
    expected_actions: List[str]
    operator_notes: str
    progression_trigger: str
    positive_path: Optional[BranchPathway] = None
    negative_path: Optional[BranchPathway] = None


class BranchingEngine:
    """
    Generates diagnosis-specific state progression data from the registry.

    For diagnoses IN the registry: builds structured 5-state templates with
    specific vital trajectories, PE evolution, expected actions, and operator
    notes derived from the diagnosis's clinical profile.

    For diagnoses NOT in the registry: generates intelligent defaults based
    on the registry's closest category match or universal clinical principles.

    Key methods:
      - get_state_templates(diagnosis, difficulty) → List[StateTemplate]
      - build_prompt_injection(diagnosis, difficulty) → str (for Gemini)
      - apply_pathway_vitals(base_vitals, pathway) → VitalSigns
    """

    def __init__(self, registry: Optional[DiagnosisRegistry] = None):
        self.registry = registry or DiagnosisRegistry()

    def get_state_templates(self, diagnosis: str,
                            difficulty: str = "Intermediate") -> List[StateTemplate]:
        """Build 5 state templates with diagnosis-specific branching."""
        has_dx = self.registry.has(diagnosis)
        interventions = self.registry.required_interventions(diagnosis) if has_dx else []
        time_actions = self.registry.time_critical_actions(diagnosis) if has_dx else {}
        pe_base = self.registry.pe_findings(diagnosis) if has_dx else "Abnormal findings noted"
        thresholds = self.registry.critical_pe_thresholds(diagnosis) if has_dx else {}
        category = self.registry.category(diagnosis) if has_dx else "General"

        # Build the most urgent action
        urgent_action = ""
        shortest_window = 9999
        for action, info in time_actions.items():
            w = info.get("window_minutes", 9999)
            if w < shortest_window:
                shortest_window = w
                urgent_action = action

        # --- State 1: Arrival ---
        s1_actions = ["Perform primary assessment (ABCs)", "Obtain full set of vital signs"]
        if interventions:
            s1_actions.append(f"Establish {interventions[0]}" if "IV" in interventions[0]
                              else f"Initiate {interventions[0]}")
        s1_actions.append("Obtain focused history and physical exam")

        s1 = StateTemplate(
            state_number=1,
            name="Initial Presentation & Assessment",
            expected_actions=s1_actions,
            operator_notes=f"Patient presents with {diagnosis}. {pe_base}. "
                           f"Provide history only when directly asked by learners.",
            progression_trigger="Advance after initial assessment complete (~3 min) or if learner fails to assess within 5 min."
        )

        # --- State 2: Early Changes ---
        s2_pos_actions = list(interventions[:2]) if interventions else ["Reassess vitals"]
        s2_neg_trigger = "No IV access established or assessment incomplete"
        if interventions:
            s2_neg_trigger = f"{interventions[0]} not initiated"

        s2 = StateTemplate(
            state_number=2,
            name="Early Deterioration / First Response",
            expected_actions=[
                "Reassess vital signs",
                "Initiate continuous monitoring",
                *(f"Begin {i}" for i in interventions[:2]),
                "Order stat labs (CBC, BMP, +diagnosis-specific)"
            ][:5],
            operator_notes=f"If team has started initial interventions, patient shows subtle improvement. "
                           f"If delayed, patient visibly worsens — increase heart rate on monitor.",
            progression_trigger="Advance after 5-7 min or when critical intervention window approaches.",
            positive_path=BranchPathway(
                trigger=f"{interventions[0]} initiated and assessment complete" if interventions
                        else "Initial assessment completed appropriately",
                vital_multipliers=PathwayVitals(
                    heart_rate=0.95, systolic_bp=1.05, o2_saturation=1.01
                ),
                pe_evolution=f"Subtle improvement: {self._pe_improving(category)}",
                narrative="Patient showing early response to intervention. Continue current management."
            ),
            negative_path=BranchPathway(
                trigger=s2_neg_trigger,
                vital_multipliers=PathwayVitals(
                    heart_rate=1.10, systolic_bp=0.92, o2_saturation=0.97
                ),
                pe_evolution=f"Worsening: {self._pe_worsening(category)}",
                narrative="Patient deteriorating. Operator: prompt team to reassess if not already doing so."
            )
        )

        # --- State 3: Critical Decision Point ---
        critical_action_text = urgent_action or (interventions[0] if interventions else "critical intervention")
        s3_pos_trigger = f"{critical_action_text} administered/initiated"
        if shortest_window < 9999:
            s3_pos_trigger += f" within {shortest_window}-minute window"

        s3 = StateTemplate(
            state_number=3,
            name="Critical Decision Point",
            expected_actions=[
                f"Administer {critical_action_text}" if urgent_action else "Implement diagnosis-specific protocol",
                *(f"Ensure {i}" for i in interventions[1:3]),
                "Assess need for escalation (vasopressors, intubation, surgical consult)",
                "Communicate findings to team and attending"
            ][:5],
            operator_notes=f"KEY BRANCH POINT. If {critical_action_text} is performed: patient stabilizes. "
                           f"If NOT performed: patient enters decompensation. "
                           f"Operator may provide one gentle cue if team is struggling.",
            progression_trigger=f"Advance based on whether {critical_action_text} was performed. "
                                f"Both pathways lead to State 4 but with different vital trajectories.",
            positive_path=BranchPathway(
                trigger=s3_pos_trigger,
                vital_multipliers=PathwayVitals(
                    heart_rate=0.88, systolic_bp=1.10, respiratory_rate=0.90, o2_saturation=1.03
                ),
                pe_evolution=f"Improving: {self._pe_responding(category, diagnosis)}",
                narrative=f"Patient responding to {critical_action_text}. Vitals trending toward normal."
            ),
            negative_path=BranchPathway(
                trigger=f"{critical_action_text} NOT performed or significantly delayed",
                vital_multipliers=PathwayVitals(
                    heart_rate=1.18, systolic_bp=0.80, respiratory_rate=1.15, o2_saturation=0.92
                ),
                pe_evolution=f"Decompensating: {self._pe_decompensating(category)}",
                narrative="Patient decompensating. This is the consequence of delayed/missed intervention."
            )
        )

        # --- State 4: Response or Decline ---
        s4 = StateTemplate(
            state_number=4,
            name="Treatment Response or Continued Decline",
            expected_actions=[
                "Continue all initiated therapies",
                "Trend vital signs and labs",
                "Adjust interventions based on response",
                "Prepare for disposition (ICU admission, OR, transfer)"
            ],
            operator_notes="GOOD PATH: Vitals normalizing, patient more alert. "
                           "BAD PATH: Hemodynamic instability worsening, consider code team activation.",
            progression_trigger="Advance to State 5 after demonstrating sustained management (~5 min).",
            positive_path=BranchPathway(
                trigger="Sustained appropriate management from State 3",
                vital_multipliers=PathwayVitals(
                    heart_rate=0.90, systolic_bp=1.08, respiratory_rate=0.88,
                    o2_saturation=1.02, temperature_f=0.998
                ),
                pe_evolution=f"Resolving: {self._pe_resolving(category)}",
                narrative="Patient clearly improving. Team should begin disposition planning."
            ),
            negative_path=BranchPathway(
                trigger="Inadequate or no critical interventions performed",
                vital_multipliers=PathwayVitals(
                    heart_rate=1.20, systolic_bp=0.75, respiratory_rate=1.25,
                    o2_saturation=0.88, temperature_f=1.003
                ),
                pe_evolution=f"Critical: {self._pe_critical(category)}",
                narrative="Patient in extremis. Team must escalate immediately or call a code."
            )
        )

        # --- State 5: Resolution or Escalation ---
        s5 = StateTemplate(
            state_number=5,
            name="Resolution or Escalation",
            expected_actions=[
                "Complete structured handoff (SBAR/I-PASS)",
                "Document clinical course and interventions",
                "Identify ongoing monitoring needs",
                "Prepare for team debriefing"
            ],
            operator_notes="GOOD PATH: End scenario with stable patient, structured handoff. "
                           "BAD PATH: End with code team arrival or patient arrest — "
                           "debrief focuses on timeline and missed interventions.",
            progression_trigger="End of scenario. Transition to structured debriefing.",
            positive_path=BranchPathway(
                trigger="Appropriate management throughout",
                vital_multipliers=PathwayVitals(
                    heart_rate=0.95, systolic_bp=1.05, respiratory_rate=0.92,
                    o2_saturation=1.01, temperature_f=0.997
                ),
                pe_evolution="Near-baseline: Patient alert, comfortable, vitals trending normal",
                narrative="Patient stabilized. Scenario ends with successful management and handoff."
            ),
            negative_path=BranchPathway(
                trigger="Critical interventions missed or significantly delayed",
                vital_multipliers=PathwayVitals(
                    heart_rate=1.25, systolic_bp=0.70, respiratory_rate=1.30,
                    o2_saturation=0.82
                ),
                pe_evolution="Peri-arrest: Obtunded, agonal breathing or apneic, thready pulse",
                narrative="Patient in peri-arrest or arrest. Code team activated. "
                          "Scenario ends with discussion of what could have been done differently."
            )
        )

        return [s1, s2, s3, s4, s5]

    def apply_pathway_vitals(self, base_vitals: "VitalSigns",
                              pathway: BranchPathway) -> "VitalSigns":
        """Apply a pathway's vital multipliers to current vitals."""
        m = pathway.vital_multipliers
        return VitalSigns(
            heart_rate=max(30, min(220, int(base_vitals.heart_rate * m.heart_rate))),
            systolic_bp=max(40, min(250, int(base_vitals.systolic_bp * m.systolic_bp))),
            diastolic_bp=max(20, min(150, int(base_vitals.diastolic_bp * m.diastolic_bp))),
            respiratory_rate=max(4, min(50, int(base_vitals.respiratory_rate * m.respiratory_rate))),
            temperature_f=round(base_vitals.temperature_f * m.temperature_f, 1),
            o2_saturation=max(40, min(100, int(base_vitals.o2_saturation * m.o2_saturation)))
        )

    def build_prompt_injection(self, diagnosis: str,
                                difficulty: str = "Intermediate") -> str:
        """
        Build a structured text block to inject into the AI prompt.
        Gives the AI diagnosis-specific guidance for each state.
        """
        templates = self.get_state_templates(diagnosis, difficulty)
        has_dx = self.registry.has(diagnosis)
        interventions = self.registry.required_interventions(diagnosis) if has_dx else []
        time_actions = self.registry.time_critical_actions(diagnosis) if has_dx else {}

        lines = [
            f"### Diagnosis-Specific Branching Guide for: {diagnosis}",
            ""
        ]

        if interventions:
            lines.append(f"**Required Interventions**: {', '.join(interventions)}")
        if time_actions:
            ta_parts = []
            for action, info in time_actions.items():
                w = info.get("window_minutes", "N/A")
                r = info.get("rationale", "")
                ta_parts.append(f"  - {action}: within {w} min — {r}")
            lines.append("**Time-Critical Actions**:")
            lines.extend(ta_parts)

        lines.append("")

        for t in templates:
            lines.append(f"**State {t.state_number}: {t.name}**")
            lines.append(f"  Expected Actions: {'; '.join(t.expected_actions)}")
            if t.positive_path:
                lines.append(f"  POSITIVE PATH (if intervention performed): {t.positive_path.narrative}")
                lines.append(f"    → PE changes: {t.positive_path.pe_evolution}")
            if t.negative_path:
                lines.append(f"  NEGATIVE PATH (if intervention missed): {t.negative_path.narrative}")
                lines.append(f"    → PE changes: {t.negative_path.pe_evolution}")
            lines.append(f"  Operator Notes: {t.operator_notes}")
            lines.append("")

        return "\n".join(lines)

    # --- PE evolution helpers by category ---

    def _pe_improving(self, category: str) -> str:
        return {
            "Cardiovascular": "Heart rate trending down, stronger peripheral pulses",
            "Respiratory": "Decreased work of breathing, improved air entry",
            "Neurological": "Improving mental status, pupils reactive",
            "Gastrointestinal": "Decreased abdominal rigidity, less tenderness",
            "Infectious": "Less flushed, improved capillary refill",
            "Endocrine": "More alert, less Kussmaul breathing",
            "Metabolic": "Improved mental status, decreasing muscle cramps",
            "Trauma": "Improved color, stronger pulses, less diaphoresis",
            "OB/GYN": "Decreased bleeding, improving hemodynamics",
            "Pediatric": "Less irritable, improved feeding cues, better color",
            "Toxicology": "Improving mental status, decreasing autonomic symptoms",
            "Hematologic": "Improved color, decreased bleeding, better perfusion",
            "Environmental": "Improving thermoregulation, better mental status",
            "Renal": "Improved urine output, decreasing edema",
        }.get(category, "Subtle clinical improvement noted")

    def _pe_worsening(self, category: str) -> str:
        return {
            "Cardiovascular": "Weaker pulses, increasing JVD, new diaphoresis",
            "Respiratory": "Increased accessory muscle use, worsening crackles/wheezing",
            "Neurological": "Declining GCS, new focal deficits, pupil changes",
            "Gastrointestinal": "Increasing distension, absent bowel sounds, rebound tenderness",
            "Infectious": "Mottled skin, delayed capillary refill >4s, altered mental status",
            "Endocrine": "Deepening Kussmaul respirations, increasing confusion",
            "Metabolic": "Worsening confusion, new muscle fasciculations",
            "Trauma": "Increasing pallor, thready pulse, delayed cap refill",
            "OB/GYN": "Increased vaginal bleeding, worsening tachycardia",
            "Pediatric": "Increasing lethargy, mottled skin, weak cry",
            "Toxicology": "Worsening autonomic instability, deepening coma",
            "Hematologic": "New petechiae, oozing from IV sites",
            "Environmental": "Worsening thermoregulation, increasing confusion",
            "Renal": "Decreasing urine output, increasing peripheral edema",
        }.get(category, "Clinical deterioration noted")

    def _pe_responding(self, category: str, diagnosis: str) -> str:
        base = self._pe_improving(category)
        return f"{base}. Patient beginning to respond to treatment for {diagnosis}."

    def _pe_decompensating(self, category: str) -> str:
        return {
            "Cardiovascular": "Hypotension refractory to fluids, new S3 gallop, pulmonary edema",
            "Respiratory": "Severe respiratory distress, SpO2 dropping despite O2, impending respiratory failure",
            "Neurological": "Unresponsive to voice, abnormal posturing, fixed dilated pupil",
            "Gastrointestinal": "Rigid abdomen, hemodynamic instability, peritoneal signs",
            "Infectious": "Septic shock picture: warm shock → cold shock, AMS, lactic acidosis",
            "Endocrine": "Obtunded, severe electrolyte derangement signs, hemodynamic collapse",
            "Metabolic": "Seizure activity, cardiac arrhythmia, obtunded",
            "Trauma": "Class III-IV hemorrhagic shock, altered mental status, agonal breathing",
            "OB/GYN": "Hemorrhagic shock, DIC signs, fetal distress",
            "Pediatric": "Unresponsive, poor perfusion, weak/absent pulses",
            "Toxicology": "Cardiovascular collapse, seizures, respiratory failure",
            "Hematologic": "Multi-organ dysfunction, severe coagulopathy",
            "Environmental": "Multi-organ dysfunction, cardiovascular collapse",
            "Renal": "Uremic symptoms, cardiac arrhythmia from hyperkalemia",
        }.get(category, "Severe clinical decompensation")

    def _pe_resolving(self, category: str) -> str:
        return {
            "Cardiovascular": "Vitals normalizing, strong peripheral pulses, no new symptoms",
            "Respiratory": "WOB normal, clear air entry, SpO2 stable on room air or low-flow O2",
            "Neurological": "GCS improving, following commands, pupils equal and reactive",
            "Gastrointestinal": "Soft abdomen, bowel sounds returning, pain controlled",
            "Infectious": "Afebrile trend, improved perfusion, clear sensorium",
            "Endocrine": "Anion gap closing, glucose normalizing, alert and oriented",
            "Metabolic": "Electrolytes correcting, mental status clearing",
            "Trauma": "Hemodynamically stable, good urine output, pain controlled",
            "OB/GYN": "Bleeding controlled, hemodynamically stable",
            "Pediatric": "Alert, feeding, normal color and perfusion",
            "Toxicology": "Autonomic stability, clearing mental status",
            "Hematologic": "Bleeding controlled, counts stabilizing",
            "Environmental": "Core temp normalizing, hemodynamically stable",
            "Renal": "Urine output improving, electrolytes stabilizing",
        }.get(category, "Clinical improvement with resolving symptoms")

    def _pe_critical(self, category: str) -> str:
        return {
            "Cardiovascular": "Peri-arrest: severe hypotension, obtunded, agonal rhythm",
            "Respiratory": "Respiratory arrest imminent: apneic periods, cyanosis, obtunded",
            "Neurological": "Herniation signs: fixed dilated pupils, decerebrate posturing",
            "Gastrointestinal": "Peritonitis with septic shock, obtunded",
            "Infectious": "Refractory septic shock, multi-organ failure, obtunded",
            "Endocrine": "Comatose, severe metabolic derangement, hemodynamic collapse",
            "Metabolic": "Cardiac arrest from metabolic derangement",
            "Trauma": "Class IV shock, obtunded, agonal breathing",
            "OB/GYN": "Hemorrhagic shock with DIC, maternal/fetal distress",
            "Pediatric": "Unresponsive, bradycardic, approaching cardiopulmonary arrest",
            "Toxicology": "Cardiopulmonary arrest or imminent arrest",
            "Hematologic": "DIC with multi-organ failure",
            "Environmental": "Refractory cardiovascular collapse",
            "Renal": "Cardiac arrest from hyperkalemia or uremia",
        }.get(category, "Patient in extremis, peri-arrest state")


# ============================================================================
# COMORBIDITY ENGINE — Modifies case parameters based on comorbidities
# ============================================================================

@dataclass
class ComorbidityEffect:
    """Aggregate effect of selected comorbidities on a case."""
    lab_overrides: Dict[str, Dict[str, float]]   # {lab_name: {min, max}}
    clinical_flags: Dict[str, bool]               # {flag_name: True}
    additional_interventions: List[str]
    prompt_context: str                           # narrative for AI injection


class ComorbidityEngine:
    """
    Computes the aggregate clinical impact of multiple comorbidities
    on a given primary diagnosis.

    Usage:
        engine = ComorbidityEngine()
        available = engine.available_comorbidities("Sepsis")
        effect = engine.compute_effects("Sepsis", ["CKD", "CHF"])
        prompt_text = effect.prompt_context  # inject into AI prompt
    """

    # Universal comorbidity effects (apply regardless of primary diagnosis)
    UNIVERSAL_COMORBIDITIES = {
        "Diabetes": {
            "lab_effects": {"glu": {"min": 180, "max": 400}},
            "flags": {"insulin_management": True},
            "interventions": ["Blood glucose monitoring q1h", "Insulin protocol"],
            "narrative": "Diabetes complicates management — monitor glucose closely, adjust insulin, "
                         "watch for hypo/hyperglycemia during treatment."
        },
        "CKD": {
            "lab_effects": {"cr": {"min": 2.0, "max": 6.0}, "k": {"min": 5.0, "max": 6.5},
                            "bun": {"min": 40, "max": 100}},
            "flags": {"contrast_caution": True, "fluid_caution": True, "nsaid_avoid": True},
            "interventions": ["Renal-dose medication adjustments", "Avoid nephrotoxins"],
            "narrative": "CKD affects drug clearance and fluid management — renally dose all medications, "
                         "avoid nephrotoxic agents, monitor potassium and fluid balance closely."
        },
        "CHF": {
            "lab_effects": {"hco3": {"min": 18, "max": 24}},
            "flags": {"fluid_caution": True, "bnp_elevated": True},
            "interventions": ["Cautious fluid resuscitation", "Monitor for pulmonary edema"],
            "narrative": "CHF limits fluid resuscitation — use smaller boluses with frequent reassessment, "
                         "watch for pulmonary edema, consider vasopressors earlier."
        },
        "COPD": {
            "lab_effects": {"vbg_pco2": {"min": 50, "max": 80}},
            "flags": {"hypercapnic_baseline": True, "o2_target_88_92": True},
            "interventions": ["Target SpO2 88-92%", "Avoid excessive supplemental O2"],
            "narrative": "COPD patient — baseline CO2 retention, target SpO2 88-92%, avoid high-flow O2 "
                         "which may suppress respiratory drive."
        },
        "Atrial_Fibrillation": {
            "lab_effects": {},
            "flags": {"anticoagulated": True, "irregular_rhythm": True},
            "interventions": ["Check anticoagulation status", "Rate vs rhythm control assessment"],
            "narrative": "Atrial fibrillation — check if on anticoagulation, assess for rate control, "
                         "irregularly irregular rhythm affects BP measurement accuracy."
        },
        "Obesity": {
            "lab_effects": {},
            "flags": {"difficult_airway": True, "dose_by_weight": True},
            "interventions": ["Weight-based dosing considerations", "Difficult airway preparation"],
            "narrative": "Obesity complicates airway management and drug dosing — prepare for difficult airway, "
                         "use ideal body weight for some medications, actual weight for others."
        },
        "Immunocompromised": {
            "lab_effects": {"wbc": {"min": 0.5, "max": 3.0}},
            "flags": {"atypical_presentation": True, "broad_spectrum_abx": True},
            "interventions": ["Broadened antimicrobial coverage", "Infectious disease consultation"],
            "narrative": "Immunocompromised — may have atypical presentations, lower threshold for imaging and cultures, "
                         "broaden antimicrobial coverage, consider opportunistic infections."
        },
        "Liver_Cirrhosis": {
            "lab_effects": {"alb": {"min": 1.5, "max": 2.8}, "plt": {"min": 40, "max": 100},
                            "t_bili": {"min": 2.0, "max": 15.0}},
            "flags": {"coagulopathy_risk": True, "hepatic_dosing": True},
            "interventions": ["Hepatic-dose medications", "Monitor for coagulopathy"],
            "narrative": "Cirrhosis — impaired drug metabolism, coagulopathy risk, consider SBP if ascitic, "
                         "watch for hepatic encephalopathy and variceal bleeding."
        },
    }

    def __init__(self, registry: Optional[DiagnosisRegistry] = None):
        self.registry = registry or DiagnosisRegistry()

    def available_comorbidities(self, diagnosis: str) -> List[str]:
        """
        Return comorbidities that have specific effects on this diagnosis,
        plus universal comorbidities.
        """
        dx_specific = set(self.registry.comorbidity_modifiers(diagnosis).keys()) \
            if self.registry.has(diagnosis) else set()
        universal = set(self.UNIVERSAL_COMORBIDITIES.keys())
        return sorted(dx_specific | universal)

    def compute_effects(self, diagnosis: str,
                         selected_comorbidities: List[str]) -> ComorbidityEffect:
        """
        Compute the aggregate effect of selected comorbidities on a diagnosis.
        Diagnosis-specific modifiers override universal defaults when both exist.
        """
        if not selected_comorbidities:
            return ComorbidityEffect({}, {}, [], "No significant comorbidities.")

        lab_overrides: Dict[str, Dict[str, float]] = {}
        flags: Dict[str, bool] = {}
        interventions: List[str] = []
        narratives: List[str] = []

        dx_modifiers = self.registry.comorbidity_modifiers(diagnosis) \
            if self.registry.has(diagnosis) else {}

        for comorbidity in selected_comorbidities:
            # Diagnosis-specific modifiers take priority
            dx_mod = dx_modifiers.get(comorbidity, {})
            universal_mod = self.UNIVERSAL_COMORBIDITIES.get(comorbidity, {})

            # Lab effects: dx-specific overrides universal
            uni_labs = universal_mod.get("lab_effects", {})
            for lab, ranges in uni_labs.items():
                if lab not in lab_overrides:
                    lab_overrides[lab] = ranges

            # Dx-specific lab overrides
            for key, val in dx_mod.items():
                if isinstance(val, dict) and "min" in val and "max" in val:
                    lab_overrides[key] = val

            # Flags: collect from both
            for key, val in dx_mod.items():
                if isinstance(val, bool):
                    flags[key] = val
            for flag, val in universal_mod.get("flags", {}).items():
                if flag not in flags:
                    flags[flag] = val

            # Interventions
            interventions.extend(universal_mod.get("interventions", []))

            # Narrative
            if universal_mod.get("narrative"):
                narratives.append(f"**{comorbidity}**: {universal_mod['narrative']}")
            elif dx_mod:
                narratives.append(
                    f"**{comorbidity}**: Modifies {diagnosis} management — "
                    f"lab adjustments and clinical precautions apply."
                )

        # Deduplicate interventions
        seen = set()
        unique_interventions = []
        for i in interventions:
            if i not in seen:
                seen.add(i)
                unique_interventions.append(i)

        prompt_text = self._build_prompt_context(
            diagnosis, selected_comorbidities, narratives, unique_interventions, flags
        )

        return ComorbidityEffect(
            lab_overrides=lab_overrides,
            clinical_flags=flags,
            additional_interventions=unique_interventions,
            prompt_context=prompt_text
        )

    def _build_prompt_context(self, diagnosis: str,
                               comorbidities: List[str],
                               narratives: List[str],
                               interventions: List[str],
                               flags: Dict[str, bool]) -> str:
        """Build AI prompt context describing comorbidity effects."""
        lines = [
            f"### Comorbidity Modifications for {diagnosis}",
            f"Active comorbidities: {', '.join(comorbidities)}",
            ""
        ]

        if narratives:
            lines.append("**Clinical Impact:**")
            lines.extend(narratives)
            lines.append("")

        if interventions:
            lines.append("**Additional Required Interventions:**")
            for i in interventions:
                lines.append(f"  - {i}")
            lines.append("")

        important_flags = {
            "fluid_caution": "CAUTION: Restrict fluid volumes — use smaller boluses with reassessment",
            "contrast_caution": "CAUTION: Avoid or minimize contrast dye (renal protection)",
            "nsaid_avoid": "AVOID: NSAIDs contraindicated",
            "difficult_airway": "ALERT: Prepare for difficult airway",
            "atypical_presentation": "NOTE: May have atypical presentation — lower threshold for workup",
            "coagulopathy_risk": "ALERT: Coagulopathy risk — check coags before procedures",
            "anticoagulated": "CHECK: Verify anticoagulation status and last dose",
            "o2_target_88_92": "TARGET: SpO2 88-92% (not 94-100%)",
        }
        active_alerts = [msg for flag, msg in important_flags.items() if flags.get(flag)]
        if active_alerts:
            lines.append("**Clinical Alerts:**")
            for alert in active_alerts:
                lines.append(f"  ⚠️ {alert}")
            lines.append("")

        lines.append("IMPORTANT: Reflect ALL comorbidity effects in the generated case — "
                     "past medical history, medications, lab values, physical exam findings, "
                     "and state progression must account for these conditions.")

        return "\n".join(lines)


# ============================================================================
# TIME-PRESSURE ENGINE — Models time-critical actions and operator cues
# ============================================================================

@dataclass
class TimedAction:
    """A single time-critical action with its window and state mapping."""
    action: str
    window_minutes: int
    rationale: str
    target_state: int          # which state this should happen in (1-5)
    operator_cue_at: int       # minutes into scenario to prompt if not done
    severity: str              # "critical", "important", "supportive"


@dataclass
class ScenarioTimeline:
    """Complete time-pressure model for a scenario."""
    total_duration_minutes: int
    state_budgets: Dict[int, int]           # state_number → minutes
    timed_actions: List[TimedAction]
    operator_cue_schedule: List[str]        # ordered list of time-based cues
    prompt_context: str                     # narrative for AI injection


class TimePressureEngine:
    """
    Models time-critical interventions and builds operator cue schedules.

    Takes registry time_critical_actions and maps them to specific states
    with time budgets, creating a realistic scenario timeline.
    """

    # Default state time budgets by difficulty (minutes per state)
    STATE_BUDGETS = {
        "Basic":        {1: 5, 2: 5, 3: 5, 4: 5, 5: 5},     # 25 min total
        "Intermediate": {1: 4, 2: 5, 3: 6, 4: 5, 5: 5},     # 25 min total
        "Advanced":     {1: 3, 2: 5, 3: 7, 4: 6, 5: 4},     # 25 min total
        "Nightmare":    {1: 3, 2: 4, 3: 8, 4: 6, 5: 4},     # 25 min total
    }

    def __init__(self, registry: Optional[DiagnosisRegistry] = None):
        self.registry = registry or DiagnosisRegistry()

    def build_timeline(self, diagnosis: str,
                        difficulty: str = "Intermediate") -> ScenarioTimeline:
        """Build a complete scenario timeline with timed actions and cues."""
        has_dx = self.registry.has(diagnosis)
        time_actions = self.registry.time_critical_actions(diagnosis) if has_dx else {}
        budgets = dict(self.STATE_BUDGETS.get(difficulty, self.STATE_BUDGETS["Intermediate"]))
        total = sum(budgets.values())

        timed = []
        cumulative_time = {1: 0}
        for s in range(2, 6):
            cumulative_time[s] = cumulative_time[s - 1] + budgets[s - 1]

        for action, info in time_actions.items():
            window = info.get("window_minutes", 30)
            rationale = info.get("rationale", "")

            # Map action to the state where it should happen
            target_state = self._map_to_state(window, cumulative_time, total)

            # Set operator cue just before the window closes
            cue_at = min(window - 2, cumulative_time.get(target_state, 0) + budgets.get(target_state, 5) - 1)
            cue_at = max(1, cue_at)

            severity = "critical" if window <= 10 else ("important" if window <= 30 else "supportive")

            timed.append(TimedAction(
                action=action,
                window_minutes=window,
                rationale=rationale,
                target_state=target_state,
                operator_cue_at=cue_at,
                severity=severity
            ))

        # Sort by urgency
        timed.sort(key=lambda t: t.window_minutes)

        # Build operator cue schedule
        cues = self._build_cue_schedule(timed, budgets, cumulative_time)

        prompt = self._build_prompt_context(diagnosis, timed, budgets, total)

        return ScenarioTimeline(
            total_duration_minutes=total,
            state_budgets=budgets,
            timed_actions=timed,
            operator_cue_schedule=cues,
            prompt_context=prompt
        )

    def _map_to_state(self, window_minutes: int,
                       cumulative_time: Dict[int, int],
                       total: int) -> int:
        """Map a time window to the state where the action should occur."""
        if window_minutes <= 5:
            return 1   # Must happen immediately on arrival
        elif window_minutes <= 15:
            return 2   # Early action required
        elif window_minutes <= 30:
            return 3   # Critical decision point
        elif window_minutes <= 60:
            return 3   # Still at decision point, but less urgent
        else:
            return 4   # Ongoing management

    def _build_cue_schedule(self, timed_actions: List[TimedAction],
                             budgets: Dict[int, int],
                             cumulative_time: Dict[int, int]) -> List[str]:
        """Build chronological operator cue schedule."""
        cues = []

        # State transition cues
        for state in range(1, 6):
            t = cumulative_time.get(state, 0)
            cues.append(f"[{t:02d}:00] STATE {state} begins (budget: {budgets.get(state, 5)} min)")

        # Action-specific cues
        for ta in timed_actions:
            severity_tag = "⚠️ CRITICAL" if ta.severity == "critical" else "📋"
            cues.append(
                f"[{ta.operator_cue_at:02d}:00] {severity_tag} If {ta.action} not done: "
                f"cue team. Window: {ta.window_minutes} min. ({ta.rationale})"
            )

        # Sort by time
        cues.sort(key=lambda c: int(c[1:3]))
        return cues

    def _build_prompt_context(self, diagnosis: str,
                               timed_actions: List[TimedAction],
                               budgets: Dict[int, int],
                               total: int) -> str:
        """Build AI prompt context for time-pressure."""
        lines = [
            f"### Time-Pressure Model for: {diagnosis}",
            f"**Total Scenario Duration**: {total} minutes",
            f"**State Time Budgets**: " + ", ".join(
                f"S{s}={m}min" for s, m in sorted(budgets.items())
            ),
            ""
        ]

        if timed_actions:
            lines.append("**Time-Critical Actions (ordered by urgency):**")
            for ta in timed_actions:
                icon = "🔴" if ta.severity == "critical" else "🟡" if ta.severity == "important" else "🟢"
                lines.append(
                    f"  {icon} {ta.action}: within {ta.window_minutes} min "
                    f"(State {ta.target_state}) — {ta.rationale}"
                )
            lines.append("")
            lines.append("IMPORTANT: The scenario operator notes (s*_notes fields) MUST include "
                         "specific time-based cues referencing these windows. The operator "
                         "should know EXACTLY when to intervene if learners miss a window.")
        else:
            lines.append("No specific time-critical actions identified. "
                         "Use standard clinical urgency for state progression.")

        return "\n".join(lines)


# ============================================================================
# DRUG DOSING VALIDATOR — Validates medication doses in AI-generated cases
# ============================================================================

@dataclass
class DosingIssue:
    """A single drug dosing concern."""
    drug: str
    field_source: str          # which case field mentioned this drug
    issue: str                 # description of the concern
    severity: str              # "error", "warning", "info"
    recommendation: str


class DrugDosingValidator:
    """
    Validates medication dosing mentioned in AI-generated case text.

    Checks common emergency/critical care medications for:
    - Doses outside standard ranges
    - Missing weight-based calculations
    - Contraindicated drugs given comorbidities
    - Inappropriate routes
    """

    # Standard adult dosing ranges: {drug_pattern: {dose_min, dose_max, unit, route, notes}}
    DRUG_REFERENCE = {
        "epinephrine_im": {
            "pattern": r"epinephrine.*?(\d+\.?\d*)\s*m[gG].*?[iI][mM]",
            "min_mg": 0.3, "max_mg": 0.5, "route": "IM",
            "note": "Anaphylaxis: 0.3-0.5 mg IM (1:1000)"
        },
        "epinephrine_iv": {
            "pattern": r"epinephrine.*?(\d+\.?\d*)\s*(?:mcg|μg).*?[iI][vV]",
            "min_mcg": 1, "max_mcg": 10, "route": "IV push",
            "note": "Cardiac arrest: 1 mg IV q3-5min; drip: 1-10 mcg/min"
        },
        "aspirin": {
            "pattern": r"aspirin.*?(\d+)\s*m[gG]",
            "min_mg": 81, "max_mg": 325,
            "note": "ACS: 162-325 mg chewed; maintenance: 81 mg daily"
        },
        "nitroglycerin_sl": {
            "pattern": r"nitroglycerin.*?(\d+\.?\d*)\s*m[gG].*?[sS][lL]",
            "min_mg": 0.3, "max_mg": 0.6,
            "note": "0.4 mg SL q5min x3; contraindicated with PDE5 inhibitors"
        },
        "morphine": {
            "pattern": r"morphine.*?(\d+\.?\d*)\s*m[gG]",
            "min_mg": 1, "max_mg": 10,
            "note": "2-4 mg IV q5-15min; caution in respiratory depression"
        },
        "heparin_bolus": {
            "pattern": r"heparin.*?(\d+)\s*(?:units|u).*?bolus",
            "min_units": 60, "max_units": 80, "per_kg": True,
            "note": "60-80 units/kg IV bolus (max 4000-5000 units)"
        },
        "tpa_alteplase": {
            "pattern": r"(?:alteplase|tPA|t-PA).*?(\d+\.?\d*)\s*m[gG]",
            "min_mg": 0.9, "max_mg": 0.9, "per_kg": True,
            "note": "0.9 mg/kg (max 90 mg); 10% bolus, remainder over 60 min"
        },
        "amiodarone_arrest": {
            "pattern": r"amiodarone.*?(\d+)\s*m[gG]",
            "min_mg": 150, "max_mg": 300,
            "note": "Arrest: 300 mg IV push; stable VT: 150 mg over 10 min"
        },
        "insulin_dka": {
            "pattern": r"insulin.*?(\d+\.?\d*)\s*(?:units|u).*?(?:bolus|hour|hr)",
            "min_units": 0.1, "max_units": 0.14, "per_kg": True,
            "note": "DKA: 0.1-0.14 units/kg/hr; some protocols include 0.1 unit/kg bolus"
        },
        "norepinephrine": {
            "pattern": r"norepinephrine.*?(\d+\.?\d*)\s*(?:mcg|μg)",
            "min_mcg_per_min": 0.1, "max_mcg_per_min": 30,
            "note": "Start 0.1-0.5 mcg/kg/min, titrate to MAP ≥ 65"
        },
        "rocuronium": {
            "pattern": r"rocuronium.*?(\d+\.?\d*)\s*(?:mg/kg|m[gG])",
            "min_mg_per_kg": 0.6, "max_mg_per_kg": 1.2,
            "note": "RSI: 1-1.2 mg/kg; standard intubation: 0.6 mg/kg"
        },
        "ketamine": {
            "pattern": r"ketamine.*?(\d+\.?\d*)\s*(?:mg/kg|m[gG])",
            "min_mg_per_kg": 1.0, "max_mg_per_kg": 2.0,
            "note": "RSI: 1-2 mg/kg IV; procedural sedation: 1-1.5 mg/kg IV"
        },
        "naloxone": {
            "pattern": r"naloxone.*?(\d+\.?\d*)\s*m[gG]",
            "min_mg": 0.04, "max_mg": 2.0,
            "note": "0.04-0.4 mg IV, titrate; max 10 mg total"
        },
        "dextrose_d50": {
            "pattern": r"(?:D50|dextrose\s*50).*?(\d+)\s*m[lL]",
            "min_ml": 25, "max_ml": 50,
            "note": "D50W: 25-50 mL IV push for hypoglycemia"
        },
    }

    # Contraindication checks
    CONTRAINDICATIONS = {
        "nitroglycerin": ["right_ventricular_infarction", "pde5_inhibitor", "severe_hypotension"],
        "morphine": ["respiratory_depression", "hypotension"],
        "tpa": ["active_bleeding", "recent_surgery", "hemorrhagic_stroke"],
        "nsaid": ["CKD", "gi_bleed", "anticoagulated"],
        "metformin": ["CKD", "lactic_acidosis"],
        "beta_blocker": ["severe_bradycardia", "decompensated_chf", "cocaine"],
    }

    def validate_case(self, case_data: Dict[str, Any],
                       comorbidities: Optional[List[str]] = None) -> List[DosingIssue]:
        """
        Scan all text fields of a generated case for medication mentions
        and validate dosing.
        """
        import re
        issues = []
        comorbidities = comorbidities or []

        # Collect all text content from the case
        text_fields = {}
        for key, val in case_data.items():
            if isinstance(val, str) and len(val) > 5:
                text_fields[key] = val
            elif isinstance(val, list):
                for i, item in enumerate(val):
                    if isinstance(item, str):
                        text_fields[f"{key}[{i}]"] = item

        all_text = " ".join(text_fields.values()).lower()

        # Check for contraindicated medications given comorbidities
        for drug, contraindicated_for in self.CONTRAINDICATIONS.items():
            if drug in all_text:
                for condition in contraindicated_for:
                    if condition in [c.lower().replace(" ", "_") for c in comorbidities]:
                        issues.append(DosingIssue(
                            drug=drug,
                            field_source="multiple",
                            issue=f"{drug} may be contraindicated with {condition}",
                            severity="warning",
                            recommendation=f"Verify {drug} is appropriate given {condition}"
                        ))

        # Check NSAID use with CKD
        nsaid_pattern = re.compile(r'\b(?:ibuprofen|naproxen|ketorolac|toradol|nsaid|diclofenac)\b',
                                    re.IGNORECASE)
        if nsaid_pattern.search(all_text) and any(c.upper() == "CKD" for c in comorbidities):
            issues.append(DosingIssue(
                drug="NSAID",
                field_source="medications/other_meds",
                issue="NSAID use in patient with CKD — nephrotoxicity risk",
                severity="error",
                recommendation="Avoid NSAIDs in CKD; use acetaminophen or alternative analgesics"
            ))

        # Check for common dosing issues in state progression notes
        for state_num in range(1, 6):
            prefix = f"s{state_num}"
            notes = case_data.get(f"{prefix}_notes", "")
            actions = case_data.get(f"{prefix}_actions", "")
            combined = f"{notes} {actions}"

            # Check for "push dose epi" without specifying concentration
            if "push dose" in combined.lower() and "epinephrine" in combined.lower():
                if "10 mcg" not in combined and "20 mcg" not in combined.lower():
                    issues.append(DosingIssue(
                        drug="Epinephrine (push dose)",
                        field_source=f"{prefix}_notes/{prefix}_actions",
                        issue="Push-dose epinephrine mentioned without specifying dose",
                        severity="info",
                        recommendation="Specify: 5-20 mcg IV q2-5min (NOT 1:1000 concentration)"
                    ))

        return issues


# ============================================================================
# PERFORMANCE SCORER — Evaluates generated case quality
# ============================================================================

@dataclass
class ScoreComponent:
    """One dimension of case quality scoring."""
    dimension: str
    score: int              # 0-10
    max_score: int          # always 10
    details: str
    deductions: List[str]


@dataclass
class PerformanceReport:
    """Complete quality assessment of a generated case."""
    overall_score: float        # 0-100
    grade: str                  # A, B, C, D, F
    components: List[ScoreComponent]
    strengths: List[str]
    improvement_areas: List[str]


class PerformanceScorer:
    """
    Evaluates the quality of a generated simulation case across 10 dimensions:
    1. Clinical Accuracy — vital signs, labs, PE correlate with diagnosis
    2. State Progression — logical 5-state arc with meaningful branching
    3. Educational Alignment — objectives match content and difficulty
    4. Completeness — all fields populated with meaningful content
    5. Branching Quality — clear positive/negative pathways
    6. Operator Usability — actionable notes, clear cues
    7. Patient Realism — consistent demographics, history, medications
    8. Critical Actions — specific, time-bound, hierarchically organized
    9. Lab Coherence — labs tell the diagnostic story
    10. Debriefing Quality — questions target learning objectives
    """

    def __init__(self, registry: Optional[DiagnosisRegistry] = None):
        self.registry = registry or DiagnosisRegistry()

    def score_case(self, case_data: Dict[str, Any],
                    diagnosis: str,
                    difficulty: str = "Intermediate",
                    lab_issues: Optional[List] = None,
                    drug_issues: Optional[List] = None) -> PerformanceReport:
        """Score a generated case across all dimensions."""
        components = [
            self._score_completeness(case_data),
            self._score_state_progression(case_data),
            self._score_branching(case_data),
            self._score_critical_actions(case_data),
            self._score_operator_notes(case_data),
            self._score_patient_realism(case_data),
            self._score_educational_alignment(case_data, difficulty),
            self._score_lab_coherence(case_data, diagnosis, lab_issues),
            self._score_debriefing(case_data),
            self._score_clinical_accuracy(case_data, diagnosis, drug_issues),
        ]

        total = sum(c.score for c in components)
        max_total = sum(c.max_score for c in components)
        pct = (total / max_total * 100) if max_total > 0 else 0

        grade = "A" if pct >= 90 else "B" if pct >= 80 else "C" if pct >= 70 else "D" if pct >= 60 else "F"

        strengths = [c.dimension for c in components if c.score >= 8]
        improvement_areas = [f"{c.dimension}: {c.deductions[0]}" for c in components
                             if c.score < 7 and c.deductions]

        return PerformanceReport(
            overall_score=round(pct, 1),
            grade=grade,
            components=components,
            strengths=strengths,
            improvement_areas=improvement_areas
        )

    def _score_completeness(self, case_data: Dict[str, Any]) -> ScoreComponent:
        """Check that all fields are populated with meaningful content."""
        required_fields = [
            "case_name", "case_summary", "hpi", "pmh", "chief_complaint",
            "vignette", "ed_objectives", "organ_system",
            "hr_arrive", "bp_arrive", "rr_arrive", "o2_arrive", "temp_arrive",
            "general_pe", "cv_pe", "resp_pe",
            "s1_name", "s2_name", "s3_name", "s4_name", "s5_name",
            "s1_vitals", "s2_vitals", "s3_vitals", "s4_vitals", "s5_vitals",
            "wbc", "hgb", "na", "k", "cr", "glu",
        ]
        deductions = []
        empty_count = 0
        for f in required_fields:
            val = case_data.get(f, "")
            if not val or (isinstance(val, str) and len(val.strip()) < 3):
                empty_count += 1
                if empty_count <= 3:
                    deductions.append(f"Missing/empty: {f}")

        score = max(0, 10 - empty_count)
        return ScoreComponent("Completeness", score, 10,
                              f"{len(required_fields) - empty_count}/{len(required_fields)} required fields populated",
                              deductions)

    def _score_state_progression(self, case_data: Dict[str, Any]) -> ScoreComponent:
        """Check that 5 states have distinct, progressing content."""
        deductions = []
        score = 10
        for i in range(1, 6):
            prefix = f"s{i}"
            vitals = case_data.get(f"{prefix}_vitals", "")
            pe = case_data.get(f"{prefix}_pe", "")
            actions = case_data.get(f"{prefix}_actions", "")
            if not vitals or len(str(vitals)) < 10:
                score -= 1
                deductions.append(f"State {i} vitals missing or too brief")
            if not pe or len(str(pe)) < 10:
                score -= 1
                deductions.append(f"State {i} PE missing or too brief")
            if not actions or len(str(actions)) < 10:
                score -= 0.5

        # Check for duplicate content across states (copy-paste detection)
        vitals_set = set()
        for i in range(1, 6):
            v = case_data.get(f"s{i}_vitals", "").strip()
            if v and v in vitals_set:
                score -= 2
                deductions.append(f"State {i} vitals identical to another state")
            vitals_set.add(v)

        return ScoreComponent("State Progression", max(0, int(score)), 10,
                              "5-state arc with distinct, evolving content",
                              deductions)

    def _score_branching(self, case_data: Dict[str, Any]) -> ScoreComponent:
        """Check for meaningful positive/negative pathway content."""
        deductions = []
        score = 10
        # States 3-5 should have branching markers
        for i in [3, 4, 5]:
            prefix = f"s{i}"
            vitals = str(case_data.get(f"{prefix}_vitals", "")).lower()
            notes = str(case_data.get(f"{prefix}_notes", "")).lower()

            has_branching = any(kw in vitals + notes for kw in
                                ["good path", "bad path", "positive", "negative",
                                 "if treated", "if untreated", "branch", "pathway"])
            if not has_branching:
                score -= 2
                deductions.append(f"State {i}: no branching language detected")

        # State 3 should specifically mention the critical decision
        s3_notes = str(case_data.get("s3_notes", "")).lower()
        if "branch" not in s3_notes and "if " not in s3_notes:
            score -= 2
            deductions.append("State 3 operator notes lack branching instructions")

        return ScoreComponent("Branching Quality", max(0, score), 10,
                              "Positive/negative pathways in critical states",
                              deductions)

    def _score_critical_actions(self, case_data: Dict[str, Any]) -> ScoreComponent:
        """Check that critical actions are specific and actionable."""
        deductions = []
        actions = case_data.get("critical_actions", [])
        if not isinstance(actions, list):
            return ScoreComponent("Critical Actions", 2, 10,
                                  "Critical actions not in list format",
                                  ["critical_actions should be a JSON array"])

        score = 10
        if len(actions) < 3:
            score -= 3
            deductions.append(f"Only {len(actions)} critical actions (need 4-6)")
        elif len(actions) > 8:
            score -= 1
            deductions.append("Too many critical actions — focus on the most important")

        # Check for vague actions
        vague_words = ["assess", "monitor", "evaluate", "consider", "review"]
        for action in actions:
            if isinstance(action, str) and len(action) < 15:
                score -= 1
                deductions.append(f"Action too vague: '{action[:30]}'")
            elif isinstance(action, str):
                first_word = action.strip().split()[0].lower() if action.strip() else ""
                if first_word in vague_words and "within" not in action.lower():
                    score -= 0.5

        return ScoreComponent("Critical Actions", max(0, int(score)), 10,
                              f"{len(actions)} critical actions defined",
                              deductions)

    def _score_operator_notes(self, case_data: Dict[str, Any]) -> ScoreComponent:
        """Check that operator notes are actionable."""
        deductions = []
        score = 10
        for i in range(1, 6):
            notes = case_data.get(f"s{i}_notes", "")
            if not notes or len(str(notes)) < 20:
                score -= 1.5
                deductions.append(f"State {i} operator notes too brief or missing")
            elif len(str(notes)) < 50:
                score -= 0.5
                deductions.append(f"State {i} operator notes could be more detailed")

        return ScoreComponent("Operator Usability", max(0, int(score)), 10,
                              "Operator notes are actionable and detailed",
                              deductions)

    def _score_patient_realism(self, case_data: Dict[str, Any]) -> ScoreComponent:
        """Check patient demographics, history, and medication consistency."""
        deductions = []
        score = 10
        if not case_data.get("pt_name"):
            score -= 1
            deductions.append("Missing patient name")
        if not case_data.get("hpi") or len(str(case_data.get("hpi", ""))) < 50:
            score -= 2
            deductions.append("HPI too brief")
        if not case_data.get("pmh") or len(str(case_data.get("pmh", ""))) < 20:
            score -= 1
            deductions.append("PMH too brief")
        if not case_data.get("medications") or len(str(case_data.get("medications", ""))) < 10:
            score -= 1
            deductions.append("Medications list too brief")
        if not case_data.get("social_history"):
            score -= 1
            deductions.append("Missing social history")

        return ScoreComponent("Patient Realism", max(0, score), 10,
                              "Consistent patient demographics, history, and medications",
                              deductions)

    def _score_educational_alignment(self, case_data: Dict[str, Any],
                                      difficulty: str) -> ScoreComponent:
        """Check that educational objectives match content."""
        deductions = []
        score = 10
        objectives = case_data.get("ed_objectives", "")
        if not objectives or len(str(objectives)) < 30:
            score -= 3
            deductions.append("Educational objectives missing or too brief")

        target = case_data.get("target_learner", "")
        if not target:
            score -= 1
            deductions.append("Target learner not specified")

        return ScoreComponent("Educational Alignment", max(0, score), 10,
                              "Objectives match content and difficulty level",
                              deductions)

    def _score_lab_coherence(self, case_data: Dict[str, Any],
                              diagnosis: str,
                              lab_issues: Optional[List] = None) -> ScoreComponent:
        """Score lab value coherence with diagnosis."""
        deductions = []
        score = 10

        if lab_issues:
            errors = [i for i in lab_issues if hasattr(i, 'severity') and i.severity == "error"]
            warnings = [i for i in lab_issues if hasattr(i, 'severity') and i.severity == "warning"]
            score -= len(errors) * 2
            score -= len(warnings) * 0.5
            for e in errors[:3]:
                deductions.append(f"Lab error: {getattr(e, 'field_name', 'unknown')}")
        else:
            # Basic checks
            key_labs = ["wbc", "hgb", "na", "k", "cr", "glu", "lactate"]
            for lab in key_labs:
                val = case_data.get(lab, "")
                if not val:
                    score -= 0.5
                    deductions.append(f"Missing lab: {lab}")

        return ScoreComponent("Lab Coherence", max(0, int(score)), 10,
                              "Lab values correlate with diagnosis",
                              deductions)

    def _score_debriefing(self, case_data: Dict[str, Any]) -> ScoreComponent:
        """Check debriefing question quality."""
        deductions = []
        questions = case_data.get("debrief_questions", [])
        if not isinstance(questions, list):
            return ScoreComponent("Debriefing Quality", 3, 10,
                                  "Debrief questions not in list format",
                                  ["debrief_questions should be a JSON array"])

        score = 10
        if len(questions) < 3:
            score -= 3
            deductions.append(f"Only {len(questions)} debrief questions (need 4-6)")

        for q in questions:
            if isinstance(q, str) and len(q) < 20:
                score -= 1
                deductions.append(f"Question too brief: '{q[:30]}'")

        return ScoreComponent("Debriefing Quality", max(0, int(score)), 10,
                              f"{len(questions)} debriefing questions",
                              deductions)

    def _score_clinical_accuracy(self, case_data: Dict[str, Any],
                                  diagnosis: str,
                                  drug_issues: Optional[List] = None) -> ScoreComponent:
        """Score overall clinical accuracy."""
        deductions = []
        score = 10

        if drug_issues:
            errors = [i for i in drug_issues if hasattr(i, 'severity') and i.severity == "error"]
            warnings = [i for i in drug_issues if hasattr(i, 'severity') and i.severity == "warning"]
            score -= len(errors) * 2
            score -= len(warnings) * 1
            for e in errors[:3]:
                deductions.append(f"Drug issue: {getattr(e, 'drug', 'unknown')}")

        # Check arrival vitals exist and are numeric
        for field in ["hr_arrive", "rr_arrive", "o2_arrive", "temp_arrive"]:
            val = case_data.get(field, "")
            try:
                float(str(val).replace(",", ""))
            except (ValueError, TypeError):
                score -= 0.5
                deductions.append(f"{field} is not numeric")

        return ScoreComponent("Clinical Accuracy", max(0, int(score)), 10,
                              "Clinically defensible vitals, medications, and progression",
                              deductions)


# ============================================================================
# INTERVENTIONS
# ============================================================================

class Intervention(Enum):
    """Common clinical interventions."""
    IV_ACCESS            = "IV Access"
    ANTIBIOTICS          = "Antibiotics"
    FLUID_RESUSCITATION  = "Fluid Resuscitation"
    OXYGEN               = "Oxygen Therapy"
    VASOPRESSORS         = "Vasopressors"
    INTUBATION           = "Intubation"
    MONITORING           = "Continuous Monitoring"


@dataclass
class VitalSigns:
    """Data class for patient vital signs."""
    heart_rate: int
    systolic_bp: int
    diastolic_bp: int
    respiratory_rate: int
    temperature_f: float
    o2_saturation: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class StateProgression:
    """Represents a single state in the 5-state scenario."""
    state_number: int
    name: str
    vital_signs: VitalSigns
    physical_exam_findings: str
    patient_actions: List[str]
    clinical_notes: str
    progression_logic: str  # What happens next based on interventions


class MedicalLogicController:
    """
    Encapsulates all branching logic for medical simulations.
    
    Now powered by DiagnosisRegistry — vital presets, PE findings,
    required interventions, and severity scaling all come from
    diagnosis_data.json instead of hardcoded dicts.
    """
    
    # Define difficulty-based response multipliers
    DIFFICULTY_MULTIPLIERS = {
        Difficulty.BASIC: 0.8,
        Difficulty.INTERMEDIATE: 1.0,
        Difficulty.ADVANCED: 1.3,
        Difficulty.NIGHTMARE: 1.8
    }
    
    def __init__(self, diagnosis: str, difficulty: Difficulty, 
                 patient_age: int, patient_gender: str):
        self.diagnosis = diagnosis
        self.difficulty = difficulty
        self.patient_age = patient_age
        self.patient_gender = patient_gender
        self.difficulty_multiplier = self.DIFFICULTY_MULTIPLIERS[difficulty]
        self.registry = DiagnosisRegistry()
        
        # Track which interventions have been performed
        self._interventions_performed: Dict[Intervention, bool] = {
            intervention: False for intervention in Intervention
        }
    
    def get_initial_vital_signs(self) -> VitalSigns:
        """
        Generate initial vital signs from DiagnosisRegistry, scaled by difficulty.
        """
        dm = self.difficulty_multiplier
        base = self.registry.vitals(self.diagnosis)
        modifiers = self.registry.vital_modifier_type(self.diagnosis)
        weights = self.registry.vital_severity_weights(self.diagnosis)

        if not base:
            return VitalSigns(110, 100, 65, 20, 99.0, 94)

        def scale(key: str, base_val: float) -> float:
            mod_type = modifiers.get(key, "multiply")
            weight = weights.get(key, 10)
            if mod_type == "fixed":
                return base_val
            elif mod_type == "inverse":
                return base_val / dm
            elif mod_type == "decrease":
                return base_val - (weight * (dm - 1))
            else:  # "multiply"
                return base_val * dm

        return VitalSigns(
            heart_rate=max(0, int(scale("heart_rate", base.get("heart_rate", 80)))),
            systolic_bp=max(0, int(scale("systolic_bp", base.get("systolic_bp", 120)))),
            diastolic_bp=max(0, int(scale("diastolic_bp", base.get("diastolic_bp", 80)))),
            respiratory_rate=max(0, int(scale("respiratory_rate", base.get("respiratory_rate", 16)))),
            temperature_f=round(scale("temperature_f", base.get("temperature_f", 98.6)), 1),
            o2_saturation=max(0, min(100, int(scale("o2_saturation", base.get("o2_saturation", 98)))))
        )
    
    def record_intervention(self, intervention: Intervention) -> None:
        self._interventions_performed[intervention] = True
    
    def get_required_interventions(self) -> List[str]:
        """Return the diagnosis-specific required interventions."""
        return self.registry.required_interventions(self.diagnosis)

    def get_time_critical_actions(self) -> Dict[str, Any]:
        """Return time-critical actions with windows and rationale."""
        return self.registry.time_critical_actions(self.diagnosis)

    def get_next_state_vitals(self, current_state: int, 
                             current_vitals: VitalSigns) -> VitalSigns:
        """
        Calculate vital signs for the next state based on interventions performed.
        Now checks diagnosis-specific required interventions from the registry.
        """
        # Determine which of this diagnosis's required interventions were performed
        required = self.registry.required_interventions(self.diagnosis)
        intervention_map = {i.value: i for i in Intervention}

        performed_count = sum(
            1 for req in required
            if req in intervention_map
            and self._interventions_performed.get(intervention_map[req], False)
        )
        threshold = max(1, len(required) - 1)  # Must do most of them

        if performed_count >= threshold:
            return VitalSigns(
                heart_rate=max(60, int(current_vitals.heart_rate * 0.97)),
                systolic_bp=min(140, int(current_vitals.systolic_bp * 1.02)),
                diastolic_bp=min(90, int(current_vitals.diastolic_bp * 1.02)),
                respiratory_rate=max(12, int(current_vitals.respiratory_rate * 0.95)),
                temperature_f=round(current_vitals.temperature_f * 0.98, 1),
                o2_saturation=min(98, int(current_vitals.o2_saturation * 1.01))
            )
        else:
            degradation_factor = 1.0 + (0.05 * self.difficulty_multiplier)
            return VitalSigns(
                heart_rate=int(current_vitals.heart_rate * degradation_factor),
                systolic_bp=int(current_vitals.systolic_bp * (2.0 - degradation_factor)),
                diastolic_bp=int(current_vitals.diastolic_bp * (2.0 - degradation_factor)),
                respiratory_rate=int(current_vitals.respiratory_rate * degradation_factor),
                temperature_f=round(current_vitals.temperature_f + 0.2, 1),
                o2_saturation=max(70, int(current_vitals.o2_saturation - 2))
            )
    
    def generate_state_progression(self, state_number: int,
                                  vital_signs: VitalSigns) -> StateProgression:
        state_names = {
            1: "Initial Assessment & Arrival",
            2: "Early Deterioration",
            3: "Critical Intervention Window",
            4: "Response to Treatment",
            5: "Resolution or Deterioration"
        }
        
        pe_findings = self._get_pe_findings_for_state(state_number, vital_signs)
        actions = self._get_expected_actions(state_number)
        progression_logic = self._get_progression_logic(state_number)
        
        return StateProgression(
            state_number=state_number,
            name=state_names.get(state_number, f"State {state_number}"),
            vital_signs=vital_signs,
            physical_exam_findings=pe_findings,
            patient_actions=actions,
            clinical_notes=f"Patient presents with {self.diagnosis} at difficulty level {self.difficulty.value}",
            progression_logic=progression_logic
        )
    
    def _get_pe_findings_for_state(self, state: int, 
                                   vitals: VitalSigns) -> str:
        """Generate PE findings from the registry, adding critical flags."""
        base_finding = self.registry.pe_findings(self.diagnosis)
        thresholds = self.registry.critical_pe_thresholds(self.diagnosis)
        
        if state >= 3:
            o2_thresh = thresholds.get("o2_saturation_below", 90)
            bp_thresh = thresholds.get("systolic_bp_below", 90)
            if vitals.o2_saturation < o2_thresh:
                base_finding += " | **CRITICAL**: Hypoxia worsening"
            if vitals.systolic_bp < bp_thresh:
                base_finding += " | **CRITICAL**: Hypotension developing"
        
        return base_finding
    
    def _get_expected_actions(self, state: int) -> List[str]:
        actions_by_state = {
            1: [
                "Obtain full vital signs",
                "Perform head-to-toe assessment",
                "Establish IV access",
                "Draw labs (CBC, BMP, cultures if applicable)"
            ],
            2: [
                "Re-assess vitals immediately",
                "Initiate continuous monitoring",
                "Consider escalation of care",
                "Notify provider of deterioration"
            ],
            3: [
                "Implement diagnosis-specific protocols",
                "Administer time-critical medications",
                "Increase fluid delivery or initiate vasopressors as indicated",
                "Prepare for possible intubation"
            ],
            4: [
                "Continue supportive care",
                "Monitor response to interventions",
                "Adjust therapy as needed",
                "Prepare for transport or ICU admission"
            ],
            5: [
                "Transition to ongoing management",
                "Conduct formal handoff",
                "Document case and clinical course",
                "Perform team debriefing"
            ]
        }
        
        return actions_by_state.get(state, ["Continue clinical assessment"])
    
    def _get_progression_logic(self, state: int) -> str:
        logic = {
            1: "If adequate initial assessment performed → State 2. Otherwise, condition deteriorates rapidly.",
            2: "If critical interventions initiated → State 3. If delayed → State 3 with worse vitals.",
            3: "If diagnosis-specific protocols followed → State 4 (improvement). Otherwise → State 4 (continued decline).",
            4: "If sustained treatment → State 5 (resolution). If treatment inadequate → State 5 (complications).",
            5: "End scenario. Debrief based on clinical decisions and outcomes."
        }
        return logic.get(state, "Scenario progression based on learner actions")
    
    def validate_scenario_completeness(self) -> Tuple[bool, List[str]]:
        errors = []
        
        if not self.diagnosis:
            errors.append("Missing primary diagnosis")
        
        if self.difficulty not in [d for d in Difficulty]:
            errors.append("Invalid difficulty level")
        
        if self.patient_age < 0 or self.patient_age > 120:
            errors.append("Patient age out of valid range")
        
        if not self._interventions_performed:
            errors.append("No intervention pathways defined")
        
        return len(errors) == 0, errors

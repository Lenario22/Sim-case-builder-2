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
    
    This controller determines how a patient's condition evolves based on:
    - Initial diagnosis and presentation
    - Clinical difficulty level
    - Learner interventions
    - Time progression
    
    The logic is deterministic and reproducible, making scenarios reusable.
    """
    
    # Define difficulty-based response multipliers
    DIFFICULTY_MULTIPLIERS = {
        Difficulty.BASIC: 0.8,          # More forgiving
        Difficulty.INTERMEDIATE: 1.0,   # Standard response
        Difficulty.ADVANCED: 1.3,       # Rapid deterioration
        Difficulty.NIGHTMARE: 1.8       # Critical instability
    }
    
    # Vital sign degradation rates (per state if intervention is missed)
    VITAL_SIGN_DEGRADATION = {
        "heart_rate": 8,
        "systolic_bp": -12,
        "diastolic_bp": -8,
        "respiratory_rate": 3,
        "temperature_f": 0.5,
        "o2_saturation": -4
    }
    
    def __init__(self, diagnosis: str, difficulty: Difficulty, 
                 patient_age: int, patient_gender: str):
        """
        Initialize the logic controller for a specific case.
        
        Args:
            diagnosis: Primary diagnosis (e.g., "Sepsis")
            difficulty: Scenario difficulty level
            patient_age: Age of patient in years
            patient_gender: Patient gender
        """
        self.diagnosis = diagnosis
        self.difficulty = difficulty
        self.patient_age = patient_age
        self.patient_gender = patient_gender
        self.difficulty_multiplier = self.DIFFICULTY_MULTIPLIERS[difficulty]
        
        # Track which interventions have been performed
        self._interventions_performed: Dict[Intervention, bool] = {
            intervention: False for intervention in Intervention
        }
    
    def get_initial_vital_signs(self) -> VitalSigns:
        """
        Generate initial vital signs based on diagnosis and difficulty.
        
        Returns:
            VitalSigns object for state 1 (arrival)
        """
        # Base vital sign presets by diagnosis
        # Each preset reflects the expected pathophysiological presentation:
        #   - Difficulty multiplier scales severity (higher = sicker patient)
        #   - Temperature reflects infection/inflammation status
        #   - O2 sat reflects respiratory/perfusion compromise
        dm = self.difficulty_multiplier
        vital_presets = {
            # --- ORIGINAL 6 DIAGNOSES ---
            "Sepsis": VitalSigns(
                heart_rate=int(110 * dm),
                systolic_bp=int(95 - (15 * (dm - 1))),
                diastolic_bp=int(60 - (10 * (dm - 1))),
                respiratory_rate=int(20 * dm),
                temperature_f=102.5,
                o2_saturation=int(94 - (3 * (dm - 1)))
            ),
            "Myocardial Infarction": VitalSigns(
                heart_rate=int(95 * dm),
                systolic_bp=int(130 - (20 * (dm - 1))),
                diastolic_bp=int(80 - (12 * (dm - 1))),
                respiratory_rate=int(18 * dm),
                temperature_f=98.6,
                o2_saturation=int(96 - (2 * (dm - 1)))
            ),
            "Anaphylaxis": VitalSigns(
                heart_rate=int(130 * dm),
                systolic_bp=int(80 - (20 * (dm - 1))),
                diastolic_bp=int(50 - (10 * (dm - 1))),
                respiratory_rate=int(26 * dm),
                temperature_f=98.6,
                o2_saturation=int(85 - (5 * (dm - 1)))
            ),
            "Pulmonary Embolism": VitalSigns(
                heart_rate=int(105 * dm),
                systolic_bp=int(110 - (15 * (dm - 1))),
                diastolic_bp=int(70 - (10 * (dm - 1))),
                respiratory_rate=int(22 * dm),
                temperature_f=99.1,
                o2_saturation=int(91 - (3 * (dm - 1)))
            ),
            "DKA": VitalSigns(
                heart_rate=int(105 * dm),
                systolic_bp=int(100 - (15 * (dm - 1))),
                diastolic_bp=int(62 - (10 * (dm - 1))),
                respiratory_rate=int(24 * dm),       # Kussmaul respirations
                temperature_f=101.2,
                o2_saturation=int(95 - (2 * (dm - 1)))
            ),
            "Asthma Exacerbation": VitalSigns(
                heart_rate=int(115 * dm),
                systolic_bp=int(135 - (10 * (dm - 1))),
                diastolic_bp=int(85 - (5 * (dm - 1))),
                respiratory_rate=int(28 * dm),
                temperature_f=99.5,
                o2_saturation=int(87 - (4 * (dm - 1)))
            ),
            # --- NEW DIAGNOSES ---
            # Stroke: hypertensive, normal temp, often normal O2
            "Stroke": VitalSigns(
                heart_rate=int(88 * dm),
                systolic_bp=int(185 - (10 * (dm - 1))),  # Hypertensive crisis common
                diastolic_bp=int(105 - (5 * (dm - 1))),
                respiratory_rate=int(16 * dm),
                temperature_f=98.6,
                o2_saturation=int(96 - (2 * (dm - 1)))
            ),
            # Pneumonia: febrile, tachypneic, hypoxic, tachycardic
            "Pneumonia": VitalSigns(
                heart_rate=int(105 * dm),
                systolic_bp=int(115 - (12 * (dm - 1))),
                diastolic_bp=int(72 - (8 * (dm - 1))),
                respiratory_rate=int(24 * dm),
                temperature_f=103.1,
                o2_saturation=int(90 - (4 * (dm - 1)))
            ),
            # GI Bleed: tachycardic, hypotensive (hypovolemic), normal temp/O2
            "GI Bleed": VitalSigns(
                heart_rate=int(115 * dm),
                systolic_bp=int(90 - (18 * (dm - 1))),
                diastolic_bp=int(55 - (10 * (dm - 1))),
                respiratory_rate=int(18 * dm),
                temperature_f=98.4,
                o2_saturation=int(97 - (1 * (dm - 1)))
            ),
            # CHF Exacerbation: tachycardic, hypertensive initially, tachypneic, hypoxic
            "CHF Exacerbation": VitalSigns(
                heart_rate=int(108 * dm),
                systolic_bp=int(165 - (15 * (dm - 1))),
                diastolic_bp=int(95 - (8 * (dm - 1))),
                respiratory_rate=int(26 * dm),
                temperature_f=98.8,
                o2_saturation=int(88 - (4 * (dm - 1)))
            ),
            # Overdose/Toxicology: bradycardic or tachycardic (depends on agent),
            # using opioid-like profile: bradypneic, hypotensive, hypothermic
            "Overdose": VitalSigns(
                heart_rate=int(62 / dm),              # Bradycardia worsens
                systolic_bp=int(95 - (15 * (dm - 1))),
                diastolic_bp=int(58 - (8 * (dm - 1))),
                respiratory_rate=max(6, int(10 / dm)),  # Respiratory depression
                temperature_f=96.8,                     # Hypothermia common
                o2_saturation=int(88 - (5 * (dm - 1)))
            ),
            # Seizure: tachycardic, hypertensive, tachypneic post-ictal, mild hyperthermia
            "Seizure": VitalSigns(
                heart_rate=int(120 * dm),
                systolic_bp=int(160 - (10 * (dm - 1))),
                diastolic_bp=int(95 - (5 * (dm - 1))),
                respiratory_rate=int(22 * dm),
                temperature_f=100.2,
                o2_saturation=int(92 - (3 * (dm - 1)))
            ),
            # Diabetic Hypoglycemia: tachycardic, diaphoretic, normal BP
            "Hypoglycemia": VitalSigns(
                heart_rate=int(105 * dm),
                systolic_bp=int(130 - (8 * (dm - 1))),
                diastolic_bp=int(78 - (5 * (dm - 1))),
                respiratory_rate=int(18 * dm),
                temperature_f=98.2,
                o2_saturation=int(98 - (1 * (dm - 1)))
            ),
            # Tension Pneumothorax: tachycardic, hypotensive, tachypneic, severely hypoxic
            "Pneumothorax": VitalSigns(
                heart_rate=int(130 * dm),
                systolic_bp=int(80 - (20 * (dm - 1))),
                diastolic_bp=int(50 - (12 * (dm - 1))),
                respiratory_rate=int(30 * dm),
                temperature_f=98.6,
                o2_saturation=int(82 - (5 * (dm - 1)))
            ),
            # Meningitis: febrile, tachycardic, may be hypotensive if septic
            "Meningitis": VitalSigns(
                heart_rate=int(115 * dm),
                systolic_bp=int(105 - (15 * (dm - 1))),
                diastolic_bp=int(65 - (10 * (dm - 1))),
                respiratory_rate=int(20 * dm),
                temperature_f=103.8,
                o2_saturation=int(96 - (2 * (dm - 1)))
            ),
            # Hyperkalemia: bradycardic, normal BP initially, normal temp/O2
            "Hyperkalemia": VitalSigns(
                heart_rate=max(35, int(55 / dm)),      # Bradycardia worsens
                systolic_bp=int(110 - (10 * (dm - 1))),
                diastolic_bp=int(68 - (5 * (dm - 1))),
                respiratory_rate=int(16 * dm),
                temperature_f=98.6,
                o2_saturation=int(97 - (1 * (dm - 1)))
            ),
            # Ectopic Pregnancy: tachycardic, hypotensive (hemorrhage), normal temp
            "Ectopic Pregnancy": VitalSigns(
                heart_rate=int(118 * dm),
                systolic_bp=int(88 - (18 * (dm - 1))),
                diastolic_bp=int(52 - (10 * (dm - 1))),
                respiratory_rate=int(20 * dm),
                temperature_f=98.6,
                o2_saturation=int(98 - (1 * (dm - 1)))
            ),
            # Thyroid Storm: severely tachycardic, hyperthermic, hypertensive
            "Thyroid Storm": VitalSigns(
                heart_rate=int(145 * dm),
                systolic_bp=int(160 - (10 * (dm - 1))),
                diastolic_bp=int(70 - (8 * (dm - 1))),  # Wide pulse pressure
                respiratory_rate=int(24 * dm),
                temperature_f=104.5,
                o2_saturation=int(95 - (2 * (dm - 1)))
            ),
            # Cardiac Arrest: pulseless — represented as extreme values
            "Cardiac Arrest": VitalSigns(
                heart_rate=0,
                systolic_bp=0,
                diastolic_bp=0,
                respiratory_rate=0,
                temperature_f=98.0,
                o2_saturation=0
            ),
        }

        return vital_presets.get(
            self.diagnosis,
            VitalSigns(110, 100, 65, 20, 99.0, 94)  # Default fallback
        )
    
    def record_intervention(self, intervention: Intervention) -> None:
        """
        Record that a specific intervention was performed.
        
        Args:
            intervention: The Intervention enum value
        """
        self._interventions_performed[intervention] = True
    
    def get_next_state_vitals(self, current_state: int, 
                             current_vitals: VitalSigns) -> VitalSigns:
        """
        Calculate vital signs for the next state based on:
        - Which interventions have been performed
        - Scenario difficulty
        - Current state number
        
        Args:
            current_state: Current state number (1-5)
            current_vitals: Current vital signs
            
        Returns:
            VitalSigns for the next state
        """
        new_vitals = current_vitals
        
        # Determine if condition improves or worsens based on interventions
        critical_interventions = [
            Intervention.IV_ACCESS,
            Intervention.ANTIBIOTICS,
            Intervention.FLUID_RESUSCITATION,
            Intervention.OXYGEN
        ]
        
        interventions_performed_count = sum(
            1 for intervention in critical_interventions
            if self._interventions_performed.get(intervention, False)
        )
        
        # If adequate interventions were performed, improve vitals
        if interventions_performed_count >= min(3, len(critical_interventions)):
            improvement_factor = 1.05  # 5% improvement per state
            new_vitals = VitalSigns(
                heart_rate=max(60, int(new_vitals.heart_rate * 0.97)),
                systolic_bp=min(140, int(new_vitals.systolic_bp * 1.02)),
                diastolic_bp=min(90, int(new_vitals.diastolic_bp * 1.02)),
                respiratory_rate=max(12, int(new_vitals.respiratory_rate * 0.95)),
                temperature_f=new_vitals.temperature_f * 0.98,
                o2_saturation=min(98, int(new_vitals.o2_saturation * 1.01))
            )
        else:
            # Condition deteriorates if interventions were inadequate
            degradation_factor = 1.0 + (0.05 * self.difficulty_multiplier)
            new_vitals = VitalSigns(
                heart_rate=int(new_vitals.heart_rate * degradation_factor),
                systolic_bp=int(new_vitals.systolic_bp * (2.0 - degradation_factor)),
                diastolic_bp=int(new_vitals.diastolic_bp * (2.0 - degradation_factor)),
                respiratory_rate=int(new_vitals.respiratory_rate * degradation_factor),
                temperature_f=new_vitals.temperature_f + 0.2,
                o2_saturation=max(70, int(new_vitals.o2_saturation - 2))
            )
        
        return new_vitals
    
    def generate_state_progression(self, state_number: int,
                                  vital_signs: VitalSigns) -> StateProgression:
        """
        Generate the content for a specific scenario state.
        
        Args:
            state_number: State number (1-5)
            vital_signs: Vital signs for this state
            
        Returns:
            StateProgression object with complete state information
        """
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
        """Generate physical exam findings based on state and diagnosis."""
        diagnosis_findings = {
            "Sepsis": "Flushed skin, tachycardia, rapid capillary refill, possible altered mental status",
            "Myocardial Infarction": "Diaphoresis, pale, anxious, possible JVD or lung crackles",
            "Anaphylaxis": "Urticaria, edema, stridor, bronchospasm, hypotension",
            "Pulmonary Embolism": "Tachycardia, tachypnea, possible decreased breath sounds",
            "DKA": "Fruity breath odor, Kussmaul respirations, dehydration signs",
            "Asthma Exacerbation": "Wheezing, reduced air movement, accessory muscle use",
            "Stroke": "Facial droop, unilateral weakness, speech difficulty, possible gaze deviation",
            "Pneumonia": "Crackles/rhonchi on auscultation, productive cough, febrile, tachypneic",
            "GI Bleed": "Pale, diaphoretic, melena or hematemesis, orthostatic hypotension, tachycardia",
            "CHF Exacerbation": "JVD, bilateral crackles, peripheral edema, S3 gallop, orthopnea",
            "Overdose": "Pinpoint pupils (opioid), decreased responsiveness, shallow respirations, cool skin",
            "Seizure": "Post-ictal confusion, tongue laceration, incontinence, tachycardia, diaphoresis",
            "Hypoglycemia": "Diaphoresis, tremor, confusion or agitation, tachycardia",
            "Pneumothorax": "Absent breath sounds unilaterally, tracheal deviation, JVD, hyperresonance to percussion",
            "Meningitis": "Nuchal rigidity, photophobia, petechial rash (if meningococcal), Kernig/Brudzinski positive",
            "Hyperkalemia": "Bradycardia, muscle weakness, peaked T-waves on ECG, possible cardiac arrhythmia",
            "Ectopic Pregnancy": "Lower abdominal tenderness, guarding, vaginal bleeding, signs of hypovolemic shock",
            "Thyroid Storm": "Severe tachycardia, hyperthermia, agitation/delirium, tremor, lid lag, diaphoresis",
            "Cardiac Arrest": "Unresponsive, no pulse, apneic, cyanosis",
        }
        
        base_finding = diagnosis_findings.get(
            self.diagnosis,
            "Abnormal vital signs noted"
        )
        
        # Add state-specific worsening
        if state >= 3 and vitals.o2_saturation < 90:
            base_finding += " | **CRITICAL**: Hypoxia worsening"
        if state >= 3 and vitals.systolic_bp < 90:
            base_finding += " | **CRITICAL**: Hypotension developing"
        
        return base_finding
    
    def _get_expected_actions(self, state: int) -> List[str]:
        """Return expected clinical actions for each state."""
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
                "Implement sepsis bundle / ACLS as appropriate",
                "Administer antibiotics within time limit",
                "Increase fluid delivery or initiate vasopressors",
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
        """Return the logic for transitioning to the next state."""
        logic = {
            1: "If adequate initial assessment performed → State 2. Otherwise, condition deteriorates rapidly.",
            2: "If critical interventions initiated → State 3. If delayed → State 3 with worse vitals.",
            3: "If sepsis bundle/emergency protocols followed → State 4 (improvement). Otherwise → State 4 (continued decline).",
            4: "If sustained treatment → State 5 (resolution). If treatment inadequate → State 5 (complications).",
            5: "End scenario. Debrief based on clinical decisions and outcomes."
        }
        return logic.get(state, "Scenario progression based on learner actions")
    
    def validate_scenario_completeness(self) -> Tuple[bool, List[str]]:
        """
        Validates that the scenario has all required components.
        
        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        errors = []
        
        if not self.diagnosis:
            errors.append("Missing primary diagnosis")
        
        if self.difficulty not in [d for d in Difficulty]:
            errors.append("Invalid difficulty level")
        
        if self.patient_age < 0 or self.patient_age > 120:
            errors.append("Patient age out of valid range")
        
        # Check that at least some intervention pathways are defined
        if not self._interventions_performed:
            errors.append("No intervention pathways defined")
        
        return len(errors) == 0, errors

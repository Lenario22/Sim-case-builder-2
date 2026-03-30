"""
Case Engine - Multi-Phase Clinical Simulation Generator

The brain of the Sim Case Builder. Uses a three-phase AI pipeline:
  Phase 1: Clinical Reasoning — AI maps out pathophysiology, timeline, interventions
  Phase 2: Full Case Generation — Guided by Phase 1, fills all 96 template fields
  Phase 3: Clinical Self-Review — AI audits its own work for inconsistencies
"""

from google import genai
from google.genai import types as genai_types
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from logic_controller import (
    CCS5Level, VectorModel, VectorAxis, ComplexityProfile,
    TaskCCF, PatientCCF, UncertaintyType, CognitiveBias,
    BranchingEngine, ComorbidityEngine, TimePressureEngine
)
from utils import robust_parse_json


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class CaseConfig:
    """Everything the engine needs to generate a case."""
    diagnosis: str
    patient_age: int
    patient_gender: str
    difficulty: str          # Legacy string kept for template compatibility
    target_learner: str
    custom_focus: str = ""
    ccs5_level: int = 0      # 0 = derive from difficulty; 1-5 = explicit CCS-5 level
    comorbidities: List[str] = field(default_factory=list)


@dataclass
class CaseResult:
    """What the engine returns after generation."""
    case_data: Dict[str, Any]
    clinical_plan: Dict[str, Any]
    complexity_profile: Dict[str, Any]   # Phase 0 output
    review_notes: str
    phases_completed: int
    log: List[str] = field(default_factory=list)


# ============================================================================
# SYSTEM PROMPT — This is what makes the engine smart.
#
# This encodes deep expertise in clinical simulation design, medical education
# pedagogy, and realistic patient progression. It transforms Gemini from a
# generic chatbot into a simulation design expert.
# ============================================================================

SYSTEM_PROMPT = """You are an expert Clinical Simulation Scientist specializing in the 'Science of the Grey.' You design cases for the University of Kentucky Simulation Center with deep expertise in medical education, complexity science, and clinical reasoning theory.

## Foundational Pedagogical Frameworks

**Jeffries Simulation Theory**: Every case has clear learning objectives, appropriate fidelity, structured debriefing hooks, and measurable outcomes. You always design BACKWARD — start from what the learner must demonstrate, then build the scenario to test it.

**INACSL Standards of Best Practice**: Clear objectives, appropriate complexity, realistic patient progression, defined critical actions, structured debriefing questions.

## The Science of the Grey: Complexity Frameworks

### Vector Model of Patient Complexity
You account for 5 axes of influence. Each axis has a magnitude (0–5) and specific contributing factors:
- **Biological**: Comorbidities, organ failure, genetic factors, immune status
- **Socioeconomic**: Insurance/access, financial barriers, housing instability
- **Cultural**: Beliefs, language barriers, health literacy, traditional medicine
- **Environmental**: Housing quality, pollution exposure, workplace hazards
- **Behavioral**: Diet, smoking, substance use, treatment adherence

For any given case, the sum of vector pressures determines the intrinsic complexity — independent of diagnosis.

### Complexity-Contributing Factors (CCFs)

**Task CCFs** (arise from the clinical environment):
Goal Conflict, Data Deluge, Time Pressure, Ambiguous Cues, Equipment Failure, Resource Limitation, Interprofessional Tension, Communication Barrier, Knowledge Gap, Ethical Dilemma, Diagnostic Uncertainty, Handoff Complexity, System Failure

**Patient CCFs** (arise from the patient):
Polypharmacy (≥5 meds), Age ≥75, Cognitive Impairment, Multimorbidity (≥3 chronic conditions), Functional Decline, Mental Health Comorbidity, Substance Use Disorder, Social Isolation, Language Barrier, Non-Adherence to Treatment, Rare or Atypical Disease

### Han's Taxonomy of Uncertainty
Differentiate the dominant type of uncertainty in each case:
- **Scientific**: Evidence gaps, conflicting guidelines, emerging pathology
- **Practical**: System failures, resource constraints, logistical barriers
- **Personal**: Patient values, goals of care, moral/existential burdens

## CCS-5 Difficulty Scale (Dreyfus Model)

- **Level 1 — Novice**: Routine, linear. Single acute symptom, high goal clarity, minimal decision steps.
- **Level 2 — Advanced Beginner**: Complicated. Common illness + 1-2 secondary diagnoses. Basic pattern recognition required.
- **Level 3 — Competent**: Moderately complex. Multimorbidity with conflicting treatment goals. Requires analytical System 2 thinking.
- **Level 4 — Proficient**: Highly complex. Atypical presentation, high extrinsic load, significant socioeconomic barriers.
- **Level 5 — Expert**: Extreme complexity. Medically Unexplained Symptoms, rare pathology, or entangled psychosocial issues. High diagnostic uncertainty, moral/existential burdens.

## Structured Clinical Reasoning (Hypothetico-Deductive Method)

For every case, simulate expert implicit reasoning through four steps:
1. **Cue Acquisition**: What initial data points (symptoms, vitals, history fragments) are clinically salient?
2. **Hypothesis Generation**: What are the 2-3 most defensible working diagnoses based on the cues?
3. **Cue Interpretation**: How does each additional piece of information support or refute each hypothesis?
4. **Hypothesis Evaluation**: What is the most defensible probabilistic conclusion and why?

## Cognitive Bias Awareness

For every case, explicitly identify which cognitive biases a learner is most at risk for:
- **Anchoring**: Over-relying on the first abnormal finding (e.g., glucose of 450 locks learner on DKA, misses underlying trigger)
- **Search Satisficing**: Stopping after one plausible diagnosis without completing the differential
- **Confirmation Bias**: Selectively interpreting data to confirm the initial impression

## Mandate for Cases Levels 4-5

For Proficient and Expert level cases, explicitly state: 'There is no single correct answer — only the most defensible probabilistic one.' Highlight where reasonable clinicians could legitimately disagree.

## Patient Progression Architecture

Patients follow pathophysiological trajectories, not random changes:
- **Compensated phase**: Body is coping. Vitals may look deceptively normal.
- **Decompensated phase**: Compensatory mechanisms fail. Critical interventions required.
- **Resolution or crisis**: Determined by whether interventions were timely and correct.

Every vital sign in every state must be explainable by the underlying pathophysiology. Every lab value must tell the diagnostic story.

## Critical Rules

1. Every field must be clinically defensible
2. Vital signs progress logically based on pathophysiology — never random numbers
3. Labs correlate with the diagnosis and clinical timeline
4. CCFs and vector scores must actually manifest in the case content
5. Critical actions are specific and time-bound
6. Debrief questions target learning objectives, not vague reflection
7. Content is appropriate for the specified learner level and CCS-5 tier
8. For Levels 4-5, acknowledge irreducible uncertainty explicitly"""


# ============================================================================
# PHASE PROMPTS
# ============================================================================

# ============================================================================
# PHASE 0 PROMPT — Complexity Profiling
# ============================================================================

PHASE0_PROMPT = """## Task: Clinical Complexity Profile

Before generating any case content, produce a rigorous complexity characterization of this scenario using the frameworks below.

**Patient Parameters:**
- Diagnosis: {diagnosis}
- Age: {age} years old
- Gender: {gender}
- CCS-5 Level: {ccs5_label} — {ccs5_description}
- Target Learner: {target_learner}
{custom_section}

**Return ONLY a valid JSON object with this exact structure:**

{{
  "ccs5_level": {ccs5_value},
  "dreyfus_stage": "{ccs5_label}",
  "vector_model": {{
    "biological":    {{"magnitude": 0, "factors": ["list of specific biological complexity factors"]}},
    "socioeconomic": {{"magnitude": 0, "factors": ["list of specific socioeconomic complexity factors"]}},
    "cultural":      {{"magnitude": 0, "factors": ["list of specific cultural complexity factors"]}},
    "environmental": {{"magnitude": 0, "factors": ["list of specific environmental factors"]}},
    "behavioral":    {{"magnitude": 0, "factors": ["list of specific behavioral factors"]}}
  }},
  "task_ccfs": ["Subset of: Goal Conflict, Data Deluge, Time Pressure, Ambiguous Cues, Equipment Failure, Resource Limitation, Interprofessional Tension, Communication Barrier, Knowledge Gap, Ethical Dilemma, Diagnostic Uncertainty, Handoff Complexity, System Failure"],
  "patient_ccfs": ["Subset of: Polypharmacy (≥5 meds), Age ≥75, Cognitive Impairment, Multimorbidity (≥3 chronic conditions), Functional Decline, Mental Health Comorbidity, Substance Use Disorder, Social Isolation, Language Barrier, Non-Adherence to Treatment, Rare or Atypical Disease"],
  "uncertainty_type": "Scientific | Practical | Personal",
  "uncertainty_rationale": "1-2 sentences explaining the dominant uncertainty source in this case",
  "chain_of_thought": {{
    "cue_acquisition": "What initial data points (symptoms, vitals, history) are clinically salient and why",
    "hypothesis_generation": "The 2-3 most defensible working diagnoses given the cues, ranked by probability",
    "cue_interpretation": "How each additional piece of data supports or refutes each hypothesis",
    "hypothesis_evaluation": "The most defensible probabilistic conclusion and the reasoning that got there"
  }},
  "cognitive_biases_at_risk": [
    {{"bias": "Bias name", "trigger": "Specific feature of THIS case that risks triggering this bias"}}
  ],
  "intrinsic_fairness_note": "For CCS Level 4-5 only: 1-2 sentences on where reasonable clinicians could legitimately disagree"
}}

Instructions:
- Set each vector axis magnitude from 0 (no pressure) to 5 (extreme pressure) based on the diagnosis and patient parameters
- Select only the CCFs that will genuinely manifest in the generated case
- Be specific — generic factor lists defeat the purpose
- The chain_of_thought should mirror how an expert would actually reason through this case"""


PHASE1_PROMPT = """## Task: Clinical Reasoning Plan

Before generating a full simulation case, I need you to think through the clinical scenario deeply. This plan will guide the full case generation.

**Patient Parameters:**
- Diagnosis: {diagnosis}
- Age: {age} years old
- Gender: {gender}
- Difficulty: {difficulty} (CCS-5: {ccs5_label})
- Target Learner: {target_learner}
{custom_section}

**Complexity Context (from Phase 0):**
{complexity_context}

**Produce a JSON object with this exact structure:**

{{
  "pathophysiology_summary": "2-3 sentence explanation of the disease process and why this patient is presenting now",
  "expected_presentation": "How this specific patient (given age, gender, comorbidities) would present — chief complaint, appearance, behavior",
  "critical_timeline": "Time-sensitive interventions and their windows (e.g., 'antibiotics within 1 hour of sepsis recognition', 'PCI within 90 minutes of STEMI diagnosis')",
  "vital_sign_trajectory": {{
    "arrival": "Expected vitals on arrival with clinical rationale",
    "if_treated_well": "How vitals improve over 30-60 min with proper interventions",
    "if_treated_poorly": "How vitals deteriorate over 30-60 min without proper interventions"
  }},
  "key_lab_expectations": "Which labs will be abnormal and WHY — tied to pathophysiology",
  "differential_diagnosis": "2-3 realistic differentials a learner might consider",
  "critical_actions_priority": ["Ordered list of must-do interventions, most urgent first"],
  "common_learner_mistakes": ["What learners at this level typically miss or do wrong"],
  "five_state_arc": {{
    "state_1": "Brief description of arrival/initial presentation",
    "state_2": "Brief description of early changes (what prompts reassessment)",
    "state_3": "Brief description of the critical decision point",
    "state_4": "Brief description of response to treatment (good path) or continued decline (bad path)",
    "state_5": "Brief description of resolution or escalation"
  }},
  "teaching_pearls": ["2-3 key clinical pearls this case should reinforce"]
}}

Think step by step. Every element must be clinically accurate for this specific diagnosis, patient, and difficulty level."""


PHASE2_PROMPT = """## Task: Generate Complete Simulation Case

Using the clinical reasoning plan below as your guide, generate a complete simulation case that fills ALL fields.

### Your Clinical Plan (from Phase 1):
{clinical_plan}

### Patient Parameters:
- Diagnosis: {diagnosis}
- Age: {age}
- Gender: {gender}
- Difficulty: {difficulty}
- Target Learner: {target_learner}
{custom_section}

### Diagnosis-Specific Branching Guide
Use this clinical reference to ensure your state progression is medically accurate
and diagnosis-specific. Your generated states MUST reflect these pathways:

{branching_context}

{comorbidity_context}

{time_pressure_context}

### Generate a JSON object with EVERY field below populated:

{{
  "case_name": "Descriptive case title",
  "key_words": "Comma-separated clinical keywords for searchability",
  "case_summary": "2-3 sentence overview of the entire scenario arc",
  "age": "{age}",
  "setting": "Clinical setting (ED, ICU, floor, clinic, prehospital)",
  "demographics": "Relevant demographic details beyond age/gender",
  "organ_system": "Primary organ system involved",
  "procedures": "Procedures learners may need to perform or discuss",
  "ed_objectives": "3-5 specific, measurable educational objectives starting with action verbs (Identify, Demonstrate, Prioritize, etc.)",
  "target_learner": "{target_learner}",
  "location": "Specific location within the clinical setting",
  "staff": "Required simulation staff and confederate roles",
  "vignette": "Brief scenario setup read aloud to learners at start (2-3 sentences, sets the scene)",

  "room": "Room/environment setup requirements",
  "manikin": "Manikin type and required capabilities",
  "moulage": "Physical appearance modifications (skin color, wounds, sweat, etc.)",
  "equipment": "All required equipment and supplies",
  "iv": "IV access setup details",
  "ae": "Available ancillary equipment",
  "antib": "Available antibiotics (if applicable)",
  "vps": "Available vasopressors (if applicable)",
  "other_meds": "Other medications that should be available",
  "tele_rythm": "Telemetry rhythm on arrival",
  "o2_sat": "O2 saturation display on arrival",
  "blood_pressure": "Blood pressure display on arrival",
  "respirations": "Respiratory rate display on arrival",
  "temperature": "Temperature display on arrival",
  "arrival_condition": "Brief description of patient condition on learner entry",

  "pt_name": "Realistic patient name",
  "gender": "{gender}",
  "weight": "Patient weight in kg (appropriate for age/build)",
  "chief_complaint": "Patient's chief complaint in their own words",
  "arrival_method": "How patient arrived (ambulance, walk-in, transfer, etc.)",
  "hpi": "Detailed history of present illness — write as a clinician would document after patient interview",
  "pmh": "Past medical history — relevant and realistic for this patient/diagnosis",
  "psh": "Past surgical history",
  "fmh": "Family medical history (relevant to diagnosis if applicable)",
  "social_history": "Social history including occupation, substances, living situation",
  "medications": "Current medications (must be consistent with PMH)",
  "allergies": "Allergies with reaction type",
  "birth_history": "Birth/OB history if relevant, otherwise 'N/A'",
  "code_status": "Code status",

  "neuro_ros": "Neurological review of systems",
  "msk_ros": "Musculoskeletal review of systems",
  "heent_ros": "HEENT review of systems",
  "endo_ros": "Endocrine review of systems",
  "cv_ros": "Cardiovascular review of systems",
  "heme_ros": "Hematologic review of systems",
  "resp_ros": "Respiratory review of systems",
  "skin_ros": "Skin/integumentary review of systems",
  "gi_ros": "Gastrointestinal review of systems",
  "psych_ros": "Psychiatric review of systems",
  "gu_ros": "Genitourinary review of systems",
  "general_ros": "General/constitutional review of systems",

  "hr_arrive": "Heart rate on arrival (number only)",
  "bp_arrive": "Blood pressure on arrival (e.g., '142/88')",
  "rr_arrive": "Respiratory rate on arrival (number only)",
  "o2_arrive": "O2 saturation on arrival (number only, percentage)",
  "temp_arrive": "Temperature on arrival (number only, Fahrenheit)",
  "rhythm_arrive": "Cardiac rhythm on arrival",
  "glucose_arrive": "Blood glucose on arrival (number only)",
  "gcs_arrive": "GCS score on arrival (number or breakdown like 'E4V5M6 = 15')",

  "general_pe": "General appearance on physical exam",
  "neuro_pe": "Neurological physical exam findings",
  "heent_pe": "HEENT physical exam findings",
  "cv_pe": "Cardiovascular physical exam findings",
  "resp_pe": "Respiratory/pulmonary physical exam findings",
  "abd_pe": "Abdominal physical exam findings",
  "gu_pe": "Genitourinary physical exam findings (if relevant, else 'Deferred')",
  "msk_pe": "Musculoskeletal physical exam findings",
  "skin_pe": "Skin/integumentary physical exam findings",
  "psych_pe": "Psychiatric/behavioral physical exam findings",

  "s1_name": "State 1 name — the arrival/initial presentation phase",
  "s1_vitals": "State 1 vital signs as a formatted string: HR, BP, RR, SpO2, Temp, Rhythm",
  "s1_pe": "State 1 physical exam changes (or 'See initial PE above')",
  "s1_actions": "Expected learner actions in State 1 — what they SHOULD do",
  "s1_notes": "Operator notes for State 1 — cues to give, confederate instructions",
  "s1_prog": "Progression trigger: what moves the scenario from State 1 to State 2",

  "s2_name": "State 2 name — early changes requiring reassessment",
  "s2_vitals": "State 2 vital signs (should show early deterioration or first response to treatment)",
  "s2_pe": "State 2 physical exam changes from State 1",
  "s2_actions": "Expected learner actions in State 2",
  "s2_notes": "Operator notes for State 2",
  "s2_prog": "Progression trigger: State 2 to State 3",

  "s3_name": "State 3 name — the critical decision point",
  "s3_vitals": "State 3 vital signs (the pivot point — worst if untreated, starting to improve if treated)",
  "s3_pe": "State 3 physical exam changes",
  "s3_actions": "Expected learner actions in State 3 — this is where critical actions must happen",
  "s3_notes": "Operator notes for State 3 — include BRANCHING: what to do if learner acts vs. doesn't",
  "s3_prog": "Progression trigger: State 3 to State 4 (include both pathways)",

  "s4_name": "State 4 name — response to treatment or continued decline",
  "s4_vitals": "State 4 vital signs (GOOD PATH: improving. BAD PATH: critical deterioration)",
  "s4_pe": "State 4 physical exam changes",
  "s4_actions": "Expected learner actions in State 4",
  "s4_notes": "Operator notes for State 4 — include both pathway instructions",
  "s4_prog": "Progression trigger: State 4 to State 5",

  "s5_name": "State 5 name — resolution or escalation",
  "s5_vitals": "State 5 vital signs (GOOD PATH: near-normal. BAD PATH: peri-arrest or arrest)",
  "s5_pe": "State 5 physical exam changes",
  "s5_actions": "Expected learner actions in State 5 — includes handoff/debrief preparation",
  "s5_notes": "Operator notes for State 5 — wrap-up instructions",
  "s5_prog": "End of scenario. Summary of expected outcome based on learner performance.",

  "wbc": "WBC count (number only, e.g., 14.2)",
  "hgb": "Hemoglobin (number only)",
  "hct": "Hematocrit (number only)",
  "plt": "Platelet count (number only)",
  "na": "Sodium (number only)",
  "k": "Potassium (number only)",
  "cl": "Chloride (number only)",
  "hco3": "Bicarbonate (number only)",
  "ag": "Anion gap (number only)",
  "bun": "BUN (number only)",
  "cr": "Creatinine (number only)",
  "glu": "Glucose (number only)",
  "ast": "AST (number only)",
  "alt": "ALT (number only)",
  "alk_phos": "Alkaline phosphatase (number only)",
  "t_bili": "Total bilirubin (number only)",
  "lipase": "Lipase (number only)",
  "ca": "Calcium (number only)",
  "mg": "Magnesium (number only)",
  "phos": "Phosphorus (number only)",
  "alb": "Albumin (number only)",
  "vbg_ph": "VBG pH (number only)",
  "vbg_pco2": "VBG pCO2 (number only)",
  "vbg_po2": "VBG pO2 (number only)",
  "vbg_hco3": "VBG HCO3 (number only)",
  "lactate": "Lactate (number only)",
  "ua_color": "Urinalysis color",
  "ua_clarity": "Urinalysis clarity",
  "ua_prot": "Urinalysis protein",
  "ua_glu": "Urinalysis glucose",
  "ua_ket": "Urinalysis ketones",

  "critical_actions": ["List of 4-6 critical actions learners MUST perform, specific and time-bound"],
  "debrief_questions": ["List of 4-6 structured debriefing questions targeting learning objectives"],
  "references": ["List of 3-5 clinical references (guidelines, studies, protocols) supporting this case"]
}}

### CRITICAL RULES:
1. Every vital sign must be clinically justified by the pathophysiology in your Phase 1 plan
2. Lab values must correlate with the diagnosis — no random numbers
3. State progression must follow the five_state_arc from your clinical plan
4. All lists (critical_actions, debrief_questions, references) must be actual JSON arrays, not strings
5. Lab values must be NUMBERS ONLY (no units, no ranges) — the template adds units
6. Arrival vitals (hr_arrive, bp_arrive, etc.) must match State 1 vitals
7. Physical exam findings must evolve across states as the patient's condition changes
8. Medications in PMH must be consistent with the past medical history
9. Do NOT use double quotes inside string values — use single quotes if needed"""


PHASE3_PROMPT = """## Task: Clinical Self-Review

Review this completed simulation case for clinical accuracy and educational quality. You are auditing your own work.

### The Case:
{case_json}

### Original Clinical Plan:
{clinical_plan}

### Check for these specific issues:

**Clinical Consistency:**
- Do vital signs progress logically across all 5 states?
- Do lab values match the diagnosis? (e.g., sepsis should have elevated lactate, DKA should have low bicarb and high glucose)
- Are physical exam findings consistent with the vital signs in each state?
- Does the medication list match the past medical history?
- Are allergies considered in the treatment plan?

**Educational Quality:**
- Are critical actions specific and time-bound (not vague)?
- Do debrief questions target the stated learning objectives?
- Is the difficulty level appropriate (not too easy/hard for the target learner)?
- Does the state progression create meaningful decision points?

**Completeness:**
- Are any fields empty, generic, or placeholder-like?
- Do all 5 states have distinct, progressing content?
- Are operator notes actionable for someone running the sim?

**Return a JSON object with this structure:**
{{
  "issues_found": ["List of specific issues found, if any"],
  "corrections": {{}},
  "quality_score": "1-10 rating with brief justification",
  "overall_assessment": "1-2 sentence summary of case quality"
}}

The "corrections" object should contain ONLY the field keys that need fixing, with corrected values. If a field is fine, do NOT include it. If no corrections are needed, return an empty object {{}}.

Be thorough but fair. Minor stylistic preferences are not issues — focus on clinical accuracy and educational value."""


# ============================================================================
# THE ENGINE
# ============================================================================

class CaseEngine:
    """
    Multi-phase clinical simulation case generator.

    Three phases, each building on the last:
      Phase 1: Clinical reasoning — AI maps the pathophysiology and scenario arc
      Phase 2: Full generation — AI fills all 96 fields guided by Phase 1
      Phase 3: Self-review — AI audits its own output for clinical consistency
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the engine.

        Args:
            api_key: Gemini API key
            model_name: Which Gemini model to use
        """
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name
        self._system_instruction = SYSTEM_PROMPT
        self.log: List[str] = []

    def _call_model(self, prompt: str, json_mode: bool = True) -> str:
        """Call the Gemini model and return the raw response text."""
        config = genai_types.GenerateContentConfig(
            systemInstruction=self._system_instruction,
            responseMimeType="application/json" if json_mode else None,
        )
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=config,
        )
        return response.text

    def _resolve_ccs5(self, config: CaseConfig) -> CCS5Level:
        """Resolve the CCS-5 level from either explicit setting or legacy difficulty string."""
        if config.ccs5_level and 1 <= config.ccs5_level <= 5:
            return CCS5Level(config.ccs5_level)
        mapping = {"Basic": CCS5Level.NOVICE, "Intermediate": CCS5Level.ADV_BEGINNER,
                   "Advanced": CCS5Level.COMPETENT, "Nightmare": CCS5Level.PROFICIENT}
        return mapping.get(config.difficulty, CCS5Level.ADV_BEGINNER)

    def generate(self, config: CaseConfig) -> CaseResult:
        """
        Run the full four-phase generation pipeline.

        Phases:
          0: Complexity Profiling (Vector Model, CCFs, CoT, Bias check)
          1: Clinical Reasoning Plan
          2: Full Case Generation (96 fields)
          3: Clinical Self-Review

        Args:
            config: CaseConfig with all patient/scenario parameters

        Returns:
            CaseResult with case_data, clinical_plan, complexity_profile, review notes, and log
        """
        self.log = []
        self._log("Engine started")

        ccs5 = self._resolve_ccs5(config)
        self._log(f"CCS-5 Level: {ccs5.label}")

        # Phase 0: Complexity Profiling
        self._log("Phase 0: Building complexity profile (Vector Model, CCFs, CoT)...")
        complexity_profile = self._phase0_complexity_profile(config, ccs5)
        self._log("Phase 0 complete")

        # Phase 1: Clinical Reasoning
        self._log("Phase 1: Building clinical reasoning plan...")
        clinical_plan = self._phase1_clinical_reasoning(config, ccs5, complexity_profile)
        self._log("Phase 1 complete")

        # Phase 2: Full Case Generation
        self._log("Phase 2: Generating full case from clinical plan...")
        case_data = self._phase2_generate_case(config, clinical_plan)
        self._log(f"Phase 2 complete — {len(case_data)} fields generated")

        # Phase 3: Clinical Self-Review
        self._log("Phase 3: AI self-review for clinical accuracy...")
        review_notes, corrections = self._phase3_clinical_review(
            case_data, clinical_plan
        )

        # Apply any corrections from Phase 3
        if corrections:
            case_data.update(corrections)
            self._log(f"Phase 3: Applied {len(corrections)} corrections")
        else:
            self._log("Phase 3: No corrections needed")

        self._log("Generation complete")

        return CaseResult(
            case_data=case_data,
            clinical_plan=clinical_plan,
            complexity_profile=complexity_profile,
            review_notes=review_notes,
            phases_completed=4,
            log=self.log.copy()
        )

    # ------------------------------------------------------------------
    # PHASE 0: Complexity Profiling
    # ------------------------------------------------------------------

    def _phase0_complexity_profile(self, config: CaseConfig,
                                   ccs5: CCS5Level) -> Dict[str, Any]:
        """
        Phase 0: Generate the complexity profile — Vector Model, CCFs,
        Han's uncertainty taxonomy, Chain-of-Thought, and bias risks.
        """
        custom_section = ""
        if config.custom_focus:
            custom_section = f"- Custom Instructions: {config.custom_focus}"

        prompt = PHASE0_PROMPT.format(
            diagnosis=config.diagnosis,
            age=config.patient_age,
            gender=config.patient_gender,
            ccs5_label=ccs5.label,
            ccs5_description=ccs5.description,
            ccs5_value=ccs5.value,
            target_learner=config.target_learner,
            custom_section=custom_section
        )

        try:
            text = self._call_model(prompt)
            return self._parse_json_response(text)
        except Exception as e:
            self._log(f"Phase 0 failed (non-critical): {str(e)}")
            return {"ccs5_level": ccs5.value, "dreyfus_stage": ccs5.label,
                    "vector_model": {}, "task_ccfs": [], "patient_ccfs": [],
                    "uncertainty_type": "Scientific", "chain_of_thought": {},
                    "cognitive_biases_at_risk": []}

    # ------------------------------------------------------------------
    # PHASE 1: Clinical Reasoning
    # ------------------------------------------------------------------

    def _phase1_clinical_reasoning(self, config: CaseConfig,
                                   ccs5: CCS5Level,
                                   complexity_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 1: Have the AI think through the clinical scenario before
        generating any case fields. This produces a structured reasoning
        document that guides Phase 2.
        """
        custom_section = ""
        if config.custom_focus:
            custom_section = f"- Custom Instructions: {config.custom_focus}"

        # Summarize the most important Phase 0 context for Phase 1
        cot = complexity_profile.get("chain_of_thought", {})
        complexity_context = json.dumps({
            "vector_model": complexity_profile.get("vector_model", {}),
            "task_ccfs": complexity_profile.get("task_ccfs", []),
            "patient_ccfs": complexity_profile.get("patient_ccfs", []),
            "uncertainty_type": complexity_profile.get("uncertainty_type", ""),
            "chain_of_thought_primer": cot,
        }, indent=2)

        prompt = PHASE1_PROMPT.format(
            diagnosis=config.diagnosis,
            age=config.patient_age,
            gender=config.patient_gender,
            difficulty=config.difficulty,
            ccs5_label=ccs5.label,
            target_learner=config.target_learner,
            custom_section=custom_section,
            complexity_context=complexity_context
        )

        text = self._call_model(prompt)
        plan = self._parse_json_response(text)
        return plan

    # ------------------------------------------------------------------
    # PHASE 2: Full Case Generation
    # ------------------------------------------------------------------

    def _phase2_generate_case(self, config: CaseConfig,
                              clinical_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: Generate all 96 case fields, guided by the clinical
        reasoning plan from Phase 1 and diagnosis-specific branching.
        """
        custom_section = ""
        if config.custom_focus:
            custom_section = f"- Custom Instructions: {config.custom_focus}"

        # Build diagnosis-specific branching context
        branching_engine = BranchingEngine()
        branching_context = branching_engine.build_prompt_injection(
            config.diagnosis, config.difficulty
        )
        self._log(f"Branching context injected ({len(branching_context)} chars)")

        # Build comorbidity context
        comorbidity_context = ""
        if config.comorbidities:
            comorbidity_engine = ComorbidityEngine()
            effect = comorbidity_engine.compute_effects(
                config.diagnosis, config.comorbidities
            )
            comorbidity_context = effect.prompt_context
            self._log(f"Comorbidity context injected: {', '.join(config.comorbidities)}")

        # Build time-pressure context
        time_engine = TimePressureEngine()
        timeline = time_engine.build_timeline(config.diagnosis, config.difficulty)
        time_pressure_context = timeline.prompt_context
        self._log(f"Time-pressure context injected ({timeline.total_duration_minutes} min scenario)")

        prompt = PHASE2_PROMPT.format(
            clinical_plan=json.dumps(clinical_plan, indent=2),
            diagnosis=config.diagnosis,
            age=config.patient_age,
            gender=config.patient_gender,
            difficulty=config.difficulty,
            target_learner=config.target_learner,
            custom_section=custom_section,
            branching_context=branching_context,
            comorbidity_context=comorbidity_context,
            time_pressure_context=time_pressure_context
        )

        text = self._call_model(prompt)
        case_data = self._parse_json_response(text)
        return case_data

    # ------------------------------------------------------------------
    # PHASE 3: Clinical Self-Review
    # ------------------------------------------------------------------

    def _phase3_clinical_review(self, case_data: Dict[str, Any],
                                clinical_plan: Dict[str, Any]
                                ) -> tuple:
        """
        Phase 3: Have the AI review its own generated case for clinical
        accuracy, consistency, and educational quality.

        Returns:
            Tuple of (review_notes_string, corrections_dict)
        """
        prompt = PHASE3_PROMPT.format(
            case_json=json.dumps(case_data, indent=2),
            clinical_plan=json.dumps(clinical_plan, indent=2)
        )

        try:
            text = self._call_model(prompt)
            review = self._parse_json_response(text)
            review_notes = review.get("overall_assessment", "Review complete")
            corrections = review.get("corrections", {})

            quality_score = review.get("quality_score", "N/A")
            issues = review.get("issues_found", [])

            self._log(f"Quality score: {quality_score}")
            if issues:
                self._log(f"Issues found: {len(issues)}")
                for issue in issues:
                    self._log(f"  - {issue}")

            return review_notes, corrections

        except Exception as e:
            self._log(f"Phase 3 review failed (non-critical): {str(e)}")
            return "Review skipped due to error", {}

    # ------------------------------------------------------------------
    # UTILITIES
    # ------------------------------------------------------------------

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        Parse JSON from a Gemini response with multi-strategy recovery.
        Delegates to the shared robust_parse_json() in utils.py.
        """
        return robust_parse_json(text)

    def _log(self, message: str) -> None:
        """Append a message to the generation log."""
        self.log.append(message)

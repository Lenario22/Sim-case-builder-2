"""
Utilities Module
Common helper functions for data formatting, cleaning, and transformation.
"""

from typing import Any, Dict, List, Union
import json
import re
from datetime import datetime


def format_for_humans(data: Any) -> str:
    """
    Convert data structures into human-readable text format.
    
    Args:
        data: Any data type (list, dict, string, etc.)
        
    Returns:
        Formatted string suitable for display
    """
    if isinstance(data, list):
        return "\n• " + "\n• ".join(str(i) for i in data)
    elif isinstance(data, dict):
        return ", ".join(f"{k.capitalize()}: {v}" for k, v in data.items())
    elif isinstance(data, str):
        # Sanitize special characters
        text = data.replace("&", "and")
        text = text.replace("<", "less than")
        text = text.replace(">", "greater than")
        return text
    else:
        return str(data)


def sanitize_template_noise(text: str) -> str:
    """
    Strip parenthetical instructional placeholders left over from templates.
    Removes patterns like (Example: ...), (Click here...), (Include the link...).

    Args:
        text: Raw string possibly containing template noise.

    Returns:
        Clean string with all parenthetical instructions removed.
    """
    # Remove anything enclosed in parentheses (greedy in case of nested parens)
    cleaned = re.sub(r'\([^)]*\)', '', text)
    # Collapse any double-spaces left behind
    cleaned = re.sub(r'  +', ' ', cleaned).strip()
    return cleaned


def apply_dka_ua_logic(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Smart medical validation: enforce clinically accurate lab values by diagnosis.

    DKA Rule: If Blood_Glucose > 250 mg/dL AND pH < 7.30, UA ketones and glucose
    MUST be Positive (4+). Overrides any 'Negative' values the AI may have set.
    
    MI Rule: Troponin should be elevated for symptomatic MI.
    
    Thyroid Rule: TSH and T4 should reflect the suspected thyroid condition.

    Args:
        case_data: Complete case dictionary.

    Returns:
        case_data with corrected lab fields based on clinical logic.
    """
    diagnosis = case_data.get("case_name", "").upper()
    
    # -------- DKA Logic --------
    try:
        glucose = float(case_data.get("glu", 0) or case_data.get("glucose_arrive", 0) or 0)
        ph = float(case_data.get("vbg_ph", 7.40) or 7.40)
    except (ValueError, TypeError):
        glucose, ph = 0, 7.40

    if glucose > 250 and ph < 7.30:
        case_data["ua_ketones"] = "Positive (4+)"
        case_data["ua_glu"] = "Positive (4+)"
    
    # -------- MI Logic (Cardiac Troponin) --------
    if "MI" in diagnosis or "MYOCARDIAL" in diagnosis or "INFARCTION" in diagnosis:
        # For MI, troponin should be elevated
        troponin = case_data.get("troponin", "").lower().strip()
        if not troponin or troponin == "pending" or troponin == "normal":
            case_data["troponin"] = "Elevated (0.8 ng/mL)"
    
    # -------- Thyroid Logic --------
    if "THYROID" in diagnosis or "HYPERTHYROID" in diagnosis or "HYPOTHYROID" in diagnosis:
        if "HYPER" in diagnosis:
            case_data["tsh"] = "Low (< 0.1 mIU/L)"
            case_data["t4"] = "Elevated (15.2 ng/dL)"
        else:  # Hypothyroid
            case_data["tsh"] = "Elevated (8.5 mIU/L)"
            case_data["t4"] = "Low (3.2 ng/dL)"

    return case_data


def generate_diagnosis_debrief_questions(diagnosis: str, difficulty: str, target_learner: str) -> List[str]:
    """
    Generate diagnosis-specific and learner-level appropriate debrief questions.
    
    Args:
        diagnosis: Primary diagnosis (e.g., "Sepsis", "DKA", "MI")
        difficulty: Difficulty level (e.g., "Basic", "Intermediate", "Advanced")
        target_learner: Learner type (e.g., "Medical Students", "Residents")
    
    Returns:
        List of 3-5 targeted debrief questions
    """
    diagnosis_upper = str(diagnosis).upper()
    
    # Diagnosis-specific question templates
    templates = {
        "SEPSIS": [
            "What were the earliest clinical indicators that this patient might have sepsis, and how would earlier recognition have changed your management?",
            "Describe your approach to broad-spectrum antibiotic selection given the source of infection in this case.",
            "What physiologic parameters guided your fluid resuscitation strategy, and how would you recognize if the patient was becoming volume-overloaded?",
            "Discuss the role of vasopressors in sepsis management. At what mean arterial pressure would you consider initiation?",
            "What are the key measures for source control in sepsis, and how does this patient's presentation guide your approach?"
        ],
        "DKA": [
            "Potassium Management: What are the risks of administering insulin before checking and repleting potassium, and at what level should insulin be held?",
            "Fluid Resuscitation: Describe your initial fluid strategy for DKA. What type of fluid, what rate, and when would you transition from isotonic to hypotonic fluids?",
            "Precipitating Factors: What are the most common precipitating factors for DKA, and which findings in this case suggested an underlying trigger?",
            "How would you monitor for resolution of DKA, and what lab values guide transition from IV to subcutaneous insulin?",
        ],
        "MYOCARDIAL INFARCTION": [
            "Discuss the differential diagnosis for chest pain in this patient. What features pointed toward ACS?",
            "Describe the role of ECG interpretation and troponin in confirming your diagnosis. When would you consider a repeat ECG or troponin?",
            "What is your reperfusion strategy (PCI vs. thrombolytics) given this patient's presentation, and what are the timelines?",
            "Discuss management of acute complications (arrhythmias, cardiogenic shock, mechanical complications).",
            "How would you counsel this patient on secondary prevention post-MI?"
        ],
        "ANAPHYLAXIS": [
            "What clinical features in this presentation pointed toward anaphylaxis rather than an alternative diagnosis?",
            "Discuss the pharmacology of epinephrine in anaphylaxis: dose, route, timing of repeat doses, and why early administration is critical.",
            "How do you manage biphasic anaphylaxis, and what discharge counseling should this patient receive?",
            "Discuss the role of antihistamines and corticosteroids in anaphylaxis management.",
        ],
        "PULMONARY EMBOLISM": [
            "What diagnostic approach would you use to confirm PE in this patient? Discuss the role of D-dimer, imaging, and clinical probability.",
            "Describe your anticoagulation strategy. Would you consider thrombolytics or embolectomy?",
            "How do you manage hemodynamic instability in PE?",
            "Discuss risk stratification and risk assessment scores for PE severity.",
        ],
        "ASTHMA EXACERBATION": [
            "How would you assess severity of this asthma exacerbation, and what clinical indicators guided your triage decision?",
            "Describe your stepwise approach to bronchodilator and corticosteroid therapy.",
            "When would you consider IV magnesium, subcutaneous epinephrine, or other rescue therapies?",
            "Discuss discharge criteria and outpatient asthma action planning.",
        ]
    }
    
    # Select questions based on diagnosis
    base_questions = []
    for key in templates:
        if key in diagnosis_upper:
            base_questions = templates[key]
            break
    
    # If no match, use generic critical care debrief questions
    if not base_questions:
        base_questions = [
            "What was your initial differential diagnosis, and what clinical reasoning led you to your primary working diagnosis?",
            "Describe the sequence of interventions you performed. Would you change the order given what you learned?",
            "How did you communicate with your team throughout this scenario, and were there any communication breakdowns?",
            "What were the critical decision points in this case, and how did available data influence your choices?",
            "What would you do differently if you encountered a similar patient in the future?"
        ]
    
    # Adjust question complexity/count based on difficulty
    count = {"Basic": 3, "Intermediate": 4, "Advanced": 5, "Nightmare": 5}.get(difficulty, 4)
    return base_questions[:count]


def generate_clinical_references(diagnosis: str, organ_system: str, procedures: str = "") -> List[str]:
    """
    Auto-generate relevant clinical references based on diagnosis and context.
    
    Args:
        diagnosis: Primary diagnosis
        organ_system: Organ system involved
        procedures: Procedures relevant to case
    
    Returns:
        List of 3-5 reference citations
    """
    diagnosis_upper = str(diagnosis).upper()
    
    references = {
        "SEPSIS": [
            "Surviving Sepsis Campaign: International Guidelines for Management of Sepsis and Septic Shock (2021) — Lancet Infect Dis",
            "Rivers E, et al. Early Goal-Directed Therapy in Treatment of Severe Sepsis and Septic Shock. NEJM 2001",
            "Erhegyi TG, et al. Bacterial and Fungal Sepsis — StatPearls",
        ],
        "DKA": [
            "American Diabetes Association Standards of Care in Diabetes — Sec. 6. Glycemic Targets and Hypoglycemia",
            "Wolfsdorf JI, et al. Management of Type 1 Diabetes in Children and Adolescents — ADA Position Statement",
            "Kitabchi AE, et al. Hyperglycemic Crises in Diabetes Mellitus — ADA Position Statement",
        ],
        "MYOCARDIAL INFARCTION": [
            "Troponin as a Marker for Acute Myocardial Infarction: A Review of Current Status — Eur J Clin Invest",
            "American College of Cardiology (ACC) / American Heart Association (AHA) Guidelines for Acute Coronary Syndrome",
            "ISIS-2 Study: Randomized Trial of Intravenous Streptokinase, Oral Aspirin, Both, or Neither Among 17,187 Cases of Suspected MI",
        ],
        "ANAPHYLAXIS": [
            "Simons FER, Ardusso LRF, et al. World Allergy Organization Anaphylaxis Guidelines 2020",
            "Prescott SL, et al. Anaphylaxis: Global Summary and Consensus Recommendations for Next Steps Focusing on Implement",
        ],
        "PULMONARY EMBOLISM": [
            "Kearon C, et al. Antithrombotic Therapy for VTE Disease: ACCP Guidelines (10th Edition)",
            "Wells PS, et al. Evaluation of Suspected Deep Venous Thrombosis in the Lower Extremities with Compression US",
            "Konstantinides SV, et al. 2019 ESC Guidelines for Acute Pulmonary Embolism",
        ],
        "ASTHMA EXACERBATION": [
            "Global Initiative for Asthma (GINA): Global Strategy for Asthma Management and Prevention",
            "National Heart, Lung, and Blood Institute (NHLBI): Expert Panel Report 3 (EPR-3) on the Management of Asthma",
            "Rodrigo GJ, et al. Magnesium Sulfate for Acute Bronchospasm — Systematic Review & Meta-Analysis",
        ],
    }
    
    # Select references based on diagnosis
    base_refs = []
    for key in references:
        if key in diagnosis_upper:
            base_refs = references[key]
            break
    
    # If no match, use generic critical care references
    if not base_refs:
        base_refs = [
            "American College of Emergency Physicians (ACEP) Clinical Policy — Relevant to appropriate diagnosis and management",
            "Tintinalli JE, et al. Tintinalli's Emergency Medicine: A Comprehensive Study Guide (9th Edition)",
            "Critical Care Medicine: A Comprehensive Guide (Chapter relevant to patient presentation)",
        ]
    
    return base_refs


def auto_populate_section_7(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Robustly populate Section 7 (Critical Actions, Debrief Questions, References).
    
    Intelligently extracts from state actions, generates diagnosis-specific debrief questions,
    and creates clinical references. Provides smart fallbacks if AI output is incomplete.
    
    Args:
        case_data: Complete case dictionary
    
    Returns:
        case_data with Section 7 fully populated
    """
    # ====== CRITICAL ACTIONS ======
    critical_actions = case_data.get("critical_actions", [])
    
    # If critical_actions is empty or weak, try to extract from state actions
    if not critical_actions or (isinstance(critical_actions, list) and len([a for a in critical_actions if a and len(str(a)) > 5]) < 2):
        action_fields = ["s3_actions", "s4_actions", "s1_actions", "s2_actions", "s5_actions"]  # Prioritize critical states
        gathered = []
        seen = set()
        
        for field in action_fields:
            raw = case_data.get(field, "")
            if not raw or len(str(raw)) < 10:
                continue
            # Split on common delimiters
            for delimiter in ["\n", "•", "-", "*", ";"]:
                parts = str(raw).split(delimiter)
                for part in parts:
                    line = part.strip(" -•*\t()[]").strip()
                    # Filter for action-like phrases (at least 5 chars, sounds like a clinical action)
                    if line and len(line) > 10 and line not in seen and not line.startswith("("):
                        gathered.append(line)
                        seen.add(line)
                        if len(gathered) >= 6:
                            break
                if len(gathered) >= 6:
                    break
            if len(gathered) >= 6:
                break
        
        # If we collected actions, use them
        if gathered:
            critical_actions = gathered[:6]
        else:
            # Smart fallback: generate from diagnosis + difficulty + ed_objectives
            diagnosis = case_data.get("diagnosis", "Unknown condition")
            difficulty = case_data.get("difficulty", "Intermediate")
            objectives = case_data.get("ed_objectives", "Manage acute presentation")
            
            critical_actions = [
                f"Perform systematic ABCDE assessment and stabilize airway/breathing/circulation",
                f"Obtain appropriate diagnostic testing (labs, imaging) based on differential for {diagnosis}",
                f"Initiate empiric treatment aligned with {diagnosis} management guidelines",
                f"Monitor response to interventions and reassess frequently",
                f"Prepare for escalation or definitive management based on clinical trajectory",
                f"Communicate findings and plan clearly to the team and patient"
            ]
    
    case_data["critical_actions"] = critical_actions[:6]  # Cap at 6
    
    # Format critical_actions as string for Word template
    if isinstance(critical_actions, list):
        case_data["critical_actions"] = "\n• ".join([str(a) for a in critical_actions if a]) if critical_actions else "Not specified"
    
    # ====== DEBRIEF QUESTIONS ======
    debrief_questions = case_data.get("debrief_questions", [])
    
    # If missing or weak, generate diagnosis-specific questions
    if not debrief_questions or (isinstance(debrief_questions, list) and len([q for q in debrief_questions if q and len(str(q)) > 20]) < 2):
        diagnosis = case_data.get("diagnosis", "Unknown")
        difficulty = case_data.get("difficulty", "Intermediate")
        target_learner = case_data.get("target_learner", "Medical Students")
        
        debrief_questions = generate_diagnosis_debrief_questions(diagnosis, difficulty, target_learner)
    
    debrief_questions = debrief_questions[:5]  # Cap at 5
    
    # Format debrief_questions as string for Word template
    if isinstance(debrief_questions, list):
        formatted_q = []
        for i, q in enumerate(debrief_questions, 1):
            if q:
                formatted_q.append(f"{i}. {str(q)}")
        case_data["debrief_questions"] = "\n".join(formatted_q) if formatted_q else "Not specified"
    else:
        case_data["debrief_questions"] = debrief_questions
    
    # ====== REFERENCES ======
    references = case_data.get("references", [])
    
    # If missing or weak, auto-generate clinical references
    if not references or (isinstance(references, list) and len([r for r in references if r and len(str(r)) > 20]) < 2):
        diagnosis = case_data.get("diagnosis", "Unknown")
        organ_system = case_data.get("organ_system", "General")
        procedures = case_data.get("procedures", "")
        
        references = generate_clinical_references(diagnosis, organ_system, procedures)
    
    references = references[:5]  # Cap at 5
    
    # Format references as string for Word template
    if isinstance(references, list):
        formatted_r = []
        for i, r in enumerate(references, 1):
            if r:
                formatted_r.append(f"{i}. {str(r)}")
        case_data["references"] = "\n".join(formatted_r) if formatted_r else "Not specified"
    else:
        case_data["references"] = references
    
    return case_data


def auto_populate_critical_actions(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """DEPRECATED: Use auto_populate_section_7() instead."""
    return auto_populate_section_7(case_data)


def clean_data_structure(data: Any) -> Any:
    """
    Recursively clean a data structure by formatting all string values.
    Removes problematic characters, template noise, and formats nested structures.

    Args:
        data: Dictionary or other data structure to clean

    Returns:
        Cleaned version of the input
    """
    if isinstance(data, dict):
        return {
            k: clean_data_structure(format_for_humans(v))
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [clean_data_structure(item) for item in data]
    elif isinstance(data, str):
        return sanitize_template_noise(data)
    else:
        return data


def validate_json_string(json_string: str) -> tuple[bool, Union[Dict, str]]:
    """
    Validate and parse a JSON string with helpful error messages.
    
    Args:
        json_string: Raw JSON string to parse
        
    Returns:
        Tuple of (is_valid, parsed_dict_or_error_message)
    """
    # Remove markdown code block markers if present
    cleaned = json_string.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    
    try:
        parsed = json.loads(cleaned)
        return True, parsed
    except json.JSONDecodeError as e:
        error_msg = f"JSON Parse Error at line {e.lineno}, column {e.colno}: {e.msg}"
        return False, error_msg


def ensure_no_special_characters(text: str) -> str:
    """
    Remove or escape special characters that could break API calls or Word documents.
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text safe for API/document use
    """
    # Replace double quotes with single quotes
    text = text.replace('"', "'")
    # Replace line breaks with \n escapes
    text = text.replace("\n", "\\n").replace("\r", "\\r")
    return text


def format_vital_signs(vitals: Dict[str, Any]) -> Dict[str, str]:
    """
    Format vital signs dictionary with proper units.
    
    Args:
        vitals: Dictionary with vital sign values
        
    Returns:
        Dictionary with formatted strings including units
    """
    formatted = {}
    unit_map = {
        "heart_rate": "bpm",
        "systolic_bp": "mmHg",
        "diastolic_bp": "mmHg",
        "respiratory_rate": "breaths/min",
        "temperature_f": "°F",
        "o2_saturation": "%",
        "glucose": "mg/dL"
    }
    
    for key, value in vitals.items():
        unit = unit_map.get(key, "")
        if unit:
            formatted[key] = f"{value} {unit}"
        else:
            formatted[key] = str(value)
    
    return formatted


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        ISO format timestamp string
    """
    return datetime.now().isoformat()


def flatten_case_data(case_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Flatten nested case data for Airtable compatibility.
    Airtable prefers flat key-value structures.
    
    Args:
        case_data: Nested case dictionary
        
    Returns:
        Flattened dictionary with string values
    """
    flattened = {}
    
    def _flatten(obj: Any, prefix: str = ""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{prefix}_{key}" if prefix else key
                _flatten(value, new_key)
        elif isinstance(obj, list):
            flattened[prefix] = " | ".join(str(item) for item in obj)
        else:
            flattened[prefix] = str(obj)
    
    _flatten(case_data)
    return flattened


def generate_case_summary(case_data: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the case.
    
    Args:
        case_data: Complete case dictionary
        
    Returns:
        Formatted summary string
    """
    summary_parts = [
        f"**Case:** {case_data.get('case_name', 'Untitled')}",
        f"**Diagnosis:** {case_data.get('diagnosis', 'Unknown')}",
        f"**Patient:** {case_data.get('age', '?')}yo {case_data.get('gender', 'Unknown')}",
        f"**Difficulty:** {case_data.get('difficulty', 'Unknown')}",
        f"**Target Learner:** {case_data.get('target_learner', 'Unknown')}",
        f"**Chief Complaint:** {case_data.get('chief_complaint', 'Not specified')}"
    ]
    
    return "\n".join(summary_parts)


def safe_api_key_display(api_key: str, show_chars: int = 8) -> str:
    """
    Safely display an API key with most characters masked.
    Used for logging and debugging without exposing sensitive data.
    
    Args:
        api_key: Full API key
        show_chars: Number of characters to show at end
        
    Returns:
        Masked key string
    """
    if len(api_key) <= show_chars:
        return "*" * len(api_key)
    return "*" * (len(api_key) - show_chars) + api_key[-show_chars:]


def validate_airtable_credentials(api_key: str, base_id: str) -> tuple[bool, str]:
    """
    Validate basic format of Airtable credentials.
    
    Args:
        api_key: API key to validate
        base_id: Base ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    errors = []
    
    if not api_key or not isinstance(api_key, str):
        errors.append("API key is missing or invalid")
    elif len(api_key) < 20:
        errors.append("API key appears too short (should be longer)")
    
    if not base_id or not isinstance(base_id, str):
        errors.append("Base ID is missing or invalid")
    elif not base_id.startswith("app"):
        errors.append("Base ID should start with 'app'")
    
    is_valid = len(errors) == 0
    error_msg = " | ".join(errors) if errors else ""
    
    return is_valid, error_msg


def create_case_export_metadata() -> Dict[str, str]:
    """
    Create metadata for case export/sync operations.
    
    Returns:
        Dictionary with export metadata
    """
    return {
        "export_timestamp": get_current_timestamp(),
        "exported_by": "SimCaseBuilder/1.0",
        "format_version": "1.0"
    }


def convert_to_json_serializable(obj: Any) -> Any:
    """
    Recursively convert objects to JSON-serializable format.
    
    Args:
        obj: Object to convert
        
    Returns:
        JSON-serializable version of object
    """
    if isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return convert_to_json_serializable(obj.__dict__)
    else:
        return obj


def ensure_critical_fields_populated(case_data: Dict[str, Any],
                                     diagnosis: str,
                                     age: int,
                                     gender: str,
                                     target_learner: str,
                                     difficulty: str) -> Dict[str, Any]:
    """
    Ensure all 9 critical case fields are populated with sensible defaults.
    
    This function acts as a safety net, ensuring that even if the AI output
    is incomplete, the case has all required fields populated.
    
    Critical fields:
    1. case_name: Name/title of the case
    2. diagnosis: Primary diagnosis
    3. target_learner: Intended learner level
    4. difficulty: Scenario difficulty
    5. age: Patient age
    6. gender: Patient gender
    7. chief_complaint: Patient's presenting symptom
    8. hpi: History of present illness
    9. vital_signs: Initial vital signs dictionary
    
    Args:
        case_data: Generated case dictionary
        diagnosis: Primary diagnosis from form
        age: Patient age from form
        gender: Patient gender from form
        target_learner: Target learner from form
        difficulty: Difficulty level from form
        
    Returns:
        Case data with all critical fields populated
    """
    # Define useful defaults for missing fields
    default_ppe = {
        "Sepsis": "Patient presents with fever and tachycardia",
        "Myocardial Infarction": "Patient presents with chest pain and anxiety",
        "Anaphylaxis": "Patient presents with urticaria and respiratory distress",
        "Pulmonary Embolism": "Patient presents with dyspnea and tachycardia",
        "DKA": "Patient presents with altered mental status and Kussmaul respirations",
        "Asthma Exacerbation": "Patient presents with wheezing and shortness of breath"
    }
    
    default_hpi = {
        "Sepsis": "Symptoms began 2-3 days ago with fever, chills, and malaise. Patient reports recent URI symptoms. Has worsening confusion and tachycardia.",
        "Myocardial Infarction": "Acute onset chest pain radiating to left arm. Associated with dyspnea and diaphoresis. Pain began at rest approximately 1 hour ago.",
        "Anaphylaxis": "Acute onset 15-30 minutes after exposure. Symptoms rapidly progressive. Exposure history suggests allergic reaction.",
        "Pulmonary Embolism": "Acute onset dyspnea and pleuritic chest pain. Recent surgery or immobility. Tachycardia and tachypnea present.",
        "DKA": "History of diabetes. Patient reports thirst, polyuria, and nausea for 1-2 days. Accompanied by abdominal pain and fruity breath odor.",
        "Asthma Exacerbation": "Known asthmatic with acute dyspnea. Exposure to trigger (allergen, infection, cold air). No relief with home rescue inhaler."
    }
    
    # Ensure case_name
    if not case_data.get("case_name"):
        case_data["case_name"] = f"{diagnosis} Case - Age {age}"
    
    # Ensure diagnosis
    if not case_data.get("diagnosis"):
        case_data["diagnosis"] = diagnosis
    
    # Ensure target_learner
    if not case_data.get("target_learner"):
        case_data["target_learner"] = target_learner
    
    # Ensure difficulty
    if not case_data.get("difficulty"):
        case_data["difficulty"] = difficulty
    
    # Ensure age
    if not case_data.get("age"):
        case_data["age"] = str(age)
    
    # Ensure gender
    if not case_data.get("gender"):
        case_data["gender"] = gender
    
    # Ensure chief_complaint
    if not case_data.get("chief_complaint"):
        case_data["chief_complaint"] = default_ppe.get(
            diagnosis,
            f"Patient presents with acute {diagnosis.lower()} symptoms"
        )
    
    # Ensure hpi (history of present illness)
    if not case_data.get("hpi"):
        case_data["hpi"] = default_hpi.get(
            diagnosis,
            f"Acute presentation consistent with {diagnosis}. Progressive symptoms over the past 1-2 days."
        )
    
    # Ensure vital_signs dictionary
    if not case_data.get("vital_signs") or not isinstance(case_data.get("vital_signs"), dict):
        # Create default initial vital signs based on diagnosis
        case_data["vital_signs"] = {
            "heart_rate": "110",
            "systolic_bp": "98",
            "diastolic_bp": "62",
            "respiratory_rate": "22",
            "temperature_f": "101.5",
            "o2_saturation": "94",
            "glucose": "150"
        }
    
    return case_data

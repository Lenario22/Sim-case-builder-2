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
        ],
        "STROKE": [
            "What clinical features helped you differentiate ischemic from hemorrhagic stroke, and how did this affect your management?",
            "Describe the time-critical steps in the stroke chain of survival. What are the thrombolytic eligibility criteria and contraindications?",
            "How did you use the NIH Stroke Scale to guide your clinical decisions and communicate severity?",
            "Discuss blood pressure management in acute stroke. When is permissive hypertension appropriate versus urgent lowering?",
            "What are the key components of a stroke team activation, and how did interprofessional communication impact this case?",
        ],
        "PNEUMONIA": [
            "How did you risk-stratify this patient using severity scoring (CURB-65, PSI)? How did the score influence disposition?",
            "Describe your empiric antibiotic selection. What patient factors influenced your choice of agent and route?",
            "What clinical and radiographic findings helped you differentiate community-acquired from hospital-acquired pneumonia?",
            "Discuss the role of blood cultures, sputum cultures, and procalcitonin in guiding pneumonia management.",
        ],
        "GI BLEED": [
            "How did you differentiate upper from lower GI bleeding in this patient, and what clinical features guided your assessment?",
            "Describe your resuscitation strategy. At what hemoglobin level and clinical parameters would you transfuse?",
            "Discuss the role and timing of endoscopy in acute GI bleeding. What are the indications for emergent versus urgent intervention?",
            "How would you manage anticoagulation in a patient with active GI bleeding who has another indication for anticoagulation?",
        ],
        "CHF": [
            "How did you differentiate acute decompensated heart failure from other causes of dyspnea in this patient?",
            "Describe your approach to acute management: diuretics, vasodilators, and oxygen. When would you consider BiPAP versus intubation?",
            "Discuss the role of BNP/NT-proBNP, echocardiography, and chest X-ray in confirming your diagnosis and guiding treatment.",
            "What precipitating factors for CHF exacerbation did you identify, and how does addressing them affect long-term outcomes?",
        ],
        "OVERDOSE": [
            "How did you identify the toxidrome in this patient? What physical exam findings were most informative?",
            "Describe your approach to airway management and supportive care in the obtunded overdose patient.",
            "Discuss the role of specific antidotes (naloxone, flumazenil, N-acetylcysteine) and their risks. When is activated charcoal appropriate?",
            "How would you approach the patient who refuses treatment after reversal? Discuss capacity assessment and safety planning.",
        ],
        "SEIZURE": [
            "How did you differentiate epileptic seizure from syncope, psychogenic non-epileptic events, or other mimics?",
            "Describe your stepwise approach to status epilepticus management: first-line, second-line, and refractory therapies.",
            "What workup is indicated for a first-time seizure versus a known epileptic with breakthrough seizure?",
            "Discuss post-ictal management and the criteria for safe discharge versus admission.",
        ],
        "PNEUMOTHORAX": [
            "How did you clinically differentiate simple from tension pneumothorax, and how did this change your urgency of intervention?",
            "Describe the indications and technique for needle decompression versus chest tube placement.",
            "What are the key imaging findings on chest X-ray and ultrasound that confirmed your diagnosis?",
            "Discuss post-procedure management and criteria for chest tube removal.",
        ],
        "MENINGITIS": [
            "What clinical features in this presentation raised your suspicion for meningitis, and how did you differentiate bacterial from viral?",
            "Describe the timing and sequence of LP, blood cultures, and empiric antibiotics. Why should antibiotics not be delayed for imaging?",
            "Discuss the role of dexamethasone in bacterial meningitis and its timing relative to antibiotic administration.",
            "How would you manage close contacts and what public health considerations apply?",
        ],
        "HYPERKALEMIA": [
            "How did you recognize hyperkalemia from the clinical presentation and ECG findings? Describe the progressive ECG changes.",
            "Describe your stepwise management: membrane stabilization, intracellular shifting, and potassium elimination.",
            "What is the role of calcium gluconate versus calcium chloride, and when is emergent dialysis indicated?",
            "Discuss the common causes of hyperkalemia in this patient and how addressing the underlying cause prevents recurrence.",
        ],
        "CARDIAC ARREST": [
            "Describe your approach to high-quality CPR. What metrics did you use to assess CPR quality during the resuscitation?",
            "How did you identify and address reversible causes (H's and T's) during the arrest?",
            "Discuss your team's adherence to ACLS algorithms. Were there any deviations, and were they justified?",
            "What are the key components of post-cardiac arrest care, and how do you prognosticate neurological outcomes?",
        ],
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
        "STROKE": [
            "Powers WJ, et al. AHA/ASA Guidelines for the Early Management of Acute Ischemic Stroke (2019)",
            "National Institute of Neurological Disorders and Stroke (NINDS) rt-PA Stroke Study Group — NEJM 1995",
            "Jauch EC, et al. AHA/ASA Guidelines for Emergency Evaluation and Treatment of Ischemic Stroke",
        ],
        "PNEUMONIA": [
            "Metlay JP, et al. ATS/IDSA Guideline on Diagnosis and Treatment of Adults with Community-Acquired Pneumonia (2019)",
            "Mandell LA, et al. IDSA/ATS Consensus Guidelines on Management of Community-Acquired Pneumonia — Clin Infect Dis",
            "Lim WS, et al. Defining Community-Acquired Pneumonia Severity on Presentation: CURB-65 — Thorax 2003",
        ],
        "GI BLEED": [
            "Laine L, et al. ACG Clinical Guideline: Upper Gastrointestinal and Ulcer Bleeding — Am J Gastroenterol 2021",
            "Villanueva C, et al. Transfusion Strategies for Acute Upper Gastrointestinal Bleeding — NEJM 2013",
            "Strate LL, Gralnek IM. ACG Clinical Guideline: Management of Patients with Acute Lower GI Bleeding",
        ],
        "CHF": [
            "Heidenreich PA, et al. AHA/ACC/HFSA Guideline for the Management of Heart Failure (2022)",
            "Ponikowski P, et al. ESC Guidelines for the Diagnosis and Treatment of Acute and Chronic Heart Failure",
            "Mebazaa A, et al. Recommendations on Pre-hospital and Early Hospital Management of Acute Heart Failure — Eur Heart J",
        ],
        "OVERDOSE": [
            "Heard K, et al. Toxicologic Emergencies — Goldfrank's Toxicologic Emergencies (11th Edition)",
            "Boyer EW, Shannon M. The Serotonin Syndrome — NEJM 2005",
            "Stolbach AI, Hoffman RS. Acute Opioid Intoxication — UpToDate Clinical Review",
        ],
        "SEIZURE": [
            "Glauser T, et al. Evidence-Based Guideline: Treatment of Convulsive Status Epilepticus — Neurology 2016",
            "Kapur J, et al. Randomized Trial of Three Anticonvulsant Medications for Status Epilepticus (ESETT) — NEJM 2019",
            "Huff JS, et al. ACEP Clinical Policy: Critical Issues in Evaluation and Management of Adult Seizures — Ann Emerg Med",
        ],
        "PNEUMOTHORAX": [
            "Roberts DJ, et al. Clinical Presentation, Diagnosis, and Management of Pneumothorax — CMAJ",
            "Baumann MH, et al. ACCP Delphi Consensus Statement: Management of Spontaneous Pneumothorax",
            "Lichtenstein DA. BLUE-Protocol and FALLS-Protocol: Lung Ultrasound in the Critically Ill — Chest",
        ],
        "MENINGITIS": [
            "Tunkel AR, et al. IDSA Practice Guidelines for Bacterial Meningitis — Clin Infect Dis 2004",
            "van de Beek D, et al. Clinical Features and Prognostic Factors in Adults with Bacterial Meningitis — NEJM 2004",
            "Brouwer MC, et al. Corticosteroids for Acute Bacterial Meningitis — Cochrane Database Syst Rev",
        ],
        "HYPERKALEMIA": [
            "Clase CM, et al. Potassium Homeostasis and Management of Dyskalemia in Kidney Diseases: KDIGO Controversies",
            "Long B, et al. Hyperkalemia in the Emergency Department — J Emerg Med 2018",
            "Weisberg LS. Management of Severe Hyperkalemia — Crit Care Med 2008",
        ],
        "CARDIAC ARREST": [
            "Panchal AR, et al. AHA Guidelines for CPR and Emergency Cardiovascular Care (2020)",
            "Soar J, et al. International Liaison Committee on Resuscitation (ILCOR) Consensus on Advanced Life Support",
            "Callaway CW, et al. AHA Scientific Statement: Post-Cardiac Arrest Care (2015)",
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


def _parse_bullet_string_to_list(text: str) -> List[str]:
    """
    Convert a bullet-formatted string back into a list of items.
    Handles strings produced by format_for_humans() or common bullet formats.

    Args:
        text: A string that may contain bullet points, numbered items, or delimited items

    Returns:
        List of individual items extracted from the string
    """
    if not text or not isinstance(text, str):
        return []

    items = []
    seen = set()

    # Split on common bullet/number patterns
    parts = re.split(r'[\n\r]+|(?:^|\s)[•\-\*]\s|(?:^|\s)\d+\.\s', text)
    for part in parts:
        line = part.strip(" -•*\t()[];,.")
        if line and len(line) > 10 and line not in seen:
            items.append(line)
            seen.add(line)

    return items


def _is_well_formed_section7_string(value: Any, min_length: int = 50) -> bool:
    """
    Check if a Section 7 field value is already a well-formed, complete string.
    A well-formed string is long enough and contains meaningful content.

    Args:
        value: The field value to check
        min_length: Minimum character length to consider well-formed

    Returns:
        True if the value is a complete, usable string
    """
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return len(stripped) >= min_length


def auto_populate_section_7(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Robustly populate Section 7 (Critical Actions, Debrief Questions, References).

    Handles both list and string inputs — clean_data_structure() may have already
    converted lists to bullet-formatted strings via format_for_humans(). This function
    detects that and avoids re-truncating well-formed strings.

    Intelligently extracts from state actions, generates diagnosis-specific debrief questions,
    and creates clinical references. Provides smart fallbacks if AI output is incomplete.

    Args:
        case_data: Complete case dictionary

    Returns:
        case_data with Section 7 fully populated
    """
    # ====== CRITICAL ACTIONS ======
    raw_actions = case_data.get("critical_actions", [])

    # Normalize: if it's already a well-formed string, check if it's complete
    if _is_well_formed_section7_string(raw_actions):
        # Already a complete string (e.g., from clean_data_structure) — keep it
        case_data["critical_actions"] = raw_actions
    else:
        # Convert string back to list if needed, or use list directly
        if isinstance(raw_actions, str):
            critical_actions = _parse_bullet_string_to_list(raw_actions)
        elif isinstance(raw_actions, list):
            critical_actions = [str(a) for a in raw_actions if a and len(str(a)) > 5]
        else:
            critical_actions = []

        # If weak (fewer than 2 meaningful items), extract from state actions
        if len(critical_actions) < 2:
            action_fields = ["s3_actions", "s4_actions", "s1_actions", "s2_actions", "s5_actions"]
            gathered = []
            seen = set()

            for field_name in action_fields:
                raw = case_data.get(field_name, "")
                if not raw or len(str(raw)) < 10:
                    continue
                extracted = _parse_bullet_string_to_list(str(raw))
                for line in extracted:
                    if line not in seen:
                        gathered.append(line)
                        seen.add(line)
                        if len(gathered) >= 6:
                            break
                if len(gathered) >= 6:
                    break

            if gathered:
                critical_actions = gathered[:6]
            else:
                # Smart fallback: generate from diagnosis
                diagnosis = case_data.get("diagnosis", "Unknown condition")
                critical_actions = [
                    "Perform systematic ABCDE assessment and stabilize airway/breathing/circulation",
                    f"Obtain appropriate diagnostic testing (labs, imaging) based on differential for {diagnosis}",
                    f"Initiate empiric treatment aligned with {diagnosis} management guidelines",
                    "Monitor response to interventions and reassess frequently",
                    "Prepare for escalation or definitive management based on clinical trajectory",
                    "Communicate findings and plan clearly to the team and patient"
                ]

        # Cap at 6 items and format as bullet string for Word template
        critical_actions = critical_actions[:6]
        case_data["critical_actions"] = ("• " + "\n• ".join(critical_actions)) if critical_actions else "Not specified"

    # ====== DEBRIEF QUESTIONS ======
    raw_debrief = case_data.get("debrief_questions", [])

    if _is_well_formed_section7_string(raw_debrief):
        case_data["debrief_questions"] = raw_debrief
    else:
        if isinstance(raw_debrief, str):
            debrief_questions = _parse_bullet_string_to_list(raw_debrief)
        elif isinstance(raw_debrief, list):
            debrief_questions = [str(q) for q in raw_debrief if q and len(str(q)) > 20]
        else:
            debrief_questions = []

        if len(debrief_questions) < 2:
            diagnosis = case_data.get("diagnosis", "Unknown")
            difficulty = case_data.get("difficulty", "Intermediate")
            target_learner = case_data.get("target_learner", "Medical Students")
            debrief_questions = generate_diagnosis_debrief_questions(diagnosis, difficulty, target_learner)

        debrief_questions = debrief_questions[:5]
        formatted_q = [f"{i}. {q}" for i, q in enumerate(debrief_questions, 1) if q]
        case_data["debrief_questions"] = "\n".join(formatted_q) if formatted_q else "Not specified"

    # ====== REFERENCES ======
    raw_refs = case_data.get("references", [])

    if _is_well_formed_section7_string(raw_refs):
        case_data["references"] = raw_refs
    else:
        if isinstance(raw_refs, str):
            references = _parse_bullet_string_to_list(raw_refs)
        elif isinstance(raw_refs, list):
            references = [str(r) for r in raw_refs if r and len(str(r)) > 20]
        else:
            references = []

        if len(references) < 2:
            diagnosis = case_data.get("diagnosis", "Unknown")
            organ_system = case_data.get("organ_system", "General")
            procedures = case_data.get("procedures", "")
            references = generate_clinical_references(diagnosis, organ_system, procedures)

        references = references[:5]
        formatted_r = [f"{i}. {r}" for i, r in enumerate(references, 1) if r]
        case_data["references"] = "\n".join(formatted_r) if formatted_r else "Not specified"

    return case_data


def auto_populate_critical_actions(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """DEPRECATED: Use auto_populate_section_7() instead."""
    return auto_populate_section_7(case_data)


def clean_data_structure(data: Any) -> Any:
    """
    Recursively clean a data structure, preserving lists and dicts.
    Only applies text formatting to string leaf values.

    Args:
        data: Dictionary or other data structure to clean

    Returns:
        Cleaned version of the input (lists stay as lists)
    """
    if isinstance(data, dict):
        return {
            k: clean_data_structure(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [clean_data_structure(item) for item in data]
    elif isinstance(data, str):
        return sanitize_template_noise(data)
    else:
        return data


def robust_parse_json(text: str) -> Dict[str, Any]:
    """
    Parse JSON from AI model output with multi-strategy recovery.

    This is the canonical JSON parser for the entire application. Handles common
    LLM output issues like markdown fences, BOM characters, trailing commas,
    and JavaScript-style comments.

    Strategies tried in order:
      1. Direct parse (fast path for clean responses)
      2. BOM removal + markdown fence stripping
      3. Regex extraction of the outermost { ... } object
      4. Trailing-comma removal (e.g. {"k":"v",} is invalid JSON)
      5. JavaScript comment stripping (// and /* */)

    Args:
        text: Raw text from an AI model response

    Returns:
        Parsed dictionary

    Raises:
        ValueError: If all recovery strategies fail
    """
    # --- Strategy 1: fast path ---
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # All remaining strategies work on a progressively cleaned string.
    cleaned = text.strip().lstrip('\ufeff')  # strip BOM

    # --- Strategy 2: strip markdown code fences ---
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', cleaned, re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    elif cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # --- Strategy 3: extract the outermost JSON object via brace matching ---
    start = cleaned.find('{')
    if start != -1:
        depth = 0
        in_string = False
        escape_next = False
        end = start
        for i, ch in enumerate(cleaned[start:], start):
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
            if not in_string:
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
        candidate = cleaned[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            cleaned = candidate  # use this tighter candidate for further repair

    # --- Strategy 4: remove trailing commas before } or ] ---
    repaired = re.sub(r',\s*([}\]])', r'\1', cleaned)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # --- Strategy 5: strip JavaScript-style comments ---
    no_comments = re.sub(r'//[^\n]*', '', repaired)
    no_comments = re.sub(r'/\*[\s\S]*?\*/', '', no_comments)
    try:
        return json.loads(no_comments)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"JSON parsing failed after all recovery strategies: {e.msg} "
            f"at line {e.lineno}, col {e.colno}"
        )


def validate_json_string(json_string: str) -> tuple[bool, Union[Dict, str]]:
    """
    Parse a JSON string with multi-strategy recovery for common LLM output issues.

    Wrapper around robust_parse_json() that returns a (success, result) tuple
    for backward compatibility.

    Returns:
        Tuple of (is_valid, parsed_dict_or_error_message)
    """
    try:
        result = robust_parse_json(json_string)
        return True, result
    except ValueError as e:
        return False, str(e)


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
        "Asthma Exacerbation": "Patient presents with wheezing and shortness of breath",
        "Stroke": "Patient presents with sudden-onset unilateral weakness and speech difficulty",
        "Pneumonia": "Patient presents with productive cough, fever, and dyspnea",
        "GI Bleed": "Patient presents with hematemesis or melena and signs of hypovolemia",
        "CHF Exacerbation": "Patient presents with worsening dyspnea, orthopnea, and peripheral edema",
        "Overdose": "Patient presents with altered mental status and respiratory depression",
        "Seizure": "Patient presents post-ictal with confusion following witnessed tonic-clonic activity",
        "Hypoglycemia": "Patient presents with diaphoresis, tremor, and altered mental status",
        "Pneumothorax": "Patient presents with acute chest pain, dyspnea, and absent breath sounds",
        "Meningitis": "Patient presents with fever, headache, neck stiffness, and photophobia",
        "Hyperkalemia": "Patient presents with generalized weakness and bradycardia",
        "Ectopic Pregnancy": "Patient presents with lower abdominal pain, vaginal bleeding, and hemodynamic instability",
        "Thyroid Storm": "Patient presents with hyperthermia, severe tachycardia, agitation, and delirium",
        "Cardiac Arrest": "Patient found unresponsive, pulseless, and apneic",
    }

    default_hpi = {
        "Sepsis": "Symptoms began 2-3 days ago with fever, chills, and malaise. Patient reports recent URI symptoms. Has worsening confusion and tachycardia.",
        "Myocardial Infarction": "Acute onset chest pain radiating to left arm. Associated with dyspnea and diaphoresis. Pain began at rest approximately 1 hour ago.",
        "Anaphylaxis": "Acute onset 15-30 minutes after exposure. Symptoms rapidly progressive. Exposure history suggests allergic reaction.",
        "Pulmonary Embolism": "Acute onset dyspnea and pleuritic chest pain. Recent surgery or immobility. Tachycardia and tachypnea present.",
        "DKA": "History of diabetes. Patient reports thirst, polyuria, and nausea for 1-2 days. Accompanied by abdominal pain and fruity breath odor.",
        "Asthma Exacerbation": "Known asthmatic with acute dyspnea. Exposure to trigger (allergen, infection, cold air). No relief with home rescue inhaler.",
        "Stroke": "Sudden onset of left-sided weakness and slurred speech approximately 45 minutes ago. Wife witnessed onset while patient was eating breakfast. No preceding headache or trauma. Last known well at 7:30 AM.",
        "Pneumonia": "Productive cough with rust-colored sputum for 3 days, worsening fever to 103F. Progressive dyspnea on exertion, now dyspneic at rest. Rigors and pleuritic chest pain on right side.",
        "GI Bleed": "Two episodes of coffee-ground emesis over past 6 hours. Reports dark, tarry stools for 2 days. Lightheaded with standing. History of NSAID use for chronic back pain.",
        "CHF Exacerbation": "Progressive dyspnea over 5 days, now unable to lie flat. Three-pillow orthopnea, paroxysmal nocturnal dyspnea. Bilateral leg swelling worsening. Reports dietary indiscretion and missed diuretic doses.",
        "Overdose": "Found unresponsive by roommate. Empty pill bottles nearby. Last seen normal 4 hours ago. Unknown substances ingested. History of depression.",
        "Seizure": "Witnessed tonic-clonic activity lasting approximately 3 minutes. Now post-ictal with confusion. No prior seizure history. Recent sleep deprivation and increased alcohol use.",
        "Hypoglycemia": "Insulin-dependent diabetic who missed lunch. Progressive tremor, diaphoresis, and confusion over past 30 minutes. Took morning insulin as usual.",
        "Pneumothorax": "Sudden onset right-sided chest pain and severe dyspnea 20 minutes ago. Tall, thin male with no preceding trauma. Progressively more dyspneic and anxious.",
        "Meningitis": "Severe headache, fever, and neck stiffness developing over 12 hours. Photophobia and one episode of vomiting. Recently exposed to college dormitory contacts with URI symptoms.",
        "Hyperkalemia": "Progressive generalized weakness over 24 hours. History of CKD stage IV, missed dialysis session. Reports tingling in extremities and palpitations.",
        "Ectopic Pregnancy": "Sharp lower abdominal pain for 6 hours, initially intermittent, now constant. Vaginal spotting. Last menstrual period 7 weeks ago. Lightheaded with standing.",
        "Thyroid Storm": "Known Graves disease, stopped methimazole 2 weeks ago. Progressive agitation, palpitations, profuse sweating, and fever over 48 hours. Diarrhea and tremor.",
        "Cardiac Arrest": "Witnessed collapse at home. Bystander CPR initiated within 2 minutes. EMS arrived in 8 minutes, found in ventricular fibrillation. One shock delivered en route.",
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


# ============================================================================
# FIELD-LENGTH VALIDATION
# ============================================================================

# Maximum field lengths (characters) for safe export to Word/Airtable
_FIELD_LENGTH_LIMITS = {
    # Section 7 fields — these are the most commonly truncated
    "critical_actions": 2000,
    "debrief_questions": 2000,
    "references": 2000,
    # Narrative fields
    "hpi": 3000,
    "case_summary": 1500,
    "vignette": 1000,
    "ed_objectives": 2000,
    # State fields
    "s1_prog": 1500, "s2_prog": 1500, "s3_prog": 1500, "s4_prog": 1500, "s5_prog": 1500,
    "s1_actions": 1500, "s2_actions": 1500, "s3_actions": 1500, "s4_actions": 1500, "s5_actions": 1500,
    "s1_notes": 1500, "s2_notes": 1500, "s3_notes": 1500, "s4_notes": 1500, "s5_notes": 1500,
}

# Minimum field lengths — fields shorter than this are likely truncated
_FIELD_MIN_LENGTHS = {
    "critical_actions": 50,
    "debrief_questions": 50,
    "references": 50,
    "hpi": 30,
    "case_summary": 20,
    "ed_objectives": 20,
}


class FieldLengthIssue:
    """Represents a field that is too long or suspiciously short."""
    def __init__(self, field_name: str, actual_length: int, limit: int,
                 issue_type: str, message: str):
        self.field_name = field_name
        self.actual_length = actual_length
        self.limit = limit
        self.issue_type = issue_type  # "too_long" or "truncated"
        self.message = message


def validate_field_lengths(case_data: Dict[str, Any]) -> List['FieldLengthIssue']:
    """
    Validate field lengths before export to catch truncation or overflow.

    Checks for:
    - Fields that exceed safe export limits (too long for Word/Airtable)
    - Fields that are suspiciously short (likely truncated by upstream processing)

    Args:
        case_data: Complete case dictionary

    Returns:
        List of FieldLengthIssue objects (empty = all good)
    """
    issues = []

    # Check for fields that are too long
    for field_name, max_len in _FIELD_LENGTH_LIMITS.items():
        value = case_data.get(field_name, "")
        if isinstance(value, str) and len(value) > max_len:
            issues.append(FieldLengthIssue(
                field_name=field_name,
                actual_length=len(value),
                limit=max_len,
                issue_type="too_long",
                message=f"{field_name} is {len(value)} chars (limit {max_len}). "
                        f"May be truncated during Word/Airtable export."
            ))

    # Check for fields that are suspiciously short (likely truncated)
    for field_name, min_len in _FIELD_MIN_LENGTHS.items():
        value = case_data.get(field_name, "")
        if isinstance(value, str) and 0 < len(value) < min_len:
            issues.append(FieldLengthIssue(
                field_name=field_name,
                actual_length=len(value),
                limit=min_len,
                issue_type="truncated",
                message=f"{field_name} is only {len(value)} chars (expected >{min_len}). "
                        f"This field may have been truncated during processing."
            ))

    return issues


def truncate_long_fields(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely truncate fields that exceed export limits, preserving content quality.
    Adds an ellipsis indicator so users know content was trimmed.

    Args:
        case_data: Complete case dictionary

    Returns:
        case_data with any oversized fields safely truncated
    """
    for field_name, max_len in _FIELD_LENGTH_LIMITS.items():
        value = case_data.get(field_name, "")
        if isinstance(value, str) and len(value) > max_len:
            # Truncate at the last complete sentence or bullet within the limit
            truncated = value[:max_len - 20]
            # Try to cut at last newline for clean formatting
            last_newline = truncated.rfind('\n')
            if last_newline > max_len // 2:
                truncated = truncated[:last_newline]
            case_data[field_name] = truncated + "\n[... truncated for export]"

    return case_data

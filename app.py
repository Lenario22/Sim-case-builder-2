"""
Clinical Simulation Case Builder
A professional Streamlit application for generating medical simulation cases.

This application demonstrates enterprise-level architecture:
- Modular design with separated concerns
- Robust state management
- Comprehensive validation
- Professional UI/UX
- Security best practices
"""

import streamlit as st
import google.generativeai as genai
import json
import io
import os
from typing import Optional, Dict, Any
from datetime import date
import random
from docxtpl import DocxTemplate
from pathlib import Path
from dotenv import load_dotenv

# Load .env file immediately
load_dotenv()

# Import custom modules
from state_manager import SimulationStateManager
from logic_controller import MedicalLogicController, Difficulty, CCS5Level
from airtable_client import AirtableClient
from validators import CaseValidator, ValidationResult
from utils import (
    format_for_humans,
    clean_data_structure,
    validate_json_string,
    format_vital_signs,
    generate_case_summary,
    safe_api_key_display,
    validate_airtable_credentials,
    create_case_export_metadata,
    ensure_critical_fields_populated,
    apply_dka_ua_logic,
    auto_populate_section_7,
    validate_field_lengths,
    truncate_long_fields,
)


# ============================================================================
# CONFIGURATION & INITIALIZATION
# ============================================================================

st.set_page_config(
    page_title="Sim Case Builder",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration from environment variables (supports both local .env and Streamlit Secrets)
# See .env.example for required setup
# On Streamlit Cloud: Use Settings → Secrets tab to add keys
# Locally: Use .env file
def get_secret(key: str, default: str = None) -> Optional[str]:
    """Get secret from Streamlit secrets (Cloud) or environment variables (local)"""
    try:
        return st.secrets[key]
    except Exception:
        # Catch any exception (KeyError, TypeError, StreamlitSecretNotFoundError, etc.)
        # and fallback to environment variables
        return os.getenv(key, default)

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
AIRTABLE_API_KEY = get_secret("AIRTABLE_PAT")  # Note: Streamlit uses AIRTABLE_PAT
AIRTABLE_BASE_ID = get_secret("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = get_secret("AIRTABLE_TABLE_NAME", "Cases")

# Validate API keys at startup
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    st.error(
        "❌ **Gemini API Key Missing or Invalid**\n\n"
        "To fix this:\n"
        "1. Get your API key from: https://aistudio.google.com/app/apikey\n"
        "2. Edit `.env` file in your project root\n"
        "3. Replace `GEMINI_API_KEY=your_gemini_api_key_here` with your actual key\n"
        "4. Restart Streamlit"
    )
    st.stop()

# Template file path
TEMPLATE_PATH = Path(__file__).parent / "Simulation Case Template_2025.docx"


# ============================================================================
# STATE INITIALIZATION
# ============================================================================

@st.cache_resource
def get_state_manager() -> SimulationStateManager:
    """Initialize state manager as a cached resource."""
    return SimulationStateManager()


state_mgr = get_state_manager()


# ============================================================================
# UI STYLING & LAYOUT COMPONENTS
# ============================================================================

def render_header(case_name: str = ""):
    """Render professional header with icon and tagline.
    If a case_name is provided it becomes the H1 title.
    """
    title = case_name if case_name else "Clinical Simulation Case Builder"
    st.markdown(f"""
    <div style='text-align: center; padding: 20px;'>
        <h1>🏥 {title}</h1>
        <p style='font-size: 16px; color: #555;'>
            Generate enterprise-grade medical simulation scenarios powered by AI
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_info():
    """Render informational sidebar."""
    with st.sidebar:
        st.markdown("### 📋 How to Use")
        st.info(
            "1. **Configure** your case parameters\n"
            "2. **Generate** AI-powered scenario progression\n"
            "3. **Validate** clinical completeness\n"
            "4. **Export** to Word template\n"
            "5. **Sync** to Airtable base"
        )
        
        # Debug section
        with st.expander("🔧 Debug Information"):
            current_state = state_mgr.get_current_state()
            case_data = state_mgr.get_case_data()
            st.write(f"**UI Stage:** {current_state}")
            st.write(f"**Case Loaded:** {'Yes' if case_data else 'No'}")
            st.write(f"**Fields in Memory:** {len(case_data)}")


def render_validation_results(validation_summary: Dict[str, Any]):
    """Render validation results in professional format."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "✓ Passed",
            "All checks" if validation_summary["is_valid"] else f"{validation_summary['total_checks'] - validation_summary['errors']}",
            delta=f"{validation_summary['info']} info"
        )
    
    with col2:
        st.metric(
            "⚠ Warnings",
            validation_summary["warnings"]
        )
    
    with col3:
        st.metric(
            "❌ Errors",
            validation_summary["errors"]
        )
    
    # Display detailed results
    if validation_summary["error_details"]:
        st.error("### Critical Issues")
        for error in validation_summary["error_details"]:
            with st.expander(f"❌ {error['field']}: {error['message']}"):
                for suggestion in error["suggestions"]:
                    st.write(f"💡 {suggestion}")
    
    if validation_summary["warning_details"]:
        st.warning("### Warnings")
        for warning in validation_summary["warning_details"]:
            st.write(f"**{warning['field']}:** {warning['message']}")


# ============================================================================
# FORM & INPUT HANDLING
# ============================================================================

def render_configuration_form() -> Optional[Dict[str, Any]]:
    """
    Render professional configuration form with enhanced UX.
    
    Returns:
        Dictionary with form values if submitted, None otherwise
    """
    with st.container(border=True):
        st.markdown("### ⚙️ Case Configuration Panel")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Patient Demographics")
            diagnosis = st.text_input(
                "Primary Diagnosis",
                placeholder="e.g., Sepsis, Myocardial Infarction",
                help="Leave blank for random diagnosis"
            )
            
            patient_age = st.number_input(
                "Patient Age",
                min_value=0,
                max_value=120,
                value=None,
                help="Leave blank for random age"
            )
            
            patient_gender = st.selectbox(
                "Patient Gender",
                ["Male", "Female", "Non-binary", "Unspecified"]
            )
        
        with col2:
            st.subheader("Learning Parameters")
            target_learner = st.selectbox(
                "Target Learner",
                ["Medical Students", "Residents", "Registered Nurses (RNs)", "Interprofessional Team"]
            )

            CCS5_OPTIONS = {
                "Level 1 — Novice (Routine)": 1,
                "Level 2 — Advanced Beginner (Complicated)": 2,
                "Level 3 — Competent (Complex)": 3,
                "Level 4 — Proficient (Highly Complex)": 4,
                "Level 5 — Expert (Extreme Complexity)": 5,
            }
            CCS5_DESCRIPTIONS = {
                1: "Routine, linear case. Single acute symptom, high goal clarity.",
                2: "Common illness + 1–2 secondary diagnoses. Basic pattern recognition required.",
                3: "Multimorbidity with conflicting treatment goals. System 2 thinking required.",
                4: "Atypical presentation, high data load, significant socioeconomic barriers.",
                5: "MUS / rare pathology / entangled psychosocial issues. High diagnostic uncertainty.",
            }
            ccs5_label = st.selectbox(
                "Difficulty — CCS-5 Scale (Dreyfus Model)",
                options=list(CCS5_OPTIONS.keys()),
                index=1,
                help="Based on the Dreyfus Model of Skill Acquisition and Vector Model of Patient Complexity"
            )
            ccs5_value = CCS5_OPTIONS[ccs5_label]
            st.caption(CCS5_DESCRIPTIONS[ccs5_value])
            # Legacy difficulty string for template compatibility
            _legacy_map = {1: "Basic", 2: "Intermediate", 3: "Advanced", 4: "Nightmare", 5: "Nightmare"}
            difficulty = _legacy_map[ccs5_value]
        
        st.markdown("### 📝 Advanced Options")
        custom_focus = st.text_area(
            "Custom Instructions (Optional)",
            placeholder="e.g., Patient is allergic to penicillin. State 3 should involve sudden hemodynamic changes.",
            height=100
        )
        
        submitted = st.form_submit_button(
            "🚀 Generate & Sync Everything",
            use_container_width=True,
            type="primary"
        )
        
        return {
            "diagnosis": diagnosis,
            "patient_age": patient_age,
            "patient_gender": patient_gender,
            "target_learner": target_learner,
            "difficulty": difficulty,
            "ccs5_value": ccs5_value,
            "ccs5_label": ccs5_label,
            "custom_focus": custom_focus,
            "submitted": submitted
        }


# ============================================================================
# COMPLEXITY PROFILE RENDERER
# ============================================================================

_VECTOR_COLORS = {
    "biological":    ("#e53935", "#ffcdd2"),
    "socioeconomic": ("#1565c0", "#bbdefb"),
    "cultural":      ("#6a1b9a", "#e1bee7"),
    "environmental": ("#2e7d32", "#c8e6c9"),
    "behavioral":    ("#e65100", "#ffe0b2"),
}
_UNCERTAINTY_ICONS = {"Scientific": "🔬", "Practical": "⚙️", "Personal": "❤️"}
_BIAS_ICONS = {
    "Anchoring": "⚓",
    "Search Satisficing": "🔍",
    "Confirmation Bias": "🪞",
    "Availability Bias": "🧠",
    "Framing Effect": "🖼️",
}


def render_complexity_profile(profile: Dict[str, Any]):
    """Render the Phase 0 complexity profile as a rich, scannable UI panel."""
    with st.expander("🧮 Complexity Profile (Vector Model · CCFs · CoT · Bias Check)", expanded=True):

        # --- CCS-5 Banner ---
        level = profile.get("ccs5_level", "?")
        stage = profile.get("dreyfus_stage", "Unknown")
        st.markdown(
            f"<div style='background:#1a237e;color:white;padding:10px 16px;"
            f"border-radius:8px;font-size:15px;'>"
            f"<b>CCS-5 Level {level} \u2014 {stage}</b></div>",
            unsafe_allow_html=True
        )
        st.markdown("")

        tab_vectors, tab_ccfs, tab_cot, tab_biases = st.tabs(
            ["📊 Vector Model", "⚡ CCFs", "🧩 Chain of Thought", "⚠️ Bias Watch"]
        )

        # --- VECTOR MODEL TAB ---
        with tab_vectors:
            vector = profile.get("vector_model", {})
            for axis in ["biological", "socioeconomic", "cultural", "environmental", "behavioral"]:
                axis_data = vector.get(axis, {})
                mag = axis_data.get("magnitude", 0)
                factors = axis_data.get("factors", [])
                bar_color, bg_color = _VECTOR_COLORS.get(axis, ("#555", "#eee"))
                col_label, col_bar, col_score = st.columns([2, 6, 1])
                with col_label:
                    st.markdown(f"**{axis.capitalize()}**")
                with col_bar:
                    filled = "█" * mag
                    empty  = "░" * (5 - mag)
                    st.markdown(
                        f"<span style='color:{bar_color};font-size:18px;"
                        f"letter-spacing:2px;'>{filled}</span>"
                        f"<span style='color:#ccc;font-size:18px;"
                        f"letter-spacing:2px;'>{empty}</span>",
                        unsafe_allow_html=True
                    )
                with col_score:
                    st.markdown(f"**{mag}/5**")
                if factors:
                    st.caption(" · ".join(factors))
            total = profile.get("vector_model", {}).get("total_pressure",
                sum(vector.get(a, {}).get("magnitude", 0)
                    for a in ["biological","socioeconomic","cultural","environmental","behavioral"]))
            st.markdown(f"**Total Vector Pressure: {total} / 25**")

            # Han's Uncertainty
            u_type = profile.get("uncertainty_type", "")
            u_rationale = profile.get("uncertainty_rationale", "")
            icon = _UNCERTAINTY_ICONS.get(u_type, "❓")
            st.markdown(
                f"<div style='background:#f3f4f6;border-left:4px solid #555;"
                f"padding:8px 12px;border-radius:4px;margin-top:12px;'>"
                f"<b>{icon} Han's Uncertainty: {u_type}</b><br/>"
                f"<span style='font-size:13px;'>{u_rationale}</span></div>",
                unsafe_allow_html=True
            )

        # --- CCF TAB ---
        with tab_ccfs:
            task_ccfs    = profile.get("task_ccfs", [])
            patient_ccfs = profile.get("patient_ccfs", [])
            col_t, col_p = st.columns(2)
            with col_t:
                st.markdown("**Task CCFs**")
                if task_ccfs:
                    for ccf in task_ccfs:
                        st.markdown(
                            f"<span style='background:#fff3e0;color:#e65100;"
                            f"padding:2px 8px;border-radius:12px;font-size:13px;"
                            f"margin:2px;display:inline-block;'>{ccf}</span>",
                            unsafe_allow_html=True
                        )
                else:
                    st.caption("None identified")
            with col_p:
                st.markdown("**Patient CCFs**")
                if patient_ccfs:
                    for ccf in patient_ccfs:
                        st.markdown(
                            f"<span style='background:#e8eaf6;color:#1a237e;"
                            f"padding:2px 8px;border-radius:12px;font-size:13px;"
                            f"margin:2px;display:inline-block;'>{ccf}</span>",
                            unsafe_allow_html=True
                        )
                else:
                    st.caption("None identified")

        # --- CHAIN OF THOUGHT TAB ---
        with tab_cot:
            cot = profile.get("chain_of_thought", {})
            steps = [
                ("🔎 Cue Acquisition",     cot.get("cue_acquisition", "")),
                ("💡 Hypothesis Generation", cot.get("hypothesis_generation", "")),
                ("🔬 Cue Interpretation",   cot.get("cue_interpretation", "")),
                ("✅ Hypothesis Evaluation", cot.get("hypothesis_evaluation", "")),
            ]
            for step_label, step_text in steps:
                if step_text:
                    st.markdown(f"**{step_label}**")
                    st.info(step_text)
            fairness = profile.get("intrinsic_fairness_note", "")
            if fairness:
                st.markdown(
                    f"<div style='background:#fce4ec;border-left:4px solid #c62828;"
                    f"padding:8px 12px;border-radius:4px;margin-top:8px;'>"
                    f"<b>⚖️ Intrinsic Fairness Note:</b><br/>{fairness}</div>",
                    unsafe_allow_html=True
                )

        # --- BIAS WATCH TAB ---
        with tab_biases:
            biases = profile.get("cognitive_biases_at_risk", [])
            if biases:
                for b in biases:
                    name    = b.get("bias", "")
                    trigger = b.get("trigger", "")
                    icon    = _BIAS_ICONS.get(name, "⚠️")
                    st.warning(f"{icon} **{name}**\n\n{trigger}")
            else:
                st.success("No specific cognitive bias risks identified for this case.")


# ============================================================================
# CASE GENERATION ENGINE
# ============================================================================

def generate_case_with_gemini(diagnosis: str, age: int, gender: str,
                             difficulty: str, custom_focus: str,
                             ccs5_value: int = 2) -> Dict[str, Any]:
    """
    Generate case using Gemini API with proper error handling.
    Now runs a Phase 0 complexity profile before the main case generation.

    Args:
        diagnosis: Primary diagnosis
        age: Patient age
        gender: Patient gender
        difficulty: Legacy difficulty string (for template)
        custom_focus: Custom instructions
        ccs5_value: CCS-5 level (1-5, Dreyfus Model)

    Returns:
        Parsed case data dictionary (with _complexity_profile embedded)
    """
    from case_engine import PHASE0_PROMPT
    from logic_controller import CCS5Level as _CCS5

    ccs5 = _CCS5(max(1, min(5, ccs5_value)))
    custom_section = f"- Custom Instructions: {custom_focus}" if custom_focus else ""

    # Build case skeleton
    case_skeleton = {
        "case_name": "", "key_words": "", "case_summary": "", "age": "",
        "setting": "", "demographics": "", "organ_system": "", "procedures": "",
        "ed_objectives": "", "target_learner": "", "location": "", "staff": "",
        "vignette": "", "room": "", "manikin": "", "moulage": "", "equipment": "",
        "iv": "", "ae": "", "antib": "", "vps": "", "other_meds": "", "tele_rythm": "",
        "o2_sat": "", "blood_pressure": "", "respirations": "", "temperature": "",
        "arrival_condition": "", "pt_name": "", "gender": "", "weight": "",
        "chief_complaint": "", "arrival_method": "", "hpi": "", "pmh": "", "psh": "",
        "fmh": "", "social_history": "", "medications": "", "allergies": "",
        "birth_history": "", "code_status": "", "neuro_ros": "", "msk_ros": "",
        "heent_ros": "", "endo_ros": "", "cv_ros": "", "heme_ros": "", "resp_ros": "",
        "skin_ros": "", "gi_ros": "", "psych_ros": "", "gu_ros": "", "general_ros": "",
        "hr_arrive": "", "bp_arrive": "", "rr_arrive": "", "o2_arrive": "",
        "temp_arrive": "", "rhythm_arrive": "", "glucose_arrive": "", "gcs_arrive": "",
        "general_pe": "", "neuro_pe": "", "heent_pe": "", "cv_pe": "", "resp_pe": "",
        "abd_pe": "", "gu_pe": "", "msk_pe": "", "skin_pe": "", "psych_pe": "",
        "s1_name": "", "s1_vitals": "", "s1_pe": "", "s1_actions": "", "s1_notes": "",
        "s1_prog": "", "s2_name": "", "s2_vitals": "", "s2_pe": "", "s2_actions": "",
        "s2_notes": "", "s2_prog": "", "s3_name": "", "s3_vitals": "", "s3_pe": "",
        "s3_actions": "", "s3_notes": "", "s3_prog": "", "s4_name": "", "s4_vitals": "",
        "s4_pe": "", "s4_actions": "", "s4_notes": "", "s4_prog": "", "s5_name": "",
        "s5_vitals": "", "s5_pe": "", "s5_actions": "", "s5_notes": "", "s5_prog": "",
        "wbc": "", "hgb": "", "hct": "", "plt": "", "na": "", "k": "", "cl": "",
        "hco3": "", "ag": "", "bun": "", "cr": "", "glu": "", "ast": "", "alt": "",
        "alk_phos": "", "t_bili": "", "lipase": "", "ca": "", "mg": "", "phos": "",
        "alb": "", "vbg_ph": "", "vbg_pco2": "", "vbg_po2": "", "vbg_hco3": "",
        "lactate": "", "ua_color": "", "ua_clarity": "", "ua_prot": "", "ua_glu": "",
        "ua_ketones": "", "troponin": "", "tsh": "", "t4": "",
        "critical_actions": ["", ""], "debrief_questions": ["", ""],
        "references": ["", ""]
    }
    
    # Construct detailed prompt
    prompt = f"""
    Generate a comprehensive medical simulation case for:
    - Diagnosis: {diagnosis}
    - Patient Age: {age}
    - Patient Gender: {gender}
    - Difficulty Level: {difficulty} (CCS-5: {ccs5.label})
    - Custom Notes: {custom_focus if custom_focus else 'None'}

    Using the CCS-5 framework, ensure complexity matches {ccs5.description}

    Return ONLY a valid JSON object that fills this exact skeleton: {json.dumps(case_skeleton)}

    CRITICAL FORMATTING RULES:
    1. If a string value must contain a double quote, escape it with a backslash: \"
    2. Use \\n for line breaks within string values — NO literal newlines inside strings
    3. Lab values (CBC, BMP, LFTs) MUST be numeric only (no units)
    4. Create dynamic 5-state branching: worse if interventions missed, better if done
    5. Ensure critical_actions and debrief_questions are non-empty arrays, never empty strings

    Ensure clinical accuracy and scenario completeness for {ccs5.label}.
    """

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Phase 0: Complexity Profile
        phase0_prompt = PHASE0_PROMPT.format(
            diagnosis=diagnosis, age=age, gender=gender,
            ccs5_label=ccs5.label, ccs5_description=ccs5.description,
            ccs5_value=ccs5.value, target_learner="Not specified",
            custom_section=custom_section
        )
        try:
            p0_response = model.generate_content(
                phase0_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            _, complexity_profile = validate_json_string(p0_response.text)
            if not isinstance(complexity_profile, dict):
                complexity_profile = {}
        except Exception:
            complexity_profile = {"ccs5_level": ccs5.value, "dreyfus_stage": ccs5.label}

        # Main case generation
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        # Parse response
        is_valid, parsed = validate_json_string(response.text)

        if not is_valid:
            raise ValueError(f"JSON parsing failed: {parsed}")

        # Clean and embed complexity profile
        cleaned = clean_data_structure(parsed)
        cleaned["_complexity_profile"] = complexity_profile
        return cleaned

    except Exception as e:
        raise Exception(f"Gemini generation failed: {str(e)}")


# ============================================================================
# AIRTABLE SYNC
# ============================================================================

def sync_case_to_airtable(case_data: Dict[str, Any], diagnosis: str,
                         target_learner: str) -> bool:
    """
    Sync generated case to Airtable with error handling.
    
    Args:
        case_data: Generated case dictionary
        diagnosis: Primary diagnosis
        target_learner: Target learner type
        
    Returns:
        True if sync successful, False otherwise
    """
    try:
        # Validate credentials
        is_valid, error_msg = validate_airtable_credentials(
            AIRTABLE_API_KEY,
            AIRTABLE_BASE_ID
        )
        
        if not is_valid:
            st.warning(f"⚠️ Airtable Configuration Issue: {error_msg}")
            return False
        
        # Initialize client
        client = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
        
        # Prepare record with proper data types
        # Age should be a number, not a string
        try:
            age_value = int(case_data.get("age") or 0)
        except (ValueError, TypeError):
            age_value = None
        
        record = {
            "Case Name": case_data.get("case_name", "Untitled Case"),
            "Diagnosis": str(diagnosis),
            "Target Learner": str(target_learner),
            "Difficulty": str(case_data.get("difficulty", "Unknown")),
            "Age": age_value,  # Send as integer, not string
            "Gender": str(case_data.get("gender", "Unspecified")),
            "Case JSON": json.dumps(case_data)
        }
        
        # Remove None/empty values to avoid Airtable rejection
        record = {k: v for k, v in record.items() if v is not None and v != ""}
        
        # Send to Airtable — if a Single Select field rejects the value,
        # retry without that field rather than failing the whole sync.
        response = client.create_record(AIRTABLE_TABLE_NAME, record)
        
        if not response.success and "select option" in response.error_message.lower():
            # A Single Select field doesn't have the option pre-configured.
            # Strip the offending fields and retry with text-safe fields only.
            select_fields = {"Target Learner", "Difficulty", "Gender", "Diagnosis"}
            trimmed = {k: v for k, v in record.items() if k not in select_fields}
            response = client.create_record(AIRTABLE_TABLE_NAME, trimmed)
            if response.success:
                st.info(
                    "💡 Some select fields were skipped because the options "
                    "aren't configured in Airtable yet. To fix: open your "
                    "Airtable table, click the field header → Customize field, "
                    "and change Single Select fields to 'Single line text'."
                )
        
        if response.success:
            st.success(
                f"✓ Successfully synced to Airtable\n"
                f"Record ID: {response.data.get('records', [{}])[0].get('id', 'Unknown')}"
            )
            return True
        else:
            st.warning(
                f"⚠️ Airtable sync failed: {response.error_message}\n"
                f"Error Type: {response.error_type.value}"
            )
            if response.retry_after:
                st.info(f"💡 Please retry after {response.retry_after} seconds")
            return False
            
    except Exception as e:
        st.error(f"❌ Sync error: {str(e)}")
        return False


# ============================================================================
# WORD DOCUMENT EXPORT
# ============================================================================

def export_to_word(case_data: Dict[str, Any], diagnosis: str) -> Optional[io.BytesIO]:
    """
    Export case to Word document using template.
    
    Args:
        case_data: Case dictionary
        diagnosis: Diagnosis for filename
        
    Returns:
        BytesIO object for download, or None if failed
    """
    try:
        if not TEMPLATE_PATH.exists():
            st.error(f"❌ Template file not found: {TEMPLATE_PATH}")
            return None
        
        doc = DocxTemplate(str(TEMPLATE_PATH))
        doc.render(case_data)
        
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        
        return bio
        
    except Exception as e:
        st.error(f"❌ Word export failed: {str(e)}")
        return None


# ============================================================================
# CASE DISPLAY FUNCTION
# ============================================================================

def display_case_content(case_data: Dict[str, Any], final_diagnosis: str, 
                        form_data: Dict[str, Any], validation_summary: str = None) -> None:
    """
    Display generated case content, complexity profile, branching states, and export options.
    Called after generation or on reruns when case exists in session state.
    
    Args:
        case_data: The complete case dictionary
        final_diagnosis: The diagnosis for the case
        form_data: Form data dictionary (for target_learner)
        validation_summary: Optional validation summary (if not provided, will be recomputed)
    """
    # Recompute validation if not provided
    if validation_summary is None:
        validator = CaseValidator()
        is_valid, validation_results = validator.validate_complete_case(case_data)
        validation_summary = validator.get_validation_summary()
    else:
        # Assume is_valid if summary exists
        is_valid = True
        validation_results = []
    
    st.markdown("---")
    st.markdown("## 📊 Case Summary & Validation")

    # Show case summary
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(generate_case_summary(case_data))
    with col2:
        st.metric("Clinical Completeness",
                 "✓ Valid" if is_valid else "✗ Incomplete")

    # Show validation results
    st.markdown("### Validation Report")
    render_validation_results(validation_summary)

    # -------- COMPLEXITY PROFILE --------
    st.markdown("---")
    st.markdown("## 🧠 Complexity Profile")
    complexity_profile = st.session_state.get("complexity_profile", {})
    if complexity_profile:
        render_complexity_profile(complexity_profile)
    else:
        st.info("ℹ️ Complexity profile not available (case generated with legacy path). Re-generate to see Vector Model, CCFs, and CoT analysis.")

    # -------- PATIENT STATE PROGRESSION (tabbed branching view) --------
    st.markdown("---")
    st.markdown("## 🔀 Patient State Progression")
    state_tabs = st.tabs(["State 1", "State 2", "State 3", "State 4", "State 5"])
    state_keys = [("s1", "Arrival / Initial Presentation"),
                  ("s2", "Early Changes"),
                  ("s3", "Critical Decision Point"),
                  ("s4", "Response to Treatment"),
                  ("s5", "Resolution or Escalation")]
    for tab, (prefix, label) in zip(state_tabs, state_keys):
        with tab:
            st.markdown(f"**{label}** — {case_data.get(f'{prefix}_name', '')}")
            vitals_col, pe_col = st.columns(2)
            with vitals_col:
                st.markdown("**Vital Signs**")
                st.info(case_data.get(f"{prefix}_vitals", "—"))
            with pe_col:
                st.markdown("**Physical Exam**")
                st.info(case_data.get(f"{prefix}_pe", "—"))

            prog_text = case_data.get(f"{prefix}_prog", "")
            notes_text = case_data.get(f"{prefix}_notes", "")
            actions_text = case_data.get(f"{prefix}_actions", "")

            pos_col, neg_col = st.columns(2)
            with pos_col:
                st.markdown(
                    "<span style='color:#2e7d32; font-weight:bold;'>✅ Positive Path (Intervention Performed)</span>",
                    unsafe_allow_html=True
                )
                # Extract positive path from prog notes if present
                positive_text = ""
                if prog_text:
                    lines = prog_text.split("\\n")
                    pos_lines = [l for l in lines if any(
                        kw in l.lower() for kw in ["improve", "good", "stable", "respond", "positive", "treated"]
                    )]
                    positive_text = "\n".join(pos_lines) if pos_lines else prog_text
                st.success(positive_text or actions_text or "—")

            with neg_col:
                st.markdown(
                    "<span style='color:#c62828; font-weight:bold;'>❌ Negative Path (No Intervention)</span>",
                    unsafe_allow_html=True
                )
                negative_text = ""
                if prog_text:
                    lines = prog_text.split("\\n")
                    neg_lines = [l for l in lines if any(
                        kw in l.lower() for kw in ["deteriorat", "declin", "worsen", "worse", "negative", "untreated", "fail"]
                    )]
                    negative_text = "\n".join(neg_lines) if neg_lines else ""
                st.error(negative_text or notes_text or "—")
    
    # -------- STAGE 4: EXPORT & SYNC --------
    st.markdown("---")
    st.markdown("## 💾 Export & Integration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Word export
        word_file = export_to_word(case_data, final_diagnosis)
        if word_file:
            st.download_button(
                label="⬇️ Download Word Document",
                data=word_file,
                file_name=f"{final_diagnosis.replace(' ', '_')}_Case.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
    
    with col2:
        # Airtable sync
        if st.button("📤 Sync to Airtable", use_container_width=True):
            sync_case_to_airtable(case_data, final_diagnosis,
                                 form_data["target_learner"])
    
    with col3:
        # JSON export
        case_json = json.dumps(case_data, indent=2, default=str)
        st.download_button(
            label="📋 Export as JSON",
            data=case_json,
            file_name=f"{final_diagnosis.replace(' ', '_')}_Case.json",
            mime="application/json",
            use_container_width=True
        )
    
    # -------- ADVANCED DEBUG PANEL --------
    with st.expander("🔍 Advanced: Full Case Data & Debug"):
        tab1, tab2, tab3 = st.tabs(["Raw JSON", "Validation Log", "Generation Log"])
        
        with tab1:
            st.json(case_data)
        
        with tab2:
            if validation_results:
                for result in validation_results:
                    color = "🟢" if result.severity == "info" \
                           else "🟡" if result.severity == "warning" else "🔴"
                    st.write(f"{color} **{result.field_name}**: {result.message}")
            else:
                st.info("No validation issues found")
        
        with tab3:
            gen_log = state_mgr.get_generation_log()
            if gen_log:
                for event in gen_log:
                    st.write(f"⏱ {event['timestamp']}: {event['message']}")
            else:
                st.info("No generation log available")


# ============================================================================
# MAIN APPLICATION FLOW
# ============================================================================

def main():
    """Main application entry point."""
    
    # Header will be updated with case_name once a case is generated
    render_header(st.session_state.get("current_case_name", ""))
    render_sidebar_info()
    
    # Get configuration form
    with st.form("case_input_form", border=False):
        form_data = render_configuration_form()
    
    # Check if form was just submitted OR if we already have a case in session state
    # (to preserve display when user clicks buttons and page reruns)
    has_case = bool(state_mgr.get_case_data())
    if not form_data["submitted"] and not has_case:
        return
    
    # If form not submitted but we have a case, skip generation and jump to display
    if not form_data["submitted"] and has_case:
        case_data = state_mgr.get_case_data()
        final_diagnosis = case_data.get("diagnosis", "Unknown")
        # Jump directly to STAGE 3: DISPLAY & VALIDATION (line ~730)
        display_case_content(case_data, final_diagnosis, form_data)
        return
    
    # -------- STAGE 1: PRE-GENERATION --------
    state_mgr.apply_state_transition("input", "generating", "User submitted form")
    
    # Resolve random values
    random_diagnoses = [
        "Sepsis", "Myocardial Infarction", "Anaphylaxis",
        "Pulmonary Embolism", "DKA", "Asthma Exacerbation",
        "Stroke", "Pneumonia", "GI Bleed", "CHF Exacerbation",
        "Overdose", "Seizure", "Pneumothorax", "Meningitis",
    ]
    
    final_diagnosis = form_data["diagnosis"] if form_data["diagnosis"] \
        else random.choice(random_diagnoses)
    final_age = form_data["patient_age"] if form_data["patient_age"] is not None \
        else random.randint(18, 85)
    
    # -------- STAGE 2: GENERATION --------
    progress_bar = st.progress(0, text="Initializing AI case generation pipeline...")
    phase_status = st.empty()

    try:
        # Step 1: Generate with Gemini (passes CCS-5 level)
        progress_bar.progress(5, text="5% — Phase 0: Building Vector Model & complexity profile...")
        phase_status.info("🧬 **Phase 0/3** — Profiling case complexity (Vector Model, CCFs, cognitive biases)...")
        case_data = generate_case_with_gemini(
            final_diagnosis,
            final_age,
            form_data["patient_gender"],
            form_data["difficulty"],
            form_data["custom_focus"],
            ccs5_value=form_data.get("ccs5_value", 2)
        )
        progress_bar.progress(50, text="50% — AI generation complete, post-processing...")
        phase_status.info("🔬 **Post-processing** — Applying medical logic, populating Section 7...")

        # Step 2: Add metadata
        progress_bar.progress(55, text="55% — Adding case metadata...")
        today = date.today().strftime("%B %d, %Y")
        metadata = create_case_export_metadata()
        case_data.update({
            "date_developed": today,
            "developer": "Sim Center Team",
            "affiliation": "University of Kentucky",
            "revision_date": today,
            "revised_by": "AI Case Builder",
            "diagnosis": final_diagnosis,
            "target_learner": form_data["target_learner"],
            "difficulty": form_data["difficulty"],
            **metadata
        })
        
        # Step 2.5: Ensure all critical fields are populated
        case_data = ensure_critical_fields_populated(
            case_data,
            diagnosis=final_diagnosis,
            age=final_age,
            gender=form_data["patient_gender"],
            target_learner=form_data["target_learner"],
            difficulty=form_data["difficulty"]
        )

        # Step 2.6: Apply smart medical logic (DKA UA fix) and auto-populate Section 7
        progress_bar.progress(60, text="60% — Applying diagnosis-specific medical logic...")
        phase_status.info("💊 **Medical Logic** — Enforcing lab correlations, populating critical actions & debrief questions...")
        case_data = apply_dka_ua_logic(case_data)
        case_data = auto_populate_section_7(case_data)

        # Step 2.7: Validate field lengths and warn about truncation/overflow
        progress_bar.progress(70, text="70% — Checking field integrity...")
        phase_status.info("📏 **Field Validation** — Checking for truncation and overflow...")
        field_issues = validate_field_lengths(case_data)
        if field_issues:
            truncated = [i for i in field_issues if i.issue_type == "truncated"]
            too_long = [i for i in field_issues if i.issue_type == "too_long"]
            if truncated:
                st.warning(
                    "**Possible truncation detected** in: "
                    + ", ".join(f"`{i.field_name}` ({i.actual_length} chars)" for i in truncated)
                    + ". These fields may be incomplete — check the exported document."
                )
            if too_long:
                st.info(
                    "**Long fields auto-trimmed** for export safety: "
                    + ", ".join(f"`{i.field_name}` ({i.actual_length} chars)" for i in too_long)
                )
                case_data = truncate_long_fields(case_data)

        # Step 3: Validate case
        progress_bar.progress(80, text="80% — Validating clinical completeness...")
        phase_status.info("✅ **Clinical Validation** — Checking completeness, consistency, and educational quality...")
        validator = CaseValidator()
        is_valid, validation_results = validator.validate_complete_case(case_data)
        validation_summary = validator.get_validation_summary()
        
        # Store in session state (also cache case_name for header)
        state_mgr.set_case_data(case_data)
        st.session_state["current_case_name"] = case_data.get("case_name", "")
        # Stash complexity profile from case_data if the engine embedded it
        complexity_profile = case_data.pop("_complexity_profile", {})
        st.session_state["complexity_profile"] = complexity_profile
        progress_bar.progress(100, text="✓ Case generation complete!")
        phase_status.success("🎉 **All phases complete** — Case generated, validated, and ready for export.")
        progress_bar.empty()
        phase_status.empty()
        
        # -------- STAGE 3: DISPLAY & VALIDATION --------
        state_mgr.apply_state_transition("generating", "generated",
                                        "Case generated and validated")
        
        # Display case content and export options
        display_case_content(case_data, final_diagnosis, form_data, validation_summary)
        
        # Success state
        state_mgr.apply_state_transition("generated", "exported",
                                        "Case exported successfully")
        
    except Exception as e:
        st.error(f"❌ Generation Error: {str(e)}")
        
        with st.expander("🤓 Debug: Full Error Details"):
            try:
                # Try to show raw AI output if available
                st.write("Raw API Response (if available in error context)")
            except:
                st.write("No additional debug information available")


if __name__ == "__main__":
    main()
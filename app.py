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
from google import genai
from google.genai import types as genai_types
import streamlit.components.v1 as components
import json
import io
import os
from typing import Optional, Dict, Any
from datetime import date
import random
from docxtpl import DocxTemplate
from pathlib import Path
from dotenv import load_dotenv

# Load .env file immediately (use explicit path so it works regardless of cwd)
load_dotenv(Path(__file__).parent / ".env")

# Import custom modules
from state_manager import SimulationStateManager
from logic_controller import MedicalLogicController, Difficulty, CCS5Level, LabValidator, DrugDosingValidator, PerformanceScorer
from case_engine import CaseEngine, CaseConfig, CaseResult, DEBRIEF_PROMPT
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
    page_title="Sim Case Builder — UK Simulation Center",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# GLOBAL STYLES — clean medical / clinical aesthetic
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Tighten top padding */
    .block-container { padding-top: 1.5rem; }

    /* Subtle background for metric cards */
    [data-testid="stMetric"] {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 12px 16px;
    }

    /* Patient identity card */
    .patient-card {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        color: white;
        padding: 20px 28px;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .patient-card h2 { margin: 0 0 4px 0; color: white; font-size: 1.6rem; }
    .patient-card .meta { opacity: 0.9; font-size: 0.95rem; }

    /* Section headers */
    .section-header {
        border-left: 4px solid #1a237e;
        padding-left: 12px;
        margin: 1.5rem 0 0.75rem 0;
        font-size: 1.15rem;
        font-weight: 600;
        color: #1a237e;
    }

    /* Vitals table styling */
    .vitals-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin: 8px 0;
    }
    .vital-cell {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 10px 14px;
        text-align: center;
    }
    .vital-cell .label { font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
    .vital-cell .value { font-size: 1.3rem; font-weight: 700; color: #1a237e; }

    /* Critical action chips */
    .action-chip {
        background: #fff3e0;
        border: 1px solid #ffcc02;
        border-radius: 6px;
        padding: 8px 14px;
        margin: 4px 0;
        font-weight: 500;
    }

    /* Grade badge */
    .grade-badge {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 8px;
        color: white;
        font-size: 1.1rem;
        font-weight: 700;
    }

    /* Clean tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }

    /* Sidebar refinements */
    section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
    section[data-testid="stSidebar"] h3 { font-size: 1rem; }

    /* Hide Streamlit branding for cleaner look */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Load configuration from environment variables (supports both local .env and Streamlit Secrets)
# See .env.example for required setup
# On Streamlit Cloud: Use Settings → Secrets tab to add keys
# Locally: Use .env file

import re as _re

def _split_pathways(text: str) -> tuple:
    """
    Split text into (positive_portion, negative_portion) using pathway markers.
    Looks for GOOD PATH / BAD PATH, POSITIVE PATH / NEGATIVE PATH,
    or if-treated / if-untreated patterns. Returns (text, '') if no split found.
    """
    if not text:
        return ("", "")

    # Try structured markers first: "GOOD PATH:" / "BAD PATH:"
    pattern = _re.compile(
        r'(?:GOOD\s*PATH|POSITIVE\s*PATH|IF\s*(?:TREATED|INTERVENTION))\s*[:：]\s*(.*?)'
        r'(?:BAD\s*PATH|NEGATIVE\s*PATH|IF\s*(?:UNTREATED|NO\s*INTERVENTION|MISSED))\s*[:：]\s*(.*)',
        _re.IGNORECASE | _re.DOTALL
    )
    m = pattern.search(text)
    if m:
        return (m.group(1).strip().rstrip('.;,'), m.group(2).strip())

    # Try line-based splitting
    lines = text.replace('\\n', '\n').split('\n')
    pos_lines, neg_lines = [], []
    pos_kw = {"improve", "good", "stable", "respond", "positive", "treated", "better", "resolv"}
    neg_kw = {"deteriorat", "declin", "worsen", "worse", "negative", "untreated", "fail", "decompens", "arrest", "critical"}

    for line in lines:
        low = line.lower()
        is_pos = any(kw in low for kw in pos_kw)
        is_neg = any(kw in low for kw in neg_kw)
        if is_neg and not is_pos:
            neg_lines.append(line.strip())
        elif is_pos:
            pos_lines.append(line.strip())

    if pos_lines and neg_lines:
        return ("\n".join(pos_lines), "\n".join(neg_lines))

    return (text, "")


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

# Startup health checks
_startup_issues = []
if not TEMPLATE_PATH.exists():
    _startup_issues.append(
        f"**Word template missing:** `{TEMPLATE_PATH.name}` — Word export will be unavailable."
    )
if not AIRTABLE_API_KEY or AIRTABLE_API_KEY == "your_airtable_pat_here":
    _startup_issues.append(
        "**Airtable PAT not configured** — Airtable sync will be unavailable."
    )
if _startup_issues:
    for issue in _startup_issues:
        st.warning(f"⚠️ {issue}", icon="⚠️")


# ============================================================================
# STATE INITIALIZATION
# ============================================================================

@st.cache_resource
def get_state_manager() -> SimulationStateManager:
    """Initialize state manager as a cached resource."""
    return SimulationStateManager()


state_mgr = get_state_manager()


@st.cache_resource
def get_diagnosis_registry():
    """Cache the 351-diagnosis registry so it's not rebuilt on every rerun."""
    from logic_controller import DiagnosisRegistry
    return DiagnosisRegistry()


@st.cache_resource
def get_comorbidity_engine():
    """Cache the comorbidity engine."""
    from logic_controller import ComorbidityEngine
    return ComorbidityEngine()


# ============================================================================
# UI STYLING & LAYOUT COMPONENTS
# ============================================================================

def render_header(case_name: str = ""):
    """Render clean clinical header."""
    if case_name:
        # When a case is loaded, show the case name as the title
        st.markdown(
            f"<div class='patient-card'>"
            f"<h2>🏥 {case_name}</h2>"
            f"<div class='meta'>University of Kentucky · Simulation Center</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='text-align:center; padding:16px 0 8px 0;'>"
            "<h1 style='margin-bottom:2px;'>🏥 Sim Case Builder</h1>"
            "<p style='font-size:15px; color:#666; margin-top:0;'>"
            "University of Kentucky · College of Medicine · Simulation Center</p>"
            "</div>",
            unsafe_allow_html=True
        )


def render_sidebar_info():
    """Render sidebar with workflow guide and quick-reference info when a case is loaded."""
    with st.sidebar:
        st.markdown("### 🏥 Sim Case Builder")
        st.caption("University of Kentucky · Simulation Center")
        st.markdown("---")

        case_data = state_mgr.get_case_data()

        if case_data and case_data.get("case_name"):
            # --- Quick-Reference Panel (shown when a case is loaded) ---
            st.markdown("#### 📋 Quick Reference")

            # Patient snapshot
            pt_name = case_data.get("pt_name", "—")
            age = case_data.get("age", "—")
            gender = case_data.get("gender", "—")
            dx = case_data.get("diagnosis", "—")
            cc = case_data.get("chief_complaint", "—")
            st.markdown(
                f"**Patient:** {pt_name}  \n"
                f"**Age / Sex:** {age} / {gender}  \n"
                f"**Dx:** {dx}  \n"
                f"**CC:** {cc}"
            )

            st.markdown("---")

            # Arrival vitals
            st.markdown("#### 🩺 Arrival Vitals")
            _v = {
                "HR": case_data.get("hr_arrive", "—"),
                "BP": case_data.get("bp_arrive", "—"),
                "RR": case_data.get("rr_arrive", "—"),
                "SpO₂": case_data.get("o2_arrive", "—"),
                "Temp": case_data.get("temp_arrive", "—"),
                "GCS": case_data.get("gcs_arrive", "—"),
            }
            for label, val in _v.items():
                st.markdown(f"**{label}:** {val}")

            st.markdown("---")

            # Critical actions
            st.markdown("#### ⚡ Critical Actions")
            _actions = case_data.get("critical_actions", [])
            if isinstance(_actions, list):
                for a in _actions:
                    if a:
                        st.markdown(f"- {a}")
            elif _actions:
                st.markdown(f"- {_actions}")

            st.markdown("---")

            # Equipment checklist
            equip = case_data.get("equipment", "")
            if equip:
                st.markdown("#### 🧰 Equipment")
                st.caption(equip)

        else:
            # --- Workflow Guide (shown before a case is generated) ---
            st.markdown("#### 📋 How to Use")
            st.info(
                "1. **Select** a diagnosis from the registry\n"
                "2. **Configure** patient demographics & difficulty\n"
                "3. **Generate** — AI builds the full case\n"
                "4. **Review** vitals, labs, state progression\n"
                "5. **Export** to Word or sync to Airtable"
            )

        # Debug section (always at bottom)
        with st.expander("🔧 Debug"):
            current_state = state_mgr.get_current_state()
            st.write(f"**State:** {current_state}")
            st.write(f"**Case Loaded:** {'Yes' if case_data else 'No'}")
            st.write(f"**Fields:** {len(case_data) if case_data else 0}")


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
            _registry = get_diagnosis_registry()
            _all_dx = ["🎲 Random Diagnosis"] + sorted(_registry.all_diagnoses) + ["✏️ Type my own..."]
            _selected_dx = st.selectbox(
                "Primary Diagnosis",
                options=_all_dx,
                index=0,
                help="Choose from 351 registry diagnoses, select Random, or type your own"
            )
            if _selected_dx == "✏️ Type my own...":
                diagnosis = st.text_input(
                    "Enter your diagnosis",
                    placeholder="e.g. Diabetic Ketoacidosis",
                )
            elif _selected_dx.startswith("🎲"):
                diagnosis = ""
            else:
                diagnosis = _selected_dx
            
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

        # --- Comorbidity Selector ---
        _comorb_engine = get_comorbidity_engine()
        _dx_for_comorb = diagnosis.strip() if diagnosis else ""
        _avail_comorb = _comorb_engine.available_comorbidities(_dx_for_comorb) if _dx_for_comorb else sorted(_comorb_engine.UNIVERSAL_COMORBIDITIES.keys())
        comorbidities = st.multiselect(
            "Patient Comorbidities (Optional)",
            options=_avail_comorb,
            default=[],
            help="Select comorbidities that will modify lab values, interventions, and case complexity"
        )

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
            "comorbidities": comorbidities,
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
# CASE GENERATION ENGINE — Uses the proper multi-phase CaseEngine
# ============================================================================

def generate_case_with_gemini(diagnosis: str, age: int, gender: str,
                             difficulty: str, custom_focus: str,
                             target_learner: str = "Not specified",
                             ccs5_value: int = 2,
                             comorbidities: Optional[list] = None,
                             progress_callback=None) -> CaseResult:
    """
    Generate a case using the multi-phase CaseEngine pipeline.

    Phases:
      0: Complexity Profiling (Vector Model, CCFs, cognitive biases)
      1: Clinical Reasoning Plan (pathophysiology, timeline, interventions)
      2: Full Case Generation (96 fields, guided by Phase 1)
      3: Clinical Self-Review (AI audits its own work and corrects issues)

    Args:
        diagnosis: Primary diagnosis
        age: Patient age
        gender: Patient gender
        difficulty: Legacy difficulty string
        custom_focus: Custom instructions
        ccs5_value: CCS-5 level (1-5)
        comorbidities: List of comorbid conditions
        progress_callback: Optional callable(pct, text) for progress updates

    Returns:
        CaseResult with case_data, clinical_plan, complexity_profile, review_notes
    """
    config = CaseConfig(
        diagnosis=diagnosis,
        patient_age=age,
        patient_gender=gender,
        difficulty=difficulty,
        target_learner=target_learner,
        custom_focus=custom_focus,
        ccs5_level=ccs5_value,
        comorbidities=comorbidities or [],
    )

    engine = CaseEngine(api_key=GEMINI_API_KEY)

    # Run the full 4-phase pipeline
    result = engine.generate(config)

    # Clean the data structure (preserves lists now)
    result.case_data = clean_data_structure(result.case_data)

    # Embed complexity profile for downstream use
    result.case_data["_complexity_profile"] = result.complexity_profile

    return result


# ============================================================================
# AI DEBRIEF FACILITATOR ENGINE
# ============================================================================

def generate_debrief_guide(case_data: Dict[str, Any],
                           diagnosis: str,
                           target_learner: str,
                           ccs5_value: int = 2,
                           complexity_profile: Optional[Dict[str, Any]] = None
                           ) -> Dict[str, Any]:
    """
    Generate a structured PEARLS-framework debriefing guide using Gemini.

    Uses the generated case data + complexity profile to produce a complete
    facilitator debrief guide with advocacy-inquiry pairs, competency mapping,
    anticipated learner errors, and a scoring rubric.
    """
    from case_engine import DEBRIEF_PROMPT, SYSTEM_PROMPT
    from logic_controller import CCS5Level as _CCS5

    ccs5 = _CCS5(max(1, min(5, ccs5_value)))

    complexity_profile = complexity_profile or {}
    biases = complexity_profile.get("cognitive_biases_at_risk", [])
    cot = complexity_profile.get("chain_of_thought", {})

    # Build a compact case summary for the prompt
    case_summary = json.dumps({
        "case_name": case_data.get("case_name", ""),
        "vignette": case_data.get("vignette", ""),
        "hpi": case_data.get("hpi", ""),
        "pmh": case_data.get("pmh", ""),
        "s1_name": case_data.get("s1_name", ""),
        "s2_name": case_data.get("s2_name", ""),
        "s3_name": case_data.get("s3_name", ""),
        "s4_name": case_data.get("s4_name", ""),
        "s5_name": case_data.get("s5_name", ""),
        "s1_actions": case_data.get("s1_actions", ""),
        "s2_actions": case_data.get("s2_actions", ""),
        "s3_actions": case_data.get("s3_actions", ""),
        "s4_actions": case_data.get("s4_actions", ""),
        "s5_actions": case_data.get("s5_actions", ""),
        "s3_notes": case_data.get("s3_notes", ""),
    }, indent=2)

    prompt = DEBRIEF_PROMPT.format(
        case_summary=case_summary,
        diagnosis=diagnosis,
        target_learner=target_learner,
        ccs5_label=ccs5.label,
        critical_actions=json.dumps(case_data.get("critical_actions", [])),
        debrief_questions=json.dumps(case_data.get("debrief_questions", [])),
        ed_objectives=case_data.get("ed_objectives", "Not specified"),
        cognitive_biases=json.dumps(biases),
        uncertainty_type=complexity_profile.get("uncertainty_type", "Not assessed"),
        chain_of_thought=json.dumps(cot),
    )

    client = genai.Client(api_key=GEMINI_API_KEY)
    json_config = genai_types.GenerateContentConfig(
        systemInstruction=SYSTEM_PROMPT,
        responseMimeType="application/json",
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=json_config,
    )

    is_valid, parsed = validate_json_string(response.text)
    if not is_valid:
        raise ValueError(f"Debrief generation JSON parse failed: {parsed}")
    return parsed


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
    Display generated case content in clinical workflow order.
    Designed for simulation educators — shows what they need first.
    """
    # Recompute validation if not provided
    if validation_summary is None:
        validator = CaseValidator()
        is_valid, validation_results = validator.validate_complete_case(case_data)
        validation_summary = validator.get_validation_summary()
    else:
        is_valid = True
        validation_results = []

    # ====================================================================
    # 1. PATIENT IDENTITY CARD
    # ====================================================================
    pt_name = case_data.get("pt_name", "Simulated Patient")
    age = case_data.get("age", "—")
    gender = case_data.get("gender", "—")
    cc = case_data.get("chief_complaint", "—")
    dx = final_diagnosis
    setting = case_data.get("setting", "")
    arrival = case_data.get("arrival_method", "")

    st.markdown(
        f"<div class='patient-card'>"
        f"<h2>{pt_name}</h2>"
        f"<div class='meta'>"
        f"{age} y/o {gender} · <b>{dx}</b> · CC: {cc}"
        f"{'  ·  ' + arrival if arrival else ''}"
        f"{'  ·  ' + setting if setting else ''}"
        f"</div></div>",
        unsafe_allow_html=True
    )

    # ====================================================================
    # 2. CLINICAL VIGNETTE & HISTORY (collapsible, expanded by default)
    # ====================================================================
    st.markdown("<div class='section-header'>📖 Clinical Vignette & History</div>", unsafe_allow_html=True)

    vignette = case_data.get("vignette", "")
    if vignette:
        st.markdown(f"> {vignette}")

    col_hx1, col_hx2 = st.columns(2)
    with col_hx1:
        hpi = case_data.get("hpi", "")
        if hpi:
            st.markdown("**HPI**")
            st.write(hpi)
        pmh = case_data.get("pmh", "")
        if pmh:
            st.markdown("**Past Medical History**")
            st.write(pmh)
        meds = case_data.get("medications", "")
        if meds:
            st.markdown("**Medications**")
            st.write(meds)
    with col_hx2:
        allergies = case_data.get("allergies", "")
        if allergies:
            st.markdown("**Allergies**")
            st.write(allergies)
        soc = case_data.get("social_history", "")
        if soc:
            st.markdown("**Social History**")
            st.write(soc)
        fmh = case_data.get("fmh", "")
        if fmh:
            st.markdown("**Family History**")
            st.write(fmh)

    # ====================================================================
    # 3. ARRIVAL VITALS — clean grid
    # ====================================================================
    st.markdown("<div class='section-header'>🩺 Arrival Assessment</div>", unsafe_allow_html=True)

    _vitals = [
        ("HR", case_data.get("hr_arrive", "—"), "bpm"),
        ("BP", case_data.get("bp_arrive", "—"), "mmHg"),
        ("RR", case_data.get("rr_arrive", "—"), "/min"),
        ("SpO₂", case_data.get("o2_arrive", "—"), "%"),
        ("Temp", case_data.get("temp_arrive", "—"), "°F"),
        ("Rhythm", case_data.get("rhythm_arrive", "—"), ""),
        ("Glucose", case_data.get("glucose_arrive", "—"), "mg/dL"),
        ("GCS", case_data.get("gcs_arrive", "—"), ""),
    ]
    vital_html = "<div class='vitals-grid'>"
    for label, value, unit in _vitals:
        vital_html += (
            f"<div class='vital-cell'>"
            f"<div class='label'>{label}</div>"
            f"<div class='value'>{value}</div>"
            f"<div class='label'>{unit}</div>"
            f"</div>"
        )
    vital_html += "</div>"
    st.markdown(vital_html, unsafe_allow_html=True)

    # Arrival PE
    with st.expander("Physical Exam on Arrival", expanded=False):
        pe_fields = [
            ("General", "general_pe"), ("Neuro", "neuro_pe"), ("HEENT", "heent_pe"),
            ("CV", "cv_pe"), ("Resp", "resp_pe"), ("Abd", "abd_pe"),
            ("GU", "gu_pe"), ("MSK", "msk_pe"), ("Skin", "skin_pe"), ("Psych", "psych_pe"),
        ]
        for label, key in pe_fields:
            val = case_data.get(key, "")
            if val:
                st.markdown(f"**{label}:** {val}")

    # ====================================================================
    # 4. LAB RESULTS — formatted table
    # ====================================================================
    st.markdown("<div class='section-header'>🧪 Laboratory Results</div>", unsafe_allow_html=True)

    lab_groups = {
        "CBC": [("WBC", "wbc"), ("Hgb", "hgb"), ("Hct", "hct"), ("Plt", "plt")],
        "BMP": [("Na", "na"), ("K", "k"), ("Cl", "cl"), ("HCO₃", "hco3"),
                ("BUN", "bun"), ("Cr", "cr"), ("Glu", "glu"), ("AG", "ag")],
        "LFTs": [("AST", "ast"), ("ALT", "alt"), ("Alk Phos", "alk_phos"),
                 ("T.Bili", "t_bili"), ("Lipase", "lipase"), ("Albumin", "alb")],
        "Other": [("Ca", "ca"), ("Mg", "mg"), ("Phos", "phos"),
                  ("Lactate", "lactate"), ("Troponin", "troponin"), ("TSH", "tsh")],
    }

    lab_cols = st.columns(len(lab_groups))
    for col, (group_name, labs) in zip(lab_cols, lab_groups.items()):
        with col:
            st.markdown(f"**{group_name}**")
            for label, key in labs:
                val = case_data.get(key, "")
                if val:
                    st.caption(f"{label}: **{val}**")

    # VBG / UA in expander
    has_vbg = any(case_data.get(k) for k in ["vbg_ph", "vbg_pco2", "vbg_po2", "vbg_hco3"])
    has_ua = any(case_data.get(k) for k in ["ua_color", "ua_clarity", "ua_prot", "ua_glu", "ua_ketones"])
    if has_vbg or has_ua:
        with st.expander("VBG / Urinalysis"):
            if has_vbg:
                st.markdown(
                    f"**VBG:** pH {case_data.get('vbg_ph', '—')} · "
                    f"pCO₂ {case_data.get('vbg_pco2', '—')} · "
                    f"pO₂ {case_data.get('vbg_po2', '—')} · "
                    f"HCO₃ {case_data.get('vbg_hco3', '—')}"
                )
            if has_ua:
                st.markdown(
                    f"**UA:** Color: {case_data.get('ua_color', '—')} · "
                    f"Clarity: {case_data.get('ua_clarity', '—')} · "
                    f"Protein: {case_data.get('ua_prot', '—')} · "
                    f"Glucose: {case_data.get('ua_glu', '—')} · "
                    f"Ketones: {case_data.get('ua_ketones', '—')}"
                )

    # ====================================================================
    # 5. PATIENT STATE PROGRESSION
    # ====================================================================
    st.markdown("<div class='section-header'>🔀 Patient State Progression</div>", unsafe_allow_html=True)

    # --- Branching Flowchart ---
    _state_labels = [
        ("S1", case_data.get("s1_name", "Arrival")),
        ("S2", case_data.get("s2_name", "Early Changes")),
        ("S3", case_data.get("s3_name", "Critical Decision")),
        ("S4", case_data.get("s4_name", "Response")),
        ("S5", case_data.get("s5_name", "Resolution")),
    ]
    def _safe_mermaid(text: str) -> str:
        return text.replace('"', "'").replace("\n", " ").replace("[", "(").replace("]", ")")[:60]

    mermaid_lines = ["graph TD"]
    for i, (sid, name) in enumerate(_state_labels):
        safe = _safe_mermaid(name) if name else f"State {i+1}"
        mermaid_lines.append(f'    {sid}["{sid}: {safe}"]')
    for i in range(len(_state_labels) - 1):
        sid_a = _state_labels[i][0]
        sid_b = _state_labels[i + 1][0]
        mermaid_lines.append(f"    {sid_a} -->|Intervention| {sid_b}")
    mermaid_lines.append('    S3 -->|"Missed / Delayed"| BAD["⚠️ Decompensation"]')
    mermaid_lines.append('    BAD -->|"Rescue"| S4')
    mermaid_lines.append("    style S1 fill:#e3f2fd,stroke:#1565c0")
    mermaid_lines.append("    style S3 fill:#fff3e0,stroke:#e65100")
    mermaid_lines.append("    style S5 fill:#e8f5e9,stroke:#2e7d32")
    mermaid_lines.append("    style BAD fill:#ffebee,stroke:#c62828")

    with st.expander("📊 Branching Flowchart", expanded=True):
        mermaid_code = "\n".join(mermaid_lines)
        mermaid_html = f"""
        <div class="mermaid">{mermaid_code}</div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>
        """
        components.html(mermaid_html, height=400, scrolling=True)

    state_tabs = st.tabs(["State 1", "State 2", "State 3", "State 4", "State 5"])
    state_keys = [("s1", "Arrival / Initial Presentation"),
                  ("s2", "Early Changes"),
                  ("s3", "Critical Decision Point"),
                  ("s4", "Response to Treatment"),
                  ("s5", "Resolution or Escalation")]
    for tab, (prefix, label) in zip(state_tabs, state_keys):
        with tab:
            st.markdown(f"**{label}** — {case_data.get(f'{prefix}_name', '')}")

            vitals_text = case_data.get(f"{prefix}_vitals", "—")
            positive_vitals, negative_vitals = _split_pathways(vitals_text)
            if negative_vitals:
                v_good, v_bad = st.columns(2)
                with v_good:
                    st.markdown("**Vitals — Good Path**")
                    st.success(positive_vitals)
                with v_bad:
                    st.markdown("**Vitals — Bad Path**")
                    st.error(negative_vitals)
            else:
                st.markdown("**Vital Signs**")
                st.info(vitals_text)

            pe_text = case_data.get(f"{prefix}_pe", "—")
            positive_pe, negative_pe = _split_pathways(pe_text)
            if negative_pe:
                pe_good, pe_bad = st.columns(2)
                with pe_good:
                    st.markdown("**PE — Good Path**")
                    st.success(positive_pe)
                with pe_bad:
                    st.markdown("**PE — Bad Path**")
                    st.error(negative_pe)
            else:
                st.markdown("**Physical Exam**")
                st.info(pe_text)

            actions_text = case_data.get(f"{prefix}_actions", "")
            notes_text = case_data.get(f"{prefix}_notes", "")
            prog_text = case_data.get(f"{prefix}_prog", "")

            if actions_text:
                st.markdown("**Expected Learner Actions**")
                st.warning(actions_text)

            positive_notes, negative_notes = _split_pathways(notes_text)
            if negative_notes:
                n_good, n_bad = st.columns(2)
                with n_good:
                    st.markdown("✅ **If Intervention Performed**")
                    st.success(positive_notes)
                with n_bad:
                    st.markdown("❌ **If Intervention Missed**")
                    st.error(negative_notes)
            elif notes_text:
                st.markdown("**Operator Notes**")
                st.info(notes_text)

            if prog_text:
                st.markdown("**Progression Trigger**")
                st.caption(prog_text)

    # ====================================================================
    # 6. CRITICAL ACTIONS & DEBRIEF
    # ====================================================================
    st.markdown("<div class='section-header'>⚡ Critical Actions & Debrief Questions</div>", unsafe_allow_html=True)

    col_ca, col_dq = st.columns(2)
    with col_ca:
        st.markdown("**Critical Actions**")
        _actions = case_data.get("critical_actions", [])
        if isinstance(_actions, list):
            for i, a in enumerate(_actions, 1):
                if a:
                    st.markdown(f"<div class='action-chip'>**{i}.** {a}</div>", unsafe_allow_html=True)
        elif _actions:
            st.markdown(f"<div class='action-chip'>{_actions}</div>", unsafe_allow_html=True)
    with col_dq:
        st.markdown("**Debrief Questions**")
        _debrief = case_data.get("debrief_questions", [])
        if isinstance(_debrief, list):
            for i, q in enumerate(_debrief, 1):
                if q:
                    st.markdown(f"{i}. {q}")
        elif _debrief:
            st.markdown(f"1. {_debrief}")

    # References
    _refs = case_data.get("references", [])
    if _refs and any(_refs):
        with st.expander("📚 References"):
            for r in _refs:
                if r:
                    st.write(f"- {r}")

    # ====================================================================
    # 6b. AI DEBRIEF FACILITATOR GUIDE (the standout feature)
    # ====================================================================
    debrief_guide = st.session_state.get("debrief_guide")
    if debrief_guide and isinstance(debrief_guide, dict):
        st.markdown(
            "<div class='section-header'>🎓 AI Debrief Facilitator Guide "
            "<span style='font-size:0.7em;color:#666;font-weight:normal;'>"
            "PEARLS Framework · Powered by Gemini</span></div>",
            unsafe_allow_html=True,
        )

        debrief_tabs = st.tabs([
            "📜 PEARLS Script",
            "🎯 Competency Map",
            "⚠️ Anticipated Errors",
            "📊 Assessment Rubric",
            "🛡️ Facilitator Prep",
        ])

        # --- TAB 1: PEARLS Script ---
        pearls = debrief_guide.get("pearls_script", {})
        with debrief_tabs[0]:
            st.markdown("##### The PEARLS Debriefing Framework")
            st.caption(
                "Promoting Excellence And Reflective Learning in Simulation — "
                "the evidence-based gold standard for sim debriefing."
            )

            # Reactions
            reactions = pearls.get("reactions", {})
            with st.expander("1️⃣ Reactions Phase", expanded=True):
                st.markdown(f"**Opening Prompt:**  \n> *\"{reactions.get('opening_prompt', '')}\"*")
                follow_ups = reactions.get("follow_up_prompts", [])
                if follow_ups:
                    st.markdown("**Follow-up Prompts:**")
                    for fp in follow_ups:
                        st.markdown(f"- *\"{fp}\"*")
                fac_notes = reactions.get("facilitator_notes", "")
                if fac_notes:
                    st.info(f"💡 **Facilitator Tip:** {fac_notes}")

            # Description
            desc = pearls.get("description", {})
            with st.expander("2️⃣ Description Phase", expanded=True):
                st.markdown(f"**Summary Prompt:**  \n> *\"{desc.get('summary_prompt', '')}\"*")
                clarifying = desc.get("clarifying_questions", [])
                if clarifying:
                    st.markdown("**Clarifying Questions:**")
                    for cq in clarifying:
                        st.markdown(f"- *\"{cq}\"*")
                facts = desc.get("key_facts_to_establish", [])
                if facts:
                    st.markdown("**Key Facts Learners Should Identify:**")
                    for fact in facts:
                        st.success(f"✓ {fact}")

            # Analysis (the core — advocacy-inquiry)
            analysis = pearls.get("analysis", {})
            with st.expander("3️⃣ Analysis Phase — Advocacy-Inquiry", expanded=True):
                ai_pairs = analysis.get("advocacy_inquiry_pairs", [])
                for idx, pair in enumerate(ai_pairs, 1):
                    st.markdown(f"**Pair {idx}**")
                    st.markdown(f"🔍 **Observation:** {pair.get('observation', '')}")
                    st.markdown(f"📢 **Advocacy:** {pair.get('advocacy', '')}")
                    st.markdown(f"❓ **Inquiry:** *\"{pair.get('inquiry', '')}\"*")
                    st.caption(f"🎯 Teaching Point: {pair.get('teaching_point', '')}")
                    st.markdown("---")

                crit_decisions = analysis.get("critical_decision_explorations", [])
                if crit_decisions:
                    st.markdown("**Critical Decision Explorations:**")
                    for cd in crit_decisions:
                        col_good, col_miss = st.columns(2)
                        st.markdown(f"**Decision:** {cd.get('decision_point', '')}")
                        with col_good:
                            st.success(f"✅ If done well: {cd.get('if_done_well', '')}")
                        with col_miss:
                            st.error(f"❌ If missed: {cd.get('if_missed', '')}")
                        st.caption(f"Clinical rationale: {cd.get('clinical_rationale', '')}")

            # Application
            application = pearls.get("application", {})
            with st.expander("4️⃣ Application Phase", expanded=True):
                st.markdown(f"**Takeaway Prompt:**  \n> *\"{application.get('takeaway_prompt', '')}\"*")
                transfer = application.get("transfer_questions", [])
                if transfer:
                    st.markdown("**Transfer to Practice:**")
                    for tq in transfer:
                        st.markdown(f"- *\"{tq}\"*")
                commit = application.get("commitment_prompt", "")
                if commit:
                    st.warning(f"🤝 **Commitment Prompt:**  \n> *\"{commit}\"*")

        # --- TAB 2: Competency Map ---
        with debrief_tabs[1]:
            st.markdown("##### ACGME / AACN Competency Alignment")
            st.caption("How this case maps to core healthcare competencies.")
            competencies = debrief_guide.get("competency_alignment", [])
            for comp in competencies:
                with st.expander(f"🎯 {comp.get('competency_domain', 'Domain')}", expanded=False):
                    st.markdown(f"**Competency:** {comp.get('specific_competency', '')}")
                    st.markdown(f"**How Case Addresses It:** {comp.get('how_case_addresses', '')}")
                    behaviors = comp.get("observable_behaviors", [])
                    if behaviors:
                        st.markdown("**Observable Behaviors:**")
                        for b in behaviors:
                            st.markdown(f"- {b}")

        # --- TAB 3: Anticipated Learner Errors ---
        with debrief_tabs[2]:
            st.markdown("##### Anticipated Learner Errors & Facilitator Responses")
            st.caption(
                "Based on the diagnosis, learner level, and cognitive bias profile. "
                "These help facilitators prepare for common gaps."
            )
            errors = debrief_guide.get("anticipated_learner_errors", [])
            for i, err in enumerate(errors, 1):
                with st.expander(f"⚠️ Error {i}: {err.get('error', '')}", expanded=False):
                    st.markdown(f"**Why It Happens:** {err.get('why_it_happens', '')}")
                    st.error(f"**Clinical Consequence:** {err.get('clinical_consequence', '')}")
                    st.info(f"**Facilitator Response:** {err.get('facilitator_response', '')}")
                    st.success(f"**Prevention Strategy:** {err.get('prevention_strategy', '')}")

        # --- TAB 4: Assessment Rubric ---
        rubric = debrief_guide.get("assessment_rubric", {})
        with debrief_tabs[3]:
            st.markdown("##### Case-Specific Assessment Rubric")
            st.caption("Ready-to-use scoring rubric tailored to this case.")
            dimensions = rubric.get("scoring_dimensions", [])
            for dim in dimensions:
                with st.expander(f"📋 {dim.get('dimension', '')} ({dim.get('weight', '')})", expanded=False):
                    col_e, col_p, col_d, col_n = st.columns(4)
                    with col_e:
                        st.markdown("**Exemplary**")
                        st.success(dim.get("exemplary", ""))
                    with col_p:
                        st.markdown("**Proficient**")
                        st.info(dim.get("proficient", ""))
                    with col_d:
                        st.markdown("**Developing**")
                        st.warning(dim.get("developing", ""))
                    with col_n:
                        st.markdown("**Novice**")
                        st.error(dim.get("novice", ""))
                    indicators = dim.get("observable_indicators", [])
                    if indicators:
                        st.markdown("**Observable Indicators:**")
                        for ind in indicators:
                            st.markdown(f"- {ind}")

            # Global rating anchors
            global_anchors = rubric.get("global_rating_anchors", {})
            if global_anchors:
                st.markdown("---")
                st.markdown("**Global Performance Rating Scale:**")
                anchor_colors = {"1_novice": "🔴", "2_developing": "🟡",
                                 "3_proficient": "🔵", "4_exemplary": "🟢"}
                for key, desc in global_anchors.items():
                    icon = anchor_colors.get(key, "⚪")
                    label = key.replace("_", " ").title()
                    st.markdown(f"{icon} **{label}:** {desc}")

        # --- TAB 5: Facilitator Preparation ---
        fac_prep = debrief_guide.get("facilitator_preparation", {})
        with debrief_tabs[4]:
            st.markdown("##### Facilitator Preparation Notes")

            # Emotional safety
            emo_note = fac_prep.get("emotional_safety_notes", "")
            if emo_note:
                st.warning(f"🛡️ **Emotional Safety:** {emo_note}")

            # Pre-brief points
            pre_brief = fac_prep.get("pre_brief_talking_points", [])
            if pre_brief:
                st.markdown("**Pre-Brief Talking Points:**")
                for pb in pre_brief:
                    st.markdown(f"- {pb}")

            # Common facilitator pitfalls
            pitfalls = fac_prep.get("common_facilitator_pitfalls", [])
            if pitfalls:
                st.markdown("**Common Facilitator Pitfalls to Avoid:**")
                for pit in pitfalls:
                    st.error(f"❌ {pit}")

            # Time allocation
            time_alloc = fac_prep.get("time_allocation", {})
            if time_alloc:
                st.markdown("**Recommended Time Allocation:**")
                def _safe_int(v, default=0):
                    try:
                        return int(v)
                    except (TypeError, ValueError):
                        return default

                _time_items = [
                    ("Reactions", _safe_int(time_alloc.get("reactions_minutes"), 3)),
                    ("Description", _safe_int(time_alloc.get("description_minutes"), 5)),
                    ("Analysis", _safe_int(time_alloc.get("analysis_minutes"), 15)),
                    ("Application", _safe_int(time_alloc.get("application_minutes"), 5)),
                ]
                total = _safe_int(time_alloc.get("total_minutes"), sum(t for _, t in _time_items))
                time_html = "<div class='vitals-grid'>"
                for phase_name, mins in _time_items:
                    time_html += (
                        f"<div class='vital-cell'>"
                        f"<div class='label'>{phase_name}</div>"
                        f"<div class='value'>{mins}</div>"
                        f"<div class='label'>min</div>"
                        f"</div>"
                    )
                time_html += (
                    f"<div class='vital-cell' style='background:#e8f5e9;border-color:#2e7d32;'>"
                    f"<div class='label'>Total</div>"
                    f"<div class='value'>{total}</div>"
                    f"<div class='label'>min</div>"
                    f"</div></div>"
                )
                st.markdown(time_html, unsafe_allow_html=True)

    # ====================================================================
    # 7. EXPORT & SYNC
    # ====================================================================
    st.markdown("<div class='section-header'>💾 Export & Integration</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        # Lazy export: only generate Word doc when download is requested
        @st.cache_data
        def _cached_word_export(_case_data_json, _diag):
            return export_to_word(json.loads(_case_data_json), _diag)
        _case_json_for_export = json.dumps(case_data, default=str)
        word_file = _cached_word_export(_case_json_for_export, final_diagnosis)
        if word_file:
            st.download_button(
                label="⬇️ Download Word Document",
                data=word_file,
                file_name=f"{final_diagnosis.replace(' ', '_')}_Case.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
    with col2:
        if st.button("📤 Sync to Airtable", use_container_width=True):
            sync_case_to_airtable(case_data, final_diagnosis,
                                 form_data["target_learner"])
    with col3:
        case_json = json.dumps(case_data, indent=2, default=str)
        st.download_button(
            label="📋 Export as JSON",
            data=case_json,
            file_name=f"{final_diagnosis.replace(' ', '_')}_Case.json",
            mime="application/json",
            use_container_width=True
        )

    # ====================================================================
    # 8. VALIDATION & QUALITY (collapsed — for review, not first glance)
    # ====================================================================
    with st.expander("✅ Validation & Quality Score", expanded=False):
        # Validation summary
        st.markdown("#### Validation Report")
        render_validation_results(validation_summary)

        # Lab validation
        lab_issues = st.session_state.get("lab_issues", [])
        if lab_issues:
            errors = [i for i in lab_issues if i.severity == "error"]
            warnings = [i for i in lab_issues if i.severity == "warning"]
            st.markdown("#### 🧪 Lab Value Validation")
            if errors:
                st.error(f"**{len(errors)} lab value(s) critically out of range**")
                for issue in errors:
                    st.write(f"🔴 **{issue.field_name}** = {issue.value} — expected [{issue.expected_min}–{issue.expected_max}]")
            if warnings:
                st.warning(f"**{len(warnings)} lab value(s) outside expected range**")
                for issue in warnings:
                    st.write(f"🟡 **{issue.field_name}** = {issue.value} — expected [{issue.expected_min}–{issue.expected_max}]")
        else:
            st.success("All lab values within expected ranges.")

        # Drug dosing
        drug_issues = st.session_state.get("drug_issues", [])
        if drug_issues:
            drug_errors = [i for i in drug_issues if i.severity == "error"]
            drug_warnings = [i for i in drug_issues if i.severity == "warning"]
            drug_info = [i for i in drug_issues if i.severity == "info"]
            st.markdown("#### 💊 Drug Dosing Validation")
            if drug_errors:
                st.error(f"**{len(drug_errors)} dosing error(s) found**")
                for issue in drug_errors:
                    st.write(f"🔴 **{issue.drug}**: {issue.issue}")
                    st.caption(f"Recommendation: {issue.recommendation}")
            if drug_warnings:
                st.warning(f"**{len(drug_warnings)} dosing warning(s)**")
                for issue in drug_warnings:
                    st.write(f"🟡 **{issue.drug}**: {issue.issue}")
                    st.caption(f"Recommendation: {issue.recommendation}")
            if drug_info:
                for issue in drug_info:
                    st.info(f"ℹ️ **{issue.drug}**: {issue.issue} — {issue.recommendation}")
        else:
            st.success("No drug dosing issues detected.")

        # Performance score
        perf_report = st.session_state.get("performance_report")
        if perf_report:
            st.markdown("#### 📊 Case Quality Score")
            grade_colors = {"A": "#2e7d32", "B": "#1565c0", "C": "#e65100", "D": "#c62828", "F": "#b71c1c"}
            color = grade_colors.get(perf_report.grade, "#555")
            st.markdown(
                f"<div class='grade-badge' style='background:{color};'>"
                f"{perf_report.overall_score}% — Grade {perf_report.grade}</div>",
                unsafe_allow_html=True
            )
            for comp in perf_report.components:
                bar = "█" * comp.score + "░" * (comp.max_score - comp.score)
                st.markdown(f"**{comp.dimension}** {bar} {comp.score}/{comp.max_score}")
                if comp.deductions:
                    for d in comp.deductions:
                        st.caption(f"  → {d}")
            if perf_report.strengths:
                st.success(f"**Strengths:** {', '.join(perf_report.strengths)}")
            if perf_report.improvement_areas:
                st.warning("**Areas for Improvement:**")
                for area in perf_report.improvement_areas:
                    st.write(f"- {area}")

        # Completeness metric
        st.metric("Clinical Completeness", "✓ Valid" if is_valid else "✗ Incomplete")

    # ====================================================================
    # 9. COMPLEXITY PROFILE (collapsed — academic detail)
    # ====================================================================
    complexity_profile = st.session_state.get("complexity_profile", {})
    if complexity_profile:
        with st.expander("🧠 Complexity Profile (Vector Model · CCFs · CoT · Bias Check)", expanded=False):
            render_complexity_profile(complexity_profile)

    # ====================================================================
    # 10. DEBUG PANEL (collapsed)
    # ====================================================================
    with st.expander("🔍 Advanced: Full Case Data & Debug"):
        tab1, tab2, tab3, tab4 = st.tabs(["Raw JSON", "Validation Log", "Engine Log (4-Phase)", "Generation Log"])
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
            debug_lab = st.session_state.get("lab_issues", [])
            if debug_lab:
                st.markdown("---")
                st.write("**Lab Validation (DiagnosisRegistry)**")
                for issue in debug_lab:
                    icon = "🔴" if issue.severity == "error" else "🟡"
                    st.write(f"{icon} {issue.message}")
        with tab3:
            phases = st.session_state.get("phases_completed", 0)
            st.write(f"**Phases completed:** {phases}/4")
            review = st.session_state.get("review_notes", "")
            if review:
                st.write(f"**Phase 3 Review:** {review}")
            engine_log = st.session_state.get("engine_log", [])
            if engine_log:
                for entry in engine_log:
                    st.write(f"⚙️ {entry}")
            else:
                st.info("No engine log available (legacy generation)")
            clinical_plan = st.session_state.get("clinical_plan")
            if clinical_plan:
                st.markdown("---")
                st.write("**Phase 1 Clinical Reasoning Plan:**")
                st.json(clinical_plan)
        with tab4:
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
    # Use the full 351-diagnosis registry for random selection
    _rand_registry = get_diagnosis_registry()
    _all_rand_dx = _rand_registry.all_diagnoses if _rand_registry.all_diagnoses else [
        "Sepsis", "Myocardial Infarction", "Anaphylaxis",
        "Pulmonary Embolism", "DKA", "Asthma Exacerbation",
        "Stroke", "Pneumonia", "GI Bleed", "CHF Exacerbation",
    ]
    
    final_diagnosis = form_data["diagnosis"] if form_data["diagnosis"] \
        else random.choice(_all_rand_dx)
    final_age = form_data["patient_age"] if form_data["patient_age"] is not None \
        else random.randint(18, 85)
    
    # -------- STAGE 2: GENERATION --------
    progress_bar = st.progress(0, text="Initializing AI case generation pipeline...")
    phase_status = st.empty()

    try:
        # Step 1: Generate with CaseEngine (full 4-phase pipeline)
        progress_bar.progress(5, text="5% — Phase 0: Building Vector Model & complexity profile...")
        phase_status.info("🧬 **Phase 0-3** — Running full CaseEngine pipeline (complexity profiling → clinical reasoning → case generation → self-review)...")
        result = generate_case_with_gemini(
            final_diagnosis,
            final_age,
            form_data["patient_gender"],
            form_data["difficulty"],
            form_data["custom_focus"],
            target_learner=form_data["target_learner"],
            ccs5_value=form_data.get("ccs5_value", 2),
            comorbidities=form_data.get("comorbidities", [])
        )

        # Extract case data and engine artifacts from CaseResult
        case_data = result.case_data
        st.session_state["engine_log"] = result.log
        st.session_state["clinical_plan"] = result.clinical_plan
        st.session_state["review_notes"] = result.review_notes
        st.session_state["phases_completed"] = result.phases_completed

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

        # Step 3b: Lab validation against diagnosis-specific expected ranges
        progress_bar.progress(85, text="85% — Validating lab values against diagnosis ranges...")
        phase_status.info("🧪 **Lab Validation** — Checking AI-generated labs against expected ranges for " + final_diagnosis + "...")
        lab_validator = LabValidator()
        lab_issues = lab_validator.validate(case_data, final_diagnosis)
        st.session_state["lab_issues"] = lab_issues

        # Step 3c: Drug dosing validation
        progress_bar.progress(88, text="88% — Validating medication dosing...")
        phase_status.info("💊 **Drug Dosing Check** — Scanning for dosing issues and contraindications...")
        drug_validator = DrugDosingValidator()
        drug_issues = drug_validator.validate_case(
            case_data, comorbidities=form_data.get("comorbidities", [])
        )
        st.session_state["drug_issues"] = drug_issues

        # Step 3d: Performance scoring
        progress_bar.progress(92, text="92% — Scoring case quality...")
        phase_status.info("📊 **Performance Scoring** — Evaluating case across 10 quality dimensions...")
        perf_scorer = PerformanceScorer()
        perf_report = perf_scorer.score_case(
            case_data, final_diagnosis, form_data["difficulty"],
            lab_issues=lab_issues, drug_issues=drug_issues
        )
        st.session_state["performance_report"] = perf_report

        # Step 4: AI Debrief Facilitator Guide
        progress_bar.progress(95, text="95% — Generating AI debrief facilitator guide...")
        phase_status.info("🎓 **AI Debrief Engine** — Building PEARLS script, competency map, anticipated errors & assessment rubric...")
        try:
            # Pull complexity profile before it gets popped
            _cp_for_debrief = case_data.get("_complexity_profile", {})
            debrief_guide = generate_debrief_guide(
                case_data=case_data,
                diagnosis=final_diagnosis,
                target_learner=form_data["target_learner"],
                ccs5_value=form_data.get("ccs5_value", 2),
                complexity_profile=_cp_for_debrief,
            )
            st.session_state["debrief_guide"] = debrief_guide
        except Exception as debrief_err:
            st.session_state["debrief_guide"] = None
            state_mgr.get_generation_log() # just to keep engine going
            # Non-critical — log but don't fail the whole pipeline
            st.toast(f"⚠️ Debrief guide generation skipped: {debrief_err}", icon="⚠️")

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
        progress_bar.empty()
        phase_status.empty()
        st.error(f"❌ Generation Error: {str(e)}")
        
        with st.expander("🤓 Debug: Full Error Details"):
            st.write(f"**Error type:** `{type(e).__name__}`")
            st.write(f"**Message:** {str(e)}")


if __name__ == "__main__":
    main()
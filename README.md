# Clinical Simulation Case Builder
## Enterprise-Grade Medical Simulation Generator

A professional Streamlit application for generating AI-powered clinical simulation cases with robust state management, validation, and Airtable integration.

---

## 🏗️ Architecture Overview

This application demonstrates **enterprise-level software design** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│               app.py (UI Layer)                     │
│         - Streamlit interface & routing             │
└──────────────┬──────────────┬──────────────┬────────┘
               │              │              │
    ┌──────────▼──┐  ┌────────▼──────┐  ┌───▼────────────┐
    │ state_      │  │   logic_      │  │  airtable_     │
    │ manager.py  │  │ controller.py │  │  client.py     │
    │             │  │               │  │                │
    │ Streamlit   │  │ Medical        │  │ API calls,     │
    │ session     │  │ branching      │  │ rate limiting, │
    │ state       │  │ rules & vital  │  │ error handling │
    │ management  │  │ sign logic     │  │                │
    └─────────────┘  └────────────────┘  └────────────────┘
               │              │              │
    ┌──────────▼──────────────▼──────────────▼────┐
    │          validators.py                      │
    │    Clinical completeness validation         │
    └────────────────┬─────────────────────────────┘
                     │
    ┌────────────────▼──────────────────┐
    │       utils.py                    │
    │  Shared utilities & helpers       │
    └───────────────────────────────────┘
```

### Module Responsibilities

#### **state_manager.py** – State Lifecycle Management
- **Purpose**: Maintains case data across Streamlit reruns
- **Key Features**:
  - Session state persistence (`st.session_state`)
  - State validation and transition tracking
  - Generation event logging for debugging
  - Safe field-level updates
- **Why It Matters**: Streamlit reruns the entire script on button clicks. This module ensures data doesn't get lost.

#### **logic_controller.py** – Medical Branching Engine
- **Purpose**: Encapsulates all clinical decision rules
- **Key Features**:
  - Diagnosis-specific vital sign presets
  - 5-state scenario progression logic
  - Intervention-based outcome branching
  - Difficulty-level multipliers for scenario scaling
  - Clinical completeness validation
- **Why It Matters**: Decouples medical logic from UI, making it easy to:
  - Add new diagnoses or branching rules
  - Audit clinical accuracy without touching UI code
  - Reuse logic in other applications (CLI, API, etc.)

#### **airtable_client.py** – Secure API Integration
- **Purpose**: Robust Airtable communication
- **Key Features**:
  - Rate limit management (respects Airtable's 5 req/sec limit)
  - Automatic retry with exponential backoff
  - Detailed error classification & messages
  - Connection pooling and timeout handling
  - Batch operations for bulk record creation
- **Why It Matters**: Production-grade API communication that won't crash on rate limits or network issues

#### **validators.py** – Quality Control Layer
- **Purpose**: Ensures cases are clinically complete before export
- **Key Features**:
  - Required field validation
  - Clinical appropriateness checks
  - State progression validation (5-state branching)
  - Vital sign bounds checking
  - Actionable error messages with suggestions
- **Why It Matters**: Prevents garbage cases from being exported. Acts as a QC filter.

#### **utils.py** – Shared Utilities
- **Purpose**: Common helper functions
- **Key Features**:
  - Data formatting & cleaning
  - JSON parsing with error recovery
  - Credential validation
  - Export metadata generation

---

## ✨ Key Enterprise Improvements

### 1. **Robust State Management**
```python
# Before: Data gets lost on rerun
if submitted:
    case_data = generate_case(...)
    # If user clicks button again, case_data is gone!

# After: State persists
state_mgr.set_case_data(case_data)
# Even after rerun, case_data is available:
case_data = state_mgr.get_case_data()
```

### 2. **Modular Logic Engine**
```python
# Before: Logic scattered across app.py (hundreds of lines)

# After: Clean separation
controller = MedicalLogicController(
    diagnosis="Sepsis",
    difficulty=Difficulty.ADVANCED,
    patient_age=65,
    patient_gender="Male"
)

# Get vital signs for any state
vitals = controller.get_initial_vital_signs()  # State 1
next_vitals = controller.get_next_state_vitals(1, vitals)  # State 2
```

### 3. **Error Handling for Airtable**
```python
# Before: Simple requests.post() with no error handling
air_res = requests.post(url, headers=headers, json=payload)
# If rate limited, the app crashes!

# After: Production-grade handling
client = AirtableClient(api_key, base_id)
response = client.create_record(table_name, fields)

if not response.success:
    if response.error_type == AirtableErrorType.RATE_LIMIT:
        print(f"Retry after {response.retry_after} seconds")
    else:
        handle_error(response.error_message)
```

### 4. **Validation Layer (The Game-Changer)**
```python
validator = CaseValidator()
is_valid, results = validator.validate_complete_case(case_data)

# Returns actionable feedback:
# ❌ "Missing required fields: critical_actions, debrief_questions"
# 💡 "Define at least 2 debrief questions for reflection"
```

### 5. **Professional UI Polish**
- **Header**: Clean, centered branding
- **Sidebar**: Intuitive "How to Use" guide + debug panel
- **Form**: Organized with `st.columns()` and professional labels
- **Validation Display**: Metrics cards showing validation stats
- **Progress Tracking**: Multi-stage progress bar (25% → 50% → 75% → 100%)
- **Export Options**: Three-column action bar (Word, Airtable, JSON)
- **Advanced Panel**: Tabbed debug interface for developers

---

## 🚀 Usage Guide

### Installation

1. **Clone and navigate**:
   ```bash
   cd sim-case-builder
   ```

2. **Create environment file** (from template):
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**:
   ```bash
   streamlit run app.py
   ```

### Configuration

Edit `.env` with your credentials:
```ini
GEMINI_API_KEY=your_gemini_key_here
AIRTABLE_API_KEY=your_pat_here
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
AIRTABLE_TABLE_NAME=Cases
```

### Workflow

1. **Configure** case parameters (diagnosis, age, difficulty, learner level)
2. **Generate** AI-powered scenario with Gemini API
3. **Validate** clinical completeness automatically
4. **Export** to Word document, JSON, or Airtable

---

## 🎯 Talking Points for Presentation

### For the Sim Center Director

1. **"Decoupled Logic" (The Engineering Selling Point)**
   - Medical rules are isolated in `logic_controller.py`
   - Easy to add new diagnoses without touching UI code
   - Clinical team can review/audit rules independently
   - Show them: `logic_controller.py` → `VITAL_SIGN_DEGRADATION` dictionary

2. **"Quality Control Filter" (The Patient Safety Angle)**
   - Validation layer ensures no "broken" cases are exported
   - Checks for: required fields, state progression, clinical bounds
   - Actionable error messages guide instructors to fix issues
   - Show them: validation results with ✓✓✓ and ❌ metrics

3. **"Enterprise-Grade Reliability" (The Operations Angle)**
   - Rate limiting prevents API crashdowns
   - Automatic retry logic on Airtable failures
   - Session state ensures no data loss on rerun
   - Detailed error logging for troubleshooting
   - Show them: the `RateLimiter` class and error types

4. **"Professional UX" (The User Experience Angle)**
   - Clean, modern interface (not amateur)
   - Guided workflow with progress tracking
   - Helpful sidebar with instructions
   - Debug panel for advanced users
   - Show them the polished form layout and export buttons

### For Medical Faculty

- "The AI respects your clinical expertise" - show the 5-state branching logic
- "Repeatable scenarios" - same diagnosis + difficulty = consistent cases
- "Customizable difficulty" - Basic → Nightmare with multiplier logic
- "Comprehensive validation" - ensures pedagogical completeness

### For IT/Deployment

- "Stateless except where needed" - Streamlit handles UI threading
- "Logging framework in place" - easy to integrate with monitoring
- "No hardcoded secrets" - uses environment variables
- "Modular design" - easy to refactor or extend

---

## 📊 File Structure

```
sim-case-builder/
├── app.py                              # Main Streamlit app
├── state_manager.py                    # Session state handling
├── logic_controller.py                 # Medical branching engine
├── airtable_client.py                  # Airtable API wrapper
├── validators.py                       # Case validation engine
├── utils.py                            # Shared utilities
├── requirements.txt                    # Dependencies
├── .env.example                        # Environment template
├── .env                                # (Your secrets - never commit!)
├── Simulation Case Template_2025.docx  # Word template
└── README.md                           # This file
```

---

## 🔒 Security Best Practices

✅ **What We Did Right**:
- API keys stored in `.env` (never hardcoded)
- Credential validation before API calls
- Safe API key display in logs (masked)
- Rate limiting to prevent abuse
- Input validation on all user inputs

⚠️ **Remember**:
- Never commit `.env` to git
- Add `.env` to `.gitignore`
- Regenerate Airtable PAT if exposed
- Use environment-specific Gemini keys (dev vs. prod)

---

## 🧪 Testing & Validation

### Manual Testing Steps

1. **Test state management**:
   - Remove custom focus, hit generate → case should still be created
   - Refresh page → case data should persist
   - Click "Generate" again → state should transition correctly

2. **Test validation layer**:
   - Generate a case → look at validation report
   - Should show errors (if any) and suggestions
   - Try with "Nightmare" difficulty → should have more critical findings

3. **Test Airtable sync**:
   - Generate case and click "Sync to Airtable"
   - Should see success message with record ID
   - Check Airtable base to verify record created

4. **Test Word export**:
   - Generate case → click "Download Word Document"
   - Open in Word, check that all fields populated
   - Verify case progression flows logically

---

## 🔧 Extending the System

### Adding a New Diagnosis

In `logic_controller.py`:

```python
def get_initial_vital_signs(self) -> VitalSigns:
    vital_presets = {
        "Sepsis": VitalSigns(...),
        # Add your diagnosis here:
        "Meningitis": VitalSigns(
            heart_rate=105,
            systolic_bp=110,
            # ... other vitals
        )
    }
```

### Adding a New Intervention Pathway

In `logic_controller.py`:

```python
class Intervention(Enum):
    IV_ACCESS = "IV Access"
    ANTIBIOTICS = "Antibiotics"
    # Add your intervention:
    SPINAL_TAP = "Lumbar Puncture"
```

### Custom Validation Rules

In `validators.py`:

```python
def _validate_custom_rules(self, case_data):
    # Add your medical/pedagogical rules here
    pass
```

---

## 📈 Performance & Optimization

- **Caching**: State manager is cached as `@st.cache_resource`
- **Rate Limiting**: Built-in token bucket rate limiter (4 req/sec)
- **Batch Operations**: Airtable client supports batch creation
- **Lazy Loading**: Templates only loaded on export

---

## 🐛 Debugging

### Enable Debug Mode

Look in sidebar → "Debug Information":
- Current UI stage
- Case loaded status
- Fields in memory

### View Generation Log

In advanced panel → "Generation Log" tab:
- Timestamps and event descriptions
- Track state transitions
- Identify where failures occur

### Check Validation Log

In advanced panel → "Validation Log" tab:
- All validation checks executed
- Severity levels (error, warning, info)
- Suggested fixes

---

## 📝 PEP 8 Compliance

- Type hints on all functions ✓
- Docstrings on all classes & public methods ✓
- 100-char line limit with rare exceptions ✓
- Clear naming conventions ✓
- No magic numbers (use enums/constants) ✓

---

## 🎓 Suggested Demo Script for Presentation

**"Imagine we're the Sim Center Director..."**

1. Show the form (polished, not amateur)
2. Fill in parameters (Sepsis, 72yo, Intermediate)
3. Hit generate (show progress bar: 25% → 50% → 75%)
4. Point out validation report: "The system caught that we need debrief questions"
5. Show the case summary
6. Click "Sync to Airtable" → show success message
7. Open Airtable to show the record imported live
8. Click the advanced panel to show the full JSON and generation log

**"Notice: No errors, no rate limits, clean UI. This is enterprise-grade."**

---

## 📞 Support & Questions

For implementation questions, refer to module docstrings. Each class has detailed documentation.

---

## 📄 License & Attribution

Built for University of Kentucky Sim Center | 2026

---

**Ready for production. Let's build better simulations.** 🏥
# Sim-case-builder-2

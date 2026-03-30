#!/usr/bin/env python3
"""
Build expanded diagnosis_data.json with 60+ diagnoses.

Run once:  python3 build_registry.py
Reads existing file, merges new diagnoses, writes back.
Delete this script after use if desired.
"""
import json, copy
from pathlib import Path

OUTPUT = Path(__file__).parent / "diagnosis_data.json"

# ── helpers ──────────────────────────────────────────────────────────────────
def dx(category, organ, vitals, modifiers, weights, pe, thresholds,
       labs, interventions, time_critical, comorbidity_mods=None):
    return {
        "category": category,
        "organ_system": organ,
        "vitals": vitals,
        "vital_modifiers": modifiers,
        "vital_severity_weights": weights,
        "pe_findings": pe,
        "critical_pe_thresholds": thresholds,
        "expected_labs": labs,
        "required_interventions": interventions,
        "time_critical_actions": time_critical,
        "comorbidity_modifiers": comorbidity_mods or {}
    }

def v(hr, sbp, dbp, rr, temp, spo2):
    return {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
            "respiratory_rate": rr, "temperature_f": temp, "o2_saturation": spo2}

STD_MOD = {"heart_rate": "multiply", "systolic_bp": "decrease", "diastolic_bp": "decrease",
           "respiratory_rate": "multiply", "temperature_f": "fixed", "o2_saturation": "decrease"}
FIXED_TEMP_MOD = dict(STD_MOD)

INV_HR_MOD = {**STD_MOD, "heart_rate": "inverse"}

def lab(mn, mx, unit, direction):
    return {"min": mn, "max": mx, "unit": unit, "direction": direction}

def tc(window, rationale):
    return {"window_minutes": window, "rationale": rationale}

# ── NEW DIAGNOSES ────────────────────────────────────────────────────────────
NEW = {}

# ═══════════════════════════════════════════════════════════════════════
# CARDIOVASCULAR
# ═══════════════════════════════════════════════════════════════════════

NEW["Aortic Dissection"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(105, 185, 105, 20, 98.6, 96),
    {**STD_MOD, "systolic_bp": "multiply"},  # hypertensive crisis
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 2},
    "Severe tearing chest/back pain, blood pressure differential between arms, wide mediastinum on CXR, diaphoresis",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"hgb": lab(8, 14, "g/dL", "variable"), "cr": lab(0.8, 3.0, "mg/dL", "variable"),
     "lactate": lab(1.0, 6.0, "mmol/L", "elevated"), "troponin": lab(0, 0.5, "ng/mL", "variable"),
     "d_dimer": lab(500, 20000, "ng/mL", "elevated")},
    ["IV Access", "Continuous Monitoring", "Oxygen Therapy"],
    {"Blood Pressure Control": tc(30, "Target SBP 100-120 to prevent propagation; IV esmolol or nitroprusside"),
     "CT Angiography": tc(30, "Emergent imaging to classify Stanford type A vs B"),
     "Surgical Consult": tc(60, "Type A requires emergent surgical repair")},
    {"Marfan Syndrome": {"aortic_root_dilation": True},
     "Cocaine Use": {"heart_rate": {"min": 120, "max": 160}}}
)

NEW["Cardiac Tamponade"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(120, 85, 60, 22, 98.6, 94),
    STD_MOD,
    {"systolic_bp": 20, "diastolic_bp": 15, "o2_saturation": 3},
    "Beck triad: hypotension, JVD, muffled heart sounds; pulsus paradoxus >10 mmHg; tachycardia",
    {"o2_saturation_below": 88, "systolic_bp_below": 70},
    {"hgb": lab(8, 14, "g/dL", "variable"), "troponin": lab(0, 1.0, "ng/mL", "variable"),
     "bnp": lab(50, 500, "pg/mL", "variable"), "lactate": lab(1.5, 6.0, "mmol/L", "elevated")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Pericardiocentesis": tc(30, "Emergent drainage if hemodynamically unstable"),
     "Bedside Echo": tc(10, "POCUS to confirm pericardial effusion and RV collapse"),
     "IV Fluid Bolus": tc(15, "Temporizing measure to increase preload")},
)

NEW["Atrial Fibrillation with RVR"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(155, 105, 65, 20, 98.6, 96),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 15, "systolic_bp": 10, "o2_saturation": 2},
    "Irregularly irregular rhythm, tachycardia, possible dyspnea, palpitations, mild diaphoresis",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"tsh": lab(0.1, 5.0, "mIU/L", "variable"), "bnp": lab(50, 600, "pg/mL", "elevated"),
     "k": lab(3.0, 5.5, "mEq/L", "variable"), "mg": lab(1.2, 2.5, "mg/dL", "variable"),
     "troponin": lab(0, 0.1, "ng/mL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"Rate Control": tc(30, "IV diltiazem or metoprolol to target HR <110"),
     "12-Lead ECG": tc(10, "Confirm AFib, rule out STEMI or WPW")},
    {"CHF": {"bnp": {"min": 300, "max": 2000}},
     "Hyperthyroidism": {"tsh": {"min": 0.01, "max": 0.1}}}
)

NEW["SVT"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(185, 100, 60, 20, 98.6, 97),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 10, "systolic_bp": 12, "o2_saturation": 1},
    "Regular narrow-complex tachycardia, palpitations, lightheadedness, anxiety, mild diaphoresis",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"troponin": lab(0, 0.04, "ng/mL", "normal"), "k": lab(3.5, 5.0, "mEq/L", "normal"),
     "mg": lab(1.5, 2.5, "mg/dL", "normal"), "tsh": lab(0.4, 4.0, "mIU/L", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"Vagal Maneuvers": tc(5, "First-line: modified Valsalva or carotid massage"),
     "Adenosine": tc(15, "6mg rapid IV push if vagal maneuvers fail; may repeat 12mg"),
     "Synchronized Cardioversion": tc(30, "If hemodynamically unstable")},
)

NEW["Hypertensive Emergency"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(100, 220, 130, 18, 98.6, 97),
    {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"systolic_bp": 10, "diastolic_bp": 8, "o2_saturation": 1},
    "Severe headache, visual changes, chest pain, possible papilledema, AMS, epistaxis",
    {"o2_saturation_below": 90, "systolic_bp_below": 90},
    {"cr": lab(1.0, 4.0, "mg/dL", "elevated"), "troponin": lab(0, 0.5, "ng/mL", "variable"),
     "bnp": lab(50, 1500, "pg/mL", "elevated"), "ua_prot": lab(0, 1, "scale", "elevated"),
     "lactate": lab(1.0, 4.0, "mmol/L", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Antihypertensive": tc(30, "Nicardipine or clevidipine drip; reduce MAP by 20-25% in first hour"),
     "Target Organ Assessment": tc(30, "CT head, ECG, renal function — identify end-organ damage"),
     "Arterial Line": tc(60, "Continuous BP monitoring for titration")},
    {"CKD": {"cr": {"min": 2.5, "max": 8.0}},
     "Pheochromocytoma": {"heart_rate": {"min": 120, "max": 160}}}
)

NEW["Third-Degree Heart Block"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(35, 80, 50, 16, 98.6, 95),
    INV_HR_MOD,
    {"heart_rate": 8, "systolic_bp": 18, "o2_saturation": 3},
    "Bradycardia, syncope or near-syncope, cannon A waves on JVP, hypotension, fatigue",
    {"o2_saturation_below": 88, "systolic_bp_below": 70},
    {"troponin": lab(0, 2.0, "ng/mL", "variable"), "k": lab(3.5, 6.5, "mEq/L", "variable"),
     "cr": lab(0.8, 2.0, "mg/dL", "variable"), "tsh": lab(0.4, 10, "mIU/L", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"Transcutaneous Pacing": tc(10, "Immediate if symptomatic; capture at lowest mA"),
     "Atropine": tc(5, "0.5mg IV q3-5min; may be ineffective in infranodal block"),
     "Transvenous Pacing": tc(60, "Definitive temporary pacing if TCP ineffective")},
)

NEW["Cardiogenic Shock"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(120, 75, 50, 24, 98.0, 89),
    STD_MOD,
    {"systolic_bp": 20, "diastolic_bp": 15, "o2_saturation": 5},
    "Cool, clammy extremities, JVD, pulmonary crackles, S3 gallop, altered mental status, oliguria",
    {"o2_saturation_below": 85, "systolic_bp_below": 70},
    {"troponin": lab(0.5, 20, "ng/mL", "elevated"), "bnp": lab(500, 5000, "pg/mL", "elevated"),
     "lactate": lab(3.0, 12.0, "mmol/L", "elevated"), "cr": lab(1.5, 5.0, "mg/dL", "elevated"),
     "ast": lab(40, 500, "U/L", "elevated"), "alt": lab(30, 400, "U/L", "elevated")},
    ["IV Access", "Vasopressors", "Oxygen Therapy", "Continuous Monitoring"],
    {"Vasopressor Initiation": tc(15, "Norepinephrine first-line per SOAP II trial"),
     "Bedside Echo": tc(15, "Assess EF, wall motion, valvular pathology"),
     "Mechanical Support Eval": tc(60, "Consider IABP, Impella, or ECMO if refractory")},
    {"CKD": {"cr": {"min": 3.0, "max": 8.0}}}
)

NEW["Unstable Angina"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(88, 150, 90, 18, 98.6, 97),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 2},
    "Substernal chest pressure, diaphoresis, radiating to left arm/jaw, mild dyspnea, anxious",
    {"o2_saturation_below": 90, "systolic_bp_below": 85},
    {"troponin": lab(0, 0.04, "ng/mL", "normal"), "bnp": lab(20, 200, "pg/mL", "normal"),
     "cr": lab(0.6, 1.4, "mg/dL", "normal"), "glu": lab(80, 200, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Look for ST depression, T-wave inversions"),
     "Aspirin + Heparin": tc(15, "Dual antiplatelet + anticoagulation per ACS protocol"),
     "Nitroglycerin": tc(10, "SL NTG for symptom relief; avoid if RV infarct or PDE5 inhibitor use")},
)

# ═══════════════════════════════════════════════════════════════════════
# RESPIRATORY
# ═══════════════════════════════════════════════════════════════════════

NEW["COPD Exacerbation"] = dx(
    "Respiratory", "Pulmonary",
    v(105, 140, 85, 26, 99.0, 86),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 5},
    "Barrel chest, pursed-lip breathing, prolonged expiratory phase, diffuse wheezes and rhonchi, accessory muscle use, tripod positioning",
    {"o2_saturation_below": 85, "systolic_bp_below": 85},
    {"wbc": lab(10, 20, "K/uL", "elevated"), "hco3": lab(28, 40, "mEq/L", "elevated"),
     "vbg_ph": lab(7.25, 7.38, "pH", "decreased"), "vbg_pco2": lab(50, 80, "mmHg", "elevated"),
     "bnp": lab(20, 200, "pg/mL", "normal")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"Bronchodilators": tc(15, "Continuous albuterol + ipratropium nebulization"),
     "Systemic Steroids": tc(60, "Prednisone 40mg or methylprednisolone 125mg IV"),
     "BiPAP": tc(30, "Non-invasive ventilation if persistent hypercapnia; avoid over-oxygenation")},
    {"CHF": {"bnp": {"min": 200, "max": 1500}},
     "OSA": {"vbg_pco2": {"min": 55, "max": 90}}}
)

NEW["Epiglottitis"] = dx(
    "Respiratory", "ENT/Airway",
    v(115, 130, 80, 24, 102.0, 92),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 4},
    "Tripod positioning, drooling, muffled hot-potato voice, stridor, sore throat, toxic appearance, trismus",
    {"o2_saturation_below": 88, "systolic_bp_below": 85},
    {"wbc": lab(14, 25, "K/uL", "elevated"), "lactate": lab(1.0, 4.0, "mmol/L", "elevated"),
     "cr": lab(0.6, 1.2, "mg/dL", "normal")},
    ["IV Access", "Oxygen Therapy", "Antibiotics"],
    {"Airway Assessment": tc(10, "Do NOT examine pharynx unless prepared for emergent airway"),
     "ENT/Anesthesia Consult": tc(15, "Double setup: OR for awake fiberoptic + surgical airway backup"),
     "IV Antibiotics": tc(30, "Ceftriaxone + steroids (dexamethasone)")},
)

NEW["Croup"] = dx(
    "Respiratory", "ENT/Airway",
    v(130, 95, 60, 30, 100.5, 93),
    {**STD_MOD, "heart_rate": "multiply", "respiratory_rate": "multiply"},
    {"systolic_bp": 5, "diastolic_bp": 3, "o2_saturation": 4},
    "Barking seal-like cough, inspiratory stridor, hoarse voice, steeple sign on AP neck X-ray, intercostal retractions",
    {"o2_saturation_below": 88, "systolic_bp_below": 70},
    {"wbc": lab(8, 18, "K/uL", "variable"), "cr": lab(0.2, 0.8, "mg/dL", "normal")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"Nebulized Epinephrine": tc(15, "Racemic epinephrine for moderate-severe croup; observe 2-4h for rebound"),
     "Dexamethasone": tc(30, "0.6 mg/kg PO/IM single dose; effective within 1 hour"),
     "Airway Monitoring": tc(5, "Continuous SpO2 and work of breathing assessment")},
)

NEW["ARDS"] = dx(
    "Respiratory", "Pulmonary",
    v(118, 95, 58, 32, 100.5, 78),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 8},
    "Severe dyspnea, diffuse bilateral crackles, cyanosis, accessory muscle use, diaphoresis, bilateral infiltrates on CXR",
    {"o2_saturation_below": 80, "systolic_bp_below": 80},
    {"vbg_ph": lab(7.20, 7.35, "pH", "decreased"), "vbg_pco2": lab(35, 60, "mmHg", "variable"),
     "lactate": lab(2.0, 8.0, "mmol/L", "elevated"), "wbc": lab(10, 30, "K/uL", "elevated"),
     "cr": lab(0.8, 3.0, "mg/dL", "elevated"), "plt": lab(80, 200, "K/uL", "variable")},
    ["IV Access", "Oxygen Therapy", "Intubation", "Continuous Monitoring"],
    {"Intubation": tc(30, "Low tidal volume ventilation 6 mL/kg IBW per ARDSNet protocol"),
     "PEEP Optimization": tc(60, "Titrate PEEP to optimize recruitment; target PaO2/FiO2 >150"),
     "Prone Positioning": tc(120, "For P/F ratio <150; 16+ hours prone per PROSEVA trial")},
    {"Sepsis": {"wbc": {"min": 15, "max": 35}, "lactate": {"min": 3.0, "max": 10.0}}}
)

NEW["Foreign Body Aspiration"] = dx(
    "Respiratory", "ENT/Airway",
    v(120, 130, 80, 28, 98.6, 88),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 6},
    "Acute onset choking, stridor or wheezing, unilateral decreased breath sounds, cyanosis, agitation, inability to speak if complete obstruction",
    {"o2_saturation_below": 85, "systolic_bp_below": 80},
    {"wbc": lab(6, 12, "K/uL", "normal"), "cr": lab(0.6, 1.2, "mg/dL", "normal")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"BLS Airway Maneuvers": tc(2, "Back blows/abdominal thrusts for complete obstruction"),
     "Direct Laryngoscopy": tc(10, "Attempt visualization and removal with Magill forceps"),
     "Surgical Airway": tc(15, "Cricothyrotomy if cannot intubate/cannot oxygenate")},
)

NEW["Smoke Inhalation"] = dx(
    "Respiratory", "Pulmonary",
    v(115, 110, 70, 26, 99.0, 90),
    STD_MOD,
    {"systolic_bp": 12, "diastolic_bp": 8, "o2_saturation": 5},
    "Carbonaceous sputum, singed nasal hairs, hoarse voice, stridor, facial burns, soot in oropharynx, tachypnea",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"co_hgb": lab(10, 50, "%", "elevated"), "lactate": lab(2.0, 10.0, "mmol/L", "elevated"),
     "vbg_ph": lab(7.20, 7.38, "pH", "decreased"), "k": lab(3.5, 6.0, "mEq/L", "variable"),
     "wbc": lab(10, 22, "K/uL", "elevated")},
    ["Oxygen Therapy", "IV Access", "Continuous Monitoring"],
    {"100% O2 via NRB": tc(5, "High-flow O2 immediately; SpO2 unreliable with CO poisoning"),
     "Early Intubation": tc(30, "Intubate before airway edema progresses; direct visualization"),
     "Cyanide Antidote": tc(30, "Hydroxocobalamin if altered mental status with lactic acidosis")},
)

# ═══════════════════════════════════════════════════════════════════════
# NEUROLOGICAL
# ═══════════════════════════════════════════════════════════════════════

NEW["Status Epilepticus"] = dx(
    "Neurological", "Neurological",
    v(130, 170, 100, 24, 101.0, 90),
    {**STD_MOD, "heart_rate": "multiply", "systolic_bp": "multiply"},
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 4},
    "Continuous or recurrent seizures >5 min, tonic-clonic activity, cyanosis, incontinence, foaming at mouth, tongue laceration",
    {"o2_saturation_below": 85, "systolic_bp_below": 80},
    {"glu": lab(60, 300, "mg/dL", "variable"), "k": lab(3.0, 6.0, "mEq/L", "variable"),
     "na": lab(120, 148, "mEq/L", "variable"), "lactate": lab(2.0, 10.0, "mmol/L", "elevated"),
     "wbc": lab(8, 20, "K/uL", "elevated"), "ck": lab(200, 10000, "U/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Benzodiazepine": tc(5, "Lorazepam 0.1mg/kg IV (max 4mg) or midazolam 10mg IM; repeat once if needed"),
     "Second-line AED": tc(20, "Levetiracetam 60mg/kg, fosphenytoin 20mg PE/kg, or valproate 40mg/kg IV"),
     "Glucose Check": tc(5, "Immediate POC glucose; D50 if hypoglycemic")},
    {"Alcohol Use": {"glu": {"min": 40, "max": 80}, "mg": {"min": 0.8, "max": 1.5}}}
)

NEW["Subarachnoid Hemorrhage"] = dx(
    "Neurological", "Neurological",
    v(95, 180, 100, 18, 98.6, 97),
    {**STD_MOD, "systolic_bp": "multiply"},
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 2},
    "Thunderclap headache (worst of life), nuchal rigidity, photophobia, possible decreased consciousness, focal neuro deficits, nausea/vomiting",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"wbc": lab(8, 18, "K/uL", "variable"), "glu": lab(100, 250, "mg/dL", "elevated"),
     "na": lab(130, 148, "mEq/L", "variable"), "troponin": lab(0, 1.0, "ng/mL", "variable"),
     "pt_inr": lab(0.9, 1.3, "INR", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Head": tc(25, "Non-contrast CT; sensitivity >95% within 6 hours of onset"),
     "BP Control": tc(30, "Target SBP <160 until aneurysm secured; nicardipine or labetalol"),
     "Neurosurgery Consult": tc(60, "Emergent for aneurysm clipping or endovascular coiling"),
     "Lumbar Puncture": tc(120, "If CT negative but clinical suspicion high; look for xanthochromia")},
)

NEW["Spinal Cord Injury"] = dx(
    "Neurological", "Neurological/MSK",
    v(60, 80, 50, 14, 96.5, 95),
    {**STD_MOD, "heart_rate": "inverse", "temperature_f": "fixed"},
    {"heart_rate": 10, "systolic_bp": 20, "o2_saturation": 3},
    "Neurogenic shock: bradycardia + hypotension + warm extremities; sensory level deficit, flaccid paralysis below level, priapism, loss of rectal tone",
    {"o2_saturation_below": 88, "systolic_bp_below": 70},
    {"hgb": lab(10, 16, "g/dL", "normal"), "lactate": lab(1.0, 4.0, "mmol/L", "variable"),
     "cr": lab(0.6, 1.4, "mg/dL", "normal")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"C-Spine Immobilization": tc(1, "Immediate inline stabilization; logroll precautions"),
     "MAP Target": tc(30, "Maintain MAP >85 for 7 days per AANS guidelines; vasopressors PRN"),
     "MRI Spine": tc(120, "Urgent imaging to define level and extent of injury"),
     "Foley Catheter": tc(60, "Neurogenic bladder — prevent overdistension")},
)

NEW["Guillain-Barre Syndrome"] = dx(
    "Neurological", "Neurological",
    v(95, 130, 80, 18, 98.6, 96),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 3},
    "Ascending symmetric weakness, areflexia, paresthesias, possible facial diplegia, difficulty swallowing, autonomic instability (BP lability, tachycardia)",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"wbc": lab(5, 12, "K/uL", "normal"), "cr": lab(0.6, 1.2, "mg/dL", "normal"),
     "k": lab(3.5, 5.0, "mEq/L", "normal"), "ck": lab(50, 300, "U/L", "normal")},
    ["IV Access", "Continuous Monitoring", "Oxygen Therapy"],
    {"NIF/VC Monitoring": tc(30, "Negative inspiratory force and vital capacity q2-4h; intubate if NIF <-20 or VC <20mL/kg"),
     "IVIG or Plasmapheresis": tc(240, "Start within first 2 weeks of symptom onset; equally effective"),
     "DVT Prophylaxis": tc(120, "Immobilized patients at high risk; enoxaparin or SCDs")},
)

NEW["Increased ICP"] = dx(
    "Neurological", "Neurological",
    v(55, 180, 100, 10, 98.6, 96),
    {**STD_MOD, "heart_rate": "inverse", "respiratory_rate": "inverse", "systolic_bp": "multiply"},
    {"heart_rate": 10, "systolic_bp": 10, "respiratory_rate": 4, "o2_saturation": 3},
    "Cushing triad: hypertension + bradycardia + irregular respirations; altered consciousness, unilateral dilated pupil, papilledema, vomiting",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"na": lab(135, 155, "mEq/L", "variable"), "glu": lab(100, 250, "mg/dL", "elevated"),
     "pt_inr": lab(0.9, 1.5, "INR", "variable"), "wbc": lab(6, 18, "K/uL", "variable")},
    ["IV Access", "Continuous Monitoring", "Intubation"],
    {"HOB Elevation": tc(5, "Elevate head of bed 30 degrees; midline head position"),
     "Mannitol/Hypertonic Saline": tc(15, "Mannitol 1g/kg or 23.4% saline 30mL for acute herniation"),
     "CT Head": tc(25, "Emergent non-contrast CT to identify cause"),
     "Neurosurgery Consult": tc(30, "For EVD placement or surgical decompression")},
)

NEW["Epidural Hematoma"] = dx(
    "Neurological", "Neurological",
    v(60, 175, 95, 12, 98.6, 96),
    {**STD_MOD, "heart_rate": "inverse", "systolic_bp": "multiply"},
    {"heart_rate": 8, "systolic_bp": 10, "o2_saturation": 3},
    "Lucid interval followed by rapid decline, unilateral dilated pupil (ipsilateral), contralateral hemiparesis, temporal skull fracture, Cushing response",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"hgb": lab(10, 16, "g/dL", "normal"), "plt": lab(150, 400, "K/uL", "normal"),
     "pt_inr": lab(0.9, 1.3, "INR", "normal"), "na": lab(135, 148, "mEq/L", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Head": tc(15, "Emergent — classic biconvex (lens-shaped) hyperdensity"),
     "Neurosurgery Consult": tc(20, "Emergent craniotomy for evacuation"),
     "Mannitol": tc(15, "Temporizing if signs of herniation while awaiting OR")},
)

# ═══════════════════════════════════════════════════════════════════════
# GI / HEPATIC
# ═══════════════════════════════════════════════════════════════════════

NEW["Acute Pancreatitis"] = dx(
    "Gastrointestinal", "GI/Hepatobiliary",
    v(110, 105, 65, 20, 100.5, 96),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 2},
    "Epigastric pain radiating to back, tenderness with guarding, distended abdomen, tachycardia, possible Cullen or Grey Turner signs if hemorrhagic",
    {"o2_saturation_below": 90, "systolic_bp_below": 85},
    {"lipase": lab(200, 5000, "U/L", "elevated"), "wbc": lab(10, 22, "K/uL", "elevated"),
     "glu": lab(100, 350, "mg/dL", "elevated"), "ca": lab(6.5, 9.0, "mg/dL", "decreased"),
     "bun": lab(15, 40, "mg/dL", "elevated"), "ast": lab(30, 300, "U/L", "elevated"),
     "alt": lab(25, 250, "U/L", "elevated"), "lactate": lab(1.0, 4.0, "mmol/L", "elevated")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Aggressive IV Fluids": tc(60, "Lactated Ringers 200-500mL/hr initially per ACG guidelines"),
     "Pain Management": tc(30, "IV hydromorphone or morphine; NSAIDs adjunct"),
     "NPO": tc(15, "Nothing by mouth until pain improving; advance diet cautiously")},
    {"Alcohol Use": {"glu": {"min": 80, "max": 200}},
     "Gallstones": {"ast": {"min": 100, "max": 500}, "alt": {"min": 80, "max": 400}}}
)

NEW["Bowel Obstruction"] = dx(
    "Gastrointestinal", "GI",
    v(108, 100, 60, 20, 99.5, 97),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 1},
    "Distended abdomen, high-pitched tinkling bowel sounds (early) or absent (late), diffuse tenderness, vomiting (bilious or feculent), inability to pass flatus",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"wbc": lab(8, 22, "K/uL", "variable"), "lactate": lab(1.0, 6.0, "mmol/L", "elevated"),
     "bun": lab(15, 45, "mg/dL", "elevated"), "cr": lab(0.8, 3.0, "mg/dL", "elevated"),
     "k": lab(2.8, 5.5, "mEq/L", "variable"), "hco3": lab(18, 28, "mEq/L", "variable")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"NGT Decompression": tc(30, "NG tube to low intermittent suction"),
     "CT Abdomen/Pelvis": tc(60, "IV contrast to evaluate transition point and identify strangulation"),
     "Surgery Consult": tc(120, "Emergent if signs of strangulation, perforation, or closed-loop")},
)

NEW["Appendicitis"] = dx(
    "Gastrointestinal", "GI",
    v(100, 120, 75, 18, 100.8, 98),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 1},
    "RLQ tenderness at McBurney point, positive Rovsing sign, rebound tenderness, guarding, anorexia, nausea, migration of pain from periumbilical to RLQ",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"wbc": lab(11, 20, "K/uL", "elevated"), "cr": lab(0.6, 1.2, "mg/dL", "normal"),
     "lipase": lab(10, 60, "U/L", "normal"), "ua_wbc": lab(0, 5, "/HPF", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Abdomen/Pelvis": tc(60, "IV contrast; sensitivity >95% for appendicitis"),
     "Surgery Consult": tc(120, "Appendectomy within 24 hours; emergent if perforation suspected"),
     "IV Antibiotics": tc(60, "Cefoxitin or pip-tazo if perforated; pre-op coverage")},
)

NEW["Cholecystitis"] = dx(
    "Gastrointestinal", "GI/Hepatobiliary",
    v(100, 130, 80, 18, 101.0, 98),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 1},
    "RUQ tenderness, positive Murphy sign, guarding, fever, nausea/vomiting, pain radiating to right scapula",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"wbc": lab(11, 22, "K/uL", "elevated"), "ast": lab(20, 200, "U/L", "elevated"),
     "alt": lab(20, 200, "U/L", "elevated"), "alk_phos": lab(80, 400, "U/L", "elevated"),
     "t_bili": lab(1.0, 5.0, "mg/dL", "elevated"), "lipase": lab(10, 100, "U/L", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"RUQ Ultrasound": tc(60, "Gallstones, wall thickening >4mm, pericholecystic fluid, sonographic Murphy"),
     "IV Antibiotics": tc(60, "Cefoxitin or pip-tazo for infectious cholecystitis"),
     "Surgery Consult": tc(120, "Cholecystectomy within 72 hours per Tokyo Guidelines")},
)

NEW["Hepatic Encephalopathy"] = dx(
    "Gastrointestinal", "GI/Hepatobiliary",
    v(90, 100, 60, 18, 98.6, 96),
    STD_MOD,
    {"systolic_bp": 12, "diastolic_bp": 8, "o2_saturation": 2},
    "Altered mental status, asterixis (flapping tremor), fetor hepaticus, jaundice, ascites, spider angiomata, palmar erythema, confusion",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"ammonia": lab(60, 200, "mcg/dL", "elevated"), "ast": lab(40, 300, "U/L", "elevated"),
     "alt": lab(30, 200, "U/L", "elevated"), "t_bili": lab(2.0, 15.0, "mg/dL", "elevated"),
     "alb": lab(1.5, 3.0, "g/dL", "decreased"), "pt_inr": lab(1.5, 4.0, "INR", "elevated"),
     "na": lab(125, 138, "mEq/L", "decreased"), "cr": lab(1.0, 4.0, "mg/dL", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"Lactulose": tc(30, "30mL PO/PR q1-2h until 3-4 BMs/day; first-line treatment"),
     "Rifaximin": tc(60, "550mg BID for secondary prophylaxis"),
     "Infection Workup": tc(60, "Precipitant search: SBP paracentesis, UA, CXR, blood cultures")},
    {"CKD": {"cr": {"min": 2.0, "max": 6.0}}}
)

NEW["Mesenteric Ischemia"] = dx(
    "Gastrointestinal", "GI/Vascular",
    v(115, 90, 55, 22, 99.5, 94),
    STD_MOD,
    {"systolic_bp": 18, "diastolic_bp": 12, "o2_saturation": 3},
    "Severe abdominal pain out of proportion to exam, abdominal distension, bloody stool (late), peritoneal signs (late), tachycardia",
    {"o2_saturation_below": 88, "systolic_bp_below": 75},
    {"lactate": lab(3.0, 15.0, "mmol/L", "elevated"), "wbc": lab(14, 30, "K/uL", "elevated"),
     "hco3": lab(12, 22, "mEq/L", "decreased"), "vbg_ph": lab(7.15, 7.35, "pH", "decreased"),
     "d_dimer": lab(500, 10000, "ng/mL", "elevated"), "amylase": lab(100, 500, "U/L", "elevated")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"CT Angiography": tc(30, "Mesenteric CTA is gold standard for diagnosis"),
     "Vascular Surgery Consult": tc(60, "Emergent for embolectomy, bypass, or bowel resection"),
     "Broad-Spectrum Antibiotics": tc(60, "Gut flora coverage: pip-tazo or meropenem"),
     "Anticoagulation": tc(60, "Heparin drip for arterial embolism per AGA guidelines")},
    {"Atrial Fibrillation": {"risk": "arterial embolism source"}}
)

# ═══════════════════════════════════════════════════════════════════════
# RENAL / METABOLIC
# ═══════════════════════════════════════════════════════════════════════

NEW["Acute Kidney Injury"] = dx(
    "Renal", "Renal",
    v(95, 150, 90, 18, 98.6, 96),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 2},
    "Decreased urine output, peripheral edema, JVD if fluid overloaded, possible uremic frost, asterixis, nausea",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"cr": lab(2.0, 10.0, "mg/dL", "elevated"), "bun": lab(30, 120, "mg/dL", "elevated"),
     "k": lab(5.0, 7.5, "mEq/L", "elevated"), "hco3": lab(12, 22, "mEq/L", "decreased"),
     "phos": lab(4.5, 10.0, "mg/dL", "elevated"), "ca": lab(6.5, 9.0, "mg/dL", "decreased")},
    ["IV Access", "Continuous Monitoring"],
    {"Fluid Assessment": tc(30, "Volume status: hypovolemic→fluids, hypervolemic→diuretics/dialysis"),
     "ECG": tc(15, "Check for hyperkalemia changes (peaked T, wide QRS)"),
     "Nephrology Consult": tc(120, "For dialysis if refractory hyperkalemia, acidosis, fluid overload, or uremia"),
     "Foley Catheter": tc(30, "Rule out post-renal obstruction; monitor UOP")},
    {"Diabetes": {"glu": {"min": 100, "max": 300}},
     "CHF": {"bnp": {"min": 300, "max": 2000}}}
)

NEW["Hyponatremia"] = dx(
    "Metabolic", "Renal/Endocrine",
    v(85, 125, 78, 16, 98.6, 97),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 1},
    "Confusion, headache, nausea/vomiting, lethargy, seizures if severe (<120), cerebral edema signs, muscle weakness",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"na": lab(105, 129, "mEq/L", "decreased"), "serum_osm": lab(240, 275, "mOsm/kg", "decreased"),
     "urine_na": lab(10, 80, "mEq/L", "variable"), "cr": lab(0.6, 2.0, "mg/dL", "variable"),
     "k": lab(3.0, 5.0, "mEq/L", "variable"), "glu": lab(70, 140, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"Sodium Level": tc(15, "Confirm with repeat BMP; assess volume status and chronicity"),
     "Hypertonic Saline": tc(30, "3% NaCl 100mL bolus for severe symptoms (seizures, coma); max correction 8mEq/24h"),
     "Volume Assessment": tc(30, "Hypovolemic→NS, euvolemic→fluid restrict, hypervolemic→diuretics")},
    {"Cirrhosis": {"alb": {"min": 1.5, "max": 3.0}},
     "CHF": {"bnp": {"min": 200, "max": 1500}}}
)

NEW["Rhabdomyolysis"] = dx(
    "Metabolic", "Renal/MSK",
    v(105, 110, 70, 18, 100.0, 96),
    STD_MOD,
    {"systolic_bp": 12, "diastolic_bp": 8, "o2_saturation": 2},
    "Muscle pain and weakness, dark tea-colored urine, swollen tender muscles, possible compartment syndrome, tachycardia",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"ck": lab(5000, 200000, "U/L", "elevated"), "cr": lab(1.5, 8.0, "mg/dL", "elevated"),
     "k": lab(5.0, 7.5, "mEq/L", "elevated"), "ca": lab(6.0, 8.5, "mg/dL", "decreased"),
     "phos": lab(4.5, 10.0, "mg/dL", "elevated"), "uric_acid": lab(8.0, 20.0, "mg/dL", "elevated"),
     "ast": lab(100, 5000, "U/L", "elevated"), "bun": lab(20, 60, "mg/dL", "elevated")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Aggressive IV Fluids": tc(30, "NS 200-300mL/hr; target UOP 200-300mL/hr to prevent ATN"),
     "ECG": tc(15, "Urgent check for hyperkalemia-induced arrhythmia"),
     "Electrolyte Correction": tc(30, "Calcium gluconate if hyperkalemic; avoid calcium otherwise (risk of deposition)"),
     "Compartment Pressure": tc(60, "Check if clinical concern; fasciotomy if >30mmHg")},
)

NEW["Tumor Lysis Syndrome"] = dx(
    "Metabolic", "Hematologic/Renal",
    v(100, 105, 65, 20, 99.5, 96),
    STD_MOD,
    {"systolic_bp": 12, "diastolic_bp": 8, "o2_saturation": 2},
    "Nausea, vomiting, muscle cramps, tetany, seizures, arrhythmia, oliguria, lethargy",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"k": lab(5.5, 8.0, "mEq/L", "elevated"), "phos": lab(5.0, 15.0, "mg/dL", "elevated"),
     "ca": lab(5.0, 7.5, "mg/dL", "decreased"), "uric_acid": lab(10, 25, "mg/dL", "elevated"),
     "cr": lab(1.5, 8.0, "mg/dL", "elevated"), "ldh": lab(500, 5000, "U/L", "elevated"),
     "k": lab(5.5, 8.0, "mEq/L", "elevated")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Rasburicase": tc(60, "0.2mg/kg IV for severe hyperuricemia; contraindicated in G6PD deficiency"),
     "Aggressive IV Fluids": tc(30, "NS 200mL/hr; target UOP >2mL/kg/hr"),
     "ECG": tc(10, "Urgent for hyperkalemia assessment"),
     "Nephrology Consult": tc(120, "Emergent dialysis if refractory hyperkalemia or oliguric renal failure")},
)

NEW["Adrenal Crisis"] = dx(
    "Endocrine", "Endocrine",
    v(115, 75, 45, 22, 99.5, 95),
    STD_MOD,
    {"systolic_bp": 20, "diastolic_bp": 15, "o2_saturation": 2},
    "Refractory hypotension despite fluids, abdominal pain, nausea/vomiting, confusion, hyperpigmentation (if chronic), weakness, dehydration",
    {"o2_saturation_below": 90, "systolic_bp_below": 65},
    {"na": lab(118, 132, "mEq/L", "decreased"), "k": lab(5.0, 7.0, "mEq/L", "elevated"),
     "glu": lab(40, 70, "mg/dL", "decreased"), "ca": lab(8.0, 11.0, "mg/dL", "elevated"),
     "cortisol": lab(0, 3, "mcg/dL", "decreased"), "cr": lab(1.0, 3.0, "mg/dL", "elevated")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"IV Hydrocortisone": tc(15, "100mg IV push STAT; do not wait for cortisol results if clinically suspected"),
     "Aggressive IV Fluids": tc(30, "NS or D5NS 1-2L bolus; these patients are severely volume depleted"),
     "Dextrose": tc(15, "D50 if hypoglycemic; D5 maintenance after")},
)

NEW["HHS"] = dx(
    "Endocrine", "Endocrine",
    v(108, 95, 55, 20, 99.0, 95),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 2},
    "Profound dehydration, altered mental status, tachycardia, hypotension, warm dry skin, no Kussmaul respirations (unlike DKA), possible focal neuro deficits",
    {"o2_saturation_below": 90, "systolic_bp_below": 75},
    {"glu": lab(600, 1500, "mg/dL", "elevated"), "serum_osm": lab(320, 400, "mOsm/kg", "elevated"),
     "na": lab(130, 155, "mEq/L", "variable"), "bun": lab(30, 80, "mg/dL", "elevated"),
     "cr": lab(1.5, 5.0, "mg/dL", "elevated"), "hco3": lab(18, 28, "mEq/L", "normal"),
     "vbg_ph": lab(7.30, 7.45, "pH", "normal")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Aggressive IV Fluids": tc(60, "NS 1-1.5L/hr first hour; switch to 0.45% if corrected Na normal/elevated"),
     "Insulin Drip": tc(120, "Start AFTER adequate volume resuscitation; 0.1-0.14 units/kg/hr"),
     "Electrolyte Monitoring": tc(60, "K+ q1-2h; replace aggressively to maintain >3.5")},
    {"CKD": {"cr": {"min": 3.0, "max": 8.0}}}
)

NEW["Myxedema Coma"] = dx(
    "Endocrine", "Endocrine",
    v(48, 85, 55, 8, 94.5, 92),
    {**STD_MOD, "heart_rate": "inverse", "respiratory_rate": "inverse", "temperature_f": "fixed"},
    {"heart_rate": 8, "systolic_bp": 15, "respiratory_rate": 3, "o2_saturation": 4},
    "Hypothermia, bradycardia, altered mental status/coma, non-pitting edema (myxedema), macroglossia, delayed DTRs, hypoventilation",
    {"o2_saturation_below": 85, "systolic_bp_below": 70},
    {"tsh": lab(40, 200, "mIU/L", "elevated"), "t4": lab(0.1, 0.5, "mcg/dL", "decreased"),
     "na": lab(115, 130, "mEq/L", "decreased"), "glu": lab(40, 70, "mg/dL", "decreased"),
     "cortisol": lab(2, 15, "mcg/dL", "variable"), "ck": lab(500, 10000, "U/L", "elevated"),
     "hco3": lab(15, 22, "mEq/L", "decreased")},
    ["IV Access", "Continuous Monitoring", "Oxygen Therapy"],
    {"IV Levothyroxine": tc(60, "200-400mcg IV loading dose; consult endocrinology"),
     "IV Hydrocortisone": tc(60, "100mg IV before T4 — rule out concurrent adrenal insufficiency"),
     "Passive Rewarming": tc(30, "Warm blankets; active rewarming can cause cardiovascular collapse"),
     "Intubation": tc(30, "If GCS depressed or hypoventilation; these patients desaturate rapidly")},
)

# ═══════════════════════════════════════════════════════════════════════
# TRAUMA
# ═══════════════════════════════════════════════════════════════════════

NEW["Hemorrhagic Shock"] = dx(
    "Trauma", "Multi-system",
    v(130, 75, 45, 26, 97.0, 94),
    STD_MOD,
    {"systolic_bp": 22, "diastolic_bp": 15, "o2_saturation": 3},
    "Pale, cool, diaphoretic, tachycardic, hypotensive, altered mental status, weak thready pulse, delayed cap refill >3s, visible hemorrhage or distended abdomen",
    {"o2_saturation_below": 88, "systolic_bp_below": 65},
    {"hgb": lab(5, 10, "g/dL", "decreased"), "hct": lab(15, 30, "%", "decreased"),
     "lactate": lab(3.0, 10.0, "mmol/L", "elevated"), "plt": lab(60, 200, "K/uL", "variable"),
     "pt_inr": lab(1.0, 2.5, "INR", "elevated"), "hco3": lab(14, 22, "mEq/L", "decreased"),
     "ca": lab(6.5, 9.0, "mg/dL", "decreased")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring", "Oxygen Therapy"],
    {"Hemorrhage Control": tc(5, "Direct pressure, tourniquet, or surgical intervention"),
     "Massive Transfusion Protocol": tc(15, "Activate MTP; 1:1:1 ratio pRBC:FFP:platelets"),
     "Permissive Hypotension": tc(10, "Target SBP 80-90 until surgical control; avoid crystalloid overload"),
     "TXA": tc(180, "1g IV within 3 hours of injury per CRASH-2 trial; then 1g over 8h")},
)

NEW["Traumatic Brain Injury"] = dx(
    "Trauma", "Neurological",
    v(65, 175, 95, 14, 98.6, 96),
    {**STD_MOD, "heart_rate": "inverse", "systolic_bp": "multiply"},
    {"heart_rate": 10, "systolic_bp": 10, "o2_saturation": 3},
    "Altered consciousness, pupil asymmetry, GCS depression, scalp laceration/hematoma, Battle sign or raccoon eyes, CSF rhinorrhea/otorrhea, focal deficits",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"hgb": lab(10, 16, "g/dL", "normal"), "plt": lab(100, 400, "K/uL", "normal"),
     "pt_inr": lab(0.9, 1.5, "INR", "variable"), "na": lab(135, 148, "mEq/L", "normal"),
     "glu": lab(100, 250, "mg/dL", "elevated"), "lactate": lab(1.0, 4.0, "mmol/L", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"CT Head": tc(25, "Non-contrast CT STAT; identify bleeds, midline shift, fractures"),
     "ICP Management": tc(15, "HOB 30°, midline position, avoid hypotension (SBP >100) and hypoxia (SpO2 >92%)"),
     "Neurosurgery Consult": tc(30, "For surgical lesions: EDH, SDH with shift, depressed fractures"),
     "Seizure Prophylaxis": tc(60, "Levetiracetam 1g IV for 7 days per BTF guidelines")},
    {"Anticoagulation": {"pt_inr": {"min": 2.0, "max": 5.0}}}
)

NEW["Major Burns"] = dx(
    "Trauma", "Skin/Multi-system",
    v(125, 100, 60, 24, 99.0, 94),
    STD_MOD,
    {"systolic_bp": 18, "diastolic_bp": 12, "o2_saturation": 3},
    "Burn wound assessment (partial vs full thickness), pain, edema, erythema or white/charred tissue, circumferential burn concern, singed hair if inhalation",
    {"o2_saturation_below": 88, "systolic_bp_below": 75},
    {"hgb": lab(12, 20, "g/dL", "elevated"), "hct": lab(40, 55, "%", "elevated"),
     "k": lab(4.0, 7.0, "mEq/L", "elevated"), "lactate": lab(2.0, 8.0, "mmol/L", "elevated"),
     "alb": lab(1.5, 3.5, "g/dL", "decreased"), "cr": lab(0.8, 3.0, "mg/dL", "variable")},
    ["IV Access", "Fluid Resuscitation", "Oxygen Therapy", "Continuous Monitoring"],
    {"Parkland Formula Fluids": tc(30, "4mL x kg x %TBSA; give half in first 8h from time of burn"),
     "Airway Assessment": tc(15, "Early intubation if inhalation injury suspected — do not wait for edema"),
     "Escharotomy": tc(120, "For circumferential full-thickness burns compromising perfusion or ventilation"),
     "Tetanus Prophylaxis": tc(60, "Tdap if not current; TIG if unknown history")},
)

NEW["Pelvic Fracture"] = dx(
    "Trauma", "MSK/Vascular",
    v(125, 80, 50, 22, 98.0, 95),
    STD_MOD,
    {"systolic_bp": 20, "diastolic_bp": 15, "o2_saturation": 2},
    "Pelvic instability on compression, perineal ecchymosis, leg length discrepancy, blood at urethral meatus, hypotension despite fluids",
    {"o2_saturation_below": 88, "systolic_bp_below": 65},
    {"hgb": lab(6, 12, "g/dL", "decreased"), "lactate": lab(2.0, 8.0, "mmol/L", "elevated"),
     "pt_inr": lab(0.9, 2.0, "INR", "variable"), "cr": lab(0.6, 2.0, "mg/dL", "variable")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Pelvic Binder": tc(10, "Circumferential compression at level of greater trochanters"),
     "Massive Transfusion Protocol": tc(15, "Activate early; these fractures bleed significantly"),
     "CT Angiography": tc(60, "Identify arterial bleeding for IR embolization"),
     "Retrograde Urethrogram": tc(60, "Before Foley if blood at urethral meatus")},
)

# ═══════════════════════════════════════════════════════════════════════
# OB/GYN
# ═══════════════════════════════════════════════════════════════════════

NEW["Eclampsia"] = dx(
    "OB/GYN", "OB/Multi-system",
    v(110, 175, 110, 20, 98.6, 96),
    {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"systolic_bp": 10, "diastolic_bp": 8, "o2_saturation": 2},
    "Tonic-clonic seizures in pregnancy (>20wk), severe hypertension, headache, visual changes, RUQ pain, hyperreflexia with clonus, facial/peripheral edema",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"plt": lab(50, 150, "K/uL", "decreased"), "ast": lab(40, 500, "U/L", "elevated"),
     "alt": lab(35, 400, "U/L", "elevated"), "cr": lab(0.8, 3.0, "mg/dL", "elevated"),
     "ldh": lab(300, 1500, "U/L", "elevated"), "uric_acid": lab(6.0, 12.0, "mg/dL", "elevated"),
     "ua_prot": lab(1, 4, "scale", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"Magnesium Sulfate": tc(5, "4-6g IV loading over 20min then 1-2g/hr; first-line for seizure prevention and treatment"),
     "IV Antihypertensive": tc(15, "IV labetalol 20mg or hydralazine 5mg; target SBP <160, DBP <110"),
     "Delivery Planning": tc(60, "Definitive treatment is delivery; consult OB stat")},
)

NEW["Placental Abruption"] = dx(
    "OB/GYN", "OB/Hematologic",
    v(125, 85, 55, 22, 98.6, 95),
    STD_MOD,
    {"systolic_bp": 20, "diastolic_bp": 15, "o2_saturation": 2},
    "Vaginal bleeding (may be concealed), rigid board-like uterus, severe abdominal pain, fetal distress, signs of hypovolemic shock, DIC if severe",
    {"o2_saturation_below": 88, "systolic_bp_below": 70},
    {"hgb": lab(6, 11, "g/dL", "decreased"), "plt": lab(50, 150, "K/uL", "decreased"),
     "pt_inr": lab(1.0, 3.0, "INR", "elevated"), "fibrinogen": lab(100, 300, "mg/dL", "decreased"),
     "lactate": lab(2.0, 8.0, "mmol/L", "elevated"), "cr": lab(0.6, 2.0, "mg/dL", "variable")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring", "Oxygen Therapy"],
    {"Large-Bore IV x2": tc(5, "Two 16-18g IVs; anticipate massive hemorrhage"),
     "Type and Crossmatch": tc(15, "Order 4 units pRBCs immediately; activate MTP if severe"),
     "Fetal Monitoring": tc(10, "Continuous CTG; persistent late decels or bradycardia = emergent delivery"),
     "OB Consult": tc(10, "Emergent cesarean delivery if hemodynamically unstable or fetal distress")},
)

NEW["Postpartum Hemorrhage"] = dx(
    "OB/GYN", "OB/Hematologic",
    v(130, 80, 50, 24, 98.6, 94),
    STD_MOD,
    {"systolic_bp": 22, "diastolic_bp": 15, "o2_saturation": 3},
    "Excessive vaginal bleeding post-delivery, boggy uterus (if atony), tachycardia, hypotension, pallor, diaphoresis, altered mental status if severe",
    {"o2_saturation_below": 88, "systolic_bp_below": 65},
    {"hgb": lab(5, 10, "g/dL", "decreased"), "plt": lab(60, 200, "K/uL", "variable"),
     "pt_inr": lab(1.0, 2.5, "INR", "elevated"), "fibrinogen": lab(100, 300, "mg/dL", "decreased"),
     "lactate": lab(2.0, 8.0, "mmol/L", "elevated"), "ca": lab(7.0, 9.0, "mg/dL", "decreased")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Uterine Massage": tc(5, "Bimanual fundal massage for uterine atony — most common cause"),
     "Uterotonics": tc(10, "Oxytocin 40U in 1L NS, methylergonovine, carboprost, misoprostol"),
     "TXA": tc(30, "1g IV within 3 hours of delivery per WOMAN trial"),
     "Massive Transfusion Protocol": tc(15, "Activate if EBL >1500mL or hemodynamically unstable")},
)

NEW["Shoulder Dystocia"] = dx(
    "OB/GYN", "OB",
    v(105, 130, 80, 20, 98.6, 97),
    STD_MOD,
    {"systolic_bp": 5, "diastolic_bp": 3, "o2_saturation": 1},
    "Turtle sign (fetal head retracts against perineum), inability to deliver anterior shoulder with routine traction, maternal distress",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"hgb": lab(10, 14, "g/dL", "normal"), "glu": lab(80, 200, "mg/dL", "variable")},
    ["Continuous Monitoring"],
    {"McRoberts Maneuver": tc(1, "Sharply flex maternal thighs to abdomen; first-line intervention"),
     "Suprapubic Pressure": tc(1, "Continuous or rocking pressure above symphysis to dislodge shoulder"),
     "Rubin or Wood Screw": tc(3, "Internal rotation maneuvers if McRoberts + suprapubic fail"),
     "Deliver Posterior Arm": tc(5, "Sweep posterior arm across chest; last resort before Zavanelli")},
)

NEW["Ovarian Torsion"] = dx(
    "OB/GYN", "GYN",
    v(110, 125, 78, 18, 99.0, 98),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 1},
    "Sudden severe unilateral lower abdominal/pelvic pain, nausea/vomiting, adnexal tenderness, guarding, possible palpable mass",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"wbc": lab(8, 18, "K/uL", "variable"), "hcg": lab(0, 5, "mIU/mL", "normal"),
     "lactate": lab(1.0, 3.0, "mmol/L", "variable"), "cr": lab(0.6, 1.2, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"Pelvic Ultrasound": tc(30, "Doppler to assess ovarian blood flow; enlarged ovary with absent/decreased flow"),
     "GYN Consult": tc(60, "Emergent laparoscopy for detorsion; salvage ovary if viable"),
     "Pain Management": tc(15, "IV morphine or ketorolac; severe pain is the norm")},
)

# ═══════════════════════════════════════════════════════════════════════
# TOXICOLOGY (expanding the existing "Overdose")
# ═══════════════════════════════════════════════════════════════════════

NEW["Acetaminophen Overdose"] = dx(
    "Toxicology", "GI/Hepatobiliary",
    v(85, 120, 75, 16, 98.6, 98),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 1},
    "Initially asymptomatic or mild nausea/vomiting (phase 1), then RUQ pain and liver tenderness (phase 2), jaundice and coagulopathy (phase 3)",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"apap_level": lab(150, 500, "mcg/mL", "elevated"), "ast": lab(20, 10000, "U/L", "elevated"),
     "alt": lab(20, 10000, "U/L", "elevated"), "pt_inr": lab(1.0, 6.0, "INR", "elevated"),
     "t_bili": lab(0.5, 15.0, "mg/dL", "elevated"), "cr": lab(0.6, 4.0, "mg/dL", "elevated"),
     "lactate": lab(1.0, 10.0, "mmol/L", "elevated"), "vbg_ph": lab(7.15, 7.40, "pH", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"APAP Level": tc(60, "4-hour post-ingestion level; plot on Rumack-Matthew nomogram"),
     "NAC": tc(480, "N-acetylcysteine 150mg/kg IV over 1h, then 50mg/kg over 4h, then 100mg/kg over 16h; start if line above treatment threshold or unknown timing"),
     "Activated Charcoal": tc(60, "1g/kg PO if within 1-2 hours of ingestion and airway protected")},
)

NEW["Organophosphate Poisoning"] = dx(
    "Toxicology", "Neurological/Multi-system",
    v(55, 90, 55, 12, 98.6, 88),
    {**STD_MOD, "heart_rate": "inverse", "respiratory_rate": "inverse"},
    {"heart_rate": 10, "systolic_bp": 15, "respiratory_rate": 4, "o2_saturation": 5},
    "SLUDGE/DUMBELS: Salivation, Lacrimation, Urination, Defecation, GI distress, Emesis; miosis, bradycardia, bronchorrhea, bronchospasm, muscle fasciculations",
    {"o2_saturation_below": 85, "systolic_bp_below": 70},
    {"cholinesterase": lab(0, 50, "%", "decreased"), "wbc": lab(6, 15, "K/uL", "normal"),
     "glu": lab(80, 200, "mg/dL", "variable"), "k": lab(3.0, 5.5, "mEq/L", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Atropine": tc(5, "2mg IV q5min until secretions dry; may need large doses (10-20mg or more)"),
     "Pralidoxime": tc(30, "1-2g IV over 15-30min; reactivates cholinesterase if given before aging"),
     "Decontamination": tc(10, "Remove clothing, wash skin with soap and water; protect healthcare workers with PPE"),
     "Intubation": tc(30, "If respiratory failure from bronchospasm/bronchorrhea; avoid succinylcholine")},
)

NEW["Carbon Monoxide Poisoning"] = dx(
    "Toxicology", "Neurological/Pulmonary",
    v(105, 120, 75, 22, 98.6, 100),  # SpO2 falsely normal!
    {**STD_MOD, "o2_saturation": "fixed"},  # SpO2 is unreliable
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 0},
    "Headache, confusion, cherry-red skin (late/unreliable), nausea, dizziness, syncope, SpO2 FALSELY NORMAL on pulse oximetry, tachycardia",
    {"o2_saturation_below": 999, "systolic_bp_below": 80},
    {"co_hgb": lab(10, 60, "%", "elevated"), "lactate": lab(2.0, 10.0, "mmol/L", "elevated"),
     "troponin": lab(0, 2.0, "ng/mL", "variable"), "vbg_ph": lab(7.20, 7.40, "pH", "decreased")},
    ["Oxygen Therapy", "IV Access", "Continuous Monitoring"],
    {"100% O2 via NRB": tc(5, "Half-life of COHb drops from 5h to 90min on 100% O2; immediately start"),
     "CO-Oximetry": tc(15, "ABG with co-oximetry is the ONLY reliable test; pulse ox cannot detect COHb"),
     "Hyperbaric Oxygen": tc(120, "Consider if COHb >25%, loss of consciousness, cardiac ischemia, or pregnancy")},
)

NEW["Alcohol Withdrawal"] = dx(
    "Toxicology", "Neurological",
    v(115, 160, 95, 22, 100.5, 96),
    {**STD_MOD, "heart_rate": "multiply", "systolic_bp": "multiply"},
    {"heart_rate": 10, "systolic_bp": 8, "o2_saturation": 2},
    "Tremor, diaphoresis, agitation, tachycardia, hypertension, hallucinations (visual), seizures, delirium tremens if severe; CIWA score elevated",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"glu": lab(60, 200, "mg/dL", "variable"), "mg": lab(0.8, 1.8, "mg/dL", "decreased"),
     "k": lab(2.8, 4.5, "mEq/L", "decreased"), "phos": lab(1.5, 3.5, "mg/dL", "decreased"),
     "ast": lab(30, 200, "U/L", "elevated"), "alt": lab(20, 100, "U/L", "elevated"),
     "ggt": lab(50, 500, "U/L", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"Benzodiazepine Protocol": tc(15, "Symptom-triggered dosing per CIWA: diazepam 10-20mg or lorazepam 2-4mg q1h PRN"),
     "Thiamine": tc(30, "100mg IV BEFORE glucose to prevent Wernicke encephalopathy"),
     "Electrolyte Repletion": tc(60, "Magnesium 2g IV, potassium and phosphorus PRN"),
     "Glucose Check": tc(10, "Hypoglycemia common in malnourished alcoholics")},
)

NEW["Serotonin Syndrome"] = dx(
    "Toxicology", "Neurological",
    v(120, 155, 90, 22, 104.0, 95),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 10, "systolic_bp": 8, "o2_saturation": 2},
    "Clonus (especially lower extremity), hyperreflexia, agitation, diaphoresis, mydriasis, hyperthermia, tremor, muscle rigidity, diarrhea",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"ck": lab(200, 5000, "U/L", "elevated"), "wbc": lab(8, 18, "K/uL", "variable"),
     "cr": lab(0.6, 3.0, "mg/dL", "variable"), "lactate": lab(1.5, 6.0, "mmol/L", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"Discontinue Serotonergic Agents": tc(5, "Stop all SSRIs, SNRIs, MAOIs, triptans, tramadol, linezolid, etc."),
     "Cyproheptadine": tc(30, "12mg PO initial, then 2mg q2h; serotonin antagonist; only available PO"),
     "Active Cooling": tc(15, "Target temp <38.5°C; ice packs, cooling blankets; avoid antipyretics (ineffective)"),
     "Benzodiazepines": tc(15, "Diazepam or lorazepam for agitation and muscle rigidity")},
)

NEW["Neuroleptic Malignant Syndrome"] = dx(
    "Toxicology", "Neurological",
    v(115, 160, 95, 24, 106.0, 93),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 8, "systolic_bp": 10, "o2_saturation": 3},
    "Lead-pipe rigidity, hyperthermia (>40°C), altered mental status, autonomic instability (BP lability, tachycardia, diaphoresis), tremor",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"ck": lab(1000, 100000, "U/L", "elevated"), "wbc": lab(10, 25, "K/uL", "elevated"),
     "cr": lab(1.0, 6.0, "mg/dL", "elevated"), "k": lab(4.5, 7.0, "mEq/L", "elevated"),
     "ast": lab(40, 500, "U/L", "elevated"), "lactate": lab(2.0, 8.0, "mmol/L", "elevated")},
    ["IV Access", "Continuous Monitoring", "Oxygen Therapy"],
    {"Stop Offending Agent": tc(5, "Discontinue all dopamine antagonists (antipsychotics, metoclopramide)"),
     "Dantrolene": tc(30, "1-2.5mg/kg IV; muscle relaxant to reduce rigidity and thermogenesis"),
     "Bromocriptine": tc(60, "2.5mg PO/NGT q8h; dopamine agonist"),
     "Active Cooling": tc(15, "Aggressive; target temp <38.5°C; ice packs, cooling blankets, cold IV fluids")},
)

# ═══════════════════════════════════════════════════════════════════════
# INFECTIOUS DISEASE
# ═══════════════════════════════════════════════════════════════════════

NEW["Necrotizing Fasciitis"] = dx(
    "Infectious", "Skin/MSK",
    v(125, 85, 50, 24, 103.5, 93),
    STD_MOD,
    {"systolic_bp": 18, "diastolic_bp": 12, "o2_saturation": 3},
    "Pain out of proportion to exam, rapidly spreading erythema, crepitus, dusky/necrotic skin, bullae, systemic toxicity (fever, tachycardia, hypotension)",
    {"o2_saturation_below": 88, "systolic_bp_below": 75},
    {"wbc": lab(15, 40, "K/uL", "elevated"), "cr": lab(1.2, 4.0, "mg/dL", "elevated"),
     "lactate": lab(3.0, 10.0, "mmol/L", "elevated"), "na": lab(128, 138, "mEq/L", "decreased"),
     "glu": lab(100, 300, "mg/dL", "elevated"), "ck": lab(500, 50000, "U/L", "elevated"),
     "hco3": lab(14, 22, "mEq/L", "decreased")},
    ["IV Access", "Antibiotics", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Broad-Spectrum Antibiotics": tc(30, "Vancomycin + pip-tazo + clindamycin (toxin suppression); IV stat"),
     "Surgical Consult": tc(60, "EMERGENT surgical debridement is the definitive treatment; do not delay"),
     "Aggressive IV Fluids": tc(30, "These patients develop severe sepsis; 30mL/kg initial bolus")},
    {"Diabetes": {"glu": {"min": 200, "max": 500}}}
)

NEW["Pyelonephritis"] = dx(
    "Infectious", "Renal",
    v(108, 110, 70, 20, 103.0, 96),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 2},
    "CVA tenderness, fever, rigors, dysuria, suprapubic tenderness, nausea/vomiting, flank pain",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"wbc": lab(12, 25, "K/uL", "elevated"), "cr": lab(0.8, 2.5, "mg/dL", "variable"),
     "ua_wbc": lab(10, 100, "/HPF", "elevated"), "ua_nitrite": lab(1, 1, "positive", "elevated"),
     "lactate": lab(1.0, 4.0, "mmol/L", "variable"), "bun": lab(10, 30, "mg/dL", "variable")},
    ["IV Access", "Antibiotics", "Continuous Monitoring"],
    {"IV Antibiotics": tc(60, "Ceftriaxone 1g IV or fluoroquinolone; broaden if septic"),
     "Blood Cultures": tc(60, "Before antibiotics if febrile/septic"),
     "CT Abdomen/Pelvis": tc(120, "If no improvement in 48-72h; rule out abscess or obstruction"),
     "IV Fluids": tc(30, "Many patients volume-depleted from fever, vomiting, poor intake")},
    {"Diabetes": {"glu": {"min": 150, "max": 300}},
     "CKD": {"cr": {"min": 2.0, "max": 5.0}}}
)

NEW["Encephalitis"] = dx(
    "Infectious", "Neurological",
    v(105, 115, 72, 18, 103.5, 96),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 2},
    "Altered mental status, fever, headache, seizures, focal neurological deficits, personality/behavioral changes, possible temporal lobe signs (HSV)",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"wbc": lab(10, 22, "K/uL", "elevated"), "csf_wbc": lab(10, 500, "cells/uL", "elevated"),
     "csf_protein": lab(50, 200, "mg/dL", "elevated"), "csf_glucose": lab(40, 80, "mg/dL", "normal"),
     "na": lab(130, 145, "mEq/L", "variable"), "cr": lab(0.6, 1.4, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Acyclovir": tc(60, "10mg/kg IV q8h; start empirically — do NOT wait for HSV PCR results"),
     "MRI Brain": tc(120, "Temporal lobe enhancement suggests HSV; more sensitive than CT"),
     "Lumbar Puncture": tc(60, "CSF analysis + HSV PCR; lymphocytic pleocytosis expected"),
     "Seizure Management": tc(15, "Levetiracetam or lorazepam; seizures common with HSV encephalitis")},
)

# ═══════════════════════════════════════════════════════════════════════
# HEMATOLOGIC / ONCOLOGIC
# ═══════════════════════════════════════════════════════════════════════

NEW["Sickle Cell Crisis"] = dx(
    "Hematologic", "Hematologic",
    v(110, 115, 72, 20, 100.5, 92),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 4},
    "Severe bone pain (back, chest, extremities), tachycardia, possible splenic sequestration (LUQ mass), jaundice, ACS if chest involvement",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"hgb": lab(5, 9, "g/dL", "decreased"), "retic": lab(5, 25, "%", "elevated"),
     "ldh": lab(300, 2000, "U/L", "elevated"), "t_bili": lab(2.0, 10.0, "mg/dL", "elevated"),
     "wbc": lab(10, 25, "K/uL", "elevated"), "lactate": lab(1.5, 5.0, "mmol/L", "elevated"),
     "cr": lab(0.6, 2.0, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Aggressive Pain Management": tc(15, "IV morphine or hydromorphone PCA; NSAIDs adjunct; do NOT undertreat pain"),
     "IV Fluids": tc(30, "NS at 1-1.5x maintenance; avoid overhydration (can precipitate ACS)"),
     "Transfusion": tc(120, "Simple or exchange transfusion if Hgb <6 or acute chest syndrome"),
     "Incentive Spirometry": tc(30, "Q2h while awake to prevent ACS; most critical preventive measure")},
)

NEW["DIC"] = dx(
    "Hematologic", "Hematologic/Multi-system",
    v(120, 85, 50, 24, 101.0, 93),
    STD_MOD,
    {"systolic_bp": 18, "diastolic_bp": 12, "o2_saturation": 3},
    "Simultaneous bleeding (oozing from IV sites, petechiae, purpura, mucosal bleeding) AND thrombosis, organ dysfunction, acrocyanosis",
    {"o2_saturation_below": 88, "systolic_bp_below": 70},
    {"plt": lab(10, 80, "K/uL", "decreased"), "pt_inr": lab(1.5, 5.0, "INR", "elevated"),
     "fibrinogen": lab(50, 200, "mg/dL", "decreased"), "d_dimer": lab(2000, 50000, "ng/mL", "elevated"),
     "ldh": lab(300, 3000, "U/L", "elevated"), "hgb": lab(6, 10, "g/dL", "decreased"),
     "cr": lab(1.0, 4.0, "mg/dL", "elevated")},
    ["IV Access", "Continuous Monitoring", "Fluid Resuscitation"],
    {"Treat Underlying Cause": tc(30, "DIC is always secondary; identify and treat trigger (sepsis, malignancy, trauma, OB)"),
     "Blood Products": tc(30, "Platelets if <10K or bleeding; FFP if INR >1.5 and bleeding; cryo if fibrinogen <100"),
     "Heparin": tc(60, "Only if thrombosis predominates (chronic DIC); NOT if active hemorrhage")},
)

NEW["Neutropenic Fever"] = dx(
    "Hematologic", "Hematologic/Infectious",
    v(108, 100, 62, 20, 102.5, 96),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 2},
    "Fever with ANC <500, often minimal localizing signs (lack of inflammatory response), tachycardia, possible perianal tenderness, oral mucositis",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"wbc": lab(0.1, 1.0, "K/uL", "decreased"), "anc": lab(0, 500, "cells/uL", "decreased"),
     "lactate": lab(1.0, 5.0, "mmol/L", "variable"), "cr": lab(0.6, 2.0, "mg/dL", "variable"),
     "plt": lab(20, 100, "K/uL", "decreased")},
    ["IV Access", "Antibiotics", "Continuous Monitoring"],
    {"Blood Cultures x2": tc(30, "Peripheral AND central line cultures before antibiotics"),
     "Empiric Antibiotics": tc(60, "Cefepime or meropenem monotherapy STAT per IDSA guidelines; do NOT delay"),
     "Chest X-Ray": tc(60, "May be falsely negative due to low WBC; CT if high suspicion"),
     "G-CSF Consideration": tc(120, "Filgrastim if expected prolonged neutropenia (>7 days)")},
)

# ═══════════════════════════════════════════════════════════════════════
# PEDIATRIC
# ═══════════════════════════════════════════════════════════════════════

NEW["Febrile Seizure"] = dx(
    "Pediatric", "Neurological",
    v(160, 90, 55, 28, 103.5, 96),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 10, "systolic_bp": 5, "o2_saturation": 2},
    "Generalized tonic-clonic activity in febrile child (6mo-5yr), post-ictal drowsiness, no focal deficits (if simple), fever source identified",
    {"o2_saturation_below": 90, "systolic_bp_below": 70},
    {"wbc": lab(8, 22, "K/uL", "variable"), "glu": lab(60, 150, "mg/dL", "normal"),
     "na": lab(135, 145, "mEq/L", "normal"), "cr": lab(0.2, 0.6, "mg/dL", "normal")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"Airway Positioning": tc(2, "Recovery position; suction PRN; do not restrain"),
     "Antipyretics": tc(15, "Acetaminophen 15mg/kg or ibuprofen 10mg/kg for fever control"),
     "Benzodiazepine": tc(5, "Midazolam 0.2mg/kg IM or diazepam 0.5mg/kg PR if seizure >5 min"),
     "Fever Source Workup": tc(60, "UA, CXR as indicated; LP if <12 months or complex features")},
)

NEW["Bronchiolitis"] = dx(
    "Pediatric", "Pulmonary",
    v(155, 85, 55, 50, 100.5, 90),
    {**STD_MOD, "heart_rate": "multiply", "respiratory_rate": "multiply"},
    {"heart_rate": 8, "systolic_bp": 5, "respiratory_rate": 8, "o2_saturation": 4},
    "Wheezing and crackles, nasal flaring, intercostal/subcostal retractions, tachypnea, copious nasal secretions, poor feeding, cough",
    {"o2_saturation_below": 88, "systolic_bp_below": 60},
    {"wbc": lab(6, 15, "K/uL", "normal"), "rsv": lab(1, 1, "positive", "elevated"),
     "cr": lab(0.1, 0.4, "mg/dL", "normal"), "na": lab(135, 145, "mEq/L", "normal")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"Nasal Suctioning": tc(10, "Bulb or deep suction to clear secretions; most effective intervention"),
     "Supplemental O2": tc(10, "Maintain SpO2 >90%; high-flow nasal cannula if moderate-severe"),
     "Hydration Assessment": tc(30, "IV or NG fluids if unable to maintain oral intake"),
     "Apnea Monitoring": tc(15, "Especially if <2 months, premature, or history of apnea")},
)

NEW["Kawasaki Disease"] = dx(
    "Pediatric", "Cardiovascular/Multi-system",
    v(140, 90, 55, 24, 104.0, 97),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 8, "systolic_bp": 5, "o2_saturation": 1},
    "Fever >5 days, bilateral conjunctival injection, strawberry tongue, cervical lymphadenopathy, polymorphous rash, extremity changes (edema, erythema, desquamation)",
    {"o2_saturation_below": 92, "systolic_bp_below": 70},
    {"wbc": lab(12, 30, "K/uL", "elevated"), "plt": lab(300, 800, "K/uL", "elevated"),
     "esr": lab(40, 100, "mm/hr", "elevated"), "crp": lab(3.0, 20.0, "mg/dL", "elevated"),
     "alb": lab(2.0, 3.5, "g/dL", "decreased"), "ast": lab(20, 100, "U/L", "elevated"),
     "na": lab(130, 138, "mEq/L", "decreased")},
    ["IV Access", "Continuous Monitoring"],
    {"IVIG": tc(240, "2g/kg IV over 10-12 hours; first-line treatment; must give within 10 days of fever onset"),
     "High-Dose Aspirin": tc(60, "80-100mg/kg/day divided q6h until afebrile; then 3-5mg/kg/day for 6-8 weeks"),
     "Echocardiogram": tc(240, "Baseline echo to assess coronary arteries; repeat at 2 and 6-8 weeks")},
)

NEW["Intussusception"] = dx(
    "Pediatric", "GI",
    v(150, 85, 55, 30, 99.5, 97),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 8, "systolic_bp": 8, "o2_saturation": 1},
    "Intermittent colicky abdominal pain (child draws knees to chest), vomiting, currant jelly stool (late), sausage-shaped mass in RUQ, lethargy between episodes",
    {"o2_saturation_below": 92, "systolic_bp_below": 60},
    {"wbc": lab(8, 18, "K/uL", "variable"), "hgb": lab(9, 14, "g/dL", "variable"),
     "cr": lab(0.1, 0.5, "mg/dL", "normal"), "na": lab(133, 145, "mEq/L", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"Abdominal Ultrasound": tc(30, "Target sign (donut sign) is diagnostic; sensitivity >95%"),
     "Air/Hydrostatic Enema": tc(120, "Therapeutic reduction by radiology; success rate 80-95%"),
     "Surgery Consult": tc(60, "Emergent if peritonitis, perforation, failed reduction, or pathologic lead point"),
     "IV Fluids": tc(30, "Maintenance + deficit replacement; these children are often dehydrated from vomiting")},
)

NEW["Neonatal Sepsis"] = dx(
    "Pediatric", "Infectious/Multi-system",
    v(180, 55, 35, 55, 96.5, 90),
    {**STD_MOD, "heart_rate": "multiply", "respiratory_rate": "multiply",
     "systolic_bp": "decrease", "temperature_f": "fixed"},
    {"heart_rate": 10, "systolic_bp": 10, "respiratory_rate": 10, "o2_saturation": 5},
    "Temperature instability (hypothermia more common than fever), poor feeding, lethargy, irritability, apnea, tachypnea, mottled skin, bulging fontanelle (if meningitis)",
    {"o2_saturation_below": 85, "systolic_bp_below": 40},
    {"wbc": lab(5, 30, "K/uL", "variable"), "crp": lab(1.0, 15.0, "mg/dL", "elevated"),
     "glu": lab(30, 80, "mg/dL", "variable"), "plt": lab(50, 200, "K/uL", "decreased"),
     "lactate": lab(2.0, 8.0, "mmol/L", "elevated")},
    ["IV Access", "Antibiotics", "Oxygen Therapy", "Continuous Monitoring"],
    {"Blood Culture": tc(30, "Before antibiotics; minimum 1mL in pediatric bottle"),
     "Empiric Antibiotics": tc(60, "Ampicillin + gentamicin for early-onset (<7 days); add cefotaxime if meningitis suspected"),
     "Lumbar Puncture": tc(120, "CSF culture and analysis; defer only if hemodynamically unstable"),
     "Glucose Check": tc(10, "Neonates at high risk for hypoglycemia; D10W bolus 2mL/kg if low")},
)

# ═══════════════════════════════════════════════════════════════════════
# ENVIRONMENTAL / OTHER
# ═══════════════════════════════════════════════════════════════════════

NEW["Heat Stroke"] = dx(
    "Environmental", "Multi-system",
    v(130, 90, 55, 28, 106.0, 94),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 10, "systolic_bp": 15, "o2_saturation": 3},
    "Core temp >40°C (104°F), altered mental status, hot dry skin (classic) or diaphoresis (exertional), tachycardia, hypotension, possible seizures",
    {"o2_saturation_below": 88, "systolic_bp_below": 75},
    {"cr": lab(1.5, 5.0, "mg/dL", "elevated"), "ck": lab(500, 50000, "U/L", "elevated"),
     "ast": lab(50, 5000, "U/L", "elevated"), "alt": lab(40, 4000, "U/L", "elevated"),
     "lactate": lab(3.0, 12.0, "mmol/L", "elevated"), "k": lab(3.0, 6.5, "mEq/L", "variable"),
     "pt_inr": lab(1.0, 3.0, "INR", "elevated")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Aggressive Cooling": tc(10, "Target <39°C within 30min; ice water immersion is gold standard; cold IV fluids, ice packs to groin/axillae/neck"),
     "Core Temperature Monitoring": tc(5, "Rectal or esophageal probe; tympanic/axillary unreliable"),
     "IV Fluids": tc(15, "NS or LR 1-2L bolus; most patients are severely volume depleted"),
     "Monitor for DIC": tc(60, "Check fibrinogen, PT/INR, platelets; DIC is major cause of death")},
)

NEW["Hypothermia"] = dx(
    "Environmental", "Cardiovascular/Multi-system",
    v(45, 80, 50, 8, 89.0, 92),
    {**STD_MOD, "heart_rate": "inverse", "respiratory_rate": "inverse", "temperature_f": "fixed"},
    {"heart_rate": 10, "systolic_bp": 15, "respiratory_rate": 3, "o2_saturation": 4},
    "Core temp <35°C (95°F), bradycardia, Osborn (J) waves on ECG, AMS progressing to coma, shivering (mild) or absence of shivering (severe), muscle rigidity",
    {"o2_saturation_below": 85, "systolic_bp_below": 65},
    {"glu": lab(40, 200, "mg/dL", "variable"), "k": lab(3.0, 7.0, "mEq/L", "variable"),
     "vbg_ph": lab(7.15, 7.35, "pH", "decreased"), "lactate": lab(2.0, 8.0, "mmol/L", "elevated"),
     "pt_inr": lab(1.0, 2.5, "INR", "elevated"), "amylase": lab(50, 300, "U/L", "elevated")},
    ["IV Access", "Continuous Monitoring", "Oxygen Therapy"],
    {"Active Rewarming": tc(30, "Warm blankets + warm IV fluids (38-42°C) for mild; invasive rewarming for severe (<30°C)"),
     "Core Temperature Monitoring": tc(5, "Esophageal or rectal; monitor continuously during rewarming"),
     "Cardiac Monitoring": tc(5, "High risk of Vfib below 30°C; avoid rough handling; defibrillation may be ineffective until rewarmed"),
     "ECMO": tc(120, "For severe hypothermia with cardiac arrest; extracorporeal rewarming is most effective")},
)

NEW["Drowning"] = dx(
    "Environmental", "Pulmonary/Multi-system",
    v(50, 75, 45, 6, 93.0, 70),
    {**STD_MOD, "heart_rate": "inverse", "respiratory_rate": "inverse", "temperature_f": "fixed"},
    {"heart_rate": 10, "systolic_bp": 18, "respiratory_rate": 4, "o2_saturation": 10},
    "Respiratory distress or arrest, hypothermia, cyanosis, altered consciousness, frothy sputum, diffuse crackles, possible cardiac arrest",
    {"o2_saturation_below": 80, "systolic_bp_below": 60},
    {"vbg_ph": lab(7.0, 7.30, "pH", "decreased"), "lactate": lab(4.0, 15.0, "mmol/L", "elevated"),
     "k": lab(3.0, 6.5, "mEq/L", "variable"), "na": lab(128, 148, "mEq/L", "variable"),
     "glu": lab(60, 250, "mg/dL", "variable")},
    ["Oxygen Therapy", "IV Access", "Continuous Monitoring", "Intubation"],
    {"Rescue Breathing/CPR": tc(1, "Initiate immediately; ventilation is priority over compressions in drowning"),
     "Supplemental O2/Intubation": tc(10, "100% O2; intubate if apneic, GCS <8, or refractory hypoxia; expect high PEEP needs"),
     "Rewarming": tc(30, "Active rewarming if hypothermic; continue resuscitation until rewarmed to 32°C"),
     "C-Spine Precautions": tc(5, "If mechanism suggests diving injury or unknown circumstances")},
)

NEW["Electrical Injury"] = dx(
    "Environmental", "Cardiovascular/Multi-system",
    v(115, 100, 65, 20, 98.6, 95),
    STD_MOD,
    {"systolic_bp": 12, "diastolic_bp": 8, "o2_saturation": 3},
    "Entry and exit wounds, cardiac arrhythmia, compartment syndrome, rhabdomyolysis, altered consciousness, tetanic muscle contraction marks, possible fractures from falls",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"ck": lab(500, 50000, "U/L", "elevated"), "troponin": lab(0, 5.0, "ng/mL", "elevated"),
     "cr": lab(0.8, 5.0, "mg/dL", "elevated"), "k": lab(4.0, 7.0, "mEq/L", "elevated"),
     "ast": lab(40, 500, "U/L", "elevated"), "lactate": lab(1.5, 6.0, "mmol/L", "elevated")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring", "Oxygen Therapy"],
    {"12-Lead ECG": tc(10, "Arrhythmia screening; cardiac monitoring x 24h minimum"),
     "Aggressive IV Fluids": tc(30, "Target UOP 1-2mL/kg/hr to prevent myoglobinuric AKI"),
     "Compartment Pressure Checks": tc(60, "High risk for compartment syndrome; fasciotomy if pressures >30mmHg"),
     "Trauma Survey": tc(30, "Secondary injuries from fall or thrown mechanism; C-spine if applicable")},
)

# ═══════════════════════════════════════════════════════════════════════
# PSYCHIATRIC
# ═══════════════════════════════════════════════════════════════════════

NEW["Acute Psychosis"] = dx(
    "Psychiatric", "Neurological/Psychiatric",
    v(110, 150, 90, 20, 99.0, 98),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 8, "systolic_bp": 8, "o2_saturation": 1},
    "Agitation, paranoid delusions, auditory/visual hallucinations, disorganized speech, combative behavior, tachycardia from sympathetic activation",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"glu": lab(70, 200, "mg/dL", "normal"), "tsh": lab(0.4, 4.0, "mIU/L", "normal"),
     "wbc": lab(6, 15, "K/uL", "normal"), "cr": lab(0.6, 1.4, "mg/dL", "normal"),
     "uds": lab(0, 1, "screen", "variable")},
    ["Continuous Monitoring"],
    {"Verbal De-escalation": tc(5, "First-line; calm environment, empathic stance, offer choices"),
     "Chemical Sedation": tc(15, "Olanzapine 10mg IM or haloperidol 5mg + lorazepam 2mg IM (B52) if de-escalation fails"),
     "Medical Clearance": tc(60, "BMP, CBC, UA, tox screen, TSH; rule out organic causes (delirium, thyroid, infection)")},
)

# ═══════════════════════════════════════════════════════════════════════
# BUILD & WRITE
# ═══════════════════════════════════════════════════════════════════════

def main():
    # Load existing
    with open(OUTPUT, "r") as f:
        data = json.load(f)

    existing_count = len(data["diagnoses"])
    
    # Merge new diagnoses (don't overwrite existing ones)
    added = 0
    for name, entry in NEW.items():
        if name not in data["diagnoses"]:
            data["diagnoses"][name] = entry
            added += 1
        else:
            print(f"  SKIP (already exists): {name}")

    # Update meta
    data["_meta"]["version"] = "2.0.0"
    data["_meta"]["description"] = (
        "Comprehensive medical knowledge database for the Sim Case Builder. "
        f"{len(data['diagnoses'])} diagnoses across {len(set(e['category'] for e in data['diagnoses'].values()))} categories. "
        "Each entry contains vitals, PE findings, expected lab ranges, required interventions, "
        "time-critical actions, and comorbidity modifiers."
    )
    data["_meta"]["last_updated"] = "2026-03-29"

    # Write
    with open(OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

    total = len(data["diagnoses"])
    categories = sorted(set(e["category"] for e in data["diagnoses"].values()))
    print(f"\n✅ Registry built: {existing_count} existing + {added} new = {total} total diagnoses")
    print(f"📂 Categories ({len(categories)}): {', '.join(categories)}")
    print(f"📄 Written to: {OUTPUT}")

if __name__ == "__main__":
    main()

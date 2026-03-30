#!/usr/bin/env python3
"""
Batch builder: Cardiovascular diagnoses.
Adds ~68 new cardiovascular diagnoses to diagnosis_data.json.
Preserves all existing entries.

Run:  python3 batch_cardiovascular.py
"""
import json
from pathlib import Path

OUTPUT = Path(__file__).parent / "diagnosis_data.json"

def lab(mn, mx, unit, direction):
    return {"min": mn, "max": mx, "unit": unit, "direction": direction}

def tc(window, rationale):
    return {"window_minutes": window, "rationale": rationale}

def v(hr, sbp, dbp, rr, temp, spo2):
    return {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
            "respiratory_rate": rr, "temperature_f": temp, "o2_saturation": spo2}

STD_MOD = {"heart_rate": "multiply", "systolic_bp": "decrease", "diastolic_bp": "decrease",
           "respiratory_rate": "multiply", "temperature_f": "fixed", "o2_saturation": "decrease"}
BRADY_MOD = {**STD_MOD, "heart_rate": "inverse"}
HYPER_MOD = {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"}

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

NEW = {}

# ─── ACUTE CORONARY SYNDROMES ────────────────────────────────────────

NEW["STEMI - Anterior Wall"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(95, 130, 80, 20, 98.6, 96),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 2},
    "Diaphoresis, clutching chest, S4 gallop, possible crackles at bases, anxious appearance",
    {"o2_saturation_below": 90, "systolic_bp_below": 85},
    {"troponin": lab(0.5, 50, "ng/mL", "elevated"), "ck_mb": lab(25, 300, "ng/mL", "elevated"),
     "bnp": lab(100, 2000, "pg/mL", "elevated"), "cr": lab(0.6, 1.4, "mg/dL", "normal"),
     "glu": lab(100, 250, "mg/dL", "elevated"), "k": lab(3.5, 5.0, "mEq/L", "normal")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "ST elevation in V1-V4; reciprocal changes in II, III, aVF"),
     "Aspirin + P2Y12 Inhibitor": tc(15, "ASA 325mg chewed + ticagrelor 180mg or clopidogrel 600mg"),
     "Cath Lab Activation": tc(30, "Door-to-balloon <90 min; call interventional cardiology STAT"),
     "Heparin": tc(30, "UFH 60 units/kg bolus (max 4000 units)")},
    {"Diabetes": {"glu": {"min": 150, "max": 400}},
     "CKD": {"cr": {"min": 2.0, "max": 5.0}}}
)

NEW["STEMI - Inferior Wall"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(55, 95, 60, 16, 98.6, 96),
    {**STD_MOD, "heart_rate": "inverse"},
    {"heart_rate": 8, "systolic_bp": 15, "o2_saturation": 2},
    "Bradycardia, diaphoresis, nausea/vomiting, possible RV involvement (JVD, clear lungs, hypotension)",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"troponin": lab(0.5, 50, "ng/mL", "elevated"), "ck_mb": lab(25, 300, "ng/mL", "elevated"),
     "bnp": lab(50, 1000, "pg/mL", "elevated"), "cr": lab(0.6, 1.4, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "ST elevation in II, III, aVF; get right-sided leads for RV infarct"),
     "Right-Sided ECG": tc(15, "V4R to evaluate RV involvement — AVOID nitroglycerin and morphine if positive"),
     "Cath Lab Activation": tc(30, "Door-to-balloon <90 min"),
     "Atropine": tc(10, "0.5mg IV for symptomatic bradycardia")},
)

NEW["STEMI - Lateral Wall"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(90, 135, 82, 18, 98.6, 96),
    STD_MOD,
    {"systolic_bp": 12, "diastolic_bp": 8, "o2_saturation": 2},
    "Left arm and jaw pain, diaphoresis, S4 gallop, anxious, possible mitral regurgitation murmur",
    {"o2_saturation_below": 90, "systolic_bp_below": 85},
    {"troponin": lab(0.5, 50, "ng/mL", "elevated"), "ck_mb": lab(25, 300, "ng/mL", "elevated"),
     "bnp": lab(100, 1500, "pg/mL", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "ST elevation in I, aVL, V5-V6; reciprocal ST depression in III, aVF"),
     "Aspirin + P2Y12 Inhibitor": tc(15, "ASA 325mg + ticagrelor 180mg"),
     "Cath Lab Activation": tc(30, "Door-to-balloon <90 min")},
)

NEW["NSTEMI"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(88, 145, 88, 18, 98.6, 97),
    STD_MOD,
    {"systolic_bp": 12, "diastolic_bp": 8, "o2_saturation": 2},
    "Substernal pressure, diaphoresis, possible radiation to arm/jaw, anxious, S4 gallop possible",
    {"o2_saturation_below": 90, "systolic_bp_below": 85},
    {"troponin": lab(0.04, 10, "ng/mL", "elevated"), "ck_mb": lab(10, 100, "ng/mL", "elevated"),
     "bnp": lab(50, 800, "pg/mL", "elevated"), "cr": lab(0.6, 1.4, "mg/dL", "normal"),
     "glu": lab(80, 200, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "ST depression and/or T-wave inversion; NO ST elevation"),
     "Serial Troponins": tc(60, "Repeat at 3 and 6 hours to document rise/fall pattern"),
     "Anticoagulation": tc(30, "Heparin drip + aspirin + P2Y12 inhibitor per ACS protocol"),
     "Risk Stratification": tc(120, "TIMI or GRACE score to determine early invasive vs conservative strategy")},
    {"Diabetes": {"glu": {"min": 150, "max": 350}}}
)

NEW["Prinzmetal Angina"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(70, 130, 80, 16, 98.6, 98),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 1},
    "Chest pain at rest (often early morning), transient ST elevation that resolves with NTG, normal exam between episodes",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"troponin": lab(0, 0.04, "ng/mL", "normal"), "cr": lab(0.6, 1.2, "mg/dL", "normal"),
     "k": lab(3.5, 5.0, "mEq/L", "normal"), "mg": lab(1.5, 2.5, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"12-Lead ECG During Pain": tc(10, "Transient ST elevation during episode; normalizes with resolution"),
     "Nitroglycerin": tc(5, "SL NTG for acute relief; IV NTG drip if recurrent"),
     "Calcium Channel Blocker": tc(60, "Diltiazem or amlodipine; mainstay of prevention. AVOID beta-blockers (can worsen spasm)")},
    {"Cocaine Use": {"heart_rate": {"min": 100, "max": 140}}}
)

# ─── ARRHYTHMIAS ─────────────────────────────────────────────────────

NEW["Ventricular Tachycardia - Stable"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(170, 95, 60, 22, 98.6, 94),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 12, "systolic_bp": 15, "o2_saturation": 3},
    "Wide-complex tachycardia on monitor, palpitations, lightheadedness, diaphoresis, still conscious and oriented",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"troponin": lab(0, 1.0, "ng/mL", "variable"), "k": lab(3.0, 5.5, "mEq/L", "variable"),
     "mg": lab(1.0, 2.5, "mg/dL", "variable"), "cr": lab(0.6, 2.0, "mg/dL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Wide QRS >120ms, AV dissociation, fusion/capture beats confirm VT over SVT with aberrancy"),
     "Amiodarone": tc(30, "150mg IV over 10 min, then 1mg/min drip x 6h; first-line for stable monomorphic VT"),
     "Defibrillator at Bedside": tc(5, "Pads on patient; can decompensate to VFib without warning"),
     "Electrolyte Correction": tc(30, "Correct K+ to >4.0 and Mg2+ to >2.0")},
)

NEW["Ventricular Tachycardia - Unstable"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(185, 70, 40, 26, 98.6, 88),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 10, "systolic_bp": 20, "o2_saturation": 5},
    "Wide-complex tachycardia, altered mental status, diaphoresis, weak pulse, near-syncope or syncope, possible chest pain",
    {"o2_saturation_below": 85, "systolic_bp_below": 70},
    {"troponin": lab(0, 5.0, "ng/mL", "variable"), "k": lab(3.0, 6.0, "mEq/L", "variable"),
     "mg": lab(0.8, 2.5, "mg/dL", "variable"), "lactate": lab(2.0, 8.0, "mmol/L", "elevated")},
    ["IV Access", "Continuous Monitoring", "Oxygen Therapy"],
    {"Synchronized Cardioversion": tc(5, "100-200J biphasic STAT; do NOT delay for amiodarone if unstable"),
     "Sedation": tc(5, "Brief sedation with etomidate or midazolam if patient is conscious"),
     "Post-Cardioversion 12-Lead": tc(15, "Assess underlying rhythm and rule out STEMI")},
)

NEW["Ventricular Fibrillation"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(0, 0, 0, 0, 98.6, 0),
    {**STD_MOD, "heart_rate": "fixed", "systolic_bp": "fixed", "o2_saturation": "fixed"},
    {"heart_rate": 0, "systolic_bp": 0, "o2_saturation": 0},
    "Pulseless, unresponsive, chaotic rhythm on monitor, no detectable blood pressure, agonal/absent respirations",
    {"o2_saturation_below": 999, "systolic_bp_below": 999},
    {"k": lab(3.0, 6.5, "mEq/L", "variable"), "mg": lab(0.8, 2.5, "mg/dL", "variable"),
     "lactate": lab(4.0, 15.0, "mmol/L", "elevated"), "troponin": lab(0, 10, "ng/mL", "variable")},
    ["IV Access", "Oxygen Therapy", "Intubation", "Continuous Monitoring"],
    {"Defibrillation": tc(2, "Immediate unsynchronized shock 120-200J biphasic; every 2 min as needed"),
     "High-Quality CPR": tc(1, "Begin immediately; 100-120 compressions/min, 2-inch depth, full recoil"),
     "Epinephrine": tc(5, "1mg IV/IO q3-5min after initial shock"),
     "Amiodarone": tc(10, "300mg IV/IO first dose after 3rd shock; 150mg for second dose")},
)

NEW["Torsades de Pointes"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(200, 60, 35, 6, 98.6, 75),
    {**STD_MOD, "heart_rate": "multiply", "systolic_bp": "decrease"},
    {"heart_rate": 10, "systolic_bp": 20, "o2_saturation": 8},
    "Polymorphic VT with twisting QRS axis, pulselessness or near-syncope, preceded by prolonged QT, possible syncope",
    {"o2_saturation_below": 80, "systolic_bp_below": 60},
    {"mg": lab(0.5, 1.5, "mg/dL", "decreased"), "k": lab(2.5, 4.0, "mEq/L", "decreased"),
     "ca": lab(7.0, 9.0, "mg/dL", "decreased"), "troponin": lab(0, 2.0, "ng/mL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Magnesium": tc(5, "2g MgSO4 IV over 2 min; first-line treatment regardless of Mg level"),
     "Defibrillation": tc(2, "Unsynchronized shock if pulseless; may self-terminate and recur"),
     "Overdrive Pacing": tc(30, "Temporary pacing at 90-110 bpm to suppress pause-dependent TdP"),
     "Stop QT-Prolonging Drugs": tc(5, "Discontinue all offending medications immediately")},
)

NEW["Atrial Flutter"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(150, 110, 68, 18, 98.6, 97),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 10, "systolic_bp": 8, "o2_saturation": 1},
    "Regular tachycardia (often 150 bpm suggesting 2:1 block), sawtooth flutter waves on ECG, palpitations, mild dyspnea",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"tsh": lab(0.1, 5.0, "mIU/L", "variable"), "troponin": lab(0, 0.04, "ng/mL", "normal"),
     "bnp": lab(50, 400, "pg/mL", "elevated"), "k": lab(3.5, 5.0, "mEq/L", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Sawtooth pattern in II, III, aVF; rate often 150 bpm (2:1 block) or 100 (3:1)"),
     "Rate Control": tc(30, "IV diltiazem 0.25mg/kg or metoprolol; target HR <110"),
     "Anticoagulation Assessment": tc(60, "CHA2DS2-VASc score; anticoagulate if score ≥2 per guidelines")},
)

NEW["Second-Degree Heart Block Type I (Wenckebach)"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(55, 110, 70, 16, 98.6, 97),
    BRADY_MOD,
    {"heart_rate": 6, "systolic_bp": 8, "o2_saturation": 1},
    "Gradually prolonging PR interval with dropped beat, usually asymptomatic or mild lightheadedness, regular irregularity",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"troponin": lab(0, 0.04, "ng/mL", "normal"), "k": lab(3.5, 5.5, "mEq/L", "normal"),
     "tsh": lab(0.4, 4.0, "mIU/L", "normal"), "digoxin_level": lab(0, 2.0, "ng/mL", "variable")},
    ["Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Progressive PR prolongation before dropped QRS; grouped beating pattern"),
     "Monitoring": tc(15, "Usually benign; observe for progression to higher-degree block"),
     "Atropine": tc(15, "Only if symptomatic (lightheadedness, syncope); 0.5mg IV")},
)

NEW["Second-Degree Heart Block Type II (Mobitz II)"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(45, 90, 55, 14, 98.6, 96),
    BRADY_MOD,
    {"heart_rate": 8, "systolic_bp": 15, "o2_saturation": 2},
    "Sudden dropped QRS without PR prolongation, possible syncope, fatigue, exercise intolerance, wide QRS baseline",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"troponin": lab(0, 0.5, "ng/mL", "variable"), "k": lab(3.5, 5.5, "mEq/L", "normal"),
     "cr": lab(0.6, 1.4, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Fixed PR with sudden dropped QRS; infranodal block; wide QRS typical"),
     "Transcutaneous Pacing": tc(15, "Pads on and ready; high risk of progressing to complete heart block"),
     "Cardiology Consult": tc(60, "Permanent pacemaker indicated for all symptomatic Mobitz II"),
     "Atropine": tc(10, "May worsen infranodal block; use with caution; TCP preferred")},
)

NEW["Sick Sinus Syndrome"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(42, 100, 62, 14, 98.6, 96),
    BRADY_MOD,
    {"heart_rate": 8, "systolic_bp": 10, "o2_saturation": 2},
    "Alternating bradycardia and tachycardia (tachy-brady syndrome), syncope, fatigue, dizziness, exercise intolerance",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"troponin": lab(0, 0.04, "ng/mL", "normal"), "tsh": lab(0.4, 4.0, "mIU/L", "normal"),
     "k": lab(3.5, 5.0, "mEq/L", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"12-Lead ECG + Telemetry": tc(10, "Sinus bradycardia, sinus pauses, or tachy-brady with paroxysmal AFib/flutter"),
     "Atropine": tc(10, "0.5mg IV for symptomatic bradycardia as bridge"),
     "Pacemaker Evaluation": tc(120, "Permanent pacemaker is definitive treatment for symptomatic SSS")},
)

NEW["Wolff-Parkinson-White Syndrome"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(200, 90, 55, 22, 98.6, 94),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 10, "systolic_bp": 15, "o2_saturation": 3},
    "Extremely rapid rate, delta wave on baseline ECG, short PR interval, wide QRS during tachycardia, possible hemodynamic instability",
    {"o2_saturation_below": 88, "systolic_bp_below": 75},
    {"troponin": lab(0, 0.5, "ng/mL", "variable"), "k": lab(3.5, 5.0, "mEq/L", "normal"),
     "mg": lab(1.5, 2.5, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Delta wave, short PR (<120ms), wide QRS; during tachycardia: irregularly irregular wide complex if AFib"),
     "Procainamide": tc(30, "First-line for stable WPW with AFib; 20-50mg/min IV. AVOID AV nodal blockers"),
     "Synchronized Cardioversion": tc(5, "If hemodynamically unstable; 100-200J biphasic"),
     "Avoid AV Nodal Blockers": tc(1, "NO adenosine, diltiazem, verapamil, digoxin — can cause VFib via unopposed accessory pathway conduction")},
)

NEW["Multifocal Atrial Tachycardia"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(130, 115, 72, 22, 98.6, 91),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 8, "systolic_bp": 8, "o2_saturation": 3},
    "Irregular rhythm with ≥3 distinct P-wave morphologies, commonly associated with COPD or pulmonary disease, mild dyspnea",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"mg": lab(1.0, 2.0, "mg/dL", "decreased"), "k": lab(3.0, 4.5, "mEq/L", "decreased"),
     "bnp": lab(50, 500, "pg/mL", "variable"), "tsh": lab(0.4, 4.0, "mIU/L", "normal")},
    ["IV Access", "Continuous Monitoring", "Oxygen Therapy"],
    {"12-Lead ECG": tc(10, "≥3 different P-wave morphologies, varying PR intervals, irregular rate >100"),
     "Magnesium Repletion": tc(30, "IV MgSO4 2g; often curative; most patients are Mg-depleted"),
     "Treat Underlying Cause": tc(60, "Optimize COPD/pulmonary disease, correct hypoxia, fix electrolytes")},
    {"COPD": {"o2_saturation": {"min": 85, "max": 92}}}
)

NEW["Junctional Rhythm"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(45, 100, 65, 14, 98.6, 97),
    BRADY_MOD,
    {"heart_rate": 6, "systolic_bp": 10, "o2_saturation": 1},
    "Regular narrow-complex rhythm at 40-60 bpm, absent or retrograde P waves, lightheadedness, fatigue",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"troponin": lab(0, 0.1, "ng/mL", "variable"), "k": lab(3.5, 5.0, "mEq/L", "normal"),
     "digoxin_level": lab(0, 2.0, "ng/mL", "variable")},
    ["Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Narrow QRS, rate 40-60, absent/inverted P waves before or after QRS"),
     "Atropine": tc(10, "0.5mg IV if symptomatic; assess for reversible causes"),
     "Drug Review": tc(30, "Check for digoxin toxicity, beta-blocker or CCB excess")},
)

NEW["Accelerated Idioventricular Rhythm"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(75, 110, 70, 16, 98.6, 97),
    STD_MOD,
    {"heart_rate": 5, "systolic_bp": 5, "o2_saturation": 1},
    "Wide-complex regular rhythm at 60-100 bpm, often seen post-reperfusion MI, usually hemodynamically stable",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"troponin": lab(0.1, 20, "ng/mL", "elevated"), "k": lab(3.5, 5.0, "mEq/L", "normal")},
    ["Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Wide QRS, regular rate 60-100; often reperfusion arrhythmia post-PCI/thrombolysis"),
     "Observation": tc(30, "Usually benign and self-limiting; do NOT treat with antiarrhythmics unless symptomatic"),
     "Monitor for Degeneration": tc(15, "Watch for acceleration to VT; keep defibrillator at bedside")},
)

# ─── VALVULAR DISEASE ────────────────────────────────────────────────

NEW["Acute Mitral Regurgitation"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(115, 85, 55, 26, 98.6, 88),
    STD_MOD,
    {"systolic_bp": 18, "diastolic_bp": 12, "o2_saturation": 5},
    "Acute pulmonary edema, new holosystolic murmur at apex radiating to axilla, bilateral crackles, JVD, S3 gallop, tachycardia",
    {"o2_saturation_below": 85, "systolic_bp_below": 75},
    {"troponin": lab(0, 5.0, "ng/mL", "variable"), "bnp": lab(500, 5000, "pg/mL", "elevated"),
     "lactate": lab(2.0, 8.0, "mmol/L", "elevated"), "cr": lab(0.8, 3.0, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Bedside Echo": tc(15, "Severe MR with flail leaflet or papillary muscle rupture; LA/LV dilation"),
     "Vasodilator Therapy": tc(30, "Nitroprusside or NTG drip to reduce afterload; IABP if hemodynamically unstable"),
     "Emergent Surgery Consult": tc(60, "Mitral valve repair/replacement for acute papillary muscle rupture")},
)

NEW["Acute Aortic Regurgitation"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(120, 80, 55, 28, 99.5, 87),
    STD_MOD,
    {"systolic_bp": 18, "diastolic_bp": 20, "o2_saturation": 5},
    "Acute pulmonary edema, wide pulse pressure, early diastolic murmur (may be soft), bilateral crackles, tachycardia, Austin Flint murmur possible",
    {"o2_saturation_below": 85, "systolic_bp_below": 70},
    {"troponin": lab(0, 2.0, "ng/mL", "variable"), "bnp": lab(500, 4000, "pg/mL", "elevated"),
     "lactate": lab(2.0, 8.0, "mmol/L", "elevated"), "d_dimer": lab(200, 10000, "ng/mL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Bedside Echo": tc(15, "Severe AR, premature mitral valve closure, LV volume overload"),
     "Vasodilator Therapy": tc(30, "Nitroprusside to reduce afterload; AVOID beta-blockers (remove compensatory tachycardia)"),
     "Emergent Surgery Consult": tc(60, "Aortic valve replacement; medical therapy is temporizing only")},
)

NEW["Aortic Stenosis - Decompensated"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(90, 95, 65, 22, 98.6, 92),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 4},
    "Crescendo-decrescendo systolic murmur at RUSB radiating to carotids, syncope or near-syncope, exertional dyspnea, pulsus parvus et tardus, S4 gallop",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"troponin": lab(0, 1.0, "ng/mL", "variable"), "bnp": lab(300, 3000, "pg/mL", "elevated"),
     "cr": lab(0.8, 2.5, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Bedside Echo": tc(30, "Aortic valve area, mean gradient, LVEF; AVA <1.0 cm² = severe"),
     "Cautious Volume Management": tc(30, "Avoid aggressive vasodilation or volume depletion — preload dependent"),
     "Cardiology/CT Surgery Consult": tc(120, "TAVR vs SAVR evaluation; medical management bridges only")},
)

NEW["Mitral Stenosis - Decompensated"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(110, 105, 68, 24, 98.6, 91),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 4},
    "Low-pitched diastolic rumble at apex with opening snap, AFib commonly coexistent, bilateral crackles, hemoptysis possible, JVD, malar flush",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"bnp": lab(300, 3000, "pg/mL", "elevated"), "troponin": lab(0, 0.1, "ng/mL", "normal"),
     "pt_inr": lab(0.9, 3.5, "INR", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "AFib common; P mitrale if in sinus; RVH possible"),
     "Rate Control": tc(30, "Slow heart rate to prolong diastolic filling time; IV beta-blocker preferred"),
     "Diuresis": tc(30, "IV furosemide for pulmonary congestion; careful not to reduce preload excessively"),
     "Echo": tc(60, "Mitral valve area, gradient, LA size, pulmonary pressures")},
)

NEW["Prosthetic Valve Thrombosis"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(105, 90, 55, 24, 99.0, 92),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 3},
    "Mechanical click absent or diminished, new murmur, acute heart failure symptoms, subtherapeutic INR history, dyspnea at rest",
    {"o2_saturation_below": 88, "systolic_bp_below": 75},
    {"pt_inr": lab(0.9, 1.5, "INR", "decreased"), "bnp": lab(300, 3000, "pg/mL", "elevated"),
     "ldh": lab(200, 800, "U/L", "elevated"), "troponin": lab(0, 0.5, "ng/mL", "variable"),
     "lactate": lab(1.5, 5.0, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"TEE": tc(60, "Transesophageal echo to assess thrombus size and valve function"),
     "Heparin Drip": tc(30, "Unfractionated heparin for immediate anticoagulation; target aPTT 60-80s"),
     "Thrombolysis vs Surgery": tc(120, "tPA for left-sided valve if surgical risk high or thrombus <1cm; surgery for large thrombus")},
)

NEW["Infective Endocarditis"] = dx(
    "Cardiovascular", "Cardiovascular/Infectious",
    v(105, 110, 68, 20, 102.5, 96),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 2},
    "New or changing murmur, fever, splinter hemorrhages, Janeway lesions, Osler nodes, Roth spots on fundoscopy, splenomegaly, petechiae",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"wbc": lab(12, 25, "K/uL", "elevated"), "crp": lab(3, 20, "mg/dL", "elevated"),
     "esr": lab(30, 100, "mm/hr", "elevated"), "cr": lab(0.8, 3.0, "mg/dL", "variable"),
     "troponin": lab(0, 0.5, "ng/mL", "variable"), "hgb": lab(8, 12, "g/dL", "decreased")},
    ["IV Access", "Antibiotics", "Continuous Monitoring"],
    {"Blood Cultures x3": tc(60, "3 sets from separate sites before antibiotics; 30 min apart"),
     "Empiric Antibiotics": tc(60, "Vancomycin + ceftriaxone for native valve; vancomycin + gentamicin + rifampin for prosthetic"),
     "TTE/TEE": tc(120, "TEE superior for vegetations; assess size, valve destruction, abscess"),
     "CT Surgery Consult": tc(240, "For large vegetations >10mm, heart failure, abscess, or embolic events")},
    {"IVDU": {"risk": "right-sided tricuspid involvement more common"}}
)

# ─── VASCULAR ────────────────────────────────────────────────────────

NEW["Acute Limb Ischemia"] = dx(
    "Cardiovascular", "Vascular",
    v(95, 130, 80, 18, 98.6, 97),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 1},
    "6 P's: Pain, Pallor, Pulselessness, Paresthesias, Paralysis, Poikilothermia; cool pale extremity, absent distal pulses, mottling",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"lactate": lab(1.5, 8.0, "mmol/L", "elevated"), "ck": lab(200, 10000, "U/L", "elevated"),
     "k": lab(4.0, 6.5, "mEq/L", "elevated"), "cr": lab(0.8, 3.0, "mg/dL", "variable"),
     "pt_inr": lab(0.9, 1.5, "INR", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"Heparin Bolus": tc(15, "80 units/kg IV bolus then 18 units/kg/hr drip; prevent clot propagation"),
     "Vascular Surgery Consult": tc(60, "Emergent for embolectomy, thrombectomy, or bypass"),
     "CTA or Angiography": tc(60, "Define location and extent of occlusion"),
     "Pain Management": tc(15, "IV opioids; limb ischemia is extremely painful")},
    {"Atrial Fibrillation": {"risk": "arterial embolism as source"}}
)

NEW["Deep Vein Thrombosis"] = dx(
    "Cardiovascular", "Vascular",
    v(88, 125, 78, 16, 99.0, 98),
    STD_MOD,
    {"systolic_bp": 5, "diastolic_bp": 3, "o2_saturation": 1},
    "Unilateral leg swelling, calf tenderness, warmth, erythema, positive Homans sign (unreliable), pitting edema, distended superficial veins",
    {"o2_saturation_below": 92, "systolic_bp_below": 90},
    {"d_dimer": lab(500, 10000, "ng/mL", "elevated"), "pt_inr": lab(0.9, 1.3, "INR", "normal"),
     "cr": lab(0.6, 1.4, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"Duplex Ultrasound": tc(120, "Compression US of symptomatic leg; non-compressibility confirms DVT"),
     "Anticoagulation": tc(60, "Enoxaparin 1mg/kg BID or rivaroxaban 15mg BID; bridge to warfarin or continue DOAC"),
     "PE Assessment": tc(30, "Monitor for dyspnea, tachycardia, chest pain suggesting PE")},
)

NEW["Abdominal Aortic Aneurysm Rupture"] = dx(
    "Cardiovascular", "Vascular",
    v(125, 70, 40, 24, 98.0, 94),
    STD_MOD,
    {"systolic_bp": 25, "diastolic_bp": 18, "o2_saturation": 3},
    "Sudden severe abdominal/back pain, pulsatile abdominal mass, hemodynamic instability, Grey Turner sign, flank ecchymosis, syncope",
    {"o2_saturation_below": 88, "systolic_bp_below": 60},
    {"hgb": lab(5, 10, "g/dL", "decreased"), "lactate": lab(3.0, 12.0, "mmol/L", "elevated"),
     "cr": lab(1.0, 4.0, "mg/dL", "elevated"), "pt_inr": lab(1.0, 2.0, "INR", "variable")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring", "Oxygen Therapy"],
    {"Large-Bore IV x2": tc(5, "Two 14-16g IVs; crossmatch for 6+ units immediately"),
     "Permissive Hypotension": tc(10, "Target SBP 70-80 until surgical repair; avoid over-resuscitation"),
     "Emergent Vascular Surgery": tc(30, "Open repair or EVAR — this is a surgical emergency"),
     "Massive Transfusion Protocol": tc(15, "Activate immediately; 1:1:1 ratio")},
)

NEW["Thoracic Aortic Aneurysm Rupture"] = dx(
    "Cardiovascular", "Vascular",
    v(120, 75, 45, 22, 98.0, 92),
    STD_MOD,
    {"systolic_bp": 25, "diastolic_bp": 18, "o2_saturation": 4},
    "Sudden tearing chest/back pain, hemodynamic collapse, mediastinal widening on CXR, possible hemothorax, muffled heart sounds if hemopericardium",
    {"o2_saturation_below": 85, "systolic_bp_below": 60},
    {"hgb": lab(5, 10, "g/dL", "decreased"), "lactate": lab(3.0, 12.0, "mmol/L", "elevated"),
     "pt_inr": lab(1.0, 2.0, "INR", "variable"), "troponin": lab(0, 2.0, "ng/mL", "variable")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring", "Oxygen Therapy"],
    {"Large-Bore IV x2": tc(5, "Massive hemorrhage anticipated"),
     "CT Angiography": tc(20, "If stable enough; defines anatomy for surgical planning"),
     "Emergent CT Surgery": tc(30, "Open repair required for ascending aortic rupture"),
     "Massive Transfusion Protocol": tc(15, "Activate immediately")},
)

NEW["Peripheral Arterial Disease - Critical Limb Ischemia"] = dx(
    "Cardiovascular", "Vascular",
    v(80, 150, 90, 16, 98.6, 97),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 1},
    "Rest pain in foot (worse with elevation), non-healing ulcers, gangrene, absent pedal pulses, ABI <0.4, dependent rubor, pallor on elevation",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"cr": lab(0.8, 3.0, "mg/dL", "variable"), "hba1c": lab(5.0, 12.0, "%", "variable"),
     "wbc": lab(6, 18, "K/uL", "variable"), "lactate": lab(1.0, 4.0, "mmol/L", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"ABI Measurement": tc(60, "Ankle-brachial index <0.4 = critical limb ischemia"),
     "Vascular Surgery Consult": tc(120, "Revascularization vs amputation; angiography for planning"),
     "Pain Management": tc(30, "Dependent positioning; opioids for rest pain"),
     "Wound Care": tc(120, "Offloading, infection assessment, debridement if needed")},
    {"Diabetes": {"hba1c": {"min": 7.0, "max": 14.0}},
     "CKD": {"cr": {"min": 2.0, "max": 6.0}}}
)

# ─── HEART FAILURE ───────────────────────────────────────────────────

NEW["Acute Decompensated Heart Failure"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(110, 155, 95, 26, 98.6, 88),
    STD_MOD,
    {"systolic_bp": 12, "diastolic_bp": 8, "o2_saturation": 5},
    "Bilateral crackles, JVD, peripheral edema, S3 gallop, orthopnea, PND, weight gain, hepatojugular reflux",
    {"o2_saturation_below": 85, "systolic_bp_below": 80},
    {"bnp": lab(400, 5000, "pg/mL", "elevated"), "troponin": lab(0, 0.5, "ng/mL", "variable"),
     "cr": lab(1.0, 4.0, "mg/dL", "elevated"), "na": lab(128, 140, "mEq/L", "variable"),
     "k": lab(3.5, 5.5, "mEq/L", "variable"), "lactate": lab(1.0, 5.0, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"IV Diuretics": tc(30, "Furosemide 40-80mg IV (or 2.5x home dose); target UOP 0.5-1mL/kg/hr"),
     "Nitroglycerin": tc(30, "SL or IV drip for afterload reduction if SBP >110; NOT if hypotensive"),
     "BiPAP": tc(15, "Non-invasive ventilation for work of breathing; reduces preload and afterload"),
     "Cardiology Consult": tc(120, "Optimize guideline-directed medical therapy; consider advanced therapies")},
    {"CKD": {"cr": {"min": 2.5, "max": 7.0}},
     "Diabetes": {"glu": {"min": 100, "max": 300}}}
)

NEW["Flash Pulmonary Edema"] = dx(
    "Cardiovascular", "Cardiovascular/Pulmonary",
    v(125, 200, 120, 32, 98.6, 80),
    {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"systolic_bp": 10, "diastolic_bp": 8, "o2_saturation": 8},
    "Acute severe dyspnea, pink frothy sputum, bilateral crackles throughout, diaphoresis, severe hypertension, tripod positioning, cyanosis",
    {"o2_saturation_below": 80, "systolic_bp_below": 80},
    {"bnp": lab(500, 5000, "pg/mL", "elevated"), "troponin": lab(0, 2.0, "ng/mL", "variable"),
     "cr": lab(1.0, 4.0, "mg/dL", "variable"), "lactate": lab(2.0, 6.0, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"IV Nitroglycerin": tc(10, "High-dose NTG drip 200-400mcg/min; most effective intervention for hypertensive flash edema"),
     "BiPAP": tc(5, "Immediate NIPPV; CPAP 10-12 cmH2O or BiPAP; dramatically reduces intubation rates"),
     "IV Furosemide": tc(30, "80mg IV; onset slower than NTG but necessary for volume removal"),
     "Intubation": tc(30, "If BiPAP fails or GCS declines; RSI with etomidate or ketamine")},
)

NEW["Right Heart Failure"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(100, 90, 55, 20, 98.6, 93),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 3},
    "JVD, hepatomegaly, ascites, peripheral edema, RV heave, loud P2, tricuspid regurgitation murmur, hepatojugular reflux, clear lungs (no pulmonary edema)",
    {"o2_saturation_below": 88, "systolic_bp_below": 75},
    {"bnp": lab(200, 3000, "pg/mL", "elevated"), "troponin": lab(0, 0.5, "ng/mL", "variable"),
     "ast": lab(30, 300, "U/L", "elevated"), "alt": lab(25, 250, "U/L", "elevated"),
     "t_bili": lab(1.0, 5.0, "mg/dL", "elevated"), "cr": lab(1.0, 3.0, "mg/dL", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Volume Assessment": tc(30, "Careful — RV failure is preload dependent; avoid aggressive diuresis"),
     "Treat Underlying Cause": tc(60, "PE, pulmonary hypertension, RV infarct; treatment differs dramatically"),
     "Inotropic Support": tc(60, "Milrinone or dobutamine for severe RV failure; reduce RV afterload")},
)

# ─── PERICARDIAL DISEASE ─────────────────────────────────────────────

NEW["Acute Pericarditis"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(95, 125, 78, 18, 100.5, 98),
    STD_MOD,
    {"systolic_bp": 5, "diastolic_bp": 3, "o2_saturation": 1},
    "Pleuritic chest pain worse when supine, improved leaning forward, pericardial friction rub (scratchy 3-component), diffuse ST elevation with PR depression on ECG",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"troponin": lab(0, 0.5, "ng/mL", "variable"), "crp": lab(1, 15, "mg/dL", "elevated"),
     "esr": lab(20, 80, "mm/hr", "elevated"), "wbc": lab(8, 18, "K/uL", "elevated")},
    ["Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Diffuse concave-up ST elevation, PR depression; Spodick sign (downsloping TP segment)"),
     "NSAID Therapy": tc(60, "Ibuprofen 600mg TID or ASA 650mg TID + colchicine 0.5mg BID for 3 months"),
     "Echo": tc(120, "Assess for pericardial effusion; most cases are small or absent")},
)

NEW["Constrictive Pericarditis"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(90, 105, 70, 18, 98.6, 96),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 2},
    "JVD with Kussmaul sign (JVD increases with inspiration), pericardial knock, hepatomegaly, ascites, peripheral edema, exertional dyspnea",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"bnp": lab(100, 500, "pg/mL", "elevated"), "alb": lab(2.0, 3.5, "g/dL", "decreased"),
     "ast": lab(25, 100, "U/L", "elevated"), "cr": lab(0.8, 2.0, "mg/dL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"Echo": tc(60, "Septal bounce, respirophasic variation, thickened pericardium"),
     "CT/MRI Chest": tc(120, "Pericardial thickening >4mm, calcification (CT), enhancement (MRI)"),
     "Cardiac Catheterization": tc(240, "Equalization of diastolic pressures across all 4 chambers"),
     "CT Surgery Consult": tc(240, "Pericardiectomy is definitive treatment for severe cases")},
)

# ─── HYPERTENSIVE EMERGENCIES ────────────────────────────────────────

NEW["Hypertensive Emergency - Aortic Dissection"] = dx(
    "Cardiovascular", "Cardiovascular/Vascular",
    v(100, 210, 120, 20, 98.6, 96),
    HYPER_MOD,
    {"systolic_bp": 10, "diastolic_bp": 8, "o2_saturation": 2},
    "Tearing interscapular pain, BP differential >20mmHg between arms, wide mediastinum on CXR, aortic regurgitation murmur possible, diaphoresis",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"cr": lab(0.8, 3.0, "mg/dL", "variable"), "troponin": lab(0, 2.0, "ng/mL", "variable"),
     "d_dimer": lab(500, 20000, "ng/mL", "elevated"), "lactate": lab(1.0, 6.0, "mmol/L", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Esmolol": tc(15, "Target HR <60 FIRST, then target SBP 100-120; esmolol 500mcg/kg bolus then 50-200mcg/kg/min"),
     "CT Angiography": tc(30, "Confirm dissection and classify Stanford Type A vs B"),
     "Arterial Line": tc(30, "Continuous BP monitoring essential for safe titration"),
     "CT Surgery Consult": tc(60, "Emergent repair for Type A; medical management ± TEVAR for Type B")},
)

NEW["Hypertensive Encephalopathy"] = dx(
    "Cardiovascular", "Cardiovascular/Neurological",
    v(95, 230, 140, 18, 98.6, 97),
    HYPER_MOD,
    {"systolic_bp": 10, "diastolic_bp": 8, "o2_saturation": 1},
    "Severe headache, altered mental status, visual changes (blurred vision, cortical blindness), papilledema, nausea/vomiting, seizures possible",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"cr": lab(1.0, 4.0, "mg/dL", "elevated"), "ua_prot": lab(0, 3, "scale", "elevated"),
     "ldh": lab(200, 800, "U/L", "elevated"), "plt": lab(80, 200, "K/uL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Nicardipine": tc(15, "5mg/hr, titrate q5min by 2.5mg/hr; target 20-25% MAP reduction in first hour"),
     "CT Head": tc(30, "Rule out hemorrhagic stroke; PRES may show posterior white matter edema on MRI"),
     "Arterial Line": tc(30, "Continuous BP monitoring for safe titration"),
     "Seizure Prophylaxis": tc(60, "Levetiracetam if seizures present; lorazepam for acute seizure")},
)

# ─── SHOCK STATES ────────────────────────────────────────────────────

NEW["Distributive Shock - Anaphylactic"] = dx(
    "Cardiovascular", "Cardiovascular/Immunologic",
    v(130, 70, 40, 28, 98.6, 88),
    STD_MOD,
    {"systolic_bp": 22, "diastolic_bp": 15, "o2_saturation": 5},
    "Hypotension, tachycardia, urticaria, angioedema, wheezing/stridor, warm flushed skin, abdominal cramping",
    {"o2_saturation_below": 85, "systolic_bp_below": 60},
    {"tryptase": lab(11, 200, "ng/mL", "elevated"), "lactate": lab(2.0, 8.0, "mmol/L", "elevated")},
    ["IV Access", "Fluid Resuscitation", "Oxygen Therapy", "Continuous Monitoring"],
    {"Epinephrine IM": tc(2, "0.3-0.5mg IM (1:1000) in anterolateral thigh; repeat q5-15min; FIRST-LINE always"),
     "Aggressive IV Fluids": tc(15, "NS 1-2L bolus; massive third-spacing occurs in anaphylaxis"),
     "Airway Assessment": tc(5, "Early intubation if stridor, tongue swelling, or voice changes — airway edema can progress rapidly"),
     "Epinephrine Drip": tc(30, "If refractory: 1-10 mcg/min IV drip; switch from 1:1000 IM to 1:10000 IV")},
)

NEW["Obstructive Shock - Tension Pneumothorax"] = dx(
    "Cardiovascular", "Cardiovascular/Pulmonary",
    v(130, 70, 40, 30, 98.6, 80),
    STD_MOD,
    {"systolic_bp": 22, "diastolic_bp": 15, "o2_saturation": 8},
    "Tracheal deviation away from affected side, absent breath sounds unilaterally, JVD, hypotension, tachycardia, hyperresonance to percussion",
    {"o2_saturation_below": 75, "systolic_bp_below": 60},
    {"lactate": lab(3.0, 12.0, "mmol/L", "elevated"), "vbg_ph": lab(7.15, 7.35, "pH", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Needle Decompression": tc(2, "14g needle 2nd ICS MCL or 5th ICS AAL; immediate lifesaving intervention"),
     "Chest Tube": tc(30, "Definitive management after needle decompression; 28-32 Fr tube thoracostomy"),
     "CXR": tc(30, "Post-procedure to confirm lung re-expansion; NOT needed before decompression if clinical diagnosis")},
)

NEW["Obstructive Shock - Massive PE"] = dx(
    "Cardiovascular", "Cardiovascular/Pulmonary",
    v(130, 70, 40, 28, 98.6, 82),
    STD_MOD,
    {"systolic_bp": 22, "diastolic_bp": 15, "o2_saturation": 6},
    "Acute dyspnea, hypoxemia, hypotension, JVD, RV strain on ECG (S1Q3T3, RBBB), possible PEA arrest",
    {"o2_saturation_below": 80, "systolic_bp_below": 65},
    {"d_dimer": lab(2000, 50000, "ng/mL", "elevated"), "troponin": lab(0.1, 5.0, "ng/mL", "elevated"),
     "bnp": lab(200, 3000, "pg/mL", "elevated"), "lactate": lab(3.0, 10.0, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Bedside Echo": tc(10, "RV dilation, McConnell sign, D-shaped septum; can diagnose in minutes"),
     "Systemic Thrombolysis": tc(30, "Alteplase 100mg IV over 2h for massive PE with hemodynamic instability; accept bleeding risk"),
     "Heparin": tc(15, "UFH 80 units/kg bolus then 18 units/kg/hr; start while awaiting imaging"),
     "Surgical/Catheter Embolectomy": tc(120, "If thrombolysis contraindicated or failed")},
)

NEW["Neurogenic Shock"] = dx(
    "Cardiovascular", "Cardiovascular/Neurological",
    v(50, 75, 45, 12, 95.5, 94),
    {**STD_MOD, "heart_rate": "inverse", "temperature_f": "fixed"},
    {"heart_rate": 10, "systolic_bp": 20, "o2_saturation": 3},
    "Hypotension + bradycardia + warm dry extremities (loss of sympathetic tone), spinal cord injury history, flaccid paralysis below level, priapism",
    {"o2_saturation_below": 88, "systolic_bp_below": 60},
    {"lactate": lab(1.0, 5.0, "mmol/L", "elevated"), "cr": lab(0.6, 1.4, "mg/dL", "normal"),
     "hgb": lab(10, 16, "g/dL", "normal")},
    ["IV Access", "Fluid Resuscitation", "Continuous Monitoring"],
    {"IV Fluids": tc(15, "Cautious fluid resuscitation first; avoid over-resuscitation"),
     "Vasopressors": tc(30, "Norepinephrine or phenylephrine to maintain MAP >85 for 7 days per AANS guidelines"),
     "Atropine": tc(15, "For symptomatic bradycardia; keep at bedside"),
     "Spinal Precautions": tc(1, "Maintain inline stabilization; logroll only")},
)

# ─── MISC CARDIOVASCULAR ─────────────────────────────────────────────

NEW["Takotsubo Cardiomyopathy"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(100, 95, 60, 20, 98.6, 93),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 3},
    "Chest pain mimicking ACS, ST elevation or T-wave inversion, often following emotional/physical stress, apical ballooning on echo, mild HF symptoms",
    {"o2_saturation_below": 88, "systolic_bp_below": 75},
    {"troponin": lab(0.1, 5.0, "ng/mL", "elevated"), "bnp": lab(200, 3000, "pg/mL", "elevated"),
     "ck_mb": lab(10, 50, "ng/mL", "elevated"), "cr": lab(0.6, 1.4, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "ST elevation or deep T-wave inversions; may mimic anterior STEMI"),
     "Cath Lab": tc(90, "Normal coronaries with apical ballooning on ventriculogram; diagnostic"),
     "Supportive Care": tc(60, "ACE inhibitor + beta-blocker; most recover fully in 4-8 weeks"),
     "Monitor for Cardiogenic Shock": tc(30, "5-10% develop severe LV dysfunction or LVOT obstruction")},
)

NEW["Myocarditis"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(105, 100, 62, 20, 100.0, 95),
    STD_MOD,
    {"systolic_bp": 12, "diastolic_bp": 8, "o2_saturation": 2},
    "Chest pain (often pleuritic), preceding viral illness, tachycardia out of proportion to fever, S3 gallop, possible heart failure signs, pericardial friction rub",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"troponin": lab(0.1, 10, "ng/mL", "elevated"), "bnp": lab(100, 2000, "pg/mL", "elevated"),
     "crp": lab(2, 15, "mg/dL", "elevated"), "esr": lab(20, 80, "mm/hr", "elevated"),
     "wbc": lab(8, 18, "K/uL", "elevated"), "ck_mb": lab(10, 100, "ng/mL", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Diffuse ST changes, low voltage, possible arrhythmias; may mimic STEMI"),
     "Echo": tc(60, "Wall motion abnormalities, reduced EF, possible pericardial effusion"),
     "Cardiac MRI": tc(240, "Gold standard for diagnosis; late gadolinium enhancement in non-coronary pattern"),
     "Heart Failure Management": tc(60, "ACE inhibitor + beta-blocker + diuretics PRN; avoid NSAIDs in acute phase")},
)

NEW["Hypertrophic Cardiomyopathy Crisis"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(120, 85, 55, 22, 98.6, 93),
    STD_MOD,
    {"systolic_bp": 18, "diastolic_bp": 12, "o2_saturation": 3},
    "Dynamic LVOT obstruction with harsh crescendo-decrescendo systolic murmur (increases with Valsalva), syncope, chest pain, dyspnea, possible sudden cardiac death",
    {"o2_saturation_below": 88, "systolic_bp_below": 70},
    {"troponin": lab(0, 2.0, "ng/mL", "variable"), "bnp": lab(200, 2000, "pg/mL", "elevated"),
     "lactate": lab(1.5, 6.0, "mmol/L", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Fluids": tc(15, "Volume loading to increase preload and reduce LVOT gradient"),
     "IV Phenylephrine": tc(15, "Pure alpha agonist increases afterload; reduces obstruction. AVOID dobutamine, milrinone, NTG"),
     "Beta-Blocker": tc(30, "IV esmolol to reduce HR and contractility; decreases LVOT gradient"),
     "Avoid Vasodilators": tc(1, "NO nitroglycerin, NO diuretics, NO inotropes — all worsen obstruction")},
)

NEW["Cardiac Contusion"] = dx(
    "Cardiovascular", "Cardiovascular/Trauma",
    v(110, 100, 65, 18, 98.6, 97),
    STD_MOD,
    {"systolic_bp": 10, "diastolic_bp": 5, "o2_saturation": 2},
    "Chest wall tenderness post-blunt trauma, steering wheel injury, arrhythmias on monitor, possible sternal fracture, anterior chest ecchymosis",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"troponin": lab(0.04, 5.0, "ng/mL", "elevated"), "ck_mb": lab(15, 100, "ng/mL", "elevated"),
     "bnp": lab(50, 500, "pg/mL", "variable")},
    ["IV Access", "Continuous Monitoring", "Oxygen Therapy"],
    {"12-Lead ECG": tc(10, "New arrhythmias, ST changes, RBBB; monitor continuously for 24-48h"),
     "Echo": tc(60, "Assess wall motion abnormalities, pericardial effusion, valve injury"),
     "24h Telemetry": tc(30, "Continuous monitoring for late arrhythmias; most significant in first 24h"),
     "Serial Troponins": tc(60, "Rising troponin confirms myocardial injury")},
)

NEW["Pacemaker Malfunction"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(35, 80, 50, 12, 98.6, 94),
    BRADY_MOD,
    {"heart_rate": 10, "systolic_bp": 18, "o2_saturation": 3},
    "Syncope or presyncope, bradycardia, pacing spikes without capture, pocket swelling or erythema if infection, possible hiccups (diaphragmatic pacing)",
    {"o2_saturation_below": 88, "systolic_bp_below": 70},
    {"troponin": lab(0, 0.5, "ng/mL", "variable"), "k": lab(3.5, 6.0, "mEq/L", "variable"),
     "cr": lab(0.6, 2.0, "mg/dL", "variable"), "wbc": lab(5, 18, "K/uL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Assess pacing spikes: failure to capture, failure to sense, or failure to output"),
     "Magnet Application": tc(5, "Place magnet over pacer to force asynchronous pacing (VOO/DOO mode)"),
     "Transcutaneous Pacing": tc(10, "External TCP if magnet fails to restore pacing; bridge to EP consult"),
     "EP/Cardiology Consult": tc(60, "Generator replacement, lead revision, or reprogramming")},
)

NEW["ICD Storm"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(140, 90, 55, 22, 98.6, 93),
    {**STD_MOD, "heart_rate": "multiply"},
    {"heart_rate": 12, "systolic_bp": 15, "o2_saturation": 3},
    "Multiple ICD shocks (≥3 in 24h), recurrent VT/VF, anxiety, diaphoresis, pain from repeated shocks, possible underlying ischemia",
    {"o2_saturation_below": 88, "systolic_bp_below": 75},
    {"troponin": lab(0, 5.0, "ng/mL", "variable"), "k": lab(3.0, 5.5, "mEq/L", "variable"),
     "mg": lab(1.0, 2.5, "mg/dL", "variable"), "lactate": lab(1.5, 6.0, "mmol/L", "elevated")},
    ["IV Access", "Continuous Monitoring", "Oxygen Therapy"],
    {"IV Amiodarone": tc(15, "150mg IV over 10 min then 1mg/min drip; suppress recurrent VT"),
     "Electrolyte Correction": tc(30, "Target K >4.0, Mg >2.0; often triggers for VT storm"),
     "Sedation/Anxiolysis": tc(15, "Midazolam or propofol; repeated shocks are traumatizing"),
     "EP Consult": tc(60, "May need VT ablation, ICD reprogramming, or deep sedation with intubation")},
)

NEW["Commotio Cordis"] = dx(
    "Cardiovascular", "Cardiovascular/Trauma",
    v(0, 0, 0, 0, 98.6, 0),
    {**STD_MOD, "heart_rate": "fixed", "systolic_bp": "fixed", "o2_saturation": "fixed"},
    {"heart_rate": 0, "systolic_bp": 0, "o2_saturation": 0},
    "Sudden cardiac arrest in young athlete after blunt chest impact (baseball, hockey puck), VFib on monitor, no structural heart disease",
    {"o2_saturation_below": 999, "systolic_bp_below": 999},
    {"troponin": lab(0, 2.0, "ng/mL", "variable"), "k": lab(3.5, 5.0, "mEq/L", "normal")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Defibrillation": tc(2, "Immediate shock for VFib; survival inversely related to time to defibrillation"),
     "High-Quality CPR": tc(1, "Begin immediately per BLS/ACLS algorithm"),
     "ACLS Protocol": tc(5, "Standard VFib arrest protocol; structurally normal heart expected"),
     "Post-Arrest Echo": tc(60, "Confirm normal cardiac anatomy; rule out HCM or other structural disease")},
)

NEW["Pulmonary Hypertension Crisis"] = dx(
    "Cardiovascular", "Cardiovascular/Pulmonary",
    v(115, 80, 50, 26, 98.6, 84),
    STD_MOD,
    {"systolic_bp": 18, "diastolic_bp": 12, "o2_saturation": 6},
    "Severe dyspnea, RV failure signs (JVD, hepatomegaly, edema), loud P2, RV heave, tricuspid regurgitation, cyanosis, possible syncope",
    {"o2_saturation_below": 80, "systolic_bp_below": 70},
    {"bnp": lab(300, 5000, "pg/mL", "elevated"), "troponin": lab(0, 2.0, "ng/mL", "variable"),
     "lactate": lab(2.0, 8.0, "mmol/L", "elevated"), "cr": lab(1.0, 3.0, "mg/dL", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Supplemental O2": tc(5, "Target SpO2 >90%; hypoxia worsens pulmonary vasoconstriction"),
     "Inhaled Nitric Oxide": tc(30, "Selective pulmonary vasodilator; 20-40 ppm; optimal for right heart rescue"),
     "IV Epoprostenol": tc(30, "If inhaled NO unavailable; start at 2ng/kg/min and titrate"),
     "Avoid Intubation If Possible": tc(15, "Positive pressure ventilation can precipitate RV collapse; use NIPPV first")},
)

NEW["Cardiac Arrest - PEA"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(0, 0, 0, 0, 98.6, 0),
    {**STD_MOD, "heart_rate": "fixed", "systolic_bp": "fixed", "o2_saturation": "fixed"},
    {"heart_rate": 0, "systolic_bp": 0, "o2_saturation": 0},
    "Pulseless with organized electrical activity on monitor, no pulse with CPR check, consider H's and T's for reversible causes",
    {"o2_saturation_below": 999, "systolic_bp_below": 999},
    {"k": lab(3.0, 7.0, "mEq/L", "variable"), "glu": lab(40, 400, "mg/dL", "variable"),
     "hgb": lab(4, 16, "g/dL", "variable"), "troponin": lab(0, 10, "ng/mL", "variable"),
     "vbg_ph": lab(6.8, 7.20, "pH", "decreased"), "lactate": lab(5, 15, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Intubation", "Continuous Monitoring"],
    {"High-Quality CPR": tc(1, "Begin immediately; 100-120/min, full recoil, minimize interruptions"),
     "Epinephrine": tc(5, "1mg IV/IO q3-5min; start immediately for non-shockable rhythm"),
     "H's and T's Workup": tc(10, "Hypovolemia, Hypoxia, H+, Hypo/Hyperkalemia, Hypothermia; Tension pneumo, Tamponade, Toxins, Thrombosis"),
     "Bedside Echo": tc(10, "Assess during pulse check — identify tamponade, RV strain (PE), hypovolemia")},
)

NEW["Cardiac Arrest - Asystole"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(0, 0, 0, 0, 98.0, 0),
    {**STD_MOD, "heart_rate": "fixed", "systolic_bp": "fixed", "o2_saturation": "fixed"},
    {"heart_rate": 0, "systolic_bp": 0, "o2_saturation": 0},
    "Pulseless, no electrical activity on monitor (confirm in ≥2 leads to rule out fine VFib), agonal or absent respirations",
    {"o2_saturation_below": 999, "systolic_bp_below": 999},
    {"k": lab(3.0, 8.0, "mEq/L", "variable"), "vbg_ph": lab(6.8, 7.15, "pH", "decreased"),
     "lactate": lab(8, 20, "mmol/L", "elevated"), "glu": lab(30, 500, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Intubation", "Continuous Monitoring"],
    {"High-Quality CPR": tc(1, "Begin immediately; do NOT defibrillate asystole"),
     "Epinephrine": tc(3, "1mg IV/IO q3-5min; start immediately for non-shockable rhythm"),
     "Confirm Asystole": tc(2, "Check ≥2 leads; check connections; rule out fine VFib"),
     "Reversible Causes": tc(10, "Aggressive search for H's and T's; asystole carries worst prognosis")},
)

NEW["Post-Cardiac Arrest Syndrome"] = dx(
    "Cardiovascular", "Cardiovascular/Multi-system",
    v(90, 85, 55, 14, 95.0, 92),
    STD_MOD,
    {"systolic_bp": 15, "diastolic_bp": 10, "o2_saturation": 4},
    "Post-ROSC: hemodynamic instability, neurological impairment (GCS variable), reperfusion injury, multi-organ dysfunction, possible rearrest",
    {"o2_saturation_below": 88, "systolic_bp_below": 70},
    {"troponin": lab(0.5, 20, "ng/mL", "elevated"), "lactate": lab(3.0, 15.0, "mmol/L", "elevated"),
     "k": lab(3.0, 6.0, "mEq/L", "variable"), "cr": lab(1.0, 5.0, "mg/dL", "elevated"),
     "vbg_ph": lab(7.10, 7.35, "pH", "decreased"), "glu": lab(100, 350, "mg/dL", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring", "Intubation"],
    {"Targeted Temperature Management": tc(60, "Target 32-36°C for 24h; cooling initiated ASAP post-ROSC per AHA guidelines"),
     "Hemodynamic Optimization": tc(30, "Target MAP >65; vasopressors (norepinephrine) and fluids as needed"),
     "12-Lead ECG": tc(10, "Assess for STEMI — emergent cath lab if ST elevation regardless of consciousness"),
     "Neuroprognostication": tc(4320, "Defer ≥72h post-rewarming; use multimodal approach (exam, EEG, SSEP, MRI)")},
)

NEW["Brugada Syndrome"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(80, 120, 75, 16, 98.6, 98),
    STD_MOD,
    {"systolic_bp": 5, "diastolic_bp": 3, "o2_saturation": 1},
    "Syncope (especially at rest or during sleep), family history of sudden death, type 1 Brugada pattern on ECG (coved ST elevation V1-V3), Asian male predominant",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"troponin": lab(0, 0.04, "ng/mL", "normal"), "k": lab(3.5, 5.0, "mEq/L", "normal"),
     "mg": lab(1.5, 2.5, "mg/dL", "normal")},
    ["Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "Type 1 pattern: coved ST elevation ≥2mm in V1-V3 with RBBB morphology"),
     "Continuous Telemetry": tc(15, "Monitor for VT/VF; most events occur during sleep or rest"),
     "EP Consult": tc(120, "ICD implantation for secondary prevention (survived arrest) or high-risk features"),
     "Avoid Triggers": tc(30, "No class Ia/Ic antiarrhythmics, no fever (antipyretics aggressively), avoid sodium channel blockers")},
)

NEW["Long QT Syndrome"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(75, 120, 75, 16, 98.6, 98),
    STD_MOD,
    {"systolic_bp": 5, "diastolic_bp": 3, "o2_saturation": 1},
    "Syncope (especially exercise-related in LQT1, auditory trigger in LQT2, sleep in LQT3), family history of sudden death, prolonged QTc (>500ms)",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"k": lab(3.5, 5.0, "mEq/L", "normal"), "mg": lab(1.5, 2.5, "mg/dL", "normal"),
     "ca": lab(8.5, 10.5, "mg/dL", "normal"), "tsh": lab(0.4, 4.0, "mIU/L", "normal")},
    ["Continuous Monitoring"],
    {"12-Lead ECG": tc(10, "QTc >500ms high risk; assess T-wave morphology for genotype; check for TdP/VF"),
     "Medication Review": tc(15, "Discontinue ALL QT-prolonging drugs (crediblemeds.org); common offenders: antiemetics, antibiotics, antipsychotics"),
     "Beta-Blocker Therapy": tc(60, "Nadolol or propranolol for LQT1/LQT2; mexiletine for LQT3"),
     "ICD Evaluation": tc(120, "For survivors of cardiac arrest; breakthrough events on beta-blockers; QTc >500 with syncope")},
)

NEW["Aortic Coarctation - Adult Presentation"] = dx(
    "Cardiovascular", "Cardiovascular",
    v(80, 180, 100, 16, 98.6, 98),
    HYPER_MOD,
    {"heart_rate": 5, "systolic_bp": 8, "o2_saturation": 1},
    "Upper extremity hypertension with lower extremity hypotension, BP differential >20mmHg, radial-femoral pulse delay, rib notching on CXR, continuous murmur",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"cr": lab(0.6, 1.4, "mg/dL", "normal"), "bnp": lab(50, 500, "pg/mL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"4-Extremity BP": tc(15, "≥20mmHg gradient between upper and lower extremities confirms coarctation"),
     "CT Angiography": tc(60, "Define anatomy and severity of coarctation; associated bicuspid aortic valve"),
     "BP Control": tc(30, "Beta-blocker first-line; avoid pure vasodilators that increase gradient"),
     "Cardiology/CT Surgery Consult": tc(120, "Balloon angioplasty with stenting or surgical repair for significant gradient")},
)

NEW["Acute Limb Ischemia - Embolic"] = dx(
    "Cardiovascular", "Vascular",
    v(100, 130, 80, 18, 98.6, 97),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 1},
    "Sudden onset 6 P's (Pain, Pallor, Pulselessness, Paresthesias, Paralysis, Poikilothermia), sharp demarcation, history of AFib or recent MI, contralateral pulses normal",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"lactate": lab(2.0, 10.0, "mmol/L", "elevated"), "ck": lab(200, 20000, "U/L", "elevated"),
     "k": lab(4.0, 7.0, "mEq/L", "elevated"), "cr": lab(0.8, 4.0, "mg/dL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"Heparin Bolus": tc(10, "80 units/kg IV immediately; prevent propagation"),
     "Emergent Embolectomy": tc(120, "Fogarty catheter embolectomy; time is tissue"),
     "Compartment Assessment": tc(60, "Post-reperfusion compartment syndrome risk; fasciotomy if pressures >30mmHg"),
     "Source Identification": tc(240, "Echo for cardiac thrombus; AFib management")},
    {"Atrial Fibrillation": {"risk": "cardioembolism source"}}
)

NEW["Mesenteric Venous Thrombosis"] = dx(
    "Cardiovascular", "Vascular/GI",
    v(95, 115, 72, 18, 99.0, 97),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 1},
    "Subacute abdominal pain (days to weeks), distension, nausea, possible bloody stool, peritoneal signs if infarction, history of hypercoagulable state",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"lactate": lab(1.5, 8.0, "mmol/L", "elevated"), "wbc": lab(10, 22, "K/uL", "elevated"),
     "d_dimer": lab(500, 15000, "ng/mL", "elevated"), "hgb": lab(10, 16, "g/dL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Angiography": tc(60, "Venous phase CTA shows filling defect in SMV/portal vein"),
     "Anticoagulation": tc(30, "Heparin drip; mainstay of treatment for non-operative MVT"),
     "Surgery Consult": tc(120, "For peritonitis, pneumatosis, or portal venous gas suggesting bowel infarction"),
     "Hypercoagulability Workup": tc(240, "Protein C/S, antithrombin, Factor V Leiden, antiphospholipid antibodies")},
)

NEW["Aortitis"] = dx(
    "Cardiovascular", "Cardiovascular/Rheumatologic",
    v(95, 145, 85, 18, 101.0, 97),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 1},
    "Back/chest pain, fever, elevated inflammatory markers, possible aortic regurgitation, limb claudication if branch vessel involvement, bruits",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"crp": lab(3, 20, "mg/dL", "elevated"), "esr": lab(40, 120, "mm/hr", "elevated"),
     "wbc": lab(10, 18, "K/uL", "elevated"), "cr": lab(0.6, 2.0, "mg/dL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Angiography": tc(60, "Aortic wall thickening and enhancement; assess for aneurysm"),
     "High-Dose Steroids": tc(60, "Prednisone 1mg/kg or methylprednisolone for giant cell arteritis/Takayasu"),
     "Rheumatology Consult": tc(120, "Classification and long-term immunosuppression plan"),
     "Temporal Artery Biopsy": tc(240, "If GCA suspected; treat while awaiting biopsy results")},
)

NEW["Superior Vena Cava Syndrome"] = dx(
    "Cardiovascular", "Cardiovascular/Oncologic",
    v(100, 120, 75, 20, 98.6, 95),
    STD_MOD,
    {"systolic_bp": 8, "diastolic_bp": 5, "o2_saturation": 2},
    "Facial/neck swelling, JVD, dilated chest wall veins (collateral circulation), Pemberton sign, cyanosis of face, dyspnea worse when supine, headache",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"wbc": lab(5, 30, "K/uL", "variable"), "ldh": lab(100, 1000, "U/L", "variable"),
     "cr": lab(0.6, 1.4, "mg/dL", "normal"), "pt_inr": lab(0.9, 1.5, "INR", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"CT Chest with Contrast": tc(60, "Identify mass, thrombus, or compression of SVC; determine etiology"),
     "Elevate HOB": tc(5, "30-45 degrees to reduce venous pressure and facial edema"),
     "Anticoagulation": tc(60, "If thrombosis contributing; heparin drip"),
     "Oncology/IR Consult": tc(120, "SVC stenting for severe symptoms; radiation or chemo for malignant etiology")},
)

# ═══════════════════════════════════════════════════════════════════════

def main():
    with open(OUTPUT, "r") as f:
        data = json.load(f)

    existing_count = len(data["diagnoses"])
    added = 0
    for name, entry in NEW.items():
        if name not in data["diagnoses"]:
            data["diagnoses"][name] = entry
            added += 1
        else:
            print(f"  SKIP (already exists): {name}")

    data["_meta"]["version"] = "2.1.0"
    data["_meta"]["last_updated"] = "2026-03-29"
    cats = sorted(set(e["category"] for e in data["diagnoses"].values()))
    data["_meta"]["description"] = (
        f"Comprehensive medical knowledge database for the Sim Case Builder. "
        f"{len(data['diagnoses'])} diagnoses across {len(cats)} categories."
    )

    with open(OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

    total = len(data["diagnoses"])
    print(f"\n✅ Cardiovascular batch: {existing_count} existing + {added} new = {total} total")
    print(f"📂 Categories ({len(cats)}): {', '.join(cats)}")

if __name__ == "__main__":
    main()

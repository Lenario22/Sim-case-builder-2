#!/usr/bin/env python3
"""
Batch builder: Neurological diagnoses.
Adds ~57 new neurological diagnoses to diagnosis_data.json.
Run:  python3 batch_neurological.py
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

def dx(category, organ, vitals, modifiers, weights, pe, thresholds,
       labs, interventions, time_critical, comorbidity_mods=None):
    return {
        "category": category, "organ_system": organ, "vitals": vitals,
        "vital_modifiers": modifiers, "vital_severity_weights": weights,
        "pe_findings": pe, "critical_pe_thresholds": thresholds,
        "expected_labs": labs, "required_interventions": interventions,
        "time_critical_actions": time_critical,
        "comorbidity_modifiers": comorbidity_mods or {}
    }

NEW = {}

# ─── STROKE ──────────────────────────────────────────────────────────

NEW["Ischemic Stroke - Large Vessel Occlusion (LVO)"] = dx(
    "Neurological", "Neurological",
    v(90, 180, 100, 16, 98.6, 97),
    {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"systolic_bp": 8, "diastolic_bp": 5, "heart_rate": 3},
    "Acute hemiplegia, facial droop, aphasia or neglect, gaze preference, NIHSS ≥6, last known well time critical, contralateral weakness",
    {"o2_saturation_below": 92, "systolic_bp_below": 90},
    {"glu": lab(60, 250, "mg/dL", "variable"), "pt_inr": lab(0.9, 1.5, "INR", "normal"),
     "plt": lab(100, 400, "K/uL", "normal"), "cr": lab(0.6, 1.4, "mg/dL", "normal"),
     "troponin": lab(0, 0.1, "ng/mL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Head Non-Contrast": tc(10, "Rule out hemorrhage; ASPECTS score; hyperdense vessel sign for LVO"),
     "CTA Head/Neck": tc(20, "Identify large vessel occlusion for thrombectomy candidacy"),
     "IV tPA": tc(60, "Alteplase 0.9mg/kg (max 90mg) if within 4.5h of symptom onset; calculate NIHSS"),
     "Thrombectomy": tc(360, "For LVO with NIHSS ≥6 up to 24h if good perfusion mismatch (DAWN/DEFUSE-3)")},
    {"Atrial Fibrillation": {"risk": "cardioembolic source"},
     "Diabetes": {"glu": {"min": 150, "max": 400}}}
)

NEW["Ischemic Stroke - Posterior Circulation"] = dx(
    "Neurological", "Neurological",
    v(85, 175, 95, 16, 98.6, 97),
    {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"systolic_bp": 8, "diastolic_bp": 5, "heart_rate": 3},
    "Vertigo, diplopia, dysarthria, ataxia, crossed deficits, nystagmus, Horner syndrome, dysphagia, possible locked-in syndrome if basilar",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"glu": lab(60, 250, "mg/dL", "variable"), "pt_inr": lab(0.9, 1.5, "INR", "normal"),
     "plt": lab(100, 400, "K/uL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Head + CTA": tc(15, "Non-contrast CT often normal in posterior fossa; CTA essential for basilar occlusion"),
     "MRI DWI": tc(60, "Far superior to CT for posterior fossa; DWI restriction confirms acute infarct"),
     "IV tPA": tc(60, "Within 4.5h window; posterior circulation strokes often diagnosed late due to non-specific symptoms"),
     "Endovascular Therapy": tc(360, "Basilar artery occlusion has high mortality; thrombectomy even up to 24h in select cases")},
)

NEW["Intracerebral Hemorrhage - Hypertensive"] = dx(
    "Neurological", "Neurological",
    v(85, 210, 120, 14, 98.6, 96),
    {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"systolic_bp": 10, "diastolic_bp": 8, "heart_rate": 3},
    "Sudden severe headache, vomiting, focal neurological deficit, altered consciousness, hypertension, signs of elevated ICP (Cushing triad late)",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"pt_inr": lab(0.9, 1.3, "INR", "normal"), "plt": lab(100, 350, "K/uL", "normal"),
     "glu": lab(80, 300, "mg/dL", "variable"), "cr": lab(0.6, 2.0, "mg/dL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Head STAT": tc(10, "Hyperdense lesion; basal ganglia/thalamus most common for hypertensive ICH"),
     "BP Reduction": tc(60, "Target SBP 130-150 with IV nicardipine or labetalol (INTERACT2/ATACH-2 data)"),
     "Reversal of Anticoagulation": tc(30, "If on anticoagulants: 4-factor PCC + vitamin K for warfarin; idarucizumab for dabigatran; andexanet alfa for Xa inhibitors"),
     "Neurosurgery Consult": tc(60, "EVD for hydrocephalus; evacuation for cerebellar >3cm or deteriorating")},
)

NEW["Intracerebral Hemorrhage - Anticoagulant-Associated"] = dx(
    "Neurological", "Neurological",
    v(80, 190, 110, 14, 98.6, 96),
    {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"systolic_bp": 10, "diastolic_bp": 8, "heart_rate": 3},
    "Expanding hemorrhage on serial CT, history of warfarin/DOAC use, may present with headache, confusion, focal deficits, or rapid decline",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"pt_inr": lab(2.0, 8.0, "INR", "elevated"), "ptt": lab(35, 100, "seconds", "elevated"),
     "plt": lab(80, 300, "K/uL", "variable"), "fibrinogen": lab(150, 400, "mg/dL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"Reversal Agent STAT": tc(15, "Warfarin: 4-factor PCC + IV vitamin K 10mg. Dabigatran: idarucizumab. Xa inhibitors: andexanet alfa or 4F-PCC"),
     "CT Head STAT": tc(10, "Quantify hematoma volume (ABC/2 method); watch for expansion"),
     "BP Control": tc(30, "Target SBP <140; nicardipine drip preferred"),
     "Repeat CT in 6h": tc(360, "Assess for hematoma expansion; expansion >6mL or >33% = poor prognosis")},
)

NEW["Subarachnoid Hemorrhage - Aneurysmal"] = dx(
    "Neurological", "Neurological",
    v(90, 185, 105, 16, 98.6, 96),
    {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"systolic_bp": 10, "diastolic_bp": 8, "heart_rate": 4},
    "Thunderclap headache ('worst headache of my life'), nuchal rigidity, photophobia, nausea/vomiting, possible LOC, Hunt-Hess grade determines severity",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"troponin": lab(0, 2.0, "ng/mL", "variable"), "na": lab(128, 142, "mEq/L", "variable"),
     "glu": lab(100, 250, "mg/dL", "elevated"), "wbc": lab(10, 20, "K/uL", "elevated"),
     "pt_inr": lab(0.9, 1.3, "INR", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Head STAT": tc(10, "Sensitivity ~95% within 6h; star-shaped hyperdensity in subarachnoid space"),
     "LP if CT Negative": tc(120, "Xanthochromia in CSF; RBC count in sequential tubes"),
     "CTA/Angiography": tc(60, "Identify aneurysm location for surgical/endovascular planning"),
     "Nimodipine": tc(60, "60mg PO q4h x21 days; reduces vasospasm-related delayed cerebral ischemia")},
)

NEW["Cerebellar Hemorrhage"] = dx(
    "Neurological", "Neurological",
    v(75, 200, 110, 14, 98.6, 97),
    {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"systolic_bp": 10, "diastolic_bp": 8, "heart_rate": 4},
    "Sudden occipital headache, vertigo, vomiting, truncal ataxia, inability to walk, nystagmus, possible rapid deterioration from brainstem compression or hydrocephalus",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"pt_inr": lab(0.9, 1.5, "INR", "variable"), "plt": lab(100, 350, "K/uL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Head STAT": tc(10, "Cerebellar hemorrhage; assess size (>3cm surgical) and hydrocephalus"),
     "Emergent Neurosurgery": tc(60, "Suboccipital craniectomy for hemorrhage >3cm with deterioration or hydrocephalus"),
     "EVD Placement": tc(60, "For acute obstructive hydrocephalus from 4th ventricle compression"),
     "Frequent Neuro Checks": tc(15, "Can deteriorate rapidly from brainstem compression; q15min initially")},
)

NEW["Transient Ischemic Attack"] = dx(
    "Neurological", "Neurological",
    v(82, 155, 92, 16, 98.6, 98),
    {**STD_MOD, "systolic_bp": "multiply"},
    {"systolic_bp": 5, "diastolic_bp": 3, "heart_rate": 2},
    "Resolved focal neurological deficit (typically <1h), hemiparesis, speech difficulty, or visual loss now resolved, normal exam at presentation",
    {"o2_saturation_below": 92, "systolic_bp_below": 90},
    {"glu": lab(70, 200, "mg/dL", "variable"), "lipid_panel": lab(0, 0, "mg/dL", "variable"),
     "hba1c": lab(5.0, 10.0, "%", "variable"), "pt_inr": lab(0.9, 1.3, "INR", "normal")},
    ["Continuous Monitoring"],
    {"MRI DWI": tc(120, "30-50% of clinical TIAs show DWI restriction = actually small strokes"),
     "CTA or Carotid US": tc(240, "Identify carotid stenosis >50% for endarterectomy candidacy"),
     "ABCD2 Score": tc(30, "Risk stratify for recurrent stroke: Age, BP, Clinical, Duration, Diabetes; score ≥4 = admit"),
     "Dual Antiplatelet": tc(60, "Aspirin + clopidogrel x21 days for high-risk TIA (POINT/CHANCE trials)")},
)

NEW["Cerebral Venous Sinus Thrombosis"] = dx(
    "Neurological", "Neurological/Vascular",
    v(90, 140, 85, 16, 100.0, 98),
    STD_MOD,
    {"systolic_bp": 5, "diastolic_bp": 3, "heart_rate": 3},
    "Progressive headache, papilledema, seizures, focal deficits, altered consciousness, may present postpartum or with OCP use, possible venous infarct with hemorrhage",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"d_dimer": lab(500, 5000, "ng/mL", "elevated"), "pt_inr": lab(0.9, 1.3, "INR", "normal"),
     "plt": lab(100, 350, "K/uL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Venogram or MR Venogram": tc(60, "Empty delta sign on CT; absent flow in venous sinuses on MRV"),
     "Anticoagulation": tc(60, "UFH or LMWH even in presence of hemorrhagic infarct; prevents propagation"),
     "Seizure Control": tc(30, "Levetiracetam first-line for acute seizures; prophylaxis debated"),
     "ICP Management": tc(120, "Acetazolamide, LP if needed; decompressive craniectomy for malignant edema")},
)

# ─── SEIZURES ────────────────────────────────────────────────────────

NEW["Status Epilepticus - Generalized Convulsive"] = dx(
    "Neurological", "Neurological",
    v(125, 170, 100, 24, 101.5, 88),
    {**STD_MOD, "systolic_bp": "multiply"},
    {"heart_rate": 8, "systolic_bp": 5, "o2_saturation": 5, "respiratory_rate": 6},
    "Continuous or recurrent generalized tonic-clonic seizures >5 min without return to baseline, tongue biting, incontinence, cyanosis, post-ictal obtundation",
    {"o2_saturation_below": 82, "systolic_bp_below": 75},
    {"glu": lab(40, 300, "mg/dL", "variable"), "na": lab(120, 145, "mEq/L", "variable"),
     "ca": lab(6.0, 10.5, "mg/dL", "variable"), "mg": lab(1.0, 2.5, "mg/dL", "variable"),
     "ck": lab(300, 50000, "U/L", "elevated"), "lactate": lab(3.0, 15.0, "mmol/L", "elevated"),
     "vbg_ph": lab(7.0, 7.30, "pH", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Benzodiazepine": tc(5, "Lorazepam 0.1mg/kg IV (max 4mg) or midazolam 10mg IM; give within 5 min"),
     "Second-Line AED": tc(20, "Levetiracetam 60mg/kg IV, fosphenytoin 20mg PE/kg, or valproate 40mg/kg if benzo fails"),
     "Third-Line/RSI": tc(40, "Midazolam, propofol, or pentobarbital drip if refractory; intubation required"),
     "Identify Cause": tc(60, "Glucose, electrolytes, toxicology, CT head, AED levels, LP if meningitis suspected")},
)

NEW["Non-Convulsive Status Epilepticus"] = dx(
    "Neurological", "Neurological",
    v(85, 140, 82, 16, 98.6, 97),
    STD_MOD,
    {"heart_rate": 3, "systolic_bp": 3, "o2_saturation": 1},
    "Altered mental status without convulsions, confusion, subtle eye movements, automatisms, can last hours undiagnosed, requires EEG for diagnosis",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"glu": lab(60, 250, "mg/dL", "variable"), "na": lab(125, 145, "mEq/L", "variable"),
     "ammonia": lab(20, 100, "umol/L", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"Continuous EEG": tc(60, "Only way to diagnose NCSE; rhythmic or periodic discharges"),
     "Benzodiazepine Trial": tc(15, "Lorazepam 0.1mg/kg IV; clinical and EEG improvement confirms diagnosis"),
     "Second-Line AED": tc(30, "Levetiracetam or fosphenytoin if benzo-responsive"),
     "Comprehensive Workup": tc(120, "CT, labs, LP, tox screen; suspect in any unexplained AMS")},
)

NEW["Eclampsia"] = dx(
    "Neurological", "Neurological/OB/GYN",
    v(115, 185, 110, 20, 99.0, 95),
    {**STD_MOD, "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"systolic_bp": 10, "diastolic_bp": 8, "heart_rate": 5},
    "Seizures in pregnant/postpartum woman with preeclampsia, hypertension, proteinuria, headache, visual changes, RUQ pain, edema, hyperreflexia+clonus",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"plt": lab(30, 100, "K/uL", "decreased"), "ast": lab(70, 500, "U/L", "elevated"),
     "alt": lab(70, 500, "U/L", "elevated"), "ldh": lab(600, 2000, "U/L", "elevated"),
     "cr": lab(0.8, 2.5, "mg/dL", "elevated"), "ua_prot": lab(1, 4, "scale", "elevated"),
     "uric_acid": lab(6, 12, "mg/dL", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Magnesium Sulfate": tc(10, "4-6g IV loading then 1-2g/hr; FIRST-LINE seizure treatment AND prophylaxis for eclampsia"),
     "IV Antihypertensive": tc(15, "Labetalol 20mg IV or hydralazine 5-10mg IV; target SBP <160"),
     "Fetal Monitoring": tc(10, "Continuous CTG; prepare for emergent delivery"),
     "Delivery": tc(240, "Definitive treatment is delivery; timing depends on gestational age and severity")},
)

NEW["Febrile Seizure - Simple"] = dx(
    "Neurological", "Neurological/Pediatric",
    v(160, 90, 55, 28, 103.5, 96),
    STD_MOD,
    {"heart_rate": 5, "respiratory_rate": 5, "o2_saturation": 2},
    "Generalized tonic-clonic seizure <15 min in febrile child 6mo-5yr, self-resolving, post-ictal drowsiness but returns to baseline, no focal features",
    {"o2_saturation_below": 90, "systolic_bp_below": 70},
    {"glu": lab(60, 150, "mg/dL", "normal"), "wbc": lab(8, 20, "K/uL", "variable")},
    ["Continuous Monitoring"],
    {"Antipyretics": tc(30, "Acetaminophen or ibuprofen for fever; does NOT prevent recurrence but improves comfort"),
     "Febrile Source Workup": tc(120, "Age-appropriate fever evaluation; LP if <12 months or meningitis suspected"),
     "Parental Reassurance": tc(30, "Benign prognosis; 30% recurrence risk; NOT epilepsy"),
     "Seizure Precautions": tc(15, "Recovery position, nothing in mouth, time the seizure")},
)

NEW["Febrile Seizure - Complex"] = dx(
    "Neurological", "Neurological/Pediatric",
    v(170, 85, 50, 30, 104.0, 92),
    STD_MOD,
    {"heart_rate": 6, "respiratory_rate": 6, "o2_saturation": 3},
    "Focal features, >15 min duration, or recurs within 24h, post-ictal Todd paralysis possible, prolonged post-ictal state",
    {"o2_saturation_below": 88, "systolic_bp_below": 65},
    {"glu": lab(50, 150, "mg/dL", "variable"), "na": lab(130, 145, "mEq/L", "variable"),
     "wbc": lab(8, 25, "K/uL", "variable"), "crp": lab(0, 10, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Benzodiazepine if Seizing": tc(5, "Midazolam 0.2mg/kg IM or lorazepam 0.1mg/kg IV if seizure ongoing"),
     "LP Consideration": tc(120, "Strongly consider if <12 months, incomplete immunizations, or meningeal signs"),
     "EEG": tc(240, "Consider for focal or prolonged seizure; higher risk of epilepsy than simple FS"),
     "MRI Brain": tc(240, "Consider if focal features or recurrent complex febrile seizures")},
)

# ─── HEADACHE ────────────────────────────────────────────────────────

NEW["Migraine with Aura - Acute"] = dx(
    "Neurological", "Neurological",
    v(75, 130, 80, 14, 98.6, 99),
    STD_MOD,
    {"systolic_bp": 3, "heart_rate": 2, "o2_saturation": 0},
    "Unilateral throbbing headache with preceding visual aura (scintillating scotoma, fortification spectra), photophobia, phonophobia, nausea/vomiting, seeking dark room",
    {"o2_saturation_below": 92, "systolic_bp_below": 90},
    {},
    ["Continuous Monitoring"],
    {"IV Fluids": tc(30, "NS bolus for dehydration; many migraineurs present volume depleted"),
     "IV Metoclopramide + Diphenhydramine": tc(30, "10mg metoclopramide + 25mg diphenhydramine; effective ER cocktail"),
     "Triptan": tc(30, "Sumatriptan 6mg SQ if not contraindicated (no vascular disease); or nasal spray"),
     "CT/MRI if Red Flags": tc(60, "First presentation, thunderclap, worst ever, focal deficits, fever, or anticoagulation")},
)

NEW["Cluster Headache - Acute"] = dx(
    "Neurological", "Neurological",
    v(80, 135, 82, 16, 98.6, 99),
    STD_MOD,
    {"systolic_bp": 2, "heart_rate": 3, "o2_saturation": 0},
    "Severe unilateral orbital/periorbital pain, ipsilateral lacrimation, rhinorrhea, conjunctival injection, ptosis, miosis, agitation (pacing, won't lie still)",
    {"o2_saturation_below": 92, "systolic_bp_below": 90},
    {},
    ["Continuous Monitoring"],
    {"High-Flow O2": tc(5, "100% O2 at 12-15 LPM via non-rebreather x15 min; 78% response rate within 15 min"),
     "Sumatriptan SQ": tc(15, "6mg SQ; fastest pharmacological treatment; nasal zolmitriptan alternative"),
     "Avoid Opioids": tc(5, "Opioids are ineffective for cluster headache and delay definitive treatment"),
     "Verapamil for Prevention": tc(120, "Start 240-960mg/day divided doses for cluster period; first-line prophylaxis")},
)

NEW["Idiopathic Intracranial Hypertension (Pseudotumor Cerebri)"] = dx(
    "Neurological", "Neurological",
    v(80, 125, 78, 16, 98.6, 99),
    STD_MOD,
    {"systolic_bp": 2, "heart_rate": 2, "o2_saturation": 0},
    "Headache (worse when supine), pulsatile tinnitus, transient visual obscurations, papilledema on fundoscopy, 6th nerve palsy, obese young woman typical",
    {"o2_saturation_below": 92, "systolic_bp_below": 90},
    {"csf_pressure": lab(25, 60, "cmH2O", "elevated")},
    ["Continuous Monitoring"],
    {"Fundoscopy": tc(30, "Bilateral papilledema; assess for cotton-wool spots, hemorrhages"),
     "MRI Brain + MRV": tc(120, "Normal brain parenchyma; empty sella, flattened posterior sclera; rule out venous sinus thrombosis"),
     "LP with Opening Pressure": tc(120, "Therapeutic AND diagnostic; OP >25 cmH2O; remove CSF until OP <20"),
     "Acetazolamide": tc(120, "250-500mg BID, titrate up; reduces CSF production; weight loss counseling")},
)

# ─── INFECTIONS ──────────────────────────────────────────────────────

NEW["Bacterial Meningitis - Adult"] = dx(
    "Neurological", "Neurological/Infectious",
    v(115, 100, 62, 20, 103.5, 97),
    STD_MOD,
    {"heart_rate": 6, "systolic_bp": 10, "o2_saturation": 2},
    "Classic triad: fever, nuchal rigidity, altered mental status; Kernig/Brudzinski signs, photophobia, headache, petechial rash (meningococcal), seizures",
    {"o2_saturation_below": 90, "systolic_bp_below": 75},
    {"wbc": lab(15, 35, "K/uL", "elevated"), "crp": lab(5, 30, "mg/dL", "elevated"),
     "procalcitonin": lab(0.5, 50, "ng/mL", "elevated"), "lactate": lab(1.5, 6.0, "mmol/L", "elevated"),
     "csf_wbc": lab(1000, 50000, "/uL", "elevated"), "csf_glucose": lab(10, 40, "mg/dL", "decreased"),
     "csf_protein": lab(100, 1000, "mg/dL", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"Empiric Antibiotics": tc(30, "Ceftriaxone 2g IV + vancomycin 15-20mg/kg IV + ampicillin (if >50yo or immunocompromised)"),
     "Dexamethasone": tc(30, "0.15mg/kg IV q6h x4 days; give BEFORE or WITH first antibiotic dose (reduces mortality in pneumococcal)"),
     "LP": tc(60, "Opening pressure, cell count, glucose, protein, Gram stain, culture; do NOT delay antibiotics for LP"),
     "Blood Cultures": tc(30, "2 sets before antibiotics if possible; do not delay treatment")},
)

NEW["Viral Meningitis"] = dx(
    "Neurological", "Neurological/Infectious",
    v(95, 115, 72, 16, 101.0, 98),
    STD_MOD,
    {"heart_rate": 4, "systolic_bp": 5, "o2_saturation": 1},
    "Headache, fever, neck stiffness (milder than bacterial), photophobia, nausea, intact mentation, no petechial rash, summer/fall seasonality for enterovirus",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"wbc": lab(8, 15, "K/uL", "variable"), "crp": lab(0.5, 5, "mg/dL", "variable"),
     "csf_wbc": lab(10, 1000, "/uL", "elevated"), "csf_glucose": lab(45, 80, "mg/dL", "normal"),
     "csf_protein": lab(50, 200, "mg/dL", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"LP": tc(60, "Lymphocytic pleocytosis, normal glucose, mildly elevated protein; send PCR panel"),
     "Empiric Antibiotics Until Ruled Out": tc(30, "Treat AS bacterial meningitis until CSF results available"),
     "Supportive Care": tc(60, "IV fluids, antipyretics, analgesics; most cases self-limiting 7-10 days"),
     "HSV PCR": tc(120, "ALWAYS test for HSV; if positive, requires acyclovir — do NOT miss")},
)

NEW["HSV Encephalitis"] = dx(
    "Neurological", "Neurological/Infectious",
    v(100, 120, 75, 18, 103.0, 97),
    STD_MOD,
    {"heart_rate": 5, "systolic_bp": 5, "o2_saturation": 1},
    "Fever, altered mental status, behavioral changes, temporal lobe seizures, olfactory hallucinations, aphasia, personality change, rapid deterioration",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"wbc": lab(8, 18, "K/uL", "variable"), "csf_wbc": lab(10, 500, "/uL", "elevated"),
     "csf_rbc": lab(10, 500, "/uL", "elevated"), "csf_protein": lab(50, 200, "mg/dL", "elevated"),
     "csf_glucose": lab(40, 80, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Acyclovir": tc(30, "10mg/kg IV q8h immediately; do NOT wait for PCR results; mortality 70% untreated vs 20% treated"),
     "MRI Brain": tc(120, "Temporal lobe T2/FLAIR hyperintensity with restricted diffusion; often asymmetric"),
     "LP with HSV PCR": tc(60, "HSV PCR is diagnostic gold standard; may be falsely negative in first 72h"),
     "EEG": tc(240, "Periodic lateralized epileptiform discharges (PLEDs) from temporal lobe")},
)

NEW["Brain Abscess"] = dx(
    "Neurological", "Neurological/Infectious",
    v(95, 125, 78, 16, 101.0, 97),
    STD_MOD,
    {"heart_rate": 4, "systolic_bp": 5, "o2_saturation": 1},
    "Headache (most common), focal neurological deficit, seizures, fever (only 50%), papilledema, signs depend on location (motor, speech, visual)",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"wbc": lab(8, 20, "K/uL", "variable"), "crp": lab(2, 15, "mg/dL", "elevated"),
     "esr": lab(20, 80, "mm/hr", "elevated"), "blood_cx": lab(0, 0, "pos/neg", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"CT or MRI with Contrast": tc(60, "Ring-enhancing lesion with central diffusion restriction on MRI (DWI); perilesional edema"),
     "Empiric IV Antibiotics": tc(60, "Ceftriaxone + metronidazole + vancomycin; cover Strep, anaerobes, Staph"),
     "Neurosurgery Consult": tc(120, "Stereotactic aspiration for lesions >2.5cm, deep location, or poor response"),
     "Seizure Prophylaxis": tc(60, "Levetiracetam for supratentorial abscesses")},
)

NEW["Spinal Epidural Abscess"] = dx(
    "Neurological", "Neurological/Infectious",
    v(100, 115, 72, 18, 102.5, 97),
    STD_MOD,
    {"heart_rate": 5, "systolic_bp": 5, "o2_saturation": 1},
    "Classic triad: back pain, fever, neurological deficit; progression: back pain → radiculopathy → motor/sensory deficit → paralysis; IVDU or spinal procedure risk",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"wbc": lab(12, 25, "K/uL", "elevated"), "crp": lab(5, 25, "mg/dL", "elevated"),
     "esr": lab(40, 120, "mm/hr", "elevated"), "blood_cx": lab(0, 0, "pos/neg", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"Emergent MRI Spine": tc(60, "Entire spine with gadolinium; epidural collection with cord compression"),
     "Blood Cultures + Empiric Antibiotics": tc(60, "Vancomycin + ceftriaxone; Staph aureus most common (>60%)"),
     "Emergent Neurosurgery": tc(240, "Surgical decompression within 24-48h of neurological deficit; better outcomes with earlier intervention"),
     "Serial Neuro Exams": tc(60, "q2-4h motor/sensory exams; any new deficits = emergent surgery")},
)

# ─── NEUROMUSCULAR ───────────────────────────────────────────────────

NEW["Guillain-Barré Syndrome"] = dx(
    "Neurological", "Neurological/Neuromuscular",
    v(90, 120, 75, 18, 98.6, 96),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 3, "heart_rate": 5},
    "Ascending symmetric weakness starting in legs, areflexia, bilateral facial weakness, paresthesias, autonomic instability (tachy/brady, BP swings), respiratory compromise",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"csf_protein": lab(50, 400, "mg/dL", "elevated"), "csf_wbc": lab(0, 10, "/uL", "normal"),
     "fvc": lab(15, 60, "mL/kg", "decreased"), "nif": lab(-20, -60, "cmH2O", "decreased")},
    ["IV Access", "Continuous Monitoring"],
    {"Serial FVC + NIF": tc(60, "q4-6h; intubate if FVC <20mL/kg, NIF >-30, or declining >30% (20/30/40 rule)"),
     "IVIG or Plasmapheresis": tc(240, "IVIG 0.4g/kg/day x5 days OR 5 sessions of PLEX; equally effective"),
     "DVT Prophylaxis": tc(120, "Enoxaparin for immobile patients"),
     "Autonomic Monitoring": tc(60, "Continuous telemetry; sudden bradycardia, blood pressure swings; may need temporary pacing")},
)

NEW["Myasthenic Crisis"] = dx(
    "Neurological", "Neurological/Neuromuscular",
    v(105, 130, 80, 24, 98.6, 90),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 4, "heart_rate": 5},
    "Worsening respiratory muscle weakness in known myasthenia gravis, dyspnea, weak cough, nasal speech, dysphagia, possible bulbar weakness, triggered by infection/medication",
    {"o2_saturation_below": 85, "systolic_bp_below": 80},
    {"fvc": lab(10, 40, "mL/kg", "decreased"), "abg_pco2": lab(40, 60, "mmHg", "elevated"),
     "abg_po2": lab(55, 80, "mmHg", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Serial FVC + NIF": tc(30, "q2-4h; intubate if FVC <15-20mL/kg or NIF >-20; do NOT rely on SpO2 alone"),
     "IVIG or Plasmapheresis": tc(240, "PLEX may work faster but IVIG equally effective; both first-line"),
     "Hold Cholinesterase Inhibitors": tc(15, "Hold pyridostigmine during crisis to assess true muscle function; restart gradually"),
     "Avoid Contraindicated Medications": tc(15, "NO aminoglycosides, fluoroquinolones, magnesium, beta-blockers — all worsen MG")},
)

NEW["Myasthenia Gravis - New Diagnosis"] = dx(
    "Neurological", "Neurological/Neuromuscular",
    v(80, 120, 75, 16, 98.6, 98),
    STD_MOD,
    {"heart_rate": 3, "systolic_bp": 3, "o2_saturation": 1},
    "Fluctuating ptosis, diplopia, fatigable weakness worse at end of day, proximal muscle weakness, difficulty chewing/swallowing, nasal voice",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"achr_ab": lab(0.5, 100, "nmol/L", "elevated"), "musk_ab": lab(0, 1, "titer", "variable")},
    ["Continuous Monitoring"],
    {"Ice Pack Test": tc(15, "Apply ice to closed eyes for 2 min; improvement in ptosis supports MG diagnosis"),
     "AChR Antibodies": tc(120, "Positive in 85% of generalized MG; if negative, check MuSK antibodies"),
     "CT Chest": tc(240, "Evaluate for thymoma (10-15% of MG patients)"),
     "Pyridostigmine": tc(60, "60mg PO TID; symptomatic treatment; titrate for optimal effect")},
)

NEW["Lambert-Eaton Myasthenic Syndrome"] = dx(
    "Neurological", "Neurological/Neuromuscular",
    v(80, 115, 72, 16, 98.6, 98),
    STD_MOD,
    {"heart_rate": 3, "systolic_bp": 3, "o2_saturation": 1},
    "Proximal leg weakness (difficulty rising from chair), hyporeflexia that IMPROVES after exercise, dry mouth, autonomic dysfunction, associated with small cell lung cancer",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"vgcc_ab": lab(0.03, 10, "nmol/L", "elevated")},
    ["Continuous Monitoring"],
    {"VGCC Antibodies": tc(120, "Elevated in 85-90% of LEMS; diagnostic marker"),
     "EMG/NCS": tc(240, "Decremental response at low-frequency stimulation; INCREMENTAL response at high-frequency or post-exercise"),
     "CT Chest": tc(120, "Screen for small cell lung cancer; 60% of LEMS is paraneoplastic"),
     "3,4-Diaminopyridine": tc(240, "First-line symptomatic treatment; enhances ACh release")},
)

NEW["Amyotrophic Lateral Sclerosis - Respiratory Failure"] = dx(
    "Neurological", "Neurological/Neuromuscular",
    v(90, 120, 75, 22, 98.6, 90),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 4, "heart_rate": 4},
    "Known ALS with progressive respiratory failure, orthopnea, morning headaches (CO2 retention), weak cough, aspiration risk, paradoxical abdominal breathing",
    {"o2_saturation_below": 85, "systolic_bp_below": 80},
    {"abg_pco2": lab(45, 65, "mmHg", "elevated"), "abg_po2": lab(55, 75, "mmHg", "decreased"),
     "fvc": lab(10, 40, "mL/kg", "decreased")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"BiPAP/NIV": tc(30, "Improves survival and quality of life; start when FVC <80% or symptoms emerge"),
     "Cough Assist Device": tc(120, "Mechanical insufflation-exsufflation for secretion management"),
     "Goals of Care Discussion": tc(120, "Discuss invasive vs non-invasive ventilation, advance directives, hospice"),
     "FVC Monitoring": tc(120, "Serial FVC tracks disease progression; <25% predicted = high mortality without ventilatory support")},
)

# ─── MOVEMENT DISORDERS / DEGENERATIVE ──────────────────────────────

NEW["Acute Dystonia - Drug Induced"] = dx(
    "Neurological", "Neurological",
    v(100, 135, 82, 18, 98.6, 98),
    STD_MOD,
    {"heart_rate": 4, "systolic_bp": 3, "o2_saturation": 1},
    "Sustained involuntary muscle contraction: torticollis, oculogyric crisis, trismus, opisthotonus, tongue protrusion; onset hours to days after dopamine antagonist",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {},
    ["IV Access", "Continuous Monitoring"],
    {"IV Diphenhydramine": tc(15, "50mg IV push; works within minutes; first-line treatment for acute dystonia"),
     "Benztropine": tc(30, "1-2mg IV/IM alternative to diphenhydramine; longer duration of action"),
     "Identify Offending Agent": tc(30, "Antipsychotics, metoclopramide, prochlorperazine most common triggers"),
     "48h Oral Anticholinergic": tc(60, "Continue benztropine or diphenhydramine PO for 48h to prevent recurrence")},
)

NEW["Neuroleptic Malignant Syndrome"] = dx(
    "Neurological", "Neurological",
    v(120, 150, 95, 22, 106.0, 94),
    {**STD_MOD, "temperature_f": "multiply"},
    {"heart_rate": 8, "systolic_bp": 8, "o2_saturation": 2, "temperature_f": 5},
    "Hyperthermia >104°F, severe 'lead-pipe' rigidity, altered mental status, autonomic instability (diaphoresis, tachycardia, labile BP), often recent antipsychotic change",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"ck": lab(1000, 100000, "U/L", "elevated"), "wbc": lab(10, 25, "K/uL", "elevated"),
     "cr": lab(1.0, 8.0, "mg/dL", "elevated"), "k": lab(4.5, 7.0, "mEq/L", "elevated"),
     "ast": lab(40, 500, "U/L", "elevated"), "lactate": lab(2.0, 10.0, "mmol/L", "elevated"),
     "myoglobin_urine": lab(100, 10000, "ng/mL", "elevated")},
    ["IV Access", "Active Cooling", "Continuous Monitoring"],
    {"Stop Causative Agent": tc(5, "Immediately discontinue all antipsychotics/dopamine antagonists"),
     "Aggressive Cooling": tc(15, "Ice packs, cold IV fluids, cooling blanket; target temp <101°F"),
     "Dantrolene": tc(30, "1-2.5mg/kg IV q5-10min to max 10mg/kg; muscle relaxant; first-line pharmacotherapy"),
     "IV Fluids + Alkalinization": tc(30, "Aggressive IVF for rhabdomyolysis; target UOP >200mL/hr; bicarb drip if myoglobinuria")},
)

NEW["Serotonin Syndrome"] = dx(
    "Neurological", "Neurological/Toxicology",
    v(115, 145, 90, 22, 103.5, 95),
    {**STD_MOD, "temperature_f": "multiply"},
    {"heart_rate": 8, "systolic_bp": 5, "o2_saturation": 2, "temperature_f": 4},
    "Triad: mental status changes (agitation, confusion), autonomic instability (diaphoresis, tachycardia, diarrhea), neuromuscular hyperactivity (CLONUS, hyperreflexia, tremor)",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"ck": lab(200, 10000, "U/L", "elevated"), "cr": lab(0.8, 3.0, "mg/dL", "variable"),
     "wbc": lab(8, 18, "K/uL", "variable"), "lactate": lab(1.5, 6.0, "mmol/L", "elevated")},
    ["IV Access", "Active Cooling", "Continuous Monitoring"],
    {"Stop Serotonergic Agents": tc(5, "Discontinue ALL serotonergic medications immediately"),
     "Cyproheptadine": tc(30, "12mg PO initial then 2mg q2h PRN; serotonin antagonist; first-line specific treatment"),
     "Benzodiazepines": tc(15, "Lorazepam 1-2mg IV for agitation, tremor, and myoclonus; do NOT use physical restraints"),
     "Cooling": tc(30, "Active cooling if temp >104°F; paralysis with intubation for severe rigidity/hyperthermia")},
)

# ─── SPINAL CORD ─────────────────────────────────────────────────────

NEW["Spinal Cord Compression - Malignant"] = dx(
    "Neurological", "Neurological/Oncologic",
    v(90, 125, 78, 16, 98.6, 98),
    STD_MOD,
    {"heart_rate": 3, "systolic_bp": 5, "o2_saturation": 1},
    "Progressive back pain, bilateral leg weakness, sensory level, bowel/bladder dysfunction, known cancer history (lung, breast, prostate most common), pain worse supine",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"wbc": lab(5, 15, "K/uL", "variable"), "ca": lab(8.5, 13.0, "mg/dL", "variable"),
     "ldh": lab(100, 600, "U/L", "variable"), "alp": lab(40, 300, "U/L", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Dexamethasone": tc(30, "10mg IV bolus then 4mg q6h; reduces cord edema; give IMMEDIATELY if suspected"),
     "Emergent MRI Spine": tc(60, "Entire spine with gadolinium; 10% have multiple levels of compression"),
     "Radiation Oncology Consult": tc(120, "Radiation therapy is first-line for most metastatic cord compression"),
     "Neurosurgery Consult": tc(120, "Surgical decompression if unstable spine, radioresistant tumor, or unknown primary")},
)

NEW["Cauda Equina Syndrome"] = dx(
    "Neurological", "Neurological",
    v(90, 130, 80, 16, 98.6, 98),
    STD_MOD,
    {"heart_rate": 3, "systolic_bp": 3, "o2_saturation": 1},
    "Bilateral sciatica, urinary retention or incontinence, saddle anesthesia, decreased rectal tone, bilateral leg weakness (lower motor neuron), severe back pain",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {},
    ["IV Access", "Continuous Monitoring"],
    {"Emergent MRI Lumbar Spine": tc(60, "Large central disc herniation or mass compressing cauda equina"),
     "Bladder Scan": tc(30, "Post-void residual >100-200mL suggests neurogenic bladder"),
     "Emergent Neurosurgical Decompression": tc(720, "Within 24-48h; better outcomes with earlier surgery; delay beyond 48h = worse prognosis"),
     "Foley Catheter": tc(30, "For urinary retention; document intake/output")},
)

NEW["Acute Transverse Myelitis"] = dx(
    "Neurological", "Neurological",
    v(85, 120, 75, 16, 99.0, 98),
    STD_MOD,
    {"heart_rate": 3, "systolic_bp": 3, "o2_saturation": 1},
    "Bilateral motor/sensory deficits with clear sensory level, rapidly progressive over hours to days, back pain at level of lesion, bowel/bladder dysfunction",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"csf_wbc": lab(5, 200, "/uL", "elevated"), "csf_protein": lab(50, 200, "mg/dL", "elevated"),
     "nmo_ab": lab(0, 1, "titer", "variable"), "mog_ab": lab(0, 1, "titer", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"MRI Spine with Gadolinium": tc(60, "T2 hyperintensity extending ≥2 vertebral segments; cord expansion"),
     "IV Methylprednisolone": tc(60, "1g/day IV for 3-5 days; first-line treatment for acute transverse myelitis"),
     "PLEX": tc(240, "If no improvement after steroids; 5 sessions over 10 days"),
     "NMO/MOG Antibodies": tc(240, "Determines if MS, NMOSD, or MOGAD; dramatically different treatment implications")},
)

NEW["Central Cord Syndrome"] = dx(
    "Neurological", "Neurological/Trauma",
    v(85, 125, 78, 16, 98.6, 98),
    STD_MOD,
    {"heart_rate": 3, "systolic_bp": 3, "o2_saturation": 1},
    "Upper extremity weakness > lower extremity ('man in a barrel'), bladder dysfunction, cervical hyperextension injury in elderly with spinal stenosis, cape-like sensory loss",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"cr": lab(0.6, 1.4, "mg/dL", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"C-Spine Precautions": tc(5, "Inline stabilization; collar until cleared"),
     "MRI Cervical Spine": tc(60, "Intramedullary T2 signal centrally; pre-existing stenosis"),
     "Neurosurgery Consult": tc(120, "Surgical decompression if acute disc herniation, unstable fracture, or worsening deficits"),
     "MAP Optimization": tc(60, "Target MAP >85 for 7 days per AANS spinal cord injury guidelines")},
)

# ─── PERIPHERAL NEUROPATHY / OTHER ──────────────────────────────────

NEW["Bell's Palsy"] = dx(
    "Neurological", "Neurological",
    v(78, 125, 78, 16, 98.6, 99),
    STD_MOD,
    {"heart_rate": 2, "systolic_bp": 2, "o2_saturation": 0},
    "Acute unilateral facial weakness involving BOTH upper AND lower face (forehead cannot wrinkle = LMN), hyperacusis, taste changes, dry eye, onset over hours",
    {"o2_saturation_below": 92, "systolic_bp_below": 90},
    {"glu": lab(70, 200, "mg/dL", "variable"), "lyme_ab": lab(0, 1, "titer", "variable")},
    ["Continuous Monitoring"],
    {"Prednisone": tc(120, "60-80mg/day x7 days then taper; best if started within 72h; improves recovery"),
     "Eye Protection": tc(30, "Artificial tears, eye patch at night; prevent corneal abrasion from incomplete closure"),
     "Rule Out Stroke": tc(60, "Central CN7 spares forehead (bilateral cortical innervation); if forehead spared = consider stroke"),
     "Consider Ramsay Hunt": tc(60, "Vesicles in ear canal = herpes zoster oticus; add valacyclovir")},
)

NEW["Trigeminal Neuralgia"] = dx(
    "Neurological", "Neurological",
    v(85, 135, 82, 16, 98.6, 99),
    STD_MOD,
    {"heart_rate": 3, "systolic_bp": 3, "o2_saturation": 0},
    "Unilateral lancinating 'electric shock' facial pain in V2/V3 distribution, triggered by touch/chewing/wind, episodes last seconds to minutes, refractory periods",
    {"o2_saturation_below": 92, "systolic_bp_below": 90},
    {},
    ["Continuous Monitoring"],
    {"Carbamazepine": tc(120, "200mg BID titrated up; first-line treatment; 70-80% response rate"),
     "MRI Brain with Thin Cuts": tc(240, "CISS/FIESTA sequence to assess for vascular loop compression of CN5; rule out MS or tumor"),
     "Rescue: IV Fosphenytoin": tc(60, "For acute severe attack unresponsive to oral medication"),
     "Neurosurgery Referral": tc(240, "Microvascular decompression for refractory cases; highest long-term success rate")},
)

NEW["Normal Pressure Hydrocephalus"] = dx(
    "Neurological", "Neurological",
    v(75, 130, 80, 14, 98.6, 98),
    STD_MOD,
    {"heart_rate": 2, "systolic_bp": 3, "o2_saturation": 0},
    "Classic triad: gait apraxia ('magnetic gait'), urinary incontinence, dementia; ventriculomegaly out of proportion to atrophy on imaging",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"csf_pressure": lab(8, 18, "cmH2O", "normal")},
    ["Continuous Monitoring"],
    {"Large-Volume LP": tc(120, "Remove 30-50mL CSF; assess gait before and after; improvement predicts shunt response"),
     "CT or MRI Brain": tc(120, "Ventriculomegaly (Evans index >0.3) with relatively preserved sulci"),
     "Gait Analysis": tc(120, "Wide-based, shuffling, magnetic gait; test before and after LP for improvement"),
     "VP Shunt Evaluation": tc(240, "Neurosurgery consult; programmable valve VP shunt is definitive treatment")},
)

NEW["Wernicke Encephalopathy"] = dx(
    "Neurological", "Neurological",
    v(95, 110, 68, 16, 98.6, 97),
    STD_MOD,
    {"heart_rate": 4, "systolic_bp": 5, "o2_saturation": 1},
    "Classic triad (all 3 present in <10%): confusion, ophthalmoplegia (CN6 palsy, nystagmus), ataxia; malnourished/alcoholic, precipitated by glucose without thiamine",
    {"o2_saturation_below": 92, "systolic_bp_below": 80},
    {"mg": lab(1.0, 2.0, "mg/dL", "decreased"), "thiamine": lab(20, 50, "nmol/L", "decreased"),
     "glu": lab(50, 200, "mg/dL", "variable"), "alb": lab(2.0, 3.5, "g/dL", "decreased")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Thiamine STAT": tc(15, "500mg IV TID x3 days then 250mg IV daily x5 days; ALWAYS give before glucose"),
     "Magnesium Repletion": tc(30, "Mg cofactor for thiamine metabolism; replete to >2.0"),
     "NO Glucose Before Thiamine": tc(5, "Glucose metabolism consumes thiamine; can precipitate/worsen Wernicke"),
     "MRI Brain": tc(240, "T2/FLAIR hyperintensity in mammillary bodies, medial thalamus, periaqueductal gray")},
)

NEW["Hepatic Encephalopathy"] = dx(
    "Neurological", "Neurological/GI",
    v(90, 100, 60, 16, 98.0, 96),
    STD_MOD,
    {"heart_rate": 4, "systolic_bp": 8, "o2_saturation": 2},
    "Altered mental status in cirrhotic patient, asterixis, fetor hepaticus, constructional apraxia, personality changes, day-night reversal, may progress to coma",
    {"o2_saturation_below": 90, "systolic_bp_below": 75},
    {"ammonia": lab(60, 300, "umol/L", "elevated"), "cr": lab(1.0, 5.0, "mg/dL", "elevated"),
     "na": lab(125, 140, "mEq/L", "decreased"), "pt_inr": lab(1.5, 4.0, "INR", "elevated"),
     "glu": lab(40, 150, "mg/dL", "variable"), "alb": lab(1.5, 3.0, "g/dL", "decreased")},
    ["IV Access", "Continuous Monitoring"],
    {"Lactulose": tc(30, "30mL PO q1-2h until bowel movement then q8h; reduces ammonia via colonic acidification"),
     "Rifaximin": tc(60, "550mg PO BID; add to lactulose for secondary prevention; non-absorbed antibiotic"),
     "Identify Precipitant": tc(60, "GI bleed, infection (SBP), constipation, medications, electrolytes, dehydration"),
     "CT Head": tc(120, "Rule out structural cause in confused cirrhotic; NOT always hepatic encephalopathy")},
    {"CKD": {"cr": {"min": 3.0, "max": 8.0}}}
)

NEW["Acute Hydrocephalus"] = dx(
    "Neurological", "Neurological",
    v(60, 190, 110, 12, 98.6, 97),
    {**STD_MOD, "heart_rate": "inverse", "systolic_bp": "multiply"},
    {"heart_rate": 8, "systolic_bp": 10, "o2_saturation": 2},
    "Headache, vomiting, altered consciousness, Cushing triad (hypertension, bradycardia, irregular respirations), papilledema, upgaze palsy (sunset sign)",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"na": lab(130, 150, "mEq/L", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Head STAT": tc(10, "Dilated ventricles with periventricular edema; identify obstructive cause"),
     "Emergent EVD": tc(30, "External ventricular drain by neurosurgery; definitive CSF diversion"),
     "Head of Bed 30°": tc(5, "Elevate HOB to promote venous drainage; avoid neck flexion/rotation"),
     "Mannitol or Hypertonic Saline": tc(30, "Mannitol 1g/kg or 23.4% NaCl 30mL for acute ICP crisis while awaiting EVD")},
)

NEW["Cerebral Edema - Malignant MCA Infarct"] = dx(
    "Neurological", "Neurological",
    v(70, 180, 100, 14, 98.6, 96),
    {**STD_MOD, "heart_rate": "inverse", "systolic_bp": "multiply"},
    {"heart_rate": 6, "systolic_bp": 10, "o2_saturation": 2},
    "Large MCA territory infarct with progressive edema 24-72h post-stroke, altered consciousness, herniation signs (fixed dilated pupil, decerebrate posturing), midline shift",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"na": lab(135, 155, "mEq/L", "variable"), "glu": lab(80, 250, "mg/dL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"CT Head": tc(15, "Large hypodensity with midline shift >5mm; effacement of basal cisterns"),
     "Decompressive Hemicraniectomy": tc(720, "For age <60 with malignant MCA stroke; reduces mortality from 78% to 29% (DECIMAL/DESTINY/HAMLET)"),
     "Osmotic Therapy": tc(30, "Mannitol 1g/kg or 23.4% NaCl; temporizing measure for ICP control"),
     "HOB 30° + Avoid Fever": tc(15, "Optimize ICP management: midline head position, avoid hyperthermia, normoventilation")},
)

NEW["Brain Death Evaluation"] = dx(
    "Neurological", "Neurological",
    v(75, 100, 60, 14, 97.5, 96),
    STD_MOD,
    {"heart_rate": 5, "systolic_bp": 15, "o2_saturation": 2},
    "Coma, absent brainstem reflexes (pupils fixed dilated, no corneal, no oculocephalic, no gag, no cough), no motor response to central pain, on ventilator",
    {"o2_saturation_below": 90, "systolic_bp_below": 70},
    {"na": lab(130, 155, "mEq/L", "variable"), "glu": lab(60, 250, "mg/dL", "variable"),
     "temp": lab(97, 99, "°F", "normal")},
    ["IV Access", "Continuous Monitoring"],
    {"Prerequisite Checklist": tc(60, "No confounders: temp >36°C, SBP >100, no paralytics, no sedatives, no severe metabolic derangement"),
     "Clinical Exam x2": tc(360, "Two separate exams by protocol; all brainstem reflexes absent; state-specific timing requirements"),
     "Apnea Test": tc(60, "Disconnect ventilator; observe 8-10min for respiratory effort; PaCO2 must rise >60 or >20 above baseline"),
     "Ancillary Testing": tc(120, "If clinical exam cannot be completed: nuclear perfusion scan, EEG, or CTA per institutional protocol")},
)

NEW["Autonomic Dysreflexia"] = dx(
    "Neurological", "Neurological",
    v(55, 220, 130, 16, 98.6, 97),
    {**STD_MOD, "heart_rate": "inverse", "systolic_bp": "multiply", "diastolic_bp": "multiply"},
    {"heart_rate": 6, "systolic_bp": 10, "diastolic_bp": 8, "o2_saturation": 1},
    "Severe paroxysmal hypertension in T6 or above spinal cord injury, pounding headache, diaphoresis/flushing above lesion, piloerection, bradycardia, nasal congestion",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {},
    ["Continuous Monitoring"],
    {"Sit Upright": tc(2, "Immediately elevate HOB to 90°; lower legs; reduces BP via orthostatic mechanism"),
     "Find and Remove Stimulus": tc(10, "Check Foley catheter (kinked, blocked), bowel impaction, skin pressure, tight clothing"),
     "Catheterize if Bladder Full": tc(15, "Use lidocaine jelly; bladder distension is #1 cause (85%)"),
     "Antihypertensive": tc(15, "Nifedipine 10mg sublingual or nitropaste 1 inch if SBP remains >150 after stimulus removal")},
)

# ─── DEMYELINATING ───────────────────────────────────────────────────

NEW["Multiple Sclerosis - Acute Relapse"] = dx(
    "Neurological", "Neurological",
    v(80, 120, 75, 16, 98.6, 98),
    STD_MOD,
    {"heart_rate": 2, "systolic_bp": 2, "o2_saturation": 1},
    "New or worsening neurological symptoms >24h: optic neuritis, internuclear ophthalmoplegia, Lhermitte sign, spasticity, ataxia, sensory deficits, bladder dysfunction",
    {"o2_saturation_below": 92, "systolic_bp_below": 85},
    {"csf_bands": lab(2, 20, "bands", "elevated"), "csf_protein": lab(20, 80, "mg/dL", "variable")},
    ["Continuous Monitoring"],
    {"MRI Brain + Spine with Gadolinium": tc(120, "New T2/FLAIR lesions with gadolinium enhancement (active); dissemination in space and time"),
     "IV Methylprednisolone": tc(60, "1g/day x3-5 days; speeds recovery from relapse but does not alter long-term disability"),
     "PLEX": tc(240, "For steroid-refractory relapse with severe disability"),
     "Neurology Consult": tc(120, "Disease-modifying therapy initiation or escalation")},
)

NEW["Optic Neuritis"] = dx(
    "Neurological", "Neurological",
    v(78, 120, 75, 16, 98.6, 99),
    STD_MOD,
    {"heart_rate": 2, "systolic_bp": 2, "o2_saturation": 0},
    "Subacute monocular vision loss over days, pain with eye movement, relative afferent pupillary defect (RAPD), red desaturation, typically young woman, often first MS presentation",
    {"o2_saturation_below": 92, "systolic_bp_below": 90},
    {"csf_bands": lab(0, 10, "bands", "variable"), "nmo_ab": lab(0, 1, "titer", "variable"),
     "mog_ab": lab(0, 1, "titer", "variable")},
    ["Continuous Monitoring"],
    {"MRI Brain + Orbits": tc(120, "Optic nerve enhancement; brain lesions predict MS conversion risk"),
     "IV Methylprednisolone": tc(60, "1g/day x3 days if severe vision loss; speeds recovery but doesn't change final visual acuity (ONTT)"),
     "Visual Acuity + Color Testing": tc(30, "Serial Snellen acuity, color plates; red desaturation very sensitive"),
     "NMO/MOG Antibodies": tc(240, "Critical to distinguish from NMOSD/MOGAD which require different treatment")},
)

NEW["Neuromyelitis Optica Spectrum Disorder (NMOSD)"] = dx(
    "Neurological", "Neurological",
    v(85, 120, 75, 16, 98.6, 97),
    STD_MOD,
    {"heart_rate": 3, "systolic_bp": 3, "o2_saturation": 1},
    "Severe optic neuritis (often bilateral) AND longitudinally extensive transverse myelitis (≥3 vertebral segments), area postrema syndrome (intractable hiccups/vomiting), AQP4-IgG positive",
    {"o2_saturation_below": 90, "systolic_bp_below": 85},
    {"nmo_ab": lab(1, 1000, "titer", "elevated"), "csf_wbc": lab(10, 500, "/uL", "elevated"),
     "csf_protein": lab(50, 200, "mg/dL", "elevated")},
    ["IV Access", "Continuous Monitoring"],
    {"IV Methylprednisolone": tc(60, "1g/day x5 days; acute relapse treatment"),
     "PLEX": tc(240, "5-7 sessions; particularly effective for NMOSD relapses; start early if severe"),
     "AQP4-IgG Testing": tc(120, "Cell-based assay most sensitive; seropositivity is diagnostic criterion"),
     "Rituximab/Eculizumab": tc(240, "B-cell depletion as maintenance therapy; DO NOT use MS drugs (interferon worsens NMOSD)")},
)

def main():
    with open(OUTPUT, "r") as f:
        data = json.load(f)

    existing = len(data["diagnoses"])
    added = 0
    for name, entry in NEW.items():
        if name not in data["diagnoses"]:
            data["diagnoses"][name] = entry
            added += 1
        else:
            print(f"  SKIP (exists): {name}")

    data["_meta"]["version"] = "2.3.0"
    data["_meta"]["last_updated"] = "2026-03-29"
    cats = sorted(set(e["category"] for e in data["diagnoses"].values()))
    data["_meta"]["description"] = (
        f"Comprehensive medical knowledge database. "
        f"{len(data['diagnoses'])} diagnoses across {len(cats)} categories."
    )

    with open(OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

    total = len(data["diagnoses"])
    print(f"\n✅ Neurological batch: {existing} existing + {added} new = {total} total")
    print(f"📂 Categories ({len(cats)}): {', '.join(cats)}")

if __name__ == "__main__":
    main()

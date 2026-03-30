#!/usr/bin/env python3
"""
Batch builder: Respiratory diagnoses.
Adds ~52 new respiratory diagnoses to diagnosis_data.json.
Run:  python3 batch_respiratory.py
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

# ─── OBSTRUCTIVE AIRWAY ─────────────────────────────────────────────

NEW["Acute Asthma Exacerbation - Mild/Moderate"] = dx(
    "Respiratory", "Pulmonary",
    v(100, 130, 80, 24, 98.6, 93),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 4, "heart_rate": 5},
    "Diffuse expiratory wheezing, prolonged expiratory phase, accessory muscle use, speaking in full sentences, tachypnea",
    {"o2_saturation_below": 88, "systolic_bp_below": 85},
    {"abg_pco2": lab(30, 42, "mmHg", "variable"), "abg_po2": lab(65, 95, "mmHg", "variable"),
     "peak_flow": lab(50, 80, "%predicted", "decreased")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"Albuterol Nebulizer": tc(15, "2.5mg neb q20min x3, then q1-4h PRN; continuous neb for severe"),
     "Ipratropium": tc(30, "0.5mg neb with first 3 albuterol treatments"),
     "Systemic Corticosteroids": tc(60, "Prednisone 40-60mg PO or methylprednisolone 125mg IV"),
     "Peak Flow Monitoring": tc(30, "Serial PEFR to assess response; target >70% predicted for discharge")},
)

NEW["Status Asthmaticus"] = dx(
    "Respiratory", "Pulmonary",
    v(130, 120, 70, 32, 98.6, 82),
    STD_MOD,
    {"respiratory_rate": 10, "o2_saturation": 8, "heart_rate": 8},
    "Severe wheezing progressing to silent chest, unable to speak, diaphoresis, accessory muscle use, paradoxical breathing, obtunded if fatigue",
    {"o2_saturation_below": 80, "systolic_bp_below": 80},
    {"abg_pco2": lab(42, 70, "mmHg", "elevated"), "abg_po2": lab(40, 70, "mmHg", "decreased"),
     "lactate": lab(2.0, 6.0, "mmol/L", "elevated"), "k": lab(3.0, 5.0, "mEq/L", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Continuous Albuterol": tc(10, "10-20mg/hr continuous nebulization; do NOT use metered-dose inhaler"),
     "IV Magnesium": tc(30, "2g MgSO4 IV over 20 min; bronchial smooth muscle relaxation"),
     "IV Corticosteroids": tc(30, "Methylprednisolone 125mg IV; takes 4-6h for effect"),
     "Intubation Preparation": tc(15, "Prepare for RSI with ketamine (bronchodilator); beware peri-intubation arrest from hyperinflation")},
)

NEW["COPD Exacerbation - Mild"] = dx(
    "Respiratory", "Pulmonary",
    v(95, 135, 82, 22, 98.6, 90),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 4, "heart_rate": 4},
    "Increased dyspnea/cough/sputum production, diffuse wheezing and rhonchi, barrel chest, pursed-lip breathing, mild accessory muscle use",
    {"o2_saturation_below": 85, "systolic_bp_below": 85},
    {"abg_pco2": lab(42, 55, "mmHg", "elevated"), "abg_po2": lab(55, 75, "mmHg", "decreased"),
     "wbc": lab(8, 15, "K/uL", "variable"), "bnp": lab(50, 300, "pg/mL", "variable")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"Bronchodilators": tc(15, "Albuterol + ipratropium neb q4-6h; short-acting bronchodilator relief"),
     "Systemic Steroids": tc(60, "Prednisone 40mg PO daily x5 days (GOLD guidelines)"),
     "Antibiotics": tc(120, "Azithromycin or doxycycline if increased sputum purulence or severity"),
     "Titrated O2": tc(15, "Target SpO2 88-92%; avoid hyperoxia causing CO2 narcosis")},
)

NEW["COPD Exacerbation - Severe with Respiratory Failure"] = dx(
    "Respiratory", "Pulmonary",
    v(115, 150, 90, 30, 99.5, 80),
    STD_MOD,
    {"respiratory_rate": 10, "o2_saturation": 8, "heart_rate": 8},
    "Severe dyspnea, tripod positioning, accessory muscle use, paradoxical abdominal breathing, cyanosis, altered mental status, minimal air movement",
    {"o2_saturation_below": 78, "systolic_bp_below": 80},
    {"abg_pco2": lab(55, 90, "mmHg", "elevated"), "abg_po2": lab(35, 60, "mmHg", "decreased"),
     "abg_ph": lab(7.18, 7.35, "pH", "decreased"), "lactate": lab(2.0, 6.0, "mmol/L", "elevated"),
     "bnp": lab(100, 1000, "pg/mL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"BiPAP": tc(15, "IPAP 12-20, EPAP 5-8; first-line for COPD with acute hypercapnic respiratory failure; reduces intubation by 50%"),
     "Bronchodilators + Steroids": tc(30, "Continuous albuterol neb + methylprednisolone 125mg IV"),
     "Intubation": tc(30, "If BiPAP fails, GCS declining, or hemodynamic instability; use low tidal volume, long expiratory time"),
     "Blood Gas Monitoring": tc(60, "Repeat ABG after 1h of BiPAP to assess response")},
)

NEW["Bronchiectasis Exacerbation"] = dx(
    "Respiratory", "Pulmonary",
    v(100, 125, 78, 22, 100.5, 92),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 4, "heart_rate": 5},
    "Chronic productive cough with purulent sputum (>200mL/day), coarse crackles, clubbing, hemoptysis possible, foul-smelling sputum",
    {"o2_saturation_below": 88, "systolic_bp_below": 85},
    {"wbc": lab(10, 22, "K/uL", "elevated"), "crp": lab(2, 15, "mg/dL", "elevated"),
     "sputum_cx": lab(0, 0, "pathogens", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Sputum Culture": tc(60, "Culture before antibiotics; Pseudomonas common in severe bronchiectasis"),
     "IV Antibiotics": tc(60, "Anti-pseudomonal coverage (piperacillin-tazobactam, cefepime, or meropenem) if severe"),
     "Chest Physiotherapy": tc(120, "Airway clearance techniques; postural drainage; Flutter/Acapella valve"),
     "CT Chest": tc(240, "HRCT to assess extent; signet ring sign, tram-track sign")},
    {"Cystic Fibrosis": {"sputum_cx": {"min": 0, "max": 0, "note": "Pseudomonas, Burkholderia likely"}}}
)

# ─── INFECTIONS ──────────────────────────────────────────────────────

NEW["Community-Acquired Pneumonia - Moderate"] = dx(
    "Respiratory", "Pulmonary",
    v(105, 120, 75, 24, 102.0, 92),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 4, "heart_rate": 5},
    "Productive cough, focal crackles and rhonchi, decreased breath sounds, dullness to percussion, egophony, tactile fremitus increased",
    {"o2_saturation_below": 88, "systolic_bp_below": 85},
    {"wbc": lab(12, 25, "K/uL", "elevated"), "crp": lab(3, 20, "mg/dL", "elevated"),
     "procalcitonin": lab(0.25, 10, "ng/mL", "elevated"), "lactate": lab(1.0, 3.0, "mmol/L", "variable"),
     "cr": lab(0.6, 1.6, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Blood Cultures": tc(60, "2 sets before antibiotics for hospitalized patients"),
     "Empiric Antibiotics": tc(60, "Ceftriaxone 1g IV + azithromycin 500mg IV per ATS/IDSA guidelines"),
     "CXR": tc(30, "Confirm infiltrate; lobar consolidation vs interstitial pattern"),
     "CURB-65 Assessment": tc(30, "Risk stratify: Confusion, Urea, RR, BP, Age ≥65; score ≥2 = admit")},
)

NEW["Hospital-Acquired Pneumonia (HAP)"] = dx(
    "Respiratory", "Pulmonary/Infectious",
    v(110, 110, 65, 26, 102.5, 88),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 5, "heart_rate": 6},
    "New or worsening cough, purulent sputum, focal crackles, fever >48h after admission, leukocytosis, new infiltrate on CXR",
    {"o2_saturation_below": 85, "systolic_bp_below": 80},
    {"wbc": lab(12, 30, "K/uL", "elevated"), "procalcitonin": lab(0.5, 20, "ng/mL", "elevated"),
     "crp": lab(5, 25, "mg/dL", "elevated"), "lactate": lab(1.5, 5.0, "mmol/L", "elevated"),
     "cr": lab(0.8, 2.5, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Respiratory Cultures": tc(60, "Before antibiotics: sputum or BAL; cover MDR pathogens"),
     "Broad-Spectrum Antibiotics": tc(60, "Piperacillin-tazobactam or meropenem ± vancomycin for MRSA risk per local antibiogram"),
     "De-escalation Plan": tc(4320, "Narrow antibiotics based on culture results within 48-72h")},
)

NEW["Ventilator-Associated Pneumonia (VAP)"] = dx(
    "Respiratory", "Pulmonary/Infectious",
    v(110, 105, 62, 28, 103.0, 87),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 6, "heart_rate": 6},
    "New infiltrate on CXR ≥48h after intubation, purulent secretions, worsening oxygenation/ventilation, fever, leukocytosis",
    {"o2_saturation_below": 83, "systolic_bp_below": 78},
    {"wbc": lab(14, 30, "K/uL", "elevated"), "procalcitonin": lab(0.5, 25, "ng/mL", "elevated"),
     "tracheal_aspirate": lab(0, 0, "CFU", "variable"), "lactate": lab(1.5, 5.0, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"BAL or Tracheal Aspirate": tc(60, "Quantitative cultures before changing antibiotics"),
     "Empiric Antibiotics": tc(60, "Double-cover gram negatives ± MRSA coverage based on risk; meropenem + vancomycin + antipseudomonal"),
     "Ventilator Bundle Review": tc(120, "HOB elevation, daily sedation vacation, SBT assessment, DVT and stress ulcer prophylaxis")},
)

NEW["Lung Abscess"] = dx(
    "Respiratory", "Pulmonary",
    v(100, 115, 72, 22, 101.5, 93),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 3, "heart_rate": 5},
    "Foul-smelling purulent sputum, night sweats, weight loss, fever, crackles over abscess, possible amphoric breath sounds, clubbing if chronic",
    {"o2_saturation_below": 88, "systolic_bp_below": 85},
    {"wbc": lab(12, 25, "K/uL", "elevated"), "crp": lab(3, 20, "mg/dL", "elevated"),
     "alb": lab(2.0, 3.5, "g/dL", "decreased"), "hgb": lab(9, 13, "g/dL", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"CT Chest": tc(120, "Thick-walled cavity with air-fluid level; typically in posterior upper lobes or superior lower lobes"),
     "Prolonged Antibiotics": tc(60, "Ampicillin-sulbactam or clindamycin + fluoroquinolone; 4-6 weeks typical course"),
     "Sputum Cultures": tc(60, "Anaerobic and aerobic cultures; mixed flora common"),
     "IR Drainage": tc(240, "Percutaneous drainage if >6cm or failing medical therapy after 7-10 days")},
)

NEW["Aspiration Pneumonia"] = dx(
    "Respiratory", "Pulmonary",
    v(105, 118, 72, 24, 101.0, 90),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 4, "heart_rate": 5},
    "Witnessed aspiration event or risk factors (altered consciousness, dysphagia), rhonchi/crackles in dependent lung zones, foul-smelling sputum",
    {"o2_saturation_below": 85, "systolic_bp_below": 80},
    {"wbc": lab(10, 22, "K/uL", "elevated"), "crp": lab(2, 15, "mg/dL", "elevated"),
     "procalcitonin": lab(0.1, 5, "ng/mL", "variable"), "abg_po2": lab(55, 80, "mmHg", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"CXR": tc(30, "Infiltrate in dependent segments — RLL (upright) or posterior upper lobes (supine)"),
     "Antibiotics": tc(60, "Ampicillin-sulbactam or clindamycin for anaerobic coverage; NOT needed for aspiration pneumonitis alone"),
     "Aspiration Precautions": tc(15, "HOB >30°, NPO, swallow eval if recurrent"),
     "Suctioning": tc(5, "Clear airway of visible aspirate if intubated")},
)

NEW["Empyema"] = dx(
    "Respiratory", "Pulmonary",
    v(110, 115, 70, 24, 102.5, 91),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 4, "heart_rate": 6},
    "Persistent fever despite antibiotics for pneumonia, decreased breath sounds with dullness to percussion, reduced chest expansion, pleuritic pain",
    {"o2_saturation_below": 86, "systolic_bp_below": 80},
    {"wbc": lab(15, 30, "K/uL", "elevated"), "crp": lab(5, 25, "mg/dL", "elevated"),
     "ldh": lab(200, 1000, "U/L", "elevated"), "glu": lab(20, 60, "mg/dL", "decreased"),
     "pleural_ph": lab(6.0, 7.20, "pH", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"CT Chest": tc(60, "Loculated pleural effusion with enhancing pleural thickening (split pleura sign)"),
     "Thoracentesis": tc(60, "Diagnostic: pH <7.20, glucose <60, LDH >3x serum, positive Gram stain/culture"),
     "Chest Tube Drainage": tc(120, "Large-bore tube for frank pus; consider tPA/DNase if loculated"),
     "VATS": tc(240, "If chest tube drainage inadequate after 72h; thoracic surgery consult")},
)

# ─── PLEURAL/CHEST WALL ─────────────────────────────────────────────

NEW["Spontaneous Pneumothorax - Primary"] = dx(
    "Respiratory", "Pulmonary",
    v(95, 120, 78, 20, 98.6, 95),
    STD_MOD,
    {"respiratory_rate": 5, "o2_saturation": 2, "heart_rate": 4},
    "Sudden pleuritic chest pain, decreased breath sounds unilaterally, hyperresonance to percussion, typically tall thin young male",
    {"o2_saturation_below": 90, "systolic_bp_below": 85},
    {"abg_po2": lab(70, 95, "mmHg", "variable")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"CXR": tc(30, "Visceral pleural line with absent lung markings peripherally; expiratory film may help"),
     "Needle Aspiration": tc(60, "For first episode >2cm on CXR; 16-18g needle 2nd ICS MCL"),
     "Chest Tube": tc(60, "If aspiration fails or large/symptomatic; 14-16 Fr anterior or pigtail catheter"),
     "High-Flow O2": tc(15, "100% O2 increases reabsorption rate 4x for small pneumothorax managed conservatively")},
)

NEW["Spontaneous Pneumothorax - Secondary"] = dx(
    "Respiratory", "Pulmonary",
    v(110, 115, 70, 26, 98.6, 86),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 5, "heart_rate": 6},
    "Dyspnea out of proportion to pneumothorax size (limited reserve), absent breath sounds, underlying lung disease (COPD, CF), cyanosis possible",
    {"o2_saturation_below": 82, "systolic_bp_below": 80},
    {"abg_po2": lab(45, 70, "mmHg", "decreased"), "abg_pco2": lab(42, 65, "mmHg", "elevated"),
     "lactate": lab(1.0, 4.0, "mmol/L", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"CXR": tc(15, "Confirm pneumothorax; may be harder to see with underlying emphysema"),
     "Chest Tube": tc(30, "All secondary pneumothorax >1cm or symptomatic require chest tube; NOT aspiration alone"),
     "Thoracic Surgery Consult": tc(120, "VATS with pleurodesis for recurrent; higher recurrence rate than primary")},
    {"COPD": {"abg_pco2": {"min": 50, "max": 80}}}
)

NEW["Hemothorax"] = dx(
    "Respiratory", "Pulmonary/Trauma",
    v(120, 90, 55, 24, 98.6, 90),
    STD_MOD,
    {"systolic_bp": 18, "diastolic_bp": 12, "o2_saturation": 4, "heart_rate": 8},
    "Decreased breath sounds with dullness to percussion, signs of hemorrhage (tachycardia, hypotension), chest wall trauma, deviated trachea if massive",
    {"o2_saturation_below": 85, "systolic_bp_below": 70},
    {"hgb": lab(6, 12, "g/dL", "decreased"), "lactate": lab(2.0, 8.0, "mmol/L", "elevated"),
     "pt_inr": lab(0.9, 2.0, "INR", "variable")},
    ["IV Access", "Fluid Resuscitation", "Oxygen Therapy", "Continuous Monitoring"],
    {"Chest Tube": tc(30, "32-36 Fr tube thoracostomy for drainage and autotransfusion assessment"),
     "Massive Transfusion": tc(15, "If initial output >1500mL or ongoing >200mL/hr for 2-4h"),
     "Thoracotomy": tc(120, "If >1500mL initial or >200mL/hr x4h; trauma surgery consult"),
     "CXR": tc(15, "Post-tube placement to assess drainage and lung re-expansion")},
)

NEW["Malignant Pleural Effusion"] = dx(
    "Respiratory", "Pulmonary/Oncologic",
    v(95, 120, 75, 22, 98.6, 91),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 4, "heart_rate": 4},
    "Progressive dyspnea, decreased breath sounds at base, dullness to percussion, weight loss, cachexia, known or suspected malignancy",
    {"o2_saturation_below": 86, "systolic_bp_below": 85},
    {"ldh": lab(200, 800, "U/L", "elevated"), "protein": lab(3.0, 6.0, "g/dL", "elevated"),
     "glu": lab(40, 100, "mg/dL", "variable"), "hgb": lab(8, 12, "g/dL", "decreased")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"Thoracentesis": tc(60, "Therapeutic AND diagnostic; exudative (Light's criteria); send cytology"),
     "Indwelling Pleural Catheter": tc(240, "For recurrent symptomatic effusion; outpatient drainage"),
     "CT Chest": tc(120, "Assess underlying tumor, pleural nodularity, adenopathy"),
     "Oncology Consult": tc(240, "Systemic therapy, pleurodesis, or palliative care discussion")},
)

NEW["Chylothorax"] = dx(
    "Respiratory", "Pulmonary",
    v(85, 118, 74, 18, 98.6, 94),
    STD_MOD,
    {"respiratory_rate": 5, "o2_saturation": 2, "heart_rate": 3},
    "Dyspnea, milky white pleural fluid, post-surgical (thoracic/esophageal) or traumatic, non-pleuritic, weight loss",
    {"o2_saturation_below": 88, "systolic_bp_below": 85},
    {"triglycerides": lab(110, 1000, "mg/dL", "elevated"), "chol": lab(40, 100, "mg/dL", "variable"),
     "alb": lab(2.0, 3.5, "g/dL", "decreased"), "lymph_count": lab(500, 5000, "/uL", "variable")},
    ["IV Access", "Continuous Monitoring"],
    {"Thoracentesis": tc(60, "Milky fluid; triglycerides >110mg/dL diagnostic; chylomicrons on lipoprotein analysis"),
     "Chest Tube": tc(120, "Continuous drainage for respiratory compromise"),
     "NPO + TPN or MCT Diet": tc(120, "Reduce chyle output; MCT are absorbed directly into portal system, bypassing lymphatics"),
     "Thoracic Duct Ligation": tc(4320, "If output >1L/day for >5 days or nutritional depletion")},
)

# ─── ACUTE RESPIRATORY FAILURE ───────────────────────────────────────

NEW["ARDS - Mild"] = dx(
    "Respiratory", "Pulmonary",
    v(105, 110, 68, 26, 100.5, 88),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 5, "heart_rate": 6},
    "Acute onset bilateral infiltrates, tachypnea, dyspnea, hypoxemia refractory to supplemental O2, crackles bilaterally, no evidence of cardiogenic cause",
    {"o2_saturation_below": 82, "systolic_bp_below": 80},
    {"abg_po2": lab(200, 300, "mmHg", "decreased"), "abg_pco2": lab(30, 45, "mmHg", "variable"),
     "bnp": lab(0, 100, "pg/mL", "normal"), "crp": lab(5, 25, "mg/dL", "elevated"),
     "lactate": lab(1.5, 4.0, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"CXR": tc(30, "Bilateral opacities not fully explained by effusions or atelectasis"),
     "High-Flow Nasal Cannula": tc(15, "HFNC at 40-60 LPM; may avoid intubation in mild ARDS"),
     "Treat Underlying Cause": tc(60, "Sepsis, pneumonia, aspiration — address the trigger"),
     "Serial ABGs": tc(120, "Monitor P/F ratio; worsening suggests progression")},
)

NEW["ARDS - Moderate/Severe"] = dx(
    "Respiratory", "Pulmonary",
    v(120, 95, 58, 32, 101.0, 78),
    STD_MOD,
    {"respiratory_rate": 10, "o2_saturation": 8, "heart_rate": 8},
    "Severe hypoxemia (P/F <150), bilateral white-out on CXR, stiff lungs on ventilator, high FiO2 requirement, refractory to recruitment",
    {"o2_saturation_below": 75, "systolic_bp_below": 70},
    {"abg_po2": lab(50, 150, "mmHg", "decreased"), "abg_pco2": lab(35, 60, "mmHg", "variable"),
     "lactate": lab(2.0, 8.0, "mmol/L", "elevated"), "bnp": lab(0, 100, "pg/mL", "normal"),
     "cr": lab(1.0, 4.0, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Intubation", "Continuous Monitoring"],
    {"Low Tidal Volume Ventilation": tc(30, "ARDSNet protocol: Vt 4-6 mL/kg IBW, plateau pressure ≤30 cmH2O"),
     "Prone Positioning": tc(120, "16+ hours/day for P/F <150; proven mortality benefit (PROSEVA trial)"),
     "Neuromuscular Blockade": tc(60, "Cisatracurium for first 48h if P/F <150; consider early in severe ARDS"),
     "Conservative Fluid Strategy": tc(120, "Target CVP <4 or PAOP <8; avoid fluid overload")},
)

NEW["Acute Respiratory Failure - Hypoxemic (Type 1)"] = dx(
    "Respiratory", "Pulmonary",
    v(110, 115, 70, 28, 99.0, 83),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 6, "heart_rate": 6},
    "Acute dyspnea, tachypnea, cyanosis, accessory muscle use, variable lung exam depending on cause, PaO2 <60 on room air",
    {"o2_saturation_below": 78, "systolic_bp_below": 80},
    {"abg_po2": lab(35, 60, "mmHg", "decreased"), "abg_pco2": lab(25, 38, "mmHg", "decreased"),
     "lactate": lab(1.5, 5.0, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"ABG": tc(30, "Confirm type 1 (hypoxemic) failure: PaO2 <60, PaCO2 normal or low"),
     "Identify Etiology": tc(60, "CXR, CT, echo — pneumonia, PE, ARDS, pneumothorax, pulmonary edema"),
     "Escalate O2 Support": tc(15, "NC → HFNC → BiPAP → intubation based on response"),
     "Treat Underlying Cause": tc(60, "Antibiotics, anticoagulation, drainage, etc. based on etiology")},
)

NEW["Acute Respiratory Failure - Hypercapnic (Type 2)"] = dx(
    "Respiratory", "Pulmonary",
    v(100, 140, 85, 12, 98.6, 85),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 5, "heart_rate": 5},
    "Somnolence, confusion, shallow rapid breathing or bradypnea, asterixis, warm flushed skin (CO2 vasodilation), headache, papilledema possible",
    {"o2_saturation_below": 80, "systolic_bp_below": 80},
    {"abg_pco2": lab(50, 90, "mmHg", "elevated"), "abg_po2": lab(40, 65, "mmHg", "decreased"),
     "abg_ph": lab(7.15, 7.35, "pH", "decreased"), "hco3": lab(28, 42, "mEq/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"ABG": tc(15, "Confirm type 2: PaCO2 >50 with acidosis; acute vs chronic (bicarb compensation)"),
     "BiPAP": tc(15, "First-line: IPAP 12-20, EPAP 5-8; addresses ventilatory failure directly"),
     "Controlled O2": tc(10, "Target SpO2 88-92%; do NOT overcorrect oxygen — drives CO2 retention"),
     "Intubation": tc(30, "If BiPAP fails, GCS <8, or hemodynamic instability")},
)

# ─── PULMONARY VASCULAR ─────────────────────────────────────────────

NEW["Submassive Pulmonary Embolism"] = dx(
    "Respiratory", "Pulmonary/Vascular",
    v(115, 100, 62, 24, 98.6, 89),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 4, "heart_rate": 8},
    "Dyspnea, tachycardia, pleuritic chest pain, RV strain on echo but hemodynamically stable, possible DVT signs",
    {"o2_saturation_below": 85, "systolic_bp_below": 85},
    {"d_dimer": lab(1000, 20000, "ng/mL", "elevated"), "troponin": lab(0.04, 2.0, "ng/mL", "elevated"),
     "bnp": lab(100, 1500, "pg/mL", "elevated"), "abg_po2": lab(55, 80, "mmHg", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"CTA Chest": tc(60, "Central or lobar PE; assess RV/LV ratio >0.9 = RV strain"),
     "Bedside Echo": tc(30, "RV dilation, McConnell sign, TAPSE <16mm = significant RV strain"),
     "Heparin Drip": tc(30, "UFH 80 units/kg bolus + 18 units/kg/hr; therapeutic anticoagulation"),
     "Risk Stratify for Escalation": tc(120, "PESI score + troponin + RV function; consider catheter-directed therapy if high risk")},
)

NEW["Saddle Pulmonary Embolism"] = dx(
    "Respiratory", "Pulmonary/Vascular",
    v(130, 75, 45, 30, 98.6, 80),
    STD_MOD,
    {"systolic_bp": 22, "diastolic_bp": 15, "o2_saturation": 8, "heart_rate": 10},
    "Acute dyspnea, near-syncope, severe hypoxemia, RV failure (JVD, RV heave), possible PEA arrest, saddle embolus at bifurcation",
    {"o2_saturation_below": 75, "systolic_bp_below": 60},
    {"d_dimer": lab(5000, 80000, "ng/mL", "elevated"), "troponin": lab(0.5, 10, "ng/mL", "elevated"),
     "bnp": lab(500, 5000, "pg/mL", "elevated"), "lactate": lab(4.0, 12.0, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Fluid Resuscitation", "Continuous Monitoring"],
    {"Systemic Thrombolysis": tc(30, "Alteplase 100mg IV over 2h if hemodynamically unstable; mortality benefit"),
     "Bedside Echo": tc(10, "Massive RV dilation; can diagnose and trigger thrombolysis before CTA"),
     "Heparin": tc(15, "Start immediately; do NOT delay for imaging if clinical suspicion high"),
     "Surgical Embolectomy": tc(120, "If thrombolysis contraindicated or failed; ECMO bridge")},
)

NEW["Pulmonary Infarction"] = dx(
    "Respiratory", "Pulmonary/Vascular",
    v(105, 115, 72, 22, 100.0, 92),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 3, "heart_rate": 5},
    "Pleuritic chest pain, hemoptysis, low-grade fever, pleural friction rub, wedge-shaped peripheral opacity on CXR (Hampton hump)",
    {"o2_saturation_below": 88, "systolic_bp_below": 85},
    {"d_dimer": lab(500, 10000, "ng/mL", "elevated"), "ldh": lab(200, 600, "U/L", "elevated"),
     "wbc": lab(8, 15, "K/uL", "variable"), "abg_po2": lab(60, 85, "mmHg", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"CTA Chest": tc(60, "Segmental/subsegmental PE with peripheral wedge-shaped consolidation"),
     "Anticoagulation": tc(30, "Standard anticoagulation for PE; additional management for infarction is supportive"),
     "Pain Management": tc(30, "NSAIDs or opioids for pleuritic pain; facilitates deep breathing")},
)

NEW["Fat Embolism Syndrome"] = dx(
    "Respiratory", "Pulmonary/Multi-system",
    v(120, 100, 60, 28, 101.0, 82),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 6, "heart_rate": 8},
    "Classic triad: respiratory distress + neurological changes + petechial rash (conjunctiva, axillae, chest) 24-72h post-long bone fracture, ARDS-like picture",
    {"o2_saturation_below": 78, "systolic_bp_below": 75},
    {"hgb": lab(8, 12, "g/dL", "decreased"), "plt": lab(80, 150, "K/uL", "decreased"),
     "lipase": lab(50, 300, "U/L", "elevated"), "abg_po2": lab(45, 70, "mmHg", "decreased"),
     "fibrinogen": lab(100, 300, "mg/dL", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Supportive Care": tc(30, "No specific treatment; supportive respiratory care is mainstay"),
     "Mechanical Ventilation": tc(60, "ARDSNet protocol if intubated; lung-protective ventilation"),
     "Early Fracture Fixation": tc(240, "Reduces ongoing fat embolization; orthopedic consult"),
     "Serial Monitoring": tc(120, "Neurological checks, platelet trends, SpO2; usually self-limiting 72h")},
)

NEW["Air Embolism"] = dx(
    "Respiratory", "Pulmonary/Vascular",
    v(130, 75, 45, 30, 98.6, 78),
    STD_MOD,
    {"systolic_bp": 20, "diastolic_bp": 15, "o2_saturation": 8, "heart_rate": 10},
    "Sudden cardiovascular collapse during central line placement/removal, mill wheel murmur on auscultation, acute dyspnea, may gasp, altered consciousness",
    {"o2_saturation_below": 72, "systolic_bp_below": 60},
    {"lactate": lab(3.0, 10.0, "mmol/L", "elevated"), "troponin": lab(0.1, 5.0, "ng/mL", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Left Lateral Decubitus + Trendelenburg": tc(2, "Durant maneuver: left side down, head down; traps air in RV apex away from RVOT"),
     "100% FiO2": tc(5, "Speeds nitrogen reabsorption from emboli"),
     "Aspiration via Central Line": tc(15, "If multi-orifice RA catheter in place, aspirate air directly"),
     "Hyperbaric Oxygen": tc(120, "If available and cerebral air embolism suspected; reduces bubble size")},
)

# ─── UPPER AIRWAY ────────────────────────────────────────────────────

NEW["Epiglottitis - Adult"] = dx(
    "Respiratory", "Upper Airway",
    v(110, 125, 78, 24, 102.5, 93),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 4, "heart_rate": 6},
    "Severe sore throat, muffled 'hot potato' voice, drooling, tripod positioning, stridor, dysphagia, fever, thumbprint sign on lateral neck XR",
    {"o2_saturation_below": 85, "systolic_bp_below": 80},
    {"wbc": lab(12, 25, "K/uL", "elevated"), "crp": lab(3, 20, "mg/dL", "elevated"),
     "blood_cx": lab(0, 0, "pos/neg", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Airway Management": tc(15, "ENT + anesthesia at bedside; fiberoptic intubation preferred; surgical airway backup ready"),
     "IV Antibiotics": tc(30, "Ceftriaxone 2g IV + vancomycin for H. influenzae, Strep, Staph coverage"),
     "IV Dexamethasone": tc(30, "0.5mg/kg IV; reduces mucosal edema"),
     "Avoid Agitation": tc(5, "NO tongue depressors, NO blind oropharyngeal exam — can precipitate complete obstruction")},
)

NEW["Angioedema - Hereditary"] = dx(
    "Respiratory", "Upper Airway/Immunologic",
    v(100, 125, 78, 22, 98.6, 94),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 3, "heart_rate": 5},
    "Non-pitting, non-pruritic swelling of face/lips/tongue/larynx, NO urticaria (distinguishes from allergic), positive family history, abdominal pain attacks",
    {"o2_saturation_below": 88, "systolic_bp_below": 80},
    {"c4": lab(2, 10, "mg/dL", "decreased"), "c1_inh_level": lab(5, 15, "mg/dL", "decreased"),
     "c1_inh_function": lab(10, 50, "%", "decreased"), "tryptase": lab(0, 11, "ng/mL", "normal")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"C1-Esterase Inhibitor Concentrate": tc(30, "Berinert 20 units/kg IV; first-line for HAE attacks"),
     "Icatibant": tc(30, "Bradykinin B2 receptor antagonist SQ; alternative to C1-INH concentrate"),
     "Airway Management": tc(15, "Early intubation if tongue/laryngeal involvement; can progress rapidly"),
     "Epinephrine/Antihistamines NOT Effective": tc(5, "Bradykinin-mediated, NOT histamine; standard allergy drugs do not work")},
)

NEW["Angioedema - ACE Inhibitor Induced"] = dx(
    "Respiratory", "Upper Airway",
    v(95, 135, 85, 20, 98.6, 96),
    STD_MOD,
    {"respiratory_rate": 5, "o2_saturation": 2, "heart_rate": 4},
    "Lip/tongue/uvula swelling in patient on ACE inhibitor, no urticaria, may occur after years on medication, African American patients at higher risk",
    {"o2_saturation_below": 90, "systolic_bp_below": 80},
    {"tryptase": lab(0, 11, "ng/mL", "normal")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Discontinue ACE Inhibitor": tc(5, "Immediately and permanently; switch to ARB with caution (small cross-reactivity risk)"),
     "Airway Assessment": tc(10, "Fiberoptic visualization of larynx if tongue/floor of mouth involved"),
     "Icatibant or Fresh Frozen Plasma": tc(30, "Off-label but emerging evidence for bradykinin-mediated angioedema"),
     "Observation 24h": tc(60, "Can worsen over 24-48h; monitor closely even after improvement")},
)

NEW["Foreign Body Aspiration - Adult"] = dx(
    "Respiratory", "Upper Airway/Pulmonary",
    v(110, 130, 80, 26, 98.6, 88),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 5, "heart_rate": 6},
    "Acute choking episode then persistent cough/wheeze, unilateral wheezing or decreased breath sounds, possible history of elderly/neurological impairment eating",
    {"o2_saturation_below": 82, "systolic_bp_below": 80},
    {"wbc": lab(6, 15, "K/uL", "variable"), "abg_po2": lab(55, 85, "mmHg", "variable")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"Back Blows + Abdominal Thrusts": tc(2, "If complete obstruction and conscious; Heimlich maneuver"),
     "Rigid Bronchoscopy": tc(60, "Definitive removal for tracheal/mainstem objects; performed under general anesthesia"),
     "Flexible Bronchoscopy": tc(120, "For distal objects; can visualize and extract with basket/forceps"),
     "CXR": tc(30, "May show radiopaque object, unilateral hyperinflation (ball-valve effect), or atelectasis")},
)

NEW["Vocal Cord Dysfunction"] = dx(
    "Respiratory", "Upper Airway",
    v(95, 125, 78, 22, 98.6, 96),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 2, "heart_rate": 4},
    "Inspiratory stridor/wheeze (NOT expiratory), 'can't get air in', throat tightness, episodes precipitated by stress/exercise, often misdiagnosed as asthma",
    {"o2_saturation_below": 92, "systolic_bp_below": 90},
    {"peak_flow": lab(70, 100, "%predicted", "variable")},
    ["Continuous Monitoring"],
    {"Laryngoscopy During Attack": tc(30, "Paradoxical vocal cord adduction on inspiration; posterior chink visible"),
     "Reassurance + Breathing Techniques": tc(15, "Panting, sniffing, pursed-lip breathing; resolves most episodes"),
     "Heliox": tc(30, "80/20 helium-oxygen mixture reduces work of breathing through narrowed airway"),
     "Speech Therapy Referral": tc(240, "Laryngeal control techniques; definitive long-term management")},
)

# ─── INTERSTITIAL/RESTRICTIVE ───────────────────────────────────────

NEW["Idiopathic Pulmonary Fibrosis Exacerbation"] = dx(
    "Respiratory", "Pulmonary",
    v(110, 115, 72, 28, 98.6, 82),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 6, "heart_rate": 6},
    "Rapid worsening of dyspnea over days to weeks in known IPF, bilateral velcro crackles at bases, clubbing, new ground-glass opacities on CT",
    {"o2_saturation_below": 78, "systolic_bp_below": 80},
    {"abg_po2": lab(40, 65, "mmHg", "decreased"), "ldh": lab(200, 600, "U/L", "elevated"),
     "kl_6": lab(1000, 5000, "U/mL", "elevated"), "crp": lab(2, 10, "mg/dL", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"High-Flow O2 or BiPAP": tc(15, "Supplemental O2; HFNC preferred; intubation has very poor prognosis"),
     "CT Chest": tc(60, "New bilateral GGOs superimposed on UIP pattern"),
     "Broad-Spectrum Antibiotics": tc(60, "Cover for infection as trigger; empiric until cultures return"),
     "Palliative Care Discussion": tc(120, "AE-IPF has >50% in-hospital mortality; goals of care essential")},
)

NEW["Sarcoidosis - Pulmonary"] = dx(
    "Respiratory", "Pulmonary/Multi-system",
    v(88, 125, 78, 20, 98.6, 95),
    STD_MOD,
    {"respiratory_rate": 5, "o2_saturation": 2, "heart_rate": 3},
    "Bilateral hilar lymphadenopathy on CXR, dry cough, dyspnea, erythema nodosum, anterior uveitis, hypercalcemia possible, young African American",
    {"o2_saturation_below": 90, "systolic_bp_below": 85},
    {"ace_level": lab(40, 120, "U/L", "elevated"), "ca": lab(10.5, 13.0, "mg/dL", "elevated"),
     "crp": lab(1, 8, "mg/dL", "elevated"), "vitd_1_25": lab(65, 150, "pg/mL", "elevated"),
     "alp": lab(40, 200, "U/L", "elevated")},
    ["Continuous Monitoring"],
    {"CXR": tc(30, "Bilateral hilar lymphadenopathy (Stage I/II) ± parenchymal infiltrates"),
     "CT Chest": tc(120, "Perilymphatic nodules, hilar/mediastinal lymphadenopathy"),
     "Biopsy": tc(240, "Non-caseating granulomas; transbronchial biopsy or lymph node sampling"),
     "Corticosteroids": tc(240, "Prednisone 20-40mg/day for symptomatic pulmonary disease; not all stages require treatment")},
)

NEW["Eosinophilic Pneumonia - Acute"] = dx(
    "Respiratory", "Pulmonary",
    v(110, 115, 72, 26, 101.0, 86),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 5, "heart_rate": 6},
    "Acute febrile illness with severe hypoxemia, bilateral infiltrates mimicking ARDS, recent new drug/smoke exposure, peripheral eosinophilia may be ABSENT initially",
    {"o2_saturation_below": 80, "systolic_bp_below": 80},
    {"eosinophils": lab(500, 5000, "/uL", "elevated"), "wbc": lab(10, 25, "K/uL", "elevated"),
     "abg_po2": lab(45, 70, "mmHg", "decreased"), "ige": lab(100, 1000, "IU/mL", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"BAL": tc(120, "BAL eosinophils >25% diagnostic; peripheral eosinophilia may lag"),
     "IV Methylprednisolone": tc(60, "125mg IV q6h then taper; dramatic and rapid response is characteristic"),
     "Stop Offending Agent": tc(15, "New medications, smoking, environmental exposures"),
     "CT Chest": tc(60, "Bilateral peripheral or random GGOs; pleural effusions common")},
)

NEW["Pulmonary Alveolar Hemorrhage"] = dx(
    "Respiratory", "Pulmonary",
    v(120, 100, 60, 28, 99.5, 82),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 6, "heart_rate": 8},
    "Hemoptysis (may be absent in 1/3), dyspnea, bilateral alveolar infiltrates, dropping hemoglobin, often in setting of vasculitis or anti-GBM disease",
    {"o2_saturation_below": 78, "systolic_bp_below": 75},
    {"hgb": lab(5, 10, "g/dL", "decreased"), "cr": lab(1.0, 6.0, "mg/dL", "elevated"),
     "anca": lab(0, 1, "titer", "variable"), "anti_gbm": lab(0, 1, "titer", "variable"),
     "ua_rbc": lab(10, 500, "/hpf", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring", "Intubation"],
    {"Bronchoscopy": tc(120, "Sequentially bloodier BAL aliquots confirm DAH; hemosiderin-laden macrophages"),
     "Pulse Steroids": tc(60, "Methylprednisolone 1g IV daily x3 days; then high-dose oral taper"),
     "Plasmapheresis": tc(120, "For anti-GBM disease or severe ANCA vasculitis with DAH"),
     "Cyclophosphamide": tc(240, "Rituximab as alternative; immunosuppression for underlying vasculitis")},
)

# ─── MISCELLANEOUS PULMONARY ─────────────────────────────────────────

NEW["Massive Hemoptysis"] = dx(
    "Respiratory", "Pulmonary",
    v(120, 100, 60, 28, 98.6, 85),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 5, "heart_rate": 8},
    "Coughing large volumes of blood (>100-600mL/24h), may see bleeding source lateralized, potential airway compromise, possible hemodynamic instability",
    {"o2_saturation_below": 80, "systolic_bp_below": 70},
    {"hgb": lab(6, 12, "g/dL", "decreased"), "pt_inr": lab(0.9, 2.0, "INR", "variable"),
     "plt": lab(50, 200, "K/uL", "variable"), "cr": lab(0.6, 2.0, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Position Bleeding Side Down": tc(2, "Lateral decubitus with affected lung dependent to protect good lung"),
     "Intubation": tc(15, "Large ETT (≥8.0) for bronchoscale; consider selective main bronchus intubation to isolate bleeding"),
     "IR Bronchial Artery Embolization": tc(120, "First-line definitive therapy; >90% success for bronchial artery source"),
     "Rigid Bronchoscopy": tc(60, "Allows airway control + visualization; can tamponade with balloon")},
)

NEW["Obstructive Sleep Apnea - Acute Decompensation"] = dx(
    "Respiratory", "Pulmonary",
    v(85, 150, 95, 14, 98.6, 84),
    STD_MOD,
    {"respiratory_rate": 5, "o2_saturation": 5, "heart_rate": 4},
    "Obesity, somnolence, morning headaches, witnessed apneic episodes, polycythemia, cor pulmonale signs (JVD, edema), Mallampati IV",
    {"o2_saturation_below": 78, "systolic_bp_below": 80},
    {"abg_pco2": lab(50, 70, "mmHg", "elevated"), "abg_po2": lab(45, 65, "mmHg", "decreased"),
     "hgb": lab(15, 20, "g/dL", "elevated"), "hct": lab(50, 60, "%", "elevated"),
     "bnp": lab(100, 800, "pg/mL", "elevated")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"BiPAP": tc(30, "Preferredover CPAP for hypercapnic respiratory failure; IPAP 14-20, EPAP 6-10"),
     "Controlled O2": tc(15, "Target SpO2 88-92%; avoid overcorrection in chronic hypercapnia"),
     "Weight-Based Dosing Caution": tc(30, "Avoid sedatives, opioids; exquisitely sensitive to respiratory depression"),
     "Polysomnography Outpatient": tc(4320, "Formal sleep study for CPAP titration after acute stabilization")},
)

NEW["Obesity Hypoventilation Syndrome"] = dx(
    "Respiratory", "Pulmonary",
    v(90, 145, 90, 12, 98.6, 82),
    STD_MOD,
    {"respiratory_rate": 5, "o2_saturation": 5, "heart_rate": 4},
    "BMI >30 with chronic daytime hypercapnia, somnolence, morning headaches, polycythemia, cor pulmonale, Pickwickian habitus",
    {"o2_saturation_below": 78, "systolic_bp_below": 80},
    {"abg_pco2": lab(50, 80, "mmHg", "elevated"), "abg_po2": lab(40, 65, "mmHg", "decreased"),
     "hco3": lab(28, 40, "mEq/L", "elevated"), "hgb": lab(16, 22, "g/dL", "elevated"),
     "bnp": lab(100, 1000, "pg/mL", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"BiPAP": tc(30, "Average volume-assured pressure support (AVAPS) or standard BiPAP; mainstay of treatment"),
     "ABG Monitoring": tc(60, "Serial ABGs to guide ventilatory support; target PaCO2 improvement"),
     "Diuretics": tc(60, "For cor pulmonale and volume overload; furosemide cautiously"),
     "Weight Loss Referral": tc(240, "Bariatric surgery evaluation for BMI >40 or >35 with comorbidities")},
)

NEW["Pulmonary Contusion"] = dx(
    "Respiratory", "Pulmonary/Trauma",
    v(115, 100, 60, 26, 98.6, 88),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 5, "heart_rate": 6},
    "Post-blunt chest trauma, progressive dyspnea over 24-48h, hemoptysis, crackles over affected area, chest wall ecchymosis, adjacent rib fractures",
    {"o2_saturation_below": 82, "systolic_bp_below": 78},
    {"abg_po2": lab(50, 75, "mmHg", "decreased"), "hgb": lab(8, 14, "g/dL", "variable"),
     "lactate": lab(1.5, 5.0, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"CT Chest": tc(60, "Ground-glass opacity/consolidation not respecting fissures; evolves over 24-48h"),
     "Lung-Protective Ventilation": tc(60, "If intubated: ARDSNet protocol; contusion can progress to ARDS"),
     "Fluid Restriction": tc(60, "Judicious fluids; avoid overhydration which worsens contusion edema"),
     "Pain Management": tc(30, "Rib blocks, epidural, or multimodal analgesia; incentive spirometry")},
)

NEW["Flail Chest"] = dx(
    "Respiratory", "Pulmonary/Trauma",
    v(120, 95, 58, 28, 98.6, 86),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 5, "heart_rate": 7},
    "Paradoxical chest wall movement (segment moves inward on inspiration), severe chest wall pain, crepitus, ≥3 consecutive ribs fractured in ≥2 places, splinting",
    {"o2_saturation_below": 80, "systolic_bp_below": 75},
    {"abg_po2": lab(45, 70, "mmHg", "decreased"), "lactate": lab(2.0, 6.0, "mmol/L", "elevated"),
     "hgb": lab(8, 14, "g/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Aggressive Pain Control": tc(30, "Epidural or intercostal nerve blocks preferred; IV opioids; adequate analgesia prevents atelectasis"),
     "Intubation + PPV": tc(60, "Positive pressure ventilation acts as internal splint; for respiratory failure"),
     "CT Chest": tc(60, "Full assessment of fractures, underlying pulmonary contusion, hemothorax"),
     "Surgical Fixation": tc(720, "Rib plating for severe flail; reduces ventilator days and ICU stay")},
)

NEW["Tracheobronchial Injury"] = dx(
    "Respiratory", "Upper Airway/Trauma",
    v(125, 90, 55, 30, 98.6, 82),
    STD_MOD,
    {"respiratory_rate": 10, "o2_saturation": 6, "heart_rate": 8},
    "Massive subcutaneous emphysema, pneumomediastinum, persistent air leak after chest tube, hemoptysis, voice change if laryngeal, Hamman sign",
    {"o2_saturation_below": 78, "systolic_bp_below": 70},
    {"abg_po2": lab(45, 70, "mmHg", "decreased"), "lactate": lab(2.0, 8.0, "mmol/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Bronchoscopy": tc(60, "Diagnostic: visualize tear; flexible for distal, rigid for proximal/if hemorrhage"),
     "Selective Intubation": tc(15, "Advance ETT past tear under bronchoscopic guidance if needed"),
     "Chest Tube": tc(30, "For pneumothorax; persistent large air leak suggests major airway injury"),
     "Thoracic Surgery Consult": tc(60, "Operative repair for tears >1/3 circumference or deteriorating")},
)

NEW["Smoke Inhalation Injury"] = dx(
    "Respiratory", "Pulmonary/Trauma",
    v(115, 110, 68, 26, 99.0, 88),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 5, "heart_rate": 6},
    "Singed nasal hairs, carbonaceous sputum, hoarseness, oropharyngeal erythema/edema, wheezing, stridor, facial burns, enclosed-space fire history",
    {"o2_saturation_below": 82, "systolic_bp_below": 80},
    {"co_hb": lab(5, 40, "%", "elevated"), "lactate": lab(2.0, 8.0, "mmol/L", "elevated"),
     "abg_po2": lab(55, 80, "mmHg", "decreased"), "cn_level": lab(0.5, 3.0, "mg/L", "elevated")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"100% FiO2": tc(5, "High-flow O2; CO half-life reduced from 5h to 1h on 100% O2; pulse ox unreliable with CO"),
     "Early Intubation": tc(30, "If ANY signs of upper airway involvement — edema rapidly progresses; intubate before swelling worsens"),
     "Bronchoscopy": tc(120, "Assess severity of lower airway injury; soot, erythema, edema below cords"),
     "Hydroxocobalamin": tc(30, "5g IV for suspected cyanide toxicity (enclosed space fire); empiric treatment")},
)

NEW["Near-Drowning / Submersion Injury"] = dx(
    "Respiratory", "Pulmonary",
    v(110, 100, 60, 26, 91.0, 78),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 8, "heart_rate": 6, "temperature_f": "decrease"},
    "Pulmonary edema, hypothermia, altered consciousness, frothy sputum, diffuse crackles, variable GCS, possible cardiac arrest",
    {"o2_saturation_below": 72, "systolic_bp_below": 70},
    {"abg_po2": lab(35, 65, "mmHg", "decreased"), "abg_ph": lab(7.10, 7.35, "pH", "decreased"),
     "lactate": lab(3.0, 15.0, "mmol/L", "elevated"), "k": lab(3.0, 6.0, "mEq/L", "variable"),
     "temp": lab(86, 96, "°F", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"100% FiO2": tc(5, "Immediate high-flow O2; non-cardiogenic pulmonary edema from surfactant washout"),
     "Rewarming": tc(30, "Active rewarming for hypothermia; warm IV fluids, Bair hugger, warm humidified O2"),
     "Intubation": tc(30, "For GCS <8, severe hypoxemia, or hemodynamic instability"),
     "C-Spine Precautions": tc(5, "If diving or mechanism suggestive of cervical injury")},
)

NEW["Transfusion-Related Acute Lung Injury (TRALI)"] = dx(
    "Respiratory", "Pulmonary/Hematologic",
    v(115, 95, 58, 28, 100.5, 82),
    STD_MOD,
    {"respiratory_rate": 8, "o2_saturation": 6, "heart_rate": 6},
    "Acute dyspnea, bilateral infiltrates, and hypoxemia within 6h of blood transfusion, no evidence of circulatory overload, non-cardiogenic pulmonary edema",
    {"o2_saturation_below": 78, "systolic_bp_below": 75},
    {"abg_po2": lab(40, 65, "mmHg", "decreased"), "bnp": lab(0, 100, "pg/mL", "normal"),
     "wbc": lab(2, 8, "K/uL", "decreased")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Stop Transfusion": tc(2, "Immediately discontinue the implicated blood product"),
     "Supportive Care": tc(30, "O2, ventilatory support as needed; diuretics NOT helpful (non-cardiogenic)"),
     "Report to Blood Bank": tc(60, "Transfusion reaction workup; donor antibody testing"),
     "Mechanical Ventilation": tc(60, "ARDSNet protocol if required; usually resolves in 48-96h")},
)

NEW["Transfusion-Associated Circulatory Overload (TACO)"] = dx(
    "Respiratory", "Pulmonary/Hematologic",
    v(110, 165, 95, 26, 98.6, 87),
    STD_MOD,
    {"respiratory_rate": 6, "o2_saturation": 5, "heart_rate": 5},
    "Dyspnea, hypertension, JVD, bilateral crackles during or shortly after transfusion, elevated BNP (distinguishes from TRALI), peripheral edema",
    {"o2_saturation_below": 82, "systolic_bp_below": 80},
    {"bnp": lab(500, 5000, "pg/mL", "elevated"), "abg_po2": lab(50, 75, "mmHg", "decreased"),
     "cr": lab(0.8, 3.0, "mg/dL", "variable")},
    ["IV Access", "Oxygen Therapy", "Continuous Monitoring"],
    {"Stop or Slow Transfusion": tc(5, "Stop immediately if severe; slow rate if mild"),
     "IV Furosemide": tc(15, "40-80mg IV; true volume overload responds to diuresis"),
     "Sit Upright": tc(5, "Elevate HOB to 45°; reduces preload"),
     "Future Transfusion Planning": tc(120, "Slower rates, concurrent diuretics, consider single-unit transfusions")},
)

# ─── SLEEP / BREATHING DISORDERS ────────────────────────────────────

NEW["Central Sleep Apnea - Cheyne-Stokes"] = dx(
    "Respiratory", "Pulmonary",
    v(80, 130, 80, 14, 98.6, 90),
    STD_MOD,
    {"respiratory_rate": 4, "o2_saturation": 3, "heart_rate": 3},
    "Crescendo-decrescendo breathing pattern with central apneas, typically in heart failure, daytime somnolence, disrupted sleep, periodic desaturations on oximetry",
    {"o2_saturation_below": 84, "systolic_bp_below": 85},
    {"bnp": lab(200, 2000, "pg/mL", "elevated"), "abg_pco2": lab(30, 38, "mmHg", "decreased"),
     "hgb": lab(12, 16, "g/dL", "normal")},
    ["Continuous Monitoring"],
    {"Optimize Heart Failure": tc(120, "Treat underlying HF; CSA may resolve with GDMT optimization"),
     "Adaptive Servo-Ventilation": tc(240, "AVOID in EF <45% (SERVE-HF trial showed harm); use for EF >45%"),
     "Supplemental O2": tc(60, "Nocturnal O2 reduces AHI; improves desaturations"),
     "Polysomnography": tc(4320, "Formal diagnosis and differentiation from obstructive events")},
)

NEW["Laryngospasm"] = dx(
    "Respiratory", "Upper Airway",
    v(130, 140, 85, 4, 98.6, 75),
    STD_MOD,
    {"respiratory_rate": 2, "o2_saturation": 8, "heart_rate": 8},
    "Complete or near-complete airway obstruction, stridor, paradoxical chest movement, occurs post-extubation or with airway irritation, unable to ventilate",
    {"o2_saturation_below": 70, "systolic_bp_below": 70},
    {"abg_po2": lab(30, 60, "mmHg", "decreased")},
    ["Oxygen Therapy", "Continuous Monitoring"],
    {"100% FiO2 with CPAP": tc(2, "Jaw thrust + firm continuous positive pressure may break laryngospasm"),
     "Succinylcholine": tc(3, "0.1-0.5mg/kg IV or 4mg/kg IM if complete obstruction unresponsive to CPAP"),
     "Intubation": tc(5, "If laryngospasm persists after succinylcholine; prepare for difficult airway"),
     "Larson Maneuver": tc(1, "Firm pressure in laryngospasm notch (behind lobule of each ear); may break spasm")},
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

    data["_meta"]["version"] = "2.2.0"
    data["_meta"]["last_updated"] = "2026-03-29"
    cats = sorted(set(e["category"] for e in data["diagnoses"].values()))
    data["_meta"]["description"] = (
        f"Comprehensive medical knowledge database. "
        f"{len(data['diagnoses'])} diagnoses across {len(cats)} categories."
    )

    with open(OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

    total = len(data["diagnoses"])
    print(f"\n✅ Respiratory batch: {existing} existing + {added} new = {total} total")
    print(f"📂 Categories ({len(cats)}): {', '.join(cats)}")

if __name__ == "__main__":
    main()

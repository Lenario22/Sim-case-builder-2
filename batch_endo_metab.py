#!/usr/bin/env python3
"""Batch 6: Endocrine & Metabolic diagnoses expansion."""
import json
from pathlib import Path

OUTPUT = Path(__file__).parent / "diagnosis_data.json"

def dx(cat,organ,vitals,mods,wts,pe,thresh,labs,intv,tca,comorbidity=None):
    return {"category":cat,"organ_system":organ,"vitals":vitals,"vital_modifiers":mods,
            "vital_severity_weights":wts,"pe_findings":pe,"critical_pe_thresholds":thresh,
            "expected_labs":labs,"required_interventions":intv,"time_critical_actions":tca,
            "comorbidity_modifiers":comorbidity or {}}

def v(hr,sbp,dbp,rr,temp,spo2):
    return {"heart_rate":hr,"systolic_bp":sbp,"diastolic_bp":dbp,"respiratory_rate":rr,"temperature_f":temp,"o2_saturation":spo2}

def lab(mn,mx,u,d):
    return {"min":mn,"max":mx,"unit":u,"direction":d}

def tc(w,r):
    return {"window_minutes":w,"rationale":r}

S={"heart_rate":"multiply","systolic_bp":"decrease","diastolic_bp":"decrease","respiratory_rate":"multiply","temperature_f":"fixed","o2_saturation":"decrease"}

N={}

N["Hyperthyroidism - Graves Disease"]=dx("Endocrine","Endocrine",v(110,145,60,20,99.5,98),
    {**S,"systolic_bp":"multiply"},{"heart_rate":10,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Diffuse goiter, exophthalmos, lid lag, pretibial myxedema, fine tremor, hyperreflexia, warm moist skin, wide pulse pressure, atrial fibrillation",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"tsh":lab(0.0,0.1,"mIU/L","decreased"),"free_t4":lab(2.5,8.0,"ng/dL","elevated"),
     "free_t3":lab(4.0,20.0,"pg/mL","elevated"),"tsi":lab(1,1,"positive","elevated")},
    ["Continuous Monitoring"],
    {"Beta-Blocker":tc(120,"Propranolol 40-80mg q6h for symptom control; also blocks T4→T3 conversion"),
     "Methimazole":tc(240,"Start 10-40mg/day; titrate based on free T4/T3; monitor CBC for agranulocytosis"),
     "Ophthalmology Referral":tc(0,"For moderate-severe Graves ophthalmopathy")},{})

N["Hypothyroidism - Myxedema Coma"]=dx("Endocrine","Endocrine",v(50,85,55,8,94.0,92),
    {"heart_rate":"inverse","systolic_bp":"decrease","diastolic_bp":"decrease","respiratory_rate":"inverse","temperature_f":"decrease","o2_saturation":"decrease"},
    {"heart_rate":10,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":4},
    "Hypothermia, altered mental status, bradycardia, hypotension, hypoventilation, non-pitting edema (myxedema), periorbital puffiness, delayed DTR relaxation phase, macroglossia",
    {"o2_saturation_below":85,"systolic_bp_below":70},
    {"tsh":lab(40,200,"mIU/L","elevated"),"free_t4":lab(0.1,0.5,"ng/dL","decreased"),
     "cortisol":lab(1,10,"mcg/dL","decreased"),"na":lab(115,132,"mEq/L","decreased"),
     "glu":lab(30,70,"mg/dL","decreased"),"ck":lab(200,5000,"U/L","elevated"),
     "abg_pco2":lab(50,80,"mmHg","elevated")},
    ["IV Access","Continuous Monitoring","ICU"],
    {"IV Levothyroxine":tc(60,"200-400mcg IV loading dose; then 50-100mcg/day IV; oral absorption unreliable"),
     "IV Hydrocortisone":tc(60,"100mg IV q8h BEFORE thyroid hormone; concomitant adrenal insufficiency may precipitate crisis"),
     "Passive Rewarming":tc(30,"Warm blankets; avoid active rewarming (vasodilation → cardiovascular collapse)"),
     "Ventilatory Support":tc(30,"Intubate for CO2 narcosis; impaired respiratory drive")},{})

N["Pheochromocytoma Crisis"]=dx("Endocrine","Endocrine/Cardiovascular",v(130,220,120,22,100.5,96),
    {**S,"heart_rate":"multiply","systolic_bp":"multiply","diastolic_bp":"multiply"},
    {"heart_rate":12,"systolic_bp":12,"diastolic_bp":10,"o2_saturation":2},
    "Episodic TRIAD: headache + sweating + palpitations; severe paroxysmal hypertension, pallor (not flushing), anxiety, tremor, chest/abdominal pain; triggered by surgery, anesthesia, medications",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"plasma_metanephrines":lab(100,5000,"pg/mL","elevated"),"urine_metanephrines":lab(400,10000,"mcg/24h","elevated"),
     "glu":lab(150,350,"mg/dL","elevated"),"hct":lab(42,55,"%","elevated"),
     "troponin":lab(0,1.0,"ng/mL","variable"),"ca":lab(8.5,12.0,"mg/dL","variable")},
    ["IV Access","Continuous Monitoring","Arterial Line"],
    {"IV Phentolamine":tc(15,"5mg IV bolus q5min for acute crisis; alpha-blocker first-line for acute management"),
     "Nitroprusside":tc(15,"0.5-10mcg/kg/min for refractory hypertension"),
     "NEVER Beta-Blocker First":tc(1,"CRITICAL: beta-blockade BEFORE alpha-blockade → unopposed alpha-stimulation → hypertensive crisis"),
     "CT/MRI Abdomen":tc(0,"After stabilization; locate tumor (90% adrenal); CT with contrast"),
     "Phenoxybenzamine":tc(0,"Long-acting oral alpha-blocker for preoperative preparation x 10-14 days before surgery")},{})

N["Adrenal Crisis"]=dx("Endocrine","Endocrine",v(115,75,45,22,100.5,95),
    S,{"heart_rate":12,"systolic_bp":22,"diastolic_bp":18,"o2_saturation":3},
    "Severe hypotension refractory to fluids and vasopressors, abdominal pain/nausea/vomiting, confusion, fatigue, hyperpigmentation (primary); triggered by stress/illness in chronic AI or abrupt steroid withdrawal",
    {"o2_saturation_below":90,"systolic_bp_below":60},
    {"cortisol":lab(0,3,"mcg/dL","decreased"),"acth":lab(100,2000,"pg/mL","elevated"),
     "na":lab(120,135,"mEq/L","decreased"),"k":lab(5.0,7.0,"mEq/L","elevated"),
     "glu":lab(30,70,"mg/dL","decreased"),"ca":lab(10,14,"mg/dL","elevated"),
     "bun":lab(25,60,"mg/dL","elevated")},
    ["IV Access","Fluid Resuscitation","Continuous Monitoring"],
    {"IV Hydrocortisone":tc(15,"100mg IV bolus STAT then 50mg IV q8h; DO NOT delay for confirmatory testing"),
     "IV NS Bolus":tc(15,"1-2L NS rapidly; often 3-5L needed in first 24h"),
     "D50 for Hypoglycemia":tc(15,"25-50mL D50W if glucose <60; then D5NS maintenance"),
     "Random Cortisol":tc(15,"Draw BEFORE giving hydrocortisone if possible; cortisol <3 diagnostic; <18 suspicious"),
     "ACTH Stimulation Test":tc(0,"Cosyntropin 250mcg IV; cortisol at 0 and 60min (do after acute stabilization)")},{})

N["Hyperosmolar Hyperglycemic State"]=dx("Endocrine","Endocrine",v(110,100,60,20,99.5,96),
    S,{"heart_rate":10,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":2},
    "Severe dehydration (often 9-12L deficit), altered mental status (proportional to osmolality), glucose >600, osmolality >320, minimal ketosis; elderly T2DM; infection common precipitant",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"glu":lab(600,1500,"mg/dL","elevated"),"serum_osm":lab(320,400,"mOsm/kg","elevated"),
     "na":lab(125,155,"mEq/L","variable"),"bun":lab(30,100,"mg/dL","elevated"),
     "cr":lab(1.5,5.0,"mg/dL","elevated"),"hco3":lab(18,30,"mEq/L","normal"),
     "k":lab(3.0,6.0,"mEq/L","variable")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Foley Catheter"],
    {"IV NS 1L/hr":tc(60,"Aggressive fluid resuscitation: 1-1.5L/hr first 2h; switch to 0.45% NS when Na corrects"),
     "Insulin Drip":tc(120,"0.1 U/kg/hr BUT only after K >3.3 and adequate volume resuscitation; too-early insulin worsens outcomes"),
     "Potassium Replacement":tc(60,"Replace before insulin if K <3.3; add 20-40 mEq/L to fluids if 3.3-5.3"),
     "DVT Prophylaxis":tc(240,"Hyperviscosity creates high thrombotic risk; enoxaparin when safe"),
     "Identify Precipitant":tc(120,"Infection, MI, stroke, medication non-compliance")},
    {"Elderly":{"cr":{"min":1.5,"max":5.0}}})

N["Hypoglycemia - Severe"]=dx("Endocrine","Endocrine",v(105,130,80,18,98.6,97),
    {**S,"systolic_bp":"multiply"},{"heart_rate":10,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Whipple triad: symptoms + glucose <70 + resolution with glucose; adrenergic: tremor, diaphoresis, tachycardia, anxiety; neuroglycopenic: confusion, seizure, coma, focal deficits mimicking stroke",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"glu":lab(10,50,"mg/dL","decreased"),"insulin":lab(5,100,"uU/mL","variable"),
     "c_peptide":lab(0.1,10,"ng/mL","variable"),"boh":lab(0,0.6,"mmol/L","decreased")},
    ["IV Access","Continuous Monitoring"],
    {"IV Dextrose":tc(5,"D50W 25-50mL IV push (12.5-25g glucose); repeat in 10-15min if no response; D10 gtt maintenance"),
     "Glucagon":tc(10,"1mg IM if no IV access; less effective in alcoholics/liver disease (depleted glycogen)"),
     "Recheck Glucose":tc(15,"Q15min until >100; then q1h x 4h; sulfonylurea hypoglycemia requires prolonged monitoring/octreotide"),
     "Identify Cause":tc(120,"Insulin/sulfonylurea dose? Missed meal? Adrenal insufficiency? Insulinoma? Factitious?")},
    {"Liver Disease":{"risk":"impaired gluconeogenesis"},"Renal Failure":{"risk":"decreased insulin clearance"}})

N["Hyperkalemia - Critical"]=dx("Metabolic","Metabolic",v(55,105,68,16,98.6,97),
    {"heart_rate":"inverse","systolic_bp":"decrease","diastolic_bp":"decrease","respiratory_rate":"multiply","temperature_f":"fixed","o2_saturation":"decrease"},
    {"heart_rate":10,"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Muscle weakness (ascending), paresthesias, palpitations, ECG changes: peaked T waves → loss of P waves → widened QRS → sine wave → VF/asystole; renal failure most common cause",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"k":lab(6.5,9.0,"mEq/L","elevated"),"cr":lab(2.0,8.0,"mg/dL","elevated"),
     "bun":lab(30,100,"mg/dL","elevated"),"ph":lab(7.10,7.35,"","decreased"),
     "hco3":lab(10,22,"mEq/L","decreased")},
    ["IV Access","Continuous Monitoring"],
    {"IV Calcium":tc(5,"Calcium gluconate 10mL of 10% over 2-3min; membrane stabilizer; repeat if persistent ECG changes"),
     "Insulin + Glucose":tc(15,"10 units regular insulin IV + D50 25g; shifts K intracellularly; onset 15-30min"),
     "Albuterol":tc(15,"10-20mg nebulized; shifts K intracellularly; additive with insulin"),
     "Sodium Bicarbonate":tc(30,"50mEq IV if metabolic acidosis (pH <7.2); modest K-lowering effect"),
     "Kayexalate or Patiromer":tc(60,"Sodium polystyrene or patiromer for GI K removal; slower onset"),
     "Emergent Dialysis":tc(120,"If refractory, K >7, or severe renal failure; definitive treatment")},
    {"ESRD":{"cr":{"min":5.0,"max":12.0},"k":{"min":6.0,"max":8.0}}})

N["Hypokalemia - Severe"]=dx("Metabolic","Metabolic",v(85,115,72,16,98.6,97),
    S,{"heart_rate":8,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Muscle weakness (may progress to paralysis), cramps, rhabdomyolysis, constipation/ileus, ECG: U waves, flattened T waves, ST depression, prolonged QT → torsades; hypomagnesemia often coexists",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"k":lab(1.5,2.8,"mEq/L","decreased"),"mg":lab(0.8,1.5,"mg/dL","decreased"),
     "cr":lab(0.6,1.5,"mg/dL","variable"),"ck":lab(100,5000,"U/L","variable"),
     "hco3":lab(26,38,"mEq/L","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"IV KCl Replacement":tc(30,"10-20 mEq/hr via central line (max 40 mEq/hr in critical); peripheral max 10 mEq/hr; cardiac monitoring REQUIRED"),
     "Magnesium Repletion":tc(30,"2g MgSO4 IV; K cannot be corrected without adequate Mg"),
     "Telemetry":tc(1,"Continuous cardiac monitoring for dysrhythmias; QT prolongation → torsades risk"),
     "Recheck K q2h":tc(120,"Frequent monitoring during aggressive repletion; large deficit (200-400 mEq total body deficit for each 1 mEq/L drop)")},{})

N["Hyponatremia - Severe Symptomatic"]=dx("Metabolic","Metabolic",v(85,128,78,16,98.6,97),
    S,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Headache, nausea, AMS, seizures, coma when Na <120; causes: SIADH, polydipsia, diuretics, adrenal insufficiency, hypothyroidism; cerebral edema risk",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"na":lab(105,125,"mEq/L","decreased"),"serum_osm":lab(240,275,"mOsm/kg","decreased"),
     "urine_na":lab(10,100,"mEq/L","variable"),"urine_osm":lab(100,800,"mOsm/kg","variable"),
     "tsh":lab(0.4,10.0,"mIU/L","variable"),"cortisol":lab(5,25,"mcg/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"3% Hypertonic Saline":tc(30,"100mL IV over 10min if seizure/severe symptoms; may repeat x2; aim Na increase 4-6 mEq/L in first 6h"),
     "Na Correction Rate":tc(360,"MAX 8 mEq/L in 24h to avoid osmotic demyelination syndrome (central pontine myelinolysis)"),
     "Identify Etiology":tc(120,"Serum/urine osm, urine Na, volume status assessment; SIADH vs cerebral salt wasting vs volume depletion"),
     "Q2h Na Monitoring":tc(120,"Serial sodium levels to ensure safe correction rate"),
     "Fluid Restriction":tc(0,"For euvolemic hyponatremia (SIADH); restrict to 500-1000mL/day")},{})

N["Hypernatremia - Severe"]=dx("Metabolic","Metabolic",v(100,105,65,18,98.6,96),
    S,{"heart_rate":8,"systolic_bp":10,"diastolic_bp":8,"o2_saturation":2},
    "Lethargy, irritability, hyperreflexia, seizures (in rapid-onset), intracranial hemorrhage (brain shrinks → bridging veins tear); elderly, restricted water access, diabetes insipidus",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"na":lab(155,180,"mEq/L","elevated"),"serum_osm":lab(320,400,"mOsm/kg","elevated"),
     "bun":lab(20,60,"mg/dL","elevated"),"cr":lab(0.8,2.5,"mg/dL","elevated"),
     "urine_osm":lab(50,1200,"mOsm/kg","variable")},
    ["IV Access","Continuous Monitoring","Foley Catheter"],
    {"Free Water Replacement":tc(60,"D5W or 0.45% NS; correct Na no faster than 10-12 mEq/L per 24h to avoid cerebral edema"),
     "Calculate Free Water Deficit":tc(30,"FWD = TBW x [(Na/140) - 1]; replace deficit + ongoing losses over 48-72h"),
     "Address Underlying Cause":tc(120,"DI (central vs nephrogenic): desmopressin trial; osmotic diuresis; inadequate intake"),
     "Q4h Na Monitoring":tc(240,"Serial levels to ensure safe correction rate")},{})

N["Hypercalcemia Crisis"]=dx("Metabolic","Metabolic",v(68,125,78,16,98.6,97),
    {"heart_rate":"inverse","systolic_bp":"decrease","diastolic_bp":"decrease","respiratory_rate":"multiply","temperature_f":"fixed","o2_saturation":"decrease"},
    {"heart_rate":8,"systolic_bp":10,"diastolic_bp":8,"o2_saturation":1},
    "Stones, bones, groans, moans, psychiatric overtones: renal stones, bone pain, abdominal pain, nausea/vomiting, AMS/confusion; shortened QT on ECG; malignancy and hyperparathyroidism account for 90%",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"ca":lab(14,20,"mg/dL","elevated"),"ionized_ca":lab(6.0,10.0,"mg/dL","elevated"),
     "pth":lab(0,300,"pg/mL","variable"),"cr":lab(1.0,4.0,"mg/dL","elevated"),
     "phos":lab(2.0,5.0,"mg/dL","variable"),"alb":lab(2.0,4.5,"g/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"IV NS Aggressive":tc(30,"200-500mL/hr; restore volume and increase renal Ca excretion"),
     "Calcitonin":tc(60,"4 IU/kg SC/IM q12h; rapid onset (4-6h) but tachyphylaxis in 48h; bridge therapy"),
     "Zoledronic Acid":tc(240,"4mg IV over 15min; onset 2-4 days; first-line for malignancy-related hypercalcemia"),
     "Furosemide":tc(120,"40mg IV ONLY after adequate volume resuscitation; promotes calciuresis; NOT first-line"),
     "Dialysis":tc(240,"For refractory or renal failure patients; low-calcium bath")},{})

N["Tumor Lysis Syndrome"]=dx("Metabolic","Metabolic/Oncologic",v(100,115,72,20,99.5,96),
    S,{"heart_rate":8,"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "After chemotherapy or spontaneous in high-burden malignancy; high K, high phosphorus, high uric acid, low calcium; AKI from urate/phosphate crystal deposition; cardiac arrhythmias from electrolyte derangements",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"k":lab(5.5,8.0,"mEq/L","elevated"),"phos":lab(5.0,12.0,"mg/dL","elevated"),
     "uric_acid":lab(8.0,25.0,"mg/dL","elevated"),"ca":lab(5.0,8.0,"mg/dL","decreased"),
     "cr":lab(1.5,6.0,"mg/dL","elevated"),"ldh":lab(500,5000,"U/L","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"IV Rasburicase":tc(120,"0.2mg/kg IV; recombinant urate oxidase; rapidly lowers uric acid; contraindicated in G6PD deficiency"),
     "Aggressive IV Fluids":tc(30,"200-250mL/hr NS; maintain UOP >2mL/kg/hr; washout crystals"),
     "Hyperkalemia Protocol":tc(15,"Calcium gluconate, insulin/glucose, albuterol, kayexalate, dialysis if refractory"),
     "Allopurinol":tc(240,"Prophylactic; 100-800mg/day; prevents NEW uric acid but doesn't reduce existing"),
     "Emergent Dialysis":tc(120,"If K >7, symptomatic hypocalcemia, volume overload, or refractory AKI")},{})

N["Rhabdomyolysis"]=dx("Metabolic","Metabolic/Renal",v(105,100,62,20,100.5,96),
    S,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":2},
    "Muscle pain/weakness/swelling, dark tea-colored urine (myoglobinuria), tender muscles; causes: crush injury, exertion, statins, seizure, drugs (cocaine, MDMA), NMS, malignant hyperthermia",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"ck":lab(5000,200000,"U/L","elevated"),"cr":lab(1.0,6.0,"mg/dL","elevated"),
     "k":lab(4.5,7.5,"mEq/L","elevated"),"ca":lab(5.5,8.5,"mg/dL","decreased"),
     "phos":lab(4.5,10.0,"mg/dL","elevated"),"urine_myoglobin":lab(1,1,"positive","elevated"),
     "ldh":lab(300,3000,"U/L","elevated"),"ast":lab(100,5000,"U/L","elevated"),
     "uric_acid":lab(6,15,"mg/dL","elevated")},
    ["IV Access","Continuous Monitoring","Foley Catheter"],
    {"Aggressive IV NS":tc(30,"200-1000mL/hr initially; target UOP >200-300mL/hr; MOST IMPORTANT intervention to prevent AKI"),
     "Electrolyte Monitoring":tc(60,"Q4h K, Ca, Phos; hyperkalemia is leading cause of death"),
     "Hyperkalemia Protocol":tc(15,"If K >6.0 or ECG changes; calcium, insulin/glucose, albuterol"),
     "Sodium Bicarbonate":tc(120,"Alkalinize urine (target pH >6.5) to prevent myoglobin precipitation in tubules; controversial"),
     "Dialysis":tc(240,"If refractory hyperkalemia, volume overload, severe AKI; conventional HD preferred")},{})

N["Lactic Acidosis"]=dx("Metabolic","Metabolic",v(115,90,55,28,99.5,93),
    S,{"heart_rate":12,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":4},
    "Kussmaul respirations, tachycardia, hypotension if severe, altered mental status; Type A (hypoperfusion: shock, cardiac arrest, mesenteric ischemia) vs Type B (metabolic: metformin, HIV meds, malignancy)",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"lactate":lab(4.0,20.0,"mmol/L","elevated"),"ph":lab(6.9,7.30,"","decreased"),
     "hco3":lab(5,18,"mEq/L","decreased"),"anion_gap":lab(16,40,"mEq/L","elevated"),
     "cr":lab(1.0,5.0,"mg/dL","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"Treat Underlying Cause":tc(30,"MOST IMPORTANT; restore perfusion for Type A; stop offending agent for Type B"),
     "IV Fluid Resuscitation":tc(30,"NS or LR for hypovolemic/distributive shock"),
     "Sodium Bicarbonate":tc(60,"Controversial; consider if pH <7.1 and hemodynamically unstable; 1-2 mEq/kg IV"),
     "Serial Lactate":tc(120,"Q2-4h; clearance >10%/hr is good prognostic sign"),
     "Dialysis":tc(240,"For metformin-associated lactic acidosis; removes metformin and corrects acidosis")},{})

N["Diabetic Foot Infection - Severe"]=dx("Endocrine","Endocrine/Infectious",v(100,118,72,18,101.5,97),
    S,{"heart_rate":8,"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Deep ulcer extending to bone/joint, purulent drainage, surrounding cellulitis >2cm, crepitus (gas gangrene), systemic toxicity; PEDIS or IWGDF classification; polymicrobial; probe-to-bone test",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"wbc":lab(12,25,"K/uL","elevated"),"esr":lab(40,100,"mm/hr","elevated"),"crp":lab(5,20,"mg/dL","elevated"),
     "glu":lab(200,400,"mg/dL","elevated"),"hba1c":lab(8,14,"%","elevated"),
     "cr":lab(0.8,3.0,"mg/dL","variable")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"IV Antibiotics":tc(60,"Vancomycin + piperacillin-tazobactam; cover MRSA + gram-neg + anaerobes"),
     "Wound Assessment":tc(120,"Depth, probe-to-bone, vascular assessment (ABI, toe pressures)"),
     "MRI Foot":tc(240,"Most sensitive for osteomyelitis; bone biopsy gold standard"),
     "Surgical Debridement":tc(240,"Remove necrotic tissue; may need partial amputation"),
     "Glycemic Control":tc(120,"Insulin drip targeting 140-180 mg/dL")},
    {"Diabetes":{"glu":{"min":200,"max":500},"hba1c":{"min":8.0,"max":14.0}}})

N["Hyperglycemic Emergency in Pregnancy"]=dx("Endocrine","Endocrine/OB",v(115,105,65,24,99.0,96),
    S,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":3},
    "DKA in pregnancy occurs at LOWER glucose levels (euglycemic DKA); faster onset, more dangerous; fetal distress common; risk factors: type 1 DM, new-onset, steroid use, tocolytic use (terbutaline)",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"glu":lab(200,500,"mg/dL","elevated"),"ph":lab(7.10,7.30,"","decreased"),
     "hco3":lab(8,18,"mEq/L","decreased"),"anion_gap":lab(14,30,"mEq/L","elevated"),
     "k":lab(3.0,6.0,"mEq/L","variable"),"boh":lab(3.0,15.0,"mmol/L","elevated")},
    ["IV Access","Continuous Monitoring","Fetal Monitoring"],
    {"Insulin Drip":tc(30,"0.1 U/kg/hr; same protocol as non-pregnant DKA"),
     "Aggressive IV Fluids":tc(15,"NS 1L first hour; adequate hydration critical for uteroplacental perfusion"),
     "Continuous Fetal Monitoring":tc(15,"Fetal distress resolves with maternal stabilization; AVOID emergent delivery until maternal pH corrected"),
     "K Replacement":tc(30,"Replace aggressively; larger shifts during treatment"),
     "OB/Endocrine Co-management":tc(60,"Joint management in ICU setting")},{})

with open(OUTPUT) as f:
    data = json.load(f)
added = 0
for name, entry in N.items():
    if name not in data["diagnoses"]:
        data["diagnoses"][name] = entry
        added += 1
data["_meta"]["last_updated"] = "2026-03-29"
with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)
cats = {}
for k2,v2 in data["diagnoses"].items():
    c = v2.get("category","?")
    cats.setdefault(c,[]).append(k2)
print(f"Added {added} endocrine/metabolic diagnoses. Total: {len(data['diagnoses'])}")
for c in sorted(cats):
    print(f"  {c}: {len(cats[c])}")

#!/usr/bin/env python3
"""Batch 7-9: Renal/Urologic + Trauma/Surgical + OB/GYN expansion."""
import json
from pathlib import Path

OUTPUT = Path(__file__).parent / "diagnosis_data.json"

def dx(cat,organ,vitals,mods,wts,pe,thresh,labs,intv,tca,comorb=None):
    return {"category":cat,"organ_system":organ,"vitals":vitals,"vital_modifiers":mods,
            "vital_severity_weights":wts,"pe_findings":pe,"critical_pe_thresholds":thresh,
            "expected_labs":labs,"required_interventions":intv,"time_critical_actions":tca,
            "comorbidity_modifiers":comorb or {}}

def v(hr,sbp,dbp,rr,temp,spo2):
    return {"heart_rate":hr,"systolic_bp":sbp,"diastolic_bp":dbp,"respiratory_rate":rr,"temperature_f":temp,"o2_saturation":spo2}

def lab(mn,mx,u,d):
    return {"min":mn,"max":mx,"unit":u,"direction":d}

def tc(w,r):
    return {"window_minutes":w,"rationale":r}

S={"heart_rate":"multiply","systolic_bp":"decrease","diastolic_bp":"decrease","respiratory_rate":"multiply","temperature_f":"fixed","o2_saturation":"decrease"}

N={}

# ═══════════════════ RENAL / UROLOGIC ═══════════════════

N["Acute Kidney Injury - Prerenal"]=dx("Renal","Renal",v(108,88,55,20,98.6,96),
    S,{"heart_rate":10,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":2},
    "Decreased UOP, orthostasis, dry mucous membranes, poor skin turgor; FENa <1%, BUN:Cr >20:1; causes: hypovolemia, heart failure, hepatorenal, NSAIDs, ACE-I",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"cr":lab(1.5,5.0,"mg/dL","elevated"),"bun":lab(30,80,"mg/dL","elevated"),
     "fe_na":lab(0.1,0.9,"%","decreased"),"urine_osm":lab(500,1200,"mOsm/kg","elevated"),
     "k":lab(4.0,6.0,"mEq/L","elevated"),"hco3":lab(16,24,"mEq/L","variable")},
    ["IV Access","Fluid Resuscitation","Continuous Monitoring","Foley Catheter"],
    {"IV Fluid Challenge":tc(30,"NS 500-1000mL bolus; monitor UOP response"),
     "Stop Nephrotoxins":tc(30,"Hold NSAIDs, ACE-I/ARBs, contrast, aminoglycosides"),
     "Monitor UOP":tc(60,"Target >0.5 mL/kg/hr; Foley for accurate measurement"),
     "Renal Ultrasound":tc(240,"Rule out obstruction if no response to fluids")},{})

N["Acute Kidney Injury - Intrinsic (ATN)"]=dx("Renal","Renal",v(95,115,72,18,98.6,97),
    S,{"heart_rate":8,"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Oliguria or non-oliguria; muddy brown granular casts on UA; FENa >2%; causes: prolonged ischemia (post-prerenal), nephrotoxins (contrast, aminoglycosides, cisplatin), rhabdomyolysis",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"cr":lab(2.0,8.0,"mg/dL","elevated"),"bun":lab(25,60,"mg/dL","elevated"),
     "fe_na":lab(2.0,5.0,"%","elevated"),"urine_osm":lab(250,400,"mOsm/kg","variable"),
     "k":lab(4.5,7.0,"mEq/L","elevated"),"phos":lab(4.5,8.0,"mg/dL","elevated")},
    ["IV Access","Continuous Monitoring","Foley Catheter"],
    {"Stop Nephrotoxins":tc(30,"Remove all offending agents immediately"),
     "Volume Optimization":tc(60,"Euvolemia — avoid both hypovolemia and overload"),
     "Electrolyte Management":tc(60,"Hyperkalemia, hyperphosphatemia, metabolic acidosis"),
     "Nephrology Consult":tc(240,"Consider dialysis if refractory electrolyte derangements, volume overload, uremia, acidosis")},{})

N["Acute Kidney Injury - Postrenal (Obstruction)"]=dx("Renal","Renal/Urologic",v(85,140,85,16,98.6,97),
    S,{"heart_rate":8,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Anuria (complete obstruction) or fluctuating UOP; suprapubic distension (bladder outlet), flank pain (ureteral); BPH, stones, malignancy; bilateral or solitary kidney obstruction required for AKI",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"cr":lab(1.5,8.0,"mg/dL","elevated"),"bun":lab(25,80,"mg/dL","elevated"),
     "k":lab(4.0,7.0,"mEq/L","elevated"),"pvr":lab(200,2000,"mL","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"Foley Catheter":tc(30,"Immediate trial; therapeutic for bladder outlet obstruction; monitor for post-obstructive diuresis"),
     "Renal Ultrasound":tc(120,"Hydronephrosis confirms obstruction; >95% sensitive"),
     "Urology Consult":tc(240,"Nephrostomy tube or ureteral stent for upper tract obstruction"),
     "Post-Obstructive Diuresis":tc(60,"Monitor after relief: may lose 200-500mL/hr; replace 50% of UOP with 0.45% NS")},{})

N["Nephrotic Syndrome"]=dx("Renal","Renal",v(82,130,82,16,98.6,98),
    S,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Massive proteinuria (>3.5g/day), hypoalbuminemia, edema (periorbital→dependent→anasarca), hyperlipidemia; hypercoagulable state (renal vein thrombosis); causes: minimal change, membranous, FSGS, diabetic",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"alb":lab(1.0,2.5,"g/dL","decreased"),"urine_protein":lab(3.5,20,"g/day","elevated"),
     "cholesterol":lab(250,500,"mg/dL","elevated"),"cr":lab(0.6,2.0,"mg/dL","variable"),
     "d_dimer":lab(500,5000,"ng/mL","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"Urine Protein/Cr Ratio":tc(120,"Quantify proteinuria; >3.5g/day diagnostic"),
     "Renal Biopsy":tc(0,"Definitive diagnosis in adults; guides treatment"),
     "Anticoagulation":tc(240,"Low threshold for DVT/PE evaluation; prophylactic if severe hypoalbuminemia"),
     "Diuretics + Albumin":tc(240,"IV albumin 25% + furosemide for refractory edema; albumin improves diuretic delivery"),
     "ACE-I/ARB":tc(0,"Reduce proteinuria; first-line for all nephrotic syndrome")},{})

N["Nephritic Syndrome / Rapidly Progressive Glomerulonephritis"]=dx("Renal","Renal",v(90,165,100,18,98.6,97),
    {**S,"systolic_bp":"multiply"},{"systolic_bp":10,"diastolic_bp":8,"o2_saturation":2},
    "Hematuria (RBC casts pathognomonic), proteinuria (sub-nephrotic <3.5g), hypertension, edema, oliguria; rapid Cr rise over days-weeks; causes: anti-GBM, ANCA vasculitis, lupus nephritis, post-infectious, IgA",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"cr":lab(2.0,8.0,"mg/dL","elevated"),"bun":lab(30,80,"mg/dL","elevated"),
     "ua_rbc":lab(10,100,"/HPF","elevated"),"c3":lab(20,60,"mg/dL","decreased"),
     "c4":lab(5,20,"mg/dL","variable"),"anca":lab(1,1,"positive","variable"),
     "anti_gbm":lab(1,1,"positive","variable"),"ana":lab(1,1,"positive","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Urgent Renal Biopsy":tc(0,"Crescentic GN on biopsy; guides immunosuppression"),
     "Pulse Methylprednisolone":tc(240,"1g IV daily x 3 days for suspected RPGN while awaiting biopsy"),
     "Plasmapheresis":tc(240,"For anti-GBM disease and ANCA vasculitis with pulmonary hemorrhage"),
     "Serologic Workup":tc(120,"ANCA, anti-GBM, ANA, complements, anti-dsDNA, ASO"),
     "Dialysis":tc(0,"If uremic or refractory to immunosuppression")},{})

N["Renal Colic - Obstructing Stone"]=dx("Renal","Renal/Urologic",v(100,155,90,20,98.6,98),
    {**S,"systolic_bp":"multiply"},{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Severe colicky flank pain radiating to groin (ureteral), restless/writhing (unlike peritonitis), nausea/vomiting, CVA tenderness, hematuria (85%), ipsilateral testicular or labial pain from referred innervation",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"ua_rbc":lab(5,100,"/HPF","elevated"),"cr":lab(0.6,2.0,"mg/dL","variable"),
     "wbc":lab(6,12,"K/uL","normal"),"ca":lab(8.5,11.0,"mg/dL","variable"),
     "uric_acid":lab(3.0,9.0,"mg/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"CT Abdomen/Pelvis (Non-contrast)":tc(120,"Gold standard; identifies stone, location, size, hydronephrosis; 97% sensitivity"),
     "IV Ketorolac":tc(15,"30mg IV; first-line analgesic — equivalent to opioids for renal colic with fewer side effects"),
     "IV Fluids":tc(60,"Maintain hydration; do NOT force fluids (no benefit and increases pain)"),
     "Tamsulosin":tc(240,"0.4mg daily for medical expulsive therapy; stones 5-10mm; speeds passage"),
     "Urology Consult":tc(240,"Stone >10mm, infected hydronephrosis (urosepsis), bilateral obstruction, solitary kidney, refractory pain")},{})

N["Urinary Retention - Acute"]=dx("Renal","Renal/Urologic",v(85,152,90,16,98.6,98),
    {**S,"systolic_bp":"multiply"},{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Suprapubic pain and distension, inability to void, palpable bladder, agitation; BPH most common cause in males; anticholinergics, opioids, post-surgical in both sexes",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"cr":lab(0.6,2.0,"mg/dL","variable"),"k":lab(3.5,5.0,"mEq/L","normal"),
     "ua":lab(0,5,"wbc/HPF","normal"),"psa":lab(1,10,"ng/mL","variable")},
    ["Continuous Monitoring"],
    {"Foley Catheter":tc(30,"Immediate decompression; record volume drained"),
     "Monitor for Post-Obstructive Diuresis":tc(60,"If >1500mL drained initially; can occur after prolonged retention"),
     "Alpha-Blocker":tc(0,"Tamsulosin 0.4mg daily for BPH-related; trial of void after catheter in 3-7 days"),
     "Medication Review":tc(60,"Stop anticholinergics, antihistamines, opioids if contributing")},{})

N["Testicular Torsion"]=dx("Renal","Urologic",v(100,140,85,18,98.6,98),
    {**S,"systolic_bp":"multiply"},{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Sudden severe unilateral scrotal pain, high-riding testis, absent cremasteric reflex, horizontal lie, nausea/vomiting; peak: neonatal and adolescent; 'bell-clapper' deformity predisposes",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(6,12,"K/uL","normal"),"ua":lab(0,5,"wbc/HPF","normal")},
    ["IV Access","Continuous Monitoring"],
    {"Manual Detorsion":tc(15,"Open-book detorsion (medial to lateral); provides immediate relief while awaiting OR"),
     "Emergent Urology Consult":tc(30,"Surgical exploration and orchiopexy within 6h; >6h = increasing testicular loss; >24h = near 100% loss"),
     "Doppler Ultrasound":tc(30,"If diagnosis uncertain; absent/decreased blood flow; but do NOT delay OR for imaging if clinical suspicion high"),
     "Bilateral Orchiopexy":tc(0,"Fix both testes; bell-clapper is bilateral anomaly")},{})

N["Priapism - Ischemic"]=dx("Renal","Urologic/Hematologic",v(95,130,80,16,98.6,98),
    S,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Painful sustained erection >4h; fully rigid corpora cavernosa, soft glans/corpus spongiosum; dark blood on aspiration (ischemic); sickle cell disease, medications (trazodone, PDE5i overdose)",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"hgb":lab(7,14,"g/dL","variable"),"wbc":lab(6,15,"K/uL","variable"),
     "reticulocyte":lab(2,15,"%","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Corporal Aspiration":tc(60,"Aspirate dark deoxygenated blood from corpus cavernosum; send ABG of aspirated blood (pO2 <40 confirms ischemic)"),
     "Phenylephrine Injection":tc(60,"100-500mcg intracavernosal q3-5min (max 1mg); alpha-agonist contracts smooth muscle"),
     "Urology Consult":tc(60,"Emergent; if aspiration + phenylephrine fails → surgical shunt"),
     "Treat Underlying Cause":tc(120,"Sickle cell: hydration + exchange transfusion; stop offending medication")},
    {"Sickle Cell":{"hgb":{"min":6,"max":10}}})

# ═══════════════════ TRAUMA / SURGICAL ═══════════════════

N["Blunt Abdominal Trauma - Splenic Injury"]=dx("Trauma","Trauma/Surgical",v(115,88,55,22,98.6,96),
    S,{"heart_rate":12,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":2},
    "LUQ pain, left shoulder pain (Kehr sign from diaphragmatic irritation), guarding, distension; most commonly injured abdominal organ in blunt trauma; grades I-V (AAST)",
    {"o2_saturation_below":90,"systolic_bp_below":70},
    {"hgb":lab(6,12,"g/dL","decreased"),"lactate":lab(2.0,6.0,"mmol/L","elevated"),
     "base_deficit":lab(-8,-2,"mEq/L","decreased")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Blood Type and Crossmatch"],
    {"FAST Exam":tc(10,"Bedside ultrasound; free fluid in Morison pouch and splenorenal recess"),
     "CT Abdomen with Contrast":tc(60,"If hemodynamically stable; grades injury and identifies active extravasation"),
     "Massive Transfusion Protocol":tc(15,"Activate for hemodynamic instability; 1:1:1 pRBC:FFP:PLT"),
     "Surgical Consult":tc(30,"Emergent splenectomy for hemodynamic instability; non-operative management for stable grade I-III"),
     "Angioembolization":tc(120,"For active blush on CT in hemodynamically stable patients")},{})

N["Blunt Abdominal Trauma - Liver Laceration"]=dx("Trauma","Trauma/Surgical",v(118,82,50,24,98.6,95),
    S,{"heart_rate":15,"systolic_bp":22,"diastolic_bp":15,"o2_saturation":3},
    "RUQ pain, guarding, distension, peritoneal signs with grade IV-V; second most common organ injured in blunt trauma; hepatic veins/IVC junction injuries most lethal",
    {"o2_saturation_below":88,"systolic_bp_below":65},
    {"hgb":lab(5,11,"g/dL","decreased"),"lactate":lab(3.0,8.0,"mmol/L","elevated"),
     "inr":lab(1.0,2.0,"INR","variable"),"ast":lab(100,3000,"U/L","elevated"),
     "alt":lab(80,2000,"U/L","elevated")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Blood Type and Crossmatch"],
    {"FAST Exam":tc(10,"Free fluid in RUQ (Morison pouch/hepatorenal recess)"),
     "Massive Transfusion Protocol":tc(15,"1:1:1 ratio; permissive hypotension (SBP 80-90) until surgical control"),
     "CT Abdomen":tc(60,"If stable; grade injury; active extravasation on arterial phase"),
     "Surgical Consult":tc(30,"Damage control laparotomy for hemodynamic instability; perihepatic packing"),
     "Angioembolization":tc(120,"For arterial blush in stable patients")},{})

N["Pneumothorax - Tension"]=dx("Trauma","Trauma/Respiratory",v(130,75,45,30,98.6,82),
    S,{"heart_rate":15,"systolic_bp":25,"diastolic_bp":18,"o2_saturation":8},
    "Severe dyspnea, tracheal deviation AWAY from affected side, absent breath sounds, hyperresonance, distended neck veins, hypotension; obstructive shock; one-way valve mechanism",
    {"o2_saturation_below":80,"systolic_bp_below":60},
    {"lactate":lab(3.0,8.0,"mmol/L","elevated"),"abg_po2":lab(40,70,"mmHg","decreased"),
     "abg_pco2":lab(45,70,"mmHg","elevated")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring"],
    {"Needle Decompression":tc(1,"14g needle, 2nd ICS midclavicular line or 5th ICS anterior axillary line; DO NOT WAIT for imaging — clinical diagnosis"),
     "Chest Tube":tc(15,"28-36Fr tube thoracostomy after needle decompression; definitive treatment"),
     "CXR":tc(30,"Only AFTER decompression to confirm resolution; never delay treatment for imaging")},{})

N["Hemothorax - Massive"]=dx("Trauma","Trauma/Surgical",v(125,78,48,28,98.6,88),
    S,{"heart_rate":15,"systolic_bp":22,"diastolic_bp":18,"o2_saturation":6},
    ">1500mL blood in pleural space; decreased breath sounds, dullness to percussion, tracheal deviation (late), hemorrhagic shock; penetrating or blunt thoracic trauma",
    {"o2_saturation_below":85,"systolic_bp_below":60},
    {"hgb":lab(5,10,"g/dL","decreased"),"lactate":lab(3.0,8.0,"mmol/L","elevated"),
     "base_deficit":lab(-10,-3,"mEq/L","decreased")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Blood Type and Crossmatch"],
    {"Chest Tube":tc(15,"36-40Fr tube thoracostomy; allows drainage and autotransfusion"),
     "Massive Transfusion Protocol":tc(15,"Activate immediately for hemodynamic instability"),
     "Thoracotomy Indications":tc(60,">1500mL initial output OR >200mL/hr for 2-4h → emergent thoracotomy"),
     "Autotransfusion":tc(30,"Collect chest tube output for autotransfusion if available")},{})

N["Flail Chest"]=dx("Trauma","Trauma/Respiratory",v(115,100,62,28,98.6,88),
    S,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":6},
    "≥3 contiguous ribs fractured in ≥2 places; paradoxical chest wall movement; severe pain limiting ventilation; UNDERLYING PULMONARY CONTUSION causes respiratory failure, not the flail segment itself",
    {"o2_saturation_below":85,"systolic_bp_below":80},
    {"hgb":lab(10,14,"g/dL","variable"),"abg_po2":lab(50,80,"mmHg","decreased"),
     "abg_pco2":lab(40,60,"mmHg","elevated"),"lactate":lab(1.5,4.0,"mmol/L","elevated")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring"],
    {"Pain Management":tc(30,"Epidural analgesia preferred; intercostal nerve blocks alternative; adequate pain control is MOST IMPORTANT intervention"),
     "Intubation":tc(60,"If respiratory failure despite optimal pain control and non-invasive ventilation"),
     "CXR/CT Chest":tc(60,"Evaluate for pulmonary contusion extent, hemothorax, pneumothorax"),
     "Surgical Fixation":tc(0,"Rib plating for severe flail; reduces ventilator days and ICU stay")},{})

N["Pelvic Fracture - Unstable with Hemorrhage"]=dx("Trauma","Trauma/Orthopedic",v(125,75,45,24,98.6,94),
    S,{"heart_rate":15,"systolic_bp":25,"diastolic_bp":18,"o2_saturation":3},
    "Hemodynamic instability, pelvic instability on compression/distraction, perineal ecchymosis, scrotal/labial hematoma, blood at urethral meatus (urethral injury); high-energy mechanism (MVC, fall from height)",
    {"o2_saturation_below":88,"systolic_bp_below":60},
    {"hgb":lab(5,10,"g/dL","decreased"),"lactate":lab(3.0,8.0,"mmol/L","elevated"),
     "base_deficit":lab(-10,-3,"mEq/L","decreased"),"inr":lab(1.0,2.0,"INR","variable")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Blood Type and Crossmatch"],
    {"Pelvic Binder":tc(5,"Apply circumferential pelvic binder at level of greater trochanters; reduces pelvic volume and tamponades venous bleeding"),
     "Massive Transfusion Protocol":tc(15,"1:1:1 ratio; permissive hypotension targeting SBP 80-90"),
     "FAST Exam":tc(10,"If positive → laparotomy first; if negative → angioembolization or preperitoneal packing"),
     "Angioembolization":tc(60,"For arterial bleeding identified on CT or angiography"),
     "Avoid Foley Until Cleared":tc(5,"If blood at urethral meatus → retrograde urethrogram before Foley")},{})

N["Traumatic Brain Injury - Severe"]=dx("Trauma","Trauma/Neurological",v(58,175,100,10,98.6,95),
    {"heart_rate":"inverse","systolic_bp":"multiply","diastolic_bp":"multiply","respiratory_rate":"inverse","temperature_f":"fixed","o2_saturation":"decrease"},
    {"heart_rate":10,"systolic_bp":10,"respiratory_rate":3,"o2_saturation":3},
    "GCS ≤8, pupil asymmetry, posturing, Cushing response (hypertension/bradycardia/irregular respirations), scalp laceration/hematoma, Battle sign, raccoon eyes, CSF otorrhea/rhinorrhea",
    {"o2_saturation_below":88,"systolic_bp_below":90},
    {"Na":lab(135,155,"mEq/L","variable"),"glu":lab(80,200,"mg/dL","variable"),
     "pt_inr":lab(0.9,2.0,"INR","variable"),"plt":lab(80,300,"K/uL","variable"),
     "lactate":lab(1.5,4.0,"mmol/L","elevated"),"ethanol":lab(0,300,"mg/dL","variable")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring","C-Spine Immobilization"],
    {"Intubation":tc(15,"GCS ≤8 = definitive airway; RSI avoiding ketamine myth (actually safe); avoid hypotension during RSI"),
     "CT Head STAT":tc(25,"Non-contrast; identify surgical lesion (EDH, SDH, ICH)"),
     "ICP Management":tc(30,"HOB 30°, mannitol 1g/kg or 23.4% NaCl if herniation signs; target ICP <22, CPP >60"),
     "Avoid Secondary Brain Injury":tc(1,"Target: SBP >100 (age 50-69) or >110 (15-49 or >70); PaO2 >60; normoglycemia; normothermia"),
     "Neurosurgery Consult":tc(30,"Emergent craniotomy for EDH, SDH with midline shift, or depressed skull fracture")},{})

N["Burns - Major (>20% TBSA)"]=dx("Trauma","Trauma/Burn",v(120,95,58,22,99.5,95),
    S,{"heart_rate":12,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "Full-thickness (painless, leathery, white/brown) or partial-thickness (painful, blistered, weeping); rule of 9s for TBSA; circumferential burns risk compartment syndrome; inhalation injury worsens prognosis",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"hgb":lab(14,20,"g/dL","elevated"),"hct":lab(42,55,"%","elevated"),
     "lactate":lab(2.0,5.0,"mmol/L","elevated"),"k":lab(4.5,6.5,"mEq/L","elevated"),
     "alb":lab(2.0,3.5,"g/dL","decreased"),"coHgb":lab(0,30,"%","variable")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Foley Catheter"],
    {"Parkland Formula":tc(30,"4mL/kg/%TBSA LR over 24h; half in first 8h from TIME OF BURN; titrate to UOP 0.5-1mL/kg/hr"),
     "Airway Assessment":tc(15,"Intubate early if: facial burns, singed nasal hairs, soot in oropharynx, stridor, hoarseness"),
     "Escharotomy":tc(120,"For circumferential full-thickness burns with vascular compromise or chest restriction"),
     "Wound Care":tc(120,"Silver sulfadiazine or mafenide acetate; debridement"),
     "Burn Center Transfer":tc(240,"Major burns per ABA criteria → transfer to verified burn center")},{})

N["Compartment Syndrome - Acute"]=dx("Trauma","Trauma/Orthopedic",v(105,135,82,20,98.6,97),
    {**S,"systolic_bp":"multiply"},{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "5 P's: Pain (out of proportion, worse with passive stretch), Pressure (tense compartment), Paresthesias (early nerve ischemia), Paralysis (LATE), Pulselessness (VERY LATE - don't wait for this); tibial fracture most common",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"ck":lab(500,50000,"U/L","elevated"),"cr":lab(0.6,3.0,"mg/dL","variable"),
     "k":lab(3.5,6.0,"mEq/L","variable"),"myoglobin":lab(100,10000,"ng/mL","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"Compartment Pressure Measurement":tc(30,"Stryker needle; absolute >30mmHg or delta pressure (diastolic - compartment) <30mmHg → fasciotomy"),
     "Emergent Fasciotomy":tc(60,"4-compartment release for leg; ALL compartments must be opened; delay >6h → muscle necrosis → amputation"),
     "Remove Constrictive Items":tc(5,"Remove cast/splint, loosen dressings immediately"),
     "IV Fluid Resuscitation":tc(30,"Anticipate rhabdomyolysis after fasciotomy; aggressive NS for renal protection")},{})

N["Fat Embolism Syndrome"]=dx("Trauma","Trauma/Respiratory",v(120,95,58,28,101.0,82),
    S,{"heart_rate":12,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":8},
    "Classic triad 24-72h after long bone fracture: respiratory insufficiency (ARDS), neurological changes (confusion→coma), petechial rash (axillae, chest, conjunctivae); Gurd criteria",
    {"o2_saturation_below":85,"systolic_bp_below":75},
    {"hgb":lab(8,12,"g/dL","decreased"),"plt":lab(50,150,"K/uL","decreased"),
     "lipase":lab(40,200,"U/L","variable"),"abg_po2":lab(40,70,"mmHg","decreased"),
     "fibrinogen":lab(100,300,"mg/dL","decreased")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring","ICU"],
    {"Supportive Care":tc(30,"No specific treatment; respiratory support with lung-protective ventilation"),
     "Early Fracture Fixation":tc(0,"Best PREVENTION; fixation within 24h reduces FES incidence"),
     "Avoid Overhydration":tc(30,"Pulmonary edema worsens ARDS; albumin may be helpful"),
     "Corticosteroids":tc(0,"Methylprednisolone prophylaxis controversial; some evidence for high-risk patients")},{})

# ═══════════════════ OB/GYN ═══════════════════

N["Ectopic Pregnancy - Ruptured"]=dx("OB/GYN","OB/GYN",v(120,82,50,22,98.6,95),
    S,{"heart_rate":15,"systolic_bp":22,"diastolic_bp":15,"o2_saturation":3},
    "Sudden severe lower abdominal pain, vaginal bleeding, signs of peritoneal irritation, shoulder pain (hemoperitoneum → diaphragmatic irritation), hemodynamic instability; positive pregnancy test",
    {"o2_saturation_below":90,"systolic_bp_below":65},
    {"hcg":lab(1500,100000,"mIU/mL","elevated"),"hgb":lab(5,10,"g/dL","decreased"),
     "type_and_screen":lab(1,1,"required","required")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Blood Type and Crossmatch"],
    {"Surgical Consult (OB/GYN)":tc(30,"Emergent laparoscopy/laparotomy for salpingectomy or salpingostomy"),
     "Quantitative hCG":tc(30,"Establishes pregnancy; level guides management in stable patients"),
     "FAST/Pelvic Ultrasound":tc(15,"Free fluid in cul-de-sac; empty uterus with adnexal mass/ring of fire"),
     "Blood Type and Rh":tc(15,"RhoGAM if Rh-negative"),
     "Massive Transfusion Protocol":tc(15,"If hemodynamically unstable")},{})

N["Placental Abruption"]=dx("OB/GYN","OB/GYN",v(115,90,55,22,98.6,95),
    S,{"heart_rate":12,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":3},
    "Painful vaginal bleeding (may be concealed in 20%), uterine tenderness, tetanic/rigid uterus, fetal distress, may have DIC; risk factors: HTN, cocaine, trauma, prior abruption",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"hgb":lab(6,11,"g/dL","decreased"),"plt":lab(40,200,"K/uL","decreased"),
     "fibrinogen":lab(100,300,"mg/dL","decreased"),"d_dimer":lab(500,10000,"ng/mL","elevated"),
     "pt_inr":lab(1.0,2.5,"INR","elevated")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Fetal Monitoring"],
    {"Continuous Fetal Monitoring":tc(5,"Non-reassuring fetal heart rate tracing → emergent C-section"),
     "Emergent Delivery":tc(30,"If fetal distress or maternal hemodynamic instability; C-section usually fastest"),
     "DIC Panel":tc(30,"Fibrinogen, PT/INR, D-dimer, platelets; fibrinogen <200 = DIC"),
     "Massive Transfusion Protocol":tc(15,"Replace blood products aggressively; cryoprecipitate for fibrinogen <150"),
     "RhoGAM":tc(120,"If Rh-negative; Kleihauer-Betke for dosing if large fetomaternal hemorrhage")},{})

N["Placenta Previa - Active Bleeding"]=dx("OB/GYN","OB/GYN",v(108,95,58,20,98.6,96),
    S,{"heart_rate":10,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":2},
    "PAINLESS bright red vaginal bleeding (classic) in 2nd/3rd trimester; DO NOT perform digital vaginal exam; complete previa covers os; marginal/low-lying less severe",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"hgb":lab(7,12,"g/dL","decreased"),"type_and_screen":lab(1,1,"required","required"),
     "fibrinogen":lab(200,450,"mg/dL","normal"),"plt":lab(100,300,"K/uL","normal")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Fetal Monitoring"],
    {"Transabdominal Ultrasound":tc(30,"CONFIRM previa; transvaginal is actually SAFE and more accurate; NO SPECULUM, NO DIGITAL EXAM until previa ruled out"),
     "Continuous Fetal Monitoring":tc(5,"Assess fetal status"),
     "Betamethasone":tc(120,"If <34 weeks and delivery not imminent; fetal lung maturity"),
     "Emergent C-Section":tc(30,"If uncontrollable hemorrhage or fetal distress; elective C-section at 36-37 weeks for stable complete previa"),
     "Blood Products Ready":tc(30,"Type and crossmatch 4 units pRBC; massive transfusion protocol on standby")},{})

N["Eclampsia"]=dx("OB/GYN","OB/GYN",v(105,175,110,20,99.0,96),
    {**S,"systolic_bp":"multiply","diastolic_bp":"multiply"},{"systolic_bp":10,"diastolic_bp":8,"o2_saturation":3},
    "Generalized tonic-clonic seizures in preeclamptic patient; headache, visual changes, RUQ/epigastric pain preceding seizure; can occur antepartum, intrapartum, or up to 6 weeks postpartum",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"plt":lab(40,150,"K/uL","decreased"),"cr":lab(0.8,2.0,"mg/dL","elevated"),
     "ast":lab(50,500,"U/L","elevated"),"alt":lab(50,500,"U/L","elevated"),
     "ldh":lab(300,1000,"U/L","elevated"),"uric_acid":lab(6,12,"mg/dL","elevated"),
     "urine_protein":lab(300,5000,"mg/g Cr","elevated")},
    ["IV Access","Magnesium Sulfate","Continuous Monitoring","Fetal Monitoring"],
    {"IV Magnesium Sulfate":tc(15,"6g IV loading dose over 15-20min then 2g/hr maintenance; FIRST-LINE anticonvulsant; superior to phenytoin and diazepam (MAGPIE trial)"),
     "IV Labetalol or Hydralazine":tc(15,"Labetalol 20mg IV then escalate; or hydralazine 5-10mg IV; target BP <160/110"),
     "Delivery Planning":tc(240,"Definitive treatment is DELIVERY; timing depends on gestational age and maternal/fetal status"),
     "Seizure Precautions":tc(5,"Left lateral position, airway management, suction, padded rails"),
     "HELLP Workup":tc(30,"CBC, LFTs, LDH, peripheral smear for schistocytes; HELLP complicates 10-20% of severe preeclampsia")},{})

N["HELLP Syndrome"]=dx("OB/GYN","OB/GYN",v(100,168,105,18,99.0,97),
    {**S,"systolic_bp":"multiply","diastolic_bp":"multiply"},{"systolic_bp":10,"diastolic_bp":8,"o2_saturation":2},
    "Hemolysis + Elevated Liver enzymes + Low Platelets; RUQ/epigastric pain, nausea, malaise; may have minimal hypertension/proteinuria (atypical preeclampsia); hepatic rupture is life-threatening complication",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"plt":lab(20,100,"K/uL","decreased"),"ldh":lab(600,3000,"U/L","elevated"),
     "ast":lab(70,2000,"U/L","elevated"),"alt":lab(50,1500,"U/L","elevated"),
     "tbili":lab(1.2,5.0,"mg/dL","elevated"),"haptoglobin":lab(0,25,"mg/dL","decreased"),
     "schistocytes":lab(1,1,"present","elevated"),"pt_inr":lab(1.0,1.5,"INR","variable")},
    ["IV Access","Magnesium Sulfate","Continuous Monitoring","Fetal Monitoring"],
    {"Emergent Delivery":tc(240,"Definitive treatment; at any gestational age if maternal status is deteriorating"),
     "Magnesium Sulfate":tc(15,"Seizure prophylaxis; same dosing as eclampsia"),
     "Platelet Transfusion":tc(60,"Transfuse if <20K or <50K before C-section"),
     "Blood Pressure Control":tc(15,"IV labetalol or hydralazine; target <160/110"),
     "CT Abdomen":tc(60,"If severe RUQ pain to evaluate for subcapsular hepatic hematoma/rupture")},{})

N["Postpartum Hemorrhage"]=dx("OB/GYN","OB/GYN",v(125,78,48,24,98.6,94),
    S,{"heart_rate":15,"systolic_bp":25,"diastolic_bp":18,"o2_saturation":3},
    "Blood loss >500mL (vaginal) or >1000mL (C-section); boggy uterus (atony, 70-80% of cases), vaginal/cervical lacerations, retained products, coagulopathy; 4 T's: TONE, TRAUMA, TISSUE, THROMBIN",
    {"o2_saturation_below":88,"systolic_bp_below":65},
    {"hgb":lab(5,10,"g/dL","decreased"),"plt":lab(50,200,"K/uL","variable"),
     "fibrinogen":lab(100,300,"mg/dL","decreased"),"pt_inr":lab(1.0,2.5,"INR","variable"),
     "lactate":lab(2.0,6.0,"mmol/L","elevated")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring"],
    {"Uterine Massage":tc(5,"Bimanual massage for atony; first-line intervention"),
     "Oxytocin":tc(5,"40 IU in 1L NS run wide for atony; methylergonovine 0.2mg IM if refractory (avoid in HTN)"),
     "Misoprostol":tc(10,"800mcg sublingual or rectal; prostaglandin for refractory atony"),
     "Tranexamic Acid":tc(30,"1g IV over 10min within 3h of delivery (WOMAN trial); reduces death from hemorrhage"),
     "Surgical Intervention":tc(60,"B-Lynch suture, uterine artery ligation, balloon tamponade, or hysterectomy for refractory hemorrhage"),
     "Massive Transfusion Protocol":tc(15,"1:1:1 ratio for hemodynamic instability")},{})

N["Amniotic Fluid Embolism"]=dx("OB/GYN","OB/GYN",v(130,65,38,32,98.6,78),
    S,{"heart_rate":15,"systolic_bp":30,"diastolic_bp":22,"o2_saturation":10},
    "Sudden cardiovascular collapse during labor/delivery or immediate postpartum; triad: hypoxia, hypotension, DIC; 60-80% mortality; immunologic (anaphylactoid) reaction to fetal material in maternal circulation",
    {"o2_saturation_below":75,"systolic_bp_below":55},
    {"plt":lab(10,50,"K/uL","decreased"),"fibrinogen":lab(50,150,"mg/dL","decreased"),
     "d_dimer":lab(5000,50000,"ng/mL","elevated"),"pt_inr":lab(2.0,5.0,"INR","elevated"),
     "abg_po2":lab(30,60,"mmHg","decreased"),"troponin":lab(0.5,10,"ng/mL","elevated")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Vasopressors","Continuous Monitoring"],
    {"Immediate Delivery":tc(5,"If undelivered; perimortem C-section within 5 minutes of cardiac arrest"),
     "Aggressive Resuscitation":tc(5,"ACLS; epinephrine, vasopressors, intubation"),
     "Massive Transfusion + Cryo":tc(15,"Treat DIC aggressively: cryoprecipitate for fibrinogen, platelets, FFP"),
     "ICU Care":tc(15,"Mechanical ventilation, ECMO if available for refractory shock"),
     "No Specific Treatment":tc(0,"Supportive only; no proven targeted therapy; A-OK (atropine, ondansetron, ketorolac) protocol anecdotal")},{})

N["Shoulder Dystocia"]=dx("OB/GYN","OB/GYN",v(95,130,80,16,98.6,98),
    S,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Head delivers but anterior shoulder impacted behind pubic symphysis; 'turtle sign' (head retracts against perineum); macrosomia, GDM, prolonged 2nd stage, prior shoulder dystocia as risk factors",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {},
    ["Continuous Monitoring"],
    {"McRoberts Maneuver":tc(1,"Sharply flex maternal thighs to abdomen; flattens sacrum, rotates pubic symphysis cephalad; FIRST maneuver"),
     "Suprapubic Pressure":tc(1,"Apply DOWNWARD pressure (not fundal!) above pubic bone to dislodge anterior shoulder; WITH McRoberts"),
     "Rubin Maneuver":tc(2,"Adduct anterior shoulder by pressure on posterior aspect; rotates to oblique diameter"),
     "Wood Screw":tc(3,"Rotate posterior shoulder 180° progressively"),
     "Delivery of Posterior Arm":tc(3,"Sweep posterior arm across chest; deliver hand and arm first; reduces shoulder diameter"),
     "Zavanelli":tc(5,"LAST RESORT: cephalic replacement (push head back) and emergent C-section")},{})

N["Uterine Rupture"]=dx("OB/GYN","OB/GYN",v(128,72,42,26,98.6,92),
    S,{"heart_rate":15,"systolic_bp":25,"diastolic_bp":18,"o2_saturation":4},
    "Sudden abdominal pain (may feel 'pop'), loss of contractions, regression of fetal station, fetal bradycardia, vaginal bleeding, shock; prior C-section scar (VBAC) is major risk factor",
    {"o2_saturation_below":85,"systolic_bp_below":60},
    {"hgb":lab(5,10,"g/dL","decreased"),"lactate":lab(3.0,8.0,"mmol/L","elevated"),
     "type_and_screen":lab(1,1,"required","required")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Fetal Monitoring"],
    {"Emergent Laparotomy":tc(15,"STAT C-section with uterine repair or hysterectomy; minutes matter for fetal survival"),
     "Massive Transfusion Protocol":tc(5,"Activate immediately; hemorrhage can be massive and rapid"),
     "Continuous Fetal Monitoring":tc(1,"Prolonged fetal bradycardia is the hallmark sign"),
     "Neonatal Resuscitation Team":tc(5,"Call NICU/peds team to delivery for fetal resuscitation")},{})

N["Cord Prolapse"]=dx("OB/GYN","OB/GYN",v(100,130,80,18,98.6,98),
    S,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Umbilical cord palpable in vagina ahead of presenting part after ROM; fetal bradycardia from cord compression; risk: polyhydramnios, malpresentation (footling breech, transverse), unengaged head, premature",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {},
    ["Continuous Monitoring","Fetal Monitoring"],
    {"Manual Elevation of Presenting Part":tc(1,"Push presenting part UP off cord with gloved hand in vagina; HOLD continuously until delivery"),
     "Emergent C-Section":tc(15,"Fastest route to delivery; team should be in OR within minutes"),
     "Trendelenburg/Knee-Chest Position":tc(1,"Gravity reduces pressure on cord"),
     "Bladder Filling":tc(5,"500-750mL NS via Foley to elevate fetal head off cord (temporizing); controversial but effective bridge"),
     "DO NOT Attempt to Replace Cord":tc(1,"Attempting to push cord back increases vasospasm and compression")},{})

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
print(f"Added {added} Renal/Trauma/OBGYN diagnoses. Total: {len(data['diagnoses'])}")
for c in sorted(cats):
    print(f"  {c}: {len(cats[c])}")

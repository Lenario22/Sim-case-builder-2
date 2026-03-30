#!/usr/bin/env python3
"""Batch 10-14: Pediatric + Toxicology + Hematologic + Psychiatric + Environmental + Immunologic/Rheumatologic expansion."""
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

# ═══════════════════ PEDIATRIC ═══════════════════

N["Pediatric Febrile Seizure - Complex"]=dx("Pediatric","Pediatric/Neurological",v(150,85,55,26,103.2,97),
    S,{"heart_rate":8,"systolic_bp":5,"o2_saturation":2},
    "Seizure >15min or focal or recurrent within 24h in child 6mo-5y with fever; rule out meningitis in <12mo; post-ictal focal deficit warrants imaging",
    {"o2_saturation_below":90,"systolic_bp_below":60},
    {"wbc":lab(5,20,"K/uL","variable"),"glu":lab(60,180,"mg/dL","variable"),
     "na":lab(130,145,"mEq/L","variable"),"csf_wbc":lab(0,5,"cells/uL","normal")},
    ["IV/IO Access","Continuous Monitoring","Seizure Precautions"],
    {"Benzodiazepine":tc(5,"Midazolam 0.2mg/kg IM/IN or diazepam 0.5mg/kg PR if no IV; lorazepam 0.1mg/kg IV if access available"),
     "Antipyretic":tc(15,"Acetaminophen 15mg/kg PR/PO; ibuprofen 10mg/kg PO if >6mo"),
     "LP Consideration":tc(120,"Recommended <12mo; consider 12-18mo; if pretreated with antibiotics or persistent altered mental status"),
     "Source Evaluation":tc(60,"UA, CXR, blood culture for fever source; treat underlying infection")},{})

N["Croup (Laryngotracheobronchitis)"]=dx("Pediatric","Pediatric/Respiratory",v(140,90,55,30,101.5,95),
    S,{"heart_rate":8,"respiratory_rate":8,"o2_saturation":4},
    "Barking/seal-like cough, inspiratory stridor, hoarse voice, steeple sign on AP neck XR; 6mo-3y peak; parainfluenza most common; Westley score for severity; worse at night",
    {"o2_saturation_below":88,"systolic_bp_below":60},
    {"wbc":lab(5,15,"K/uL","variable")},
    ["Continuous Monitoring","Oxygen Therapy"],
    {"Dexamethasone":tc(30,"0.6mg/kg PO/IM single dose; reduces return visits and intubation; effective for ALL severity levels"),
     "Nebulized Racemic Epinephrine":tc(15,"0.5mL of 2.25% in 3mL NS; for moderate-severe stridor at rest; observe 2-4h for rebound"),
     "Heliox":tc(30,"70:30 helium:oxygen for severe cases while awaiting steroid effect; reduces turbulent flow"),
     "Keep Child Calm":tc(5,"Avoid agitation — increases airway obstruction; let child sit in parent's lap; avoid unnecessary procedures")},{})

N["Epiglottitis - Pediatric/Adult"]=dx("Pediatric","Pediatric/Respiratory",v(135,95,60,28,103.5,92),
    S,{"heart_rate":10,"respiratory_rate":10,"o2_saturation":6},
    "Drooling, dysphagia, distress, tripod positioning, muffled 'hot potato' voice; thumb sign on lateral neck XR; H. influenzae (pre-vaccine) or now S. aureus/Strep; COMPLETE airway obstruction risk",
    {"o2_saturation_below":85,"systolic_bp_below":60},
    {"wbc":lab(12,25,"K/uL","elevated"),"blood_cx":lab(1,1,"pending","pending")},
    ["IV Access","Continuous Monitoring","Airway Equipment Ready"],
    {"Airway Management":tc(15,"DO NOT examine throat or agitate child; take DIRECTLY to OR for controlled intubation with ENT/anesthesia backup for surgical airway"),
     "IV Antibiotics":tc(30,"Ceftriaxone 50mg/kg + vancomycin after airway secured; do NOT delay airway for IV access"),
     "Keep Child Calm":tc(1,"Absolute priority; allow comfortable position; avoid labs/imaging until airway secured"),
     "Dexamethasone":tc(60,"0.6mg/kg IV to reduce airway edema after intubation")},{})

N["Bronchiolitis - Severe"]=dx("Pediatric","Pediatric/Respiratory",v(160,80,50,50,100.5,88),
    S,{"heart_rate":8,"respiratory_rate":10,"o2_saturation":6},
    "Wheezing, crackles, tachypnea, nasal flaring, subcostal/intercostal retractions, poor feeding, apnea in young infants (<2mo); RSV most common; peak 2-6mo; winter seasonality",
    {"o2_saturation_below":85,"systolic_bp_below":55},
    {"rsv_rapid":lab(1,1,"positive","positive"),"wbc":lab(5,15,"K/uL","variable"),
     "abg_pco2":lab(45,65,"mmHg","elevated")},
    ["Continuous Monitoring","Oxygen Therapy","IV Access"],
    {"Supplemental O2":tc(15,"High-flow nasal cannula (HFNC) preferred over standard NC; reduces intubation rates"),
     "Nasal Suctioning":tc(15,"Gentle bulb or catheter suction; obligate nasal breathers — clearance improves feeding and breathing"),
     "IV Fluids":tc(60,"If unable to feed; maintain hydration; avoid overhydration"),
     "CPAP/HFNC":tc(30,"For moderate-severe: HFNC 2L/kg/min; CPAP for impending respiratory failure"),
     "Avoid Unnecessary Treatments":tc(5,"NO routine albuterol, NO steroids (unless prior wheeze history), NO antibiotics unless bacterial superinfection")},{})

N["Intussusception"]=dx("Pediatric","Pediatric/GI",v(145,85,52,26,99.5,98),
    S,{"heart_rate":10,"systolic_bp":10,"o2_saturation":2},
    "Colicky intermittent abdominal pain (drawing up legs, screaming q15-20min), vomiting, 'currant jelly' stool (late, bloody mucus), sausage-shaped mass RUQ; ileocolic most common; 6mo-3y peak; lead point concern >2y",
    {"o2_saturation_below":92,"systolic_bp_below":55},
    {"wbc":lab(8,18,"K/uL","variable"),"hgb":lab(10,14,"g/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Ultrasound":tc(60,"'Target sign' or 'pseudokidney' sign; >95% sensitivity; first-line imaging"),
     "Air Enema Reduction":tc(120,"Therapeutic and diagnostic; 80-90% success rate; contraindicated if peritonitis or perforation"),
     "Surgical Consult":tc(120,"Failed reduction, perforation, peritonitis, shock, or lead point concern (>2y) → operative reduction"),
     "IV Fluid Resuscitation":tc(30,"Correct dehydration before reduction attempt; bolus 20mL/kg NS"),
     "NG Tube":tc(60,"If bilious vomiting or distension; decompression before reduction")},{})

N["Pyloric Stenosis"]=dx("Pediatric","Pediatric/GI",v(155,78,48,28,98.6,98),
    S,{"heart_rate":8,"systolic_bp":8,"o2_saturation":1},
    "Projectile non-bilious vomiting in 2-8 week old; hungry after vomiting; palpable 'olive' mass RUQ (best after vomiting); visible gastric peristaltic waves; firstborn males most common",
    {"o2_saturation_below":92,"systolic_bp_below":50},
    {"na":lab(125,138,"mEq/L","decreased"),"k":lab(2.5,3.8,"mEq/L","decreased"),
     "cl":lab(80,98,"mEq/L","decreased"),"hco3":lab(28,40,"mEq/L","elevated"),
     "ph":lab(7.45,7.55,"arterial","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"Correct Electrolytes FIRST":tc(120,"Hypochloremic hypokalemic metabolic alkalosis must be corrected before surgery; NS + KCl after UOP confirmed"),
     "Ultrasound":tc(60,"Pyloric muscle thickness >4mm, channel length >16mm; 95% sensitive and specific"),
     "Surgical Consult":tc(240,"Ramstedt pyloromyotomy (laparoscopic); definitive cure; NOT an emergency until electrolytes corrected"),
     "NPO + NG Tube":tc(30,"Decompress stomach; prevent aspiration")},{})

N["Neonatal Sepsis - Early Onset"]=dx("Pediatric","Pediatric/Infectious",v(170,58,35,50,96.5,92),
    S,{"heart_rate":10,"systolic_bp":15,"respiratory_rate":8,"o2_saturation":5},
    "Temperature instability (hypothermia MORE common than fever in neonates), poor feeding, lethargy, apnea, tachypnea, grunting, mottled/pale skin, hypoglycemia; <72h of life; GBS and E. coli predominate",
    {"o2_saturation_below":85,"systolic_bp_below":40},
    {"wbc":lab(0,5,"K/uL","decreased"),"plt":lab(30,150,"K/uL","decreased"),
     "crp":lab(5,50,"mg/L","elevated"),"glu":lab(20,60,"mg/dL","decreased"),
     "blood_cx":lab(1,1,"pending","pending"),"csf_wbc":lab(0,30,"cells/uL","variable"),
     "lactate":lab(2.0,6.0,"mmol/L","elevated")},
    ["IV/IO Access","Oxygen Therapy","Continuous Monitoring"],
    {"Ampicillin + Gentamicin":tc(30,"Empiric within 1h of suspicion; Ampicillin 50mg/kg + Gentamicin 4mg/kg; add cefotaxime if meningitis suspected"),
     "Blood Culture":tc(15,"Before antibiotics if possible; but do NOT delay antibiotics for cultures"),
     "Lumbar Puncture":tc(120,"If stable enough; CSF culture, cell count, protein, glucose; delay if hemodynamically unstable"),
     "Glucose Monitoring":tc(15,"D10W bolus 2mL/kg for hypoglycemia; maintain glucose >45mg/dL"),
     "Volume Resuscitation":tc(30,"10-20mL/kg NS bolus for hypotension; epinephrine drip if refractory")},{})

N["Kawasaki Disease"]=dx("Pediatric","Pediatric/Cardiac/Immunologic",v(140,90,55,22,103.5,98),
    S,{"heart_rate":8,"systolic_bp":5,"o2_saturation":1},
    "CRASH and Burn: Conjunctivitis (bilateral non-exudative), Rash (polymorphous), Adenopathy (cervical, unilateral >1.5cm), Strawberry tongue + lip fissures, Hand/foot changes (edema→desquamation); fever ≥5 days required; coronary artery aneurysm risk",
    {"o2_saturation_below":92,"systolic_bp_below":60},
    {"wbc":lab(12,30,"K/uL","elevated"),"plt":lab(400,1000,"K/uL","elevated"),
     "esr":lab(40,100,"mm/hr","elevated"),"crp":lab(5,30,"mg/dL","elevated"),
     "alb":lab(2.0,3.0,"g/dL","decreased"),"alt":lab(40,200,"U/L","elevated"),
     "ua_wbc":lab(10,50,"/HPF","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"IVIG":tc(240,"2g/kg single infusion over 10-12h; within first 10 days of illness; reduces coronary aneurysm risk from 25% to <5%"),
     "High-dose Aspirin":tc(240,"80-100mg/kg/day divided q6h until afebrile 48h; then 3-5mg/kg/day for 6-8 weeks (antiplatelet dose)"),
     "Echocardiogram":tc(240,"Baseline and repeat at 2 weeks and 6-8 weeks; coronary artery Z-scores; proximal LAD and RCA most affected"),
     "Incomplete Kawasaki Workup":tc(120,"If <4 criteria + fever ≥5d: CRP ≥3.0 or ESR ≥40 + ≥3 supplemental lab criteria → treat")},{})

N["Meningococcemia"]=dx("Pediatric","Pediatric/Infectious",v(150,70,40,28,103.5,93),
    S,{"heart_rate":12,"systolic_bp":20,"diastolic_bp":15,"o2_saturation":4},
    "Rapidly progressive petechial→purpuric rash (non-blanching), meningismus, altered mental status, DIC, purpura fulminans (hemorrhagic skin necrosis); N. meningitidis; can progress from well to dead in hours",
    {"o2_saturation_below":88,"systolic_bp_below":55},
    {"wbc":lab(2,25,"K/uL","variable"),"plt":lab(10,100,"K/uL","decreased"),
     "fibrinogen":lab(50,200,"mg/dL","decreased"),"pt_inr":lab(1.5,4.0,"INR","elevated"),
     "lactate":lab(3.0,10.0,"mmol/L","elevated"),"csf_wbc":lab(100,10000,"cells/uL","elevated"),
     "blood_cx":lab(1,1,"pending","pending")},
    ["IV Access","Fluid Resuscitation","Vasopressors","Continuous Monitoring"],
    {"IV Ceftriaxone":tc(15,"100mg/kg IV IMMEDIATELY; do NOT delay for LP; most critical intervention"),
     "Aggressive Fluid Resuscitation":tc(15,"60mL/kg NS in first hour; may need 100-200mL/kg in first hours"),
     "DIC Management":tc(60,"Cryo for fibrinogen <100, platelets for <20K or active bleeding, FFP for INR >1.5"),
     "Droplet Precautions":tc(15,"Until 24h of effective antibiotics"),
     "Chemoprophylaxis for Contacts":tc(240,"Rifampin, cipro, or ceftriaxone for close contacts; notify public health")},{})

N["Non-Accidental Trauma (Child Abuse)"]=dx("Pediatric","Pediatric/Trauma",v(130,82,50,24,98.6,97),
    S,{"heart_rate":8,"systolic_bp":10,"o2_saturation":2},
    "Injuries inconsistent with developmental stage or history; multiple bruises in various stages of healing; patterned injuries (belt, iron, cigarette); posterior rib fractures, metaphyseal corner fractures, retinal hemorrhages (shaken baby); delay in seeking care",
    {"o2_saturation_below":90,"systolic_bp_below":55},
    {"hgb":lab(8,14,"g/dL","variable"),"plt":lab(100,400,"K/uL","variable"),
     "ast":lab(20,300,"U/L","variable"),"alt":lab(20,200,"U/L","variable"),
     "lipase":lab(10,300,"U/L","variable"),"ua":lab(0,50,"rbc/HPF","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Skeletal Survey":tc(240,"All children <2y; AP of all long bones, hands, feet, AP/lateral skull, AP/lateral spine, AP chest/pelvis"),
     "CT Head":tc(120,"If <1y, altered mental status, or suspicion of abusive head trauma; subdural hematoma classic"),
     "Social Work/CPS Report":tc(60,"MANDATORY reporting; failure to report is medical and legal error"),
     "Ophthalmology Consult":tc(240,"Dilated fundoscopic exam for retinal hemorrhages if head injury suspected"),
     "Documentation":tc(30,"Precise description of all injuries with measurements, photos, and exact quotes from caregivers")},{})

# ═══════════════════ TOXICOLOGY ═══════════════════

N["Acetaminophen Overdose - Acute"]=dx("Toxicology","Toxicology/Hepatic",v(90,115,72,18,98.6,98),
    S,{"heart_rate":5,"systolic_bp":5,"o2_saturation":1},
    "Phase 1 (0-24h): nausea, vomiting, malaise, diaphoresis; Phase 2 (24-72h): clinical improvement but rising LFTs and RUQ pain; Phase 3 (72-96h): hepatic necrosis, coagulopathy, encephalopathy, renal failure; Phase 4: recovery or death",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"apap_level":lab(150,500,"mcg/mL","elevated"),"ast":lab(20,10000,"U/L","variable"),
     "alt":lab(20,10000,"U/L","variable"),"pt_inr":lab(1.0,6.0,"INR","variable"),
     "cr":lab(0.6,4.0,"mg/dL","variable"),"lactate":lab(0.5,10.0,"mmol/L","variable"),
     "ph":lab(7.1,7.45,"arterial","variable")},
    ["IV Access","Continuous Monitoring"],
    {"N-Acetylcysteine (NAC)":tc(60,"MOST efficacious within 8h; IV: 150mg/kg over 1h, then 50mg/kg over 4h, then 100mg/kg over 16h; continue if INR rising or liver failure"),
     "Serum APAP Level at 4h":tc(240,"Plot on Rumack-Matthew nomogram; treat if ABOVE treatment line"),
     "Activated Charcoal":tc(60,"1g/kg PO if within 1-2h of ingestion and alert/protecting airway"),
     "King's College Criteria":tc(0,"Transplant criteria: pH <7.3 OR INR >6.5 + Cr >3.4 + grade 3-4 encephalopathy → transplant evaluation"),
     "Poison Center":tc(30,"1-800-222-1222; guidance on NAC protocol and disposition")},{})

N["Salicylate (Aspirin) Toxicity"]=dx("Toxicology","Toxicology/Metabolic",v(105,120,75,28,100.5,97),
    S,{"heart_rate":8,"respiratory_rate":8,"systolic_bp":8,"o2_saturation":2},
    "Tinnitus, nausea, vomiting, diaphoresis, tachypnea (respiratory alkalosis → mixed metabolic acidosis); altered mental status (late); ARDS, cerebral edema; primary respiratory alkalosis with anion gap metabolic acidosis is CLASSIC",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"salicylate":lab(30,100,"mg/dL","elevated"),"ph":lab(7.1,7.55,"arterial","variable"),
     "hco3":lab(8,22,"mEq/L","decreased"),"k":lab(3.0,5.5,"mEq/L","variable"),
     "lactate":lab(2.0,8.0,"mmol/L","elevated"),"glu":lab(40,150,"mg/dL","variable"),
     "pt_inr":lab(1.0,2.0,"INR","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Sodium Bicarbonate":tc(30,"150mEq NaHCO3 in 1L D5W at 1.5-2x maintenance; target urine pH >7.5; alkalinize serum to trap salicylate in ionized form"),
     "D5W with Dextrose":tc(30,"CNS glucose may be low even with normal serum glucose; give D50 for altered mental status"),
     "Hemodialysis":tc(120,"Level >100mg/dL, renal failure, pulmonary edema, CNS symptoms, clinical deterioration despite treatment"),
     "Activated Charcoal":tc(60,"Multi-dose (q4h) for sustained-release preparations; aspirin forms bezoars"),
     "Avoid Intubation If Possible":tc(5,"Patient's tachypnea is compensatory; if must intubate, match the high minute ventilation to prevent acute acidemia → cardiac arrest")},{})

N["Opioid Overdose"]=dx("Toxicology","Toxicology/Respiratory",v(55,88,55,6,96.5,78),
    {"heart_rate":"inverse","systolic_bp":"decrease","diastolic_bp":"decrease","respiratory_rate":"inverse","temperature_f":"decrease","o2_saturation":"decrease"},
    {"respiratory_rate":10,"o2_saturation":8,"systolic_bp":10},
    "Classic toxidrome: Respiratory depression (the killer), miosis (pinpoint pupils), CNS depression, decreased bowel sounds, hypothermia; needle tracks, nasal erosion; fentanyl: rapid onset, may need repeated naloxone",
    {"o2_saturation_below":75,"systolic_bp_below":70},
    {"uds":lab(1,1,"positive opiates","positive"),"abg_pco2":lab(55,90,"mmHg","elevated"),
     "abg_po2":lab(35,65,"mmHg","decreased"),"lactate":lab(2.0,6.0,"mmol/L","elevated")},
    ["IV/IO/IM Access","Bag-Valve Mask Ventilation","Continuous Monitoring"],
    {"Naloxone (Narcan)":tc(3,"0.4-2mg IV/IM/IN; repeat q2-3min; titrate to respiratory drive (RR>12), NOT full consciousness; START LOW in known opioid-dependent to avoid acute withdrawal → pulmonary edema"),
     "Bag-Valve Mask":tc(1,"Ventilate BEFORE naloxone if severe; oxygenation is the priority"),
     "Naloxone Infusion":tc(30,"If repeated boluses needed (long-acting opioid): 2/3 of effective bolus dose per hour"),
     "Observe 4-6h minimum":tc(0,"Naloxone half-life (30-90min) shorter than most opioids; renarcotization risk; fentanyl patches may need 24h observation")},{})

N["Benzodiazepine Overdose"]=dx("Toxicology","Toxicology/Neurological",v(60,95,60,8,97.0,92),
    {"heart_rate":"inverse","systolic_bp":"decrease","diastolic_bp":"decrease","respiratory_rate":"inverse","temperature_f":"fixed","o2_saturation":"decrease"},
    {"respiratory_rate":5,"o2_saturation":4,"systolic_bp":8},
    "CNS depression, slurred speech, ataxia, hypotonia, respiratory depression (usually less severe than opioids unless co-ingestion); rarely fatal alone; co-ingestion with opioids/alcohol dramatically increases lethality",
    {"o2_saturation_below":85,"systolic_bp_below":75},
    {"uds":lab(1,1,"positive benzodiazepines","positive"),"abg_pco2":lab(45,65,"mmHg","elevated"),
     "ethanol":lab(0,400,"mg/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Supportive Care":tc(15,"Airway management, ventilatory support; usually sufficient alone"),
     "Flumazenil Contraindicated Usually":tc(5,"0.2mg IV; AVOID in chronic benzo users (seizures), co-ingestion with proconvulsants (TCAs), or unknown ingestion; only for pure benzo OD in benzo-naive patient"),
     "Activated Charcoal":tc(60,"1g/kg if within 1h and protecting airway"),
     "Monitor for Co-Ingestion":tc(30,"Screen for opioids, alcohol, TCAs; co-ingestion is the real danger")},{})

N["Tricyclic Antidepressant (TCA) Overdose"]=dx("Toxicology","Toxicology/Cardiac",v(125,82,50,22,99.0,95),
    S,{"heart_rate":12,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "Anticholinergic toxidrome (tachycardia, mydriasis, dry skin, urinary retention, ileus) PLUS sodium channel blockade (wide QRS >100ms, terminal R in aVR >3mm), seizures, hypotension; lethal in small amounts; amitriptyline most toxic",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"qrs":lab(100,200,"ms","prolonged"),"ph":lab(7.1,7.45,"arterial","variable"),
     "k":lab(3.0,5.5,"mEq/L","variable"),"lactate":lab(2.0,6.0,"mmol/L","elevated")},
    ["IV Access","Continuous Monitoring","12-Lead ECG"],
    {"Sodium Bicarbonate":tc(15,"1-2mEq/kg IV bolus for QRS >100ms; then infusion (150mEq in 1L D5W); target pH 7.50-7.55; overcomes sodium channel blockade"),
     "Continuous ECG Monitoring":tc(5,"QRS width predicts toxicity: >100ms = seizure risk, >160ms = arrhythmia risk"),
     "Avoid Contraindicated Drugs":tc(5,"NO class IA/IC antiarrhythmics (procainamide, flecainide); NO physostigmine; NO flumazenil (if co-ingested benzos)"),
     "Intralipid":tc(60,"20% IV lipid emulsion for refractory cardiovascular collapse; 1.5mL/kg bolus then 0.25mL/kg/min"),
     "Seizure Management":tc(15,"Benzodiazepines ONLY (lorazepam 0.1mg/kg IV); NO phenytoin (worsens cardiac toxicity)")},{})

N["Sympathomimetic Toxidrome (Cocaine/Amphetamines)"]=dx("Toxicology","Toxicology/Cardiac",v(130,185,110,22,101.5,97),
    {**S,"systolic_bp":"multiply","diastolic_bp":"multiply"},{"systolic_bp":10,"diastolic_bp":8,"heart_rate":10,"o2_saturation":2},
    "Hypertension, tachycardia, hyperthermia, agitation/psychosis, mydriasis, diaphoresis, seizures; cocaine-specific: chest pain (coronary vasospasm/MI), aortic dissection; amphetamine-specific: serotonin syndrome overlap possible",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"troponin":lab(0,2.0,"ng/mL","variable"),"ck":lab(200,5000,"U/L","variable"),
     "cr":lab(0.6,3.0,"mg/dL","variable"),"k":lab(3.0,6.0,"mEq/L","variable"),
     "uds":lab(1,1,"positive","positive")},
    ["IV Access","Continuous Monitoring","Cooling Measures"],
    {"Benzodiazepines":tc(15,"FIRST-LINE for agitation, seizures, hypertension, tachycardia, chest pain; addresses sympathetic excess; diazepam 5-10mg IV or midazolam 5mg IM"),
     "Avoid Beta-Blockers":tc(5,"ABSOLUTELY CONTRAINDICATED — unopposed alpha stimulation → paradoxical hypertension; labetalol also avoided (weak beta >> alpha block)"),
     "Chest Pain Workup":tc(30,"ECG, troponin; nitro and benzodiazepines for coronary vasospasm; PCI if STEMI"),
     "Active Cooling":tc(15,"For hyperthermia >104°F; ice packs, evaporative cooling; rhabdomyolysis risk"),
     "Phentolamine":tc(30,"Alpha-blocker for refractory hypertension if benzos fail")},{})

N["Anticholinergic Toxidrome"]=dx("Toxicology","Toxicology/Neurological",v(115,135,82,20,101.5,97),
    {**S,"systolic_bp":"multiply"},{"systolic_bp":8,"heart_rate":8,"o2_saturation":2},
    "'Hot as a hare (hyperthermia), dry as a bone (anhydrosis), red as a beet (vasodilation), blind as a bat (mydriasis), mad as a hatter (delirium), full as a flask (urinary retention)'; absent bowel sounds, seizures; diphenhydramine, jimsonweed, TCAs",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"glu":lab(80,180,"mg/dL","variable"),"qrs":lab(80,120,"ms","normal")},
    ["IV Access","Continuous Monitoring"],
    {"Physostigmine":tc(30,"0.5-2mg IV slow push; for PURE anticholinergic toxicity with severe agitation/delirium; reversible AChE inhibitor; AVOID if TCA, QRS >100, or cardiac history"),
     "Benzodiazepines":tc(15,"For agitation/seizures if physostigmine contraindicated or unavailable"),
     "Active Cooling":tc(15,"Cannot sweat in anticholinergic toxicity; external cooling for hyperthermia"),
     "Foley Catheter":tc(60,"For urinary retention; must monitor volume"),
     "Activated Charcoal":tc(60,"If within 1-2h; note: decreased GI motility may extend absorption window")},{})

N["Carbon Monoxide Poisoning"]=dx("Toxicology","Toxicology/Respiratory",v(105,120,75,22,98.6,95),
    S,{"heart_rate":8,"systolic_bp":8,"o2_saturation":1},
    "Headache, nausea, confusion, cherry red skin (LATE/unreliable); pulse ox falsely normal (reads COHgb as OxyHgb); house fire, enclosed space heater, car exhaust; multiple patients from same location",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"coHgb":lab(10,60,"%","elevated"),"lactate":lab(2.0,8.0,"mmol/L","elevated"),
     "troponin":lab(0,2.0,"ng/mL","variable"),"abg_po2":lab(60,100,"mmHg","variable")},
    ["IV Access","100% High-Flow O2","Continuous Monitoring"],
    {"100% O2 via NRB":tc(5,"IMMEDIATELY; reduces CO half-life from 5-6h to 60-90min; continue until COHgb <5% and asymptomatic"),
     "Hyperbaric Oxygen":tc(240,"COHgb >25%, pregnancy, neurological symptoms, cardiac ischemia, loss of consciousness; reduces delayed neuropsychiatric sequelae"),
     "Coexisting Cyanide Exposure":tc(30,"Fire victims: assume concomitant cyanide poisoning; hydroxocobalamin (Cyanokit) 5g IV if suspected"),
     "ECG + Troponin":tc(60,"CO binds myoglobin → direct myocardial toxicity; increased MI risk"),
     "Fetal Assessment":tc(30,"If pregnant: fetal Hgb has higher CO affinity than maternal Hgb; lower threshold for HBO")},{})

N["Organophosphate/Nerve Agent Poisoning"]=dx("Toxicology","Toxicology/Neurological",v(50,90,55,30,98.6,88),
    {"heart_rate":"inverse","systolic_bp":"decrease","diastolic_bp":"decrease","respiratory_rate":"multiply","temperature_f":"fixed","o2_saturation":"decrease"},
    {"heart_rate":10,"systolic_bp":10,"respiratory_rate":8,"o2_saturation":6},
    "DUMBELS: Diarrhea, Urination, Miosis, Bradycardia/Bronchospasm/Bronchorrhea, Emesis, Lacrimation, Salivation; cholinergic crisis; muscle fasciculations, weakness, seizures; pesticides, sarin, VX",
    {"o2_saturation_below":82,"systolic_bp_below":70},
    {"rbc_ache":lab(10,50,"%","decreased"),"lactate":lab(2.0,6.0,"mmol/L","elevated")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring","Decontamination"],
    {"Atropine":tc(5,"2mg IV q5min, doubling dose until (dry secretions); may need very large doses (100+ mg); does NOT reverse nicotinic effects (weakness/fasciculations)"),
     "Pralidoxime (2-PAM)":tc(30,"1-2g IV over 15-30min then infusion 500mg/hr; reactivates AChE before 'aging'; most effective early; reverses nicotinic effects"),
     "Decontamination":tc(5,"Remove all clothing, wash skin with soap and water; protect yourself FIRST — PPE for all providers"),
     "Benzodiazepines":tc(15,"Diazepam 10mg IV for seizures; midazolam IM if no IV"),
     "Intubation":tc(30,"For respiratory failure from bronchorrhea/bronchospasm/muscle weakness; avoid succinylcholine (prolonged paralysis)")},{})

# ═══════════════════ HEMATOLOGIC ═══════════════════

N["Sickle Cell Vaso-Occlusive Crisis"]=dx("Hematologic","Hematologic",v(105,118,72,20,100.5,94),
    S,{"heart_rate":8,"systolic_bp":5,"o2_saturation":4},
    "Severe bone/joint pain, chest pain (acute chest syndrome), priapism, stroke, splenic sequestration; triggered by dehydration, cold, infection, hypoxia, stress; dactylitis in children",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"hgb":lab(5,9,"g/dL","decreased"),"reticulocyte":lab(5,20,"%","elevated"),
     "ldh":lab(300,1000,"U/L","elevated"),"tbili":lab(1.5,5.0,"mg/dL","elevated"),
     "wbc":lab(10,25,"K/uL","elevated"),"lactate":lab(1.5,4.0,"mmol/L","elevated")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring","Pain Management"],
    {"IV Opioid Analgesia":tc(15,"Morphine 0.1mg/kg or hydromorphone 0.015mg/kg IV q15min until controlled; do NOT undertreat pain; PCA when stabilized"),
     "IV Fluids":tc(30,"NS at 1-1.5x maintenance; avoid overhydration (ACS risk)"),
     "Acute Chest Syndrome Screening":tc(60,"CXR if fever >38.5°C, respiratory symptoms, or chest pain; new infiltrate + fever/respiratory symptoms = ACS"),
     "Exchange Transfusion":tc(240,"For HgbS >30% crisis, ACS, stroke, or priapism >4h; target HgbS <30%"),
     "Incentive Spirometry":tc(30,"q2h while awake; PROVEN to reduce ACS risk during vaso-occlusive crisis")},{})

N["Disseminated Intravascular Coagulation (DIC)"]=dx("Hematologic","Hematologic",v(115,82,50,24,101.0,93),
    S,{"heart_rate":12,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":4},
    "Simultaneous thrombosis and hemorrhage; petechiae, purpura, oozing from lines/wounds, end-organ damage (renal, hepatic, CNS); triggers: sepsis, trauma, AML (especially APL), obstetric complications, pancreatitis",
    {"o2_saturation_below":88,"systolic_bp_below":65},
    {"plt":lab(10,80,"K/uL","decreased"),"fibrinogen":lab(50,150,"mg/dL","decreased"),
     "d_dimer":lab(5000,80000,"ng/mL","elevated"),"pt_inr":lab(1.5,4.0,"INR","elevated"),
     "ptt":lab(40,90,"sec","prolonged"),"schistocytes":lab(1,1,"present","present"),
     "ldh":lab(300,2000,"U/L","elevated")},
    ["IV Access","Continuous Monitoring","Blood Products"],
    {"Treat Underlying Cause":tc(30,"MOST IMPORTANT; DIC is ALWAYS secondary; antibiotics for sepsis, delivery for obstetric cause, chemo for APL"),
     "Cryoprecipitate":tc(30,"10 units for fibrinogen <100-150; each unit raises fibrinogen ~5-10mg/dL"),
     "Platelet Transfusion":tc(30,"Target >50K if bleeding; >20K prophylactic; may need ongoing due to consumption"),
     "FFP":tc(30,"15mL/kg for INR >1.5 with bleeding"),
     "Tranexamic Acid":tc(60,"Controversial; may help with hemorrhagic phenotype; avoid in acute thrombotic DIC; consider in obstetric DIC")},{})

N["Heparin-Induced Thrombocytopenia (HIT)"]=dx("Hematologic","Hematologic",v(95,125,78,18,99.0,96),
    S,{"heart_rate":8,"systolic_bp":8,"o2_saturation":2},
    "Platelet drop >50% from baseline 5-10 days after heparin exposure (or sooner if prior exposure); PARADOXICALLY pro-THROMBOTIC (not bleeding); DVT, PE, limb ischemia, stroke; 4T score for probability",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"plt":lab(20,100,"K/uL","decreased"),"hit_antibody":lab(1,1,"positive","positive"),
     "sra":lab(1,1,"positive","positive"),"d_dimer":lab(500,5000,"ng/mL","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"Stop ALL Heparin":tc(5,"Includes flushes, heparin-coated catheters, and LMWH; cross-reactivity with LMWH"),
     "Start Alternative Anticoagulant":tc(30,"Argatroban (direct thrombin inhibitor) preferred; bivalirudin for PCI; fondaparinux off-label; target PTT 1.5-3x baseline"),
     "4T Score":tc(30,"Calculate: Timing, Thrombocytopenia degree, Thrombosis, oTher causes; ≥4 = intermediate/high → send HIT antibody and treat while waiting"),
     "Duplex Ultrasound":tc(240,"Screen for DVT even if asymptomatic; 50% have subclinical thrombosis at diagnosis"),
     "Transition to Warfarin Carefully":tc(0,"Do NOT start warfarin until platelets >150K; overlap with argatroban 5+ days; premature warfarin → warfarin-induced skin necrosis/venous limb gangrene")},{})

N["Thrombotic Thrombocytopenic Purpura (TTP)"]=dx("Hematologic","Hematologic",v(110,105,65,20,100.5,96),
    S,{"heart_rate":10,"systolic_bp":8,"o2_saturation":2},
    "Classic pentad (rarely all present): thrombocytopenia, MAHA (schistocytes), neurological symptoms (confusion, seizures, focal deficits), renal dysfunction, fever; ADAMTS13 deficiency; young women predominate",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"plt":lab(5,30,"K/uL","decreased"),"hgb":lab(5,9,"g/dL","decreased"),
     "ldh":lab(500,3000,"U/L","elevated"),"tbili":lab(2,8,"mg/dL","elevated"),
     "haptoglobin":lab(0,10,"mg/dL","decreased"),"schistocytes":lab(1,1,">1%","present"),
     "cr":lab(0.8,2.5,"mg/dL","elevated"),"adamts13":lab(0,10,"%","decreased")},
    ["IV Access","Continuous Monitoring"],
    {"Emergent Plasma Exchange (PLEX)":tc(240,"DEFINITIVE treatment; reduces mortality from 90% to <20%; daily until platelet normalization + LDH normal; start plasma infusion if PLEX delayed"),
     "Corticosteroids":tc(120,"Methylprednisolone 1g IV daily x 3 days then prednisone 1mg/kg"),
     "DO NOT TRANSFUSE Platelets":tc(5,"CONTRAINDICATED unless life-threatening hemorrhage; 'fuel on the fire' — triggers more thrombosis"),
     "ADAMTS13 Activity":tc(120,"Send BEFORE plasma exchange (dilutes level); <10% confirmatory; >20% consider alternative diagnosis"),
     "Rituximab":tc(0,"For refractory or relapsing; anti-CD20 antibody addresses autoimmune etiology")},{})

N["Immune Thrombocytopenic Purpura (ITP) - Severe"]=dx("Hematologic","Hematologic",v(90,118,72,16,98.6,98),
    S,{"heart_rate":5,"systolic_bp":5,"o2_saturation":1},
    "Isolated thrombocytopenia with petechiae, purpura, mucosal bleeding (wet purpura = higher hemorrhage risk), menorrhagia; normal WBC and Hgb; no schistocytes (distinguishes from TTP/HUS); diagnosis of exclusion",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"plt":lab(1,30,"K/uL","decreased"),"hgb":lab(8,14,"g/dL","variable"),
     "wbc":lab(4,10,"K/uL","normal"),"peripheral_smear":lab(1,1,"large platelets, no schistocytes","normal")},
    ["IV Access","Continuous Monitoring"],
    {"Platelet Transfusion":tc(15,"Only for life-threatening bleeding or prior to emergent surgery; will be consumed rapidly but may be temporizing"),
     "IV Methylprednisolone":tc(120,"1g IV daily x 3 days for severe; or dexamethasone 40mg IV daily x 4 days"),
     "IVIG":tc(120,"1g/kg IV; for severe bleeding or pre-procedure; faster onset than steroids (24-48h); expensive"),
     "Tranexamic Acid":tc(60,"Adjunct for mucosal bleeding; holding pressure"),
     "Anti-D Immunoglobulin":tc(0,"50mcg/kg IV for Rh-positive patients with intact spleen; avoid if hemolysis/anemia")},{})

# ═══════════════════ PSYCHIATRIC ═══════════════════

N["Serotonin Syndrome"]=dx("Psychiatric","Psychiatric/Toxicology",v(112,155,95,22,103.0,96),
    {**S,"systolic_bp":"multiply","diastolic_bp":"multiply"},{"systolic_bp":8,"diastolic_bp":6,"heart_rate":8,"o2_saturation":2},
    "Triad: mental status changes (agitation, confusion), autonomic instability (hyperthermia, tachycardia, diaphoresis, diarrhea), neuromuscular excitability (clonus > rigidity, hyperreflexia, myoclonus); LOWER extremity clonus prominent; Hunter criteria",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"ck":lab(200,5000,"U/L","variable"),"cr":lab(0.6,2.0,"mg/dL","variable"),
     "wbc":lab(8,15,"K/uL","variable"),"lactate":lab(1.5,5.0,"mmol/L","elevated")},
    ["IV Access","Continuous Monitoring","Cooling Measures"],
    {"Stop Serotonergic Agents":tc(5,"IMMEDIATELY; SSRIs, SNRIs, MAOIs, tramadol, linezolid, triptans, fentanyl, ondansetron (weak), St. John's Wort"),
     "Benzodiazepines":tc(15,"Diazepam 5-10mg IV for agitation and myoclonus; first-line symptomatic treatment"),
     "Cyproheptadine":tc(30,"Serotonin antagonist; 12mg PO/NG loading then 2mg q2h; only PO/NG available"),
     "Active Cooling":tc(15,"For hyperthermia >104°F; neuromuscular paralysis with non-depolarizing agent + intubation for severe rigidity/hyperthermia"),
     "Distinguish from NMS":tc(5,"SS: clonus + hyperreflexia + rapid onset; NMS: lead-pipe rigidity + bradyreflexia + slow onset (days)")},{})

N["Neuroleptic Malignant Syndrome (NMS)"]=dx("Psychiatric","Psychiatric/Neurological",v(110,160,100,24,105.0,95),
    {**S,"systolic_bp":"multiply","diastolic_bp":"multiply"},{"systolic_bp":8,"diastolic_bp":6,"heart_rate":8,"o2_saturation":3},
    "FEVER + lead-pipe RIGIDITY + altered mental status + autonomic instability; develops over DAYS after starting/increasing antipsychotic or stopping dopaminergic; bradyreflexia (vs SS hyperreflexia); CK massively elevated",
    {"o2_saturation_below":88,"systolic_bp_below":75},
    {"ck":lab(1000,100000,"U/L","elevated"),"cr":lab(1.0,5.0,"mg/dL","elevated"),
     "k":lab(4.0,7.0,"mEq/L","elevated"),"wbc":lab(10,20,"K/uL","elevated"),
     "lactate":lab(2.0,8.0,"mmol/L","elevated"),"myoglobin":lab(100,10000,"ng/mL","elevated"),
     "ast":lab(50,500,"U/L","elevated")},
    ["IV Access","Continuous Monitoring","Cooling Measures","ICU"],
    {"Stop Offending Agent":tc(5,"Discontinue ALL antipsychotics and anti-emetics (metoclopramide, prochlorperazine)"),
     "Dantrolene":tc(60,"1-2.5mg/kg IV q5min; skeletal muscle relaxant; reduces rigidity and thermogenesis; continue 1mg/kg q4-8h"),
     "Bromocriptine":tc(60,"2.5-5mg PO/NG q8h; dopamine agonist; restores dopaminergic tone; DO NOT give with dantrolene (some controversy)"),
     "Aggressive IV Fluids":tc(30,"Rhabdomyolysis prevention; NS at 200-300mL/hr initially; target UOP 200-300mL/hr"),
     "Active Cooling":tc(15,"External cooling for hyperthermia; benzodiazepines adjunct for rigidity")},{})

N["Acute Psychosis - Agitated/Violent"]=dx("Psychiatric","Psychiatric",v(110,145,90,20,98.6,98),
    {**S,"systolic_bp":"multiply"},{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Acute behavioral emergency; disorganized speech, paranoia, hallucinations, agitation, self-harm risk; MUST rule out organic causes: hypoglycemia, hypoxia, head injury, intoxication, infection, thyroid, seizure",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"glu":lab(60,200,"mg/dL","variable"),"tsh":lab(0.1,10,"mIU/L","variable"),
     "uds":lab(0,1,"variable","variable"),"ethanol":lab(0,400,"mg/dL","variable"),
     "wbc":lab(4,15,"K/uL","variable")},
    ["Continuous Monitoring"],
    {"Verbal De-escalation":tc(5,"FIRST-LINE always; L.E.A.P technique; offer food/water/blanket; reduce stimuli; nonthreatening posture"),
     "Haloperidol + Lorazepam + Diphenhydramine":tc(15,"'B52': haloperidol 5mg + lorazepam 2mg + diphenhydramine 50mg IM; or olanzapine 10mg IM (do NOT combine with IM benzos → respiratory depression)"),
     "Medical Clearance":tc(120,"Glucose, vitals, UDS, +/- CT head, +/- LP; rule out organic psychosis before psychiatric disposition"),
     "Physical Restraints":tc(5," Last resort; 1:1 monitoring; reassess q15min; remove ASAP; document indication and monitoring")},{})

N["Suicidal Ideation with Plan - High Risk"]=dx("Psychiatric","Psychiatric",v(85,130,80,16,98.6,98),
    S,{"systolic_bp":3,"diastolic_bp":2,"o2_saturation":1},
    "Active suicidal ideation with specific plan, intent, and access to means; risk factors: prior attempt, psychiatric illness, substance use, recent loss, social isolation, male >65, chronic pain; assess lethal means",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"glu":lab(70,110,"mg/dL","normal"),"tsh":lab(0.5,4.5,"mIU/L","normal"),
     "uds":lab(0,1,"variable","variable"),"ethanol":lab(0,400,"mg/dL","variable"),
     "apap_level":lab(0,10,"mcg/mL","normal"),"salicylate":lab(0,5,"mg/dL","normal")},
    ["Continuous 1:1 Observation","Search for Means"],
    {"1:1 Observation":tc(5,"Constant visual observation; remove all potential means of self-harm from environment (sharps, cords, medications, belts)"),
     "Psychiatric Evaluation":tc(120,"Formal risk assessment including Columbia Suicide Severity Rating Scale (C-SSRS); determine inpatient vs outpatient level of care"),
     "Means Restriction":tc(15,"Lethal means counseling; remove access to firearms (most lethal method), medications, bridges"),
     "Medical Workup":tc(60,"Check APAP/salicylate levels, UDS, EtOH (co-ingestions); TSH; medical clearance"),
     "Safety Planning":tc(240,"If discharge planned: identify warning signs, coping strategies, contacts, restrict means; Crisis Text Line (741741), 988 Suicide Lifeline")},{})

# ═══════════════════ ENVIRONMENTAL ═══════════════════

N["Heat Stroke - Exertional"]=dx("Environmental","Environmental",v(135,85,52,28,106.5,96),
    S,{"heart_rate":12,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":2},
    "Core temp >104°F (40°C) + CNS dysfunction (confusion, seizures, coma); may or may not be sweating; exertional: young athletes/military; classic: elderly, medications, heat wave; rhabdomyolysis, DIC, liver/renal failure",
    {"o2_saturation_below":90,"systolic_bp_below":70},
    {"ck":lab(500,50000,"U/L","elevated"),"cr":lab(1.0,5.0,"mg/dL","elevated"),
     "ast":lab(50,5000,"U/L","elevated"),"k":lab(3.5,6.5,"mEq/L","variable"),
     "lactate":lab(2.0,10.0,"mmol/L","elevated"),"pt_inr":lab(1.0,3.0,"INR","variable"),
     "plt":lab(30,200,"K/uL","variable")},
    ["IV Access","Continuous Monitoring","Rapid Cooling"],
    {"Rapid Cooling":tc(5,"Target: reduce core temp to 101.3°F (38.5°C) within 30min; COLD WATER IMMERSION is best (reduces temp fastest); evaporative cooling if immersion unavailable"),
     "IV Fluids":tc(15,"NS 1-2L bolus; anticipate massive fluid requirements; monitor UOP"),
     "Avoid Antipyretics":tc(5,"NSAIDs and acetaminophen are INEFFECTIVE; heatstroke is NOT from prostaglandin elevation"),
     "Continuous Core Temperature":tc(5,"Rectal or esophageal probe; tympanic and axillary are inaccurate at extremes"),
     "Monitor for Complications":tc(60,"Rhabdomyolysis (CK q6h), DIC (coag panel), hepatic failure (LFTs may rise for 48-72h), renal failure")},{})

N["Hypothermia - Severe (<82.4°F / <28°C)"]=dx("Environmental","Environmental",v(35,72,42,6,82.0,88),
    {"heart_rate":"inverse","systolic_bp":"decrease","diastolic_bp":"decrease","respiratory_rate":"inverse","temperature_f":"decrease","o2_saturation":"decrease"},
    {"heart_rate":15,"systolic_bp":15,"respiratory_rate":8,"o2_saturation":5},
    "Altered mental status, bradycardia, J/Osborn waves on ECG, VF risk below 82.4°F (28°C); 'not dead until warm and dead'; loss of shivering below 86°F; paradoxical undressing; atrial fibrillation common",
    {"o2_saturation_below":80,"systolic_bp_below":55},
    {"k":lab(3.0,8.0,"mEq/L","variable"),"glu":lab(40,200,"mg/dL","variable"),
     "ph":lab(7.0,7.35,"arterial","variable"),"lactate":lab(2.0,8.0,"mmol/L","elevated"),
     "abg_pco2":lab(35,60,"mmHg","variable")},
    ["IV Access","Continuous Monitoring","Handle Gently"],
    {"Passive + Active External Rewarming":tc(15,"Remove wet clothes; warm blankets, Bair hugger; warm IV fluids (40-42°C); avoid rough handling (triggers VF)"),
     "Active Core Rewarming":tc(30,"For severe: warm humidified O2, warm peritoneal/pleural lavage, intravascular warming catheter; ECMO for cardiac arrest or refractory"),
     "Cardiac Monitoring":tc(5,"J waves, prolonged intervals, AF; one defibrillation attempt if VF; if unsuccessful, defer additional shocks until >30°C; continue CPR"),
     "Avoid Vasopressors Until Rewarmed":tc(5,"Drugs accumulate and may cause toxicity when patient warms and metabolism resumes; may give once if >30°C"),
     "Check Potassium":tc(15,"K >12 mEq/L associated with non-survivable injury; K <12 → aggressive rewarming")},{})

N["Drowning (Submersion Injury)"]=dx("Environmental","Environmental/Respiratory",v(110,88,55,28,95.0,80),
    S,{"heart_rate":10,"systolic_bp":12,"respiratory_rate":8,"o2_saturation":8},
    "Pulmonary edema (both fresh and saltwater), aspiration pneumonia/pneumonitis, ARDS, hypothermia; fresh water absorbed into pulmonary vasculature; saltwater pulls fluid into alveoli; 'dry drowning' (laryngospasm without aspiration) is largely a myth",
    {"o2_saturation_below":75,"systolic_bp_below":65},
    {"abg_po2":lab(35,70,"mmHg","decreased"),"abg_pco2":lab(40,65,"mmHg","elevated"),
     "lactate":lab(2.0,8.0,"mmol/L","elevated"),"na":lab(125,150,"mEq/L","variable"),
     "hgb":lab(8,16,"g/dL","variable")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring","Warming if hypothermic"],
    {"Ventilatory Support":tc(10,"High-flow O2, CPAP, or intubation with PEEP (critical for surfactant washout); lung-protective ventilation for ARDS"),
     "C-Spine Precautions":tc(5,"If diving/trauma mechanism; maintain immobilization until cleared"),
     "Rewarming":tc(15,"If hypothermic; see hypothermia protocol; may require prolonged resuscitation ('not dead until warm and dead')"),
     "Observe 6-8h Minimum":tc(0,"All submersion victims; delayed pulmonary edema may develop; if asymptomatic with normal CXR at 6h → consider discharge"),
     "Bronchoscopy":tc(120,"If aspiration of particulate matter (sand, vomitus)")},{})

N["High Altitude Cerebral Edema (HACE)"]=dx("Environmental","Environmental/Neurological",v(110,120,75,22,99.0,85),
    S,{"heart_rate":8,"systolic_bp":5,"o2_saturation":8},
    "Ataxia + altered mental status at altitude; progression of AMS (acute mountain sickness); truncal ataxia on tandem gait is early sign; papilledema, retinal hemorrhages; above 2500m; vasogenic edema",
    {"o2_saturation_below":75,"systolic_bp_below":80},
    {"abg_po2":lab(35,60,"mmHg","decreased"),"abg_pco2":lab(25,35,"mmHg","decreased"),
     "hgb":lab(14,20,"g/dL","elevated")},
    ["Oxygen Therapy","Continuous Monitoring"],
    {"Immediate Descent":tc(30,"DESCEND at least 300-1000m; single most important intervention; helicopter evacuation if unable to walk"),
     "Dexamethasone":tc(15,"8mg IV/IM loading then 4mg q6h; reduces vasogenic edema; bridge until descent possible"),
     "Supplemental O2":tc(10,"Target SpO2 >90%; Gamow bag if supplemental O2 unavailable (portable hyperbaric chamber)"),
     "Avoid Sedatives":tc(5,"Mask neurological deterioration"),
     "HAPE Coexistence":tc(15,"50% of HACE patients have concurrent HAPE; nifedipine 30mg ER + O2 if pulmonary edema present")},{})

N["Anaphylaxis - Severe"]=dx("Immunologic/Allergic","Immunologic",v(125,72,42,26,98.6,90),
    S,{"heart_rate":12,"systolic_bp":25,"diastolic_bp":18,"o2_saturation":6},
    "Rapid onset (minutes to hours) of skin involvement (urticaria/angioedema) + respiratory compromise (stridor/wheeze/dyspnea) + hypotension/tachycardia; biphasic reaction in 5-20% (recurrence 1-72h); common triggers: food (nuts, shellfish), drugs (PCN, NSAIDs), Hymenoptera stings, latex",
    {"o2_saturation_below":82,"systolic_bp_below":55},
    {"tryptase":lab(11.5,200,"ng/mL","elevated")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring"],
    {"Epinephrine IM":tc(1,"0.3-0.5mg (0.01mg/kg in children) IM mid-outer thigh; REPEAT q5-15min if needed; FIRST-LINE — no contraindications in anaphylaxis; delays increase mortality"),
     "IV Fluids":tc(15,"NS 1-2L rapid bolus for hypotension; may need 5-10L due to distributive shock and third spacing"),
     "Albuterol Nebulizer":tc(15,"2.5-5mg for bronchospasm not responsive to epinephrine"),
     "Epinephrine Drip":tc(30,"For refractory hypotension: 1-4mcg/min; after 2-3 IM doses without response"),
     "Observation 4-6h minimum":tc(0,"Biphasic reaction risk; 12-24h observation for severe reactions; discharge with EpiPen prescription and allergy referral")},{})

N["Angioedema - Hereditary (HAE)"]=dx("Immunologic/Allergic","Immunologic",v(95,115,72,20,98.6,96),
    S,{"heart_rate":8,"systolic_bp":8,"o2_saturation":4},
    "Non-pruritic, non-pitting swelling of face/lips/tongue/larynx/intestine; NO urticaria (distinguishes from allergic angioedema); does NOT respond to epinephrine, antihistamines, or steroids; C1-INH deficiency; family history in 75%",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"c4":lab(2,10,"mg/dL","decreased"),"c1_inh_level":lab(5,30,"%","decreased"),
     "c1_inh_function":lab(10,40,"%","decreased")},
    ["IV Access","Continuous Monitoring","Airway Management"],
    {"C1-INH Concentrate":tc(30,"Berinert 20 units/kg IV; or Cinryze 1000 units IV; FIRST-LINE treatment; replaces deficient protein"),
     "Icatibant":tc(30,"Bradykinin B2 receptor antagonist; 30mg SC; alternative to C1-INH concentrate"),
     "Ecallantide":tc(30,"Kallikrein inhibitor; 30mg SC; monitor 30min for anaphylaxis risk (healthcare setting only)"),
     "Airway Management":tc(15,"Early intubation if airway involvement; may need surgical airway if rapid progression"),
     "Epinephrine + Antihistamines + Steroids WILL NOT WORK":tc(5,"Bradykinin-mediated, NOT histamine-mediated; these drugs are ineffective but should be given while considering diagnosis")},{})

N["Systemic Lupus Erythematosus - Flare"]=dx("Immunologic/Allergic","Immunologic/Rheumatologic",v(100,108,68,18,100.5,97),
    S,{"heart_rate":8,"systolic_bp":8,"o2_saturation":2},
    "Multi-organ flare: malar 'butterfly' rash, arthritis, serositis (pleural/pericardial effusion), nephritis (edema, proteinuria), CNS lupus (seizures, psychosis), cytopenias, fatigue, fever; triggered by UV exposure, infection, medication changes",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"wbc":lab(2,6,"K/uL","decreased"),"hgb":lab(7,11,"g/dL","decreased"),
     "plt":lab(30,150,"K/uL","decreased"),"cr":lab(0.6,3.0,"mg/dL","variable"),
     "c3":lab(20,60,"mg/dL","decreased"),"c4":lab(3,15,"mg/dL","decreased"),
     "anti_dsdna":lab(1,1,"elevated","elevated"),"esr":lab(40,100,"mm/hr","elevated"),
     "urine_protein":lab(300,5000,"mg/g Cr","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"Pulse Methylprednisolone":tc(240,"1g IV daily x 3 days for severe flare (nephritis, cerebritis, severe cytopenias)"),
     "Hydroxychloroquine":tc(0,"Maintain/resume; reduces flares by 50%; should NEVER be stopped"),
     "Mycophenolate/Cyclophosphamide":tc(0,"For lupus nephritis; MMF preferred for induction in most (ALMS trial); cyclophosphamide for severe proliferative nephritis"),
     "Evaluate for Infection":tc(60,"Immunosuppressed patients: always rule out infection before treating flare as they may mimic each other"),
     "Renal Biopsy":tc(0,"Active urine sediment with rising creatinine → biopsy to classify ISN/RPS class; guides treatment")},{})

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
print(f"Added {added} Peds/Tox/Heme/Psych/Env/Immuno diagnoses. Total: {len(data['diagnoses'])}")
for c in sorted(cats):
    print(f"  {c}: {len(cats[c])}")

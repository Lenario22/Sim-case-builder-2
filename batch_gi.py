#!/usr/bin/env python3
"""Batch 4: Gastrointestinal diagnoses expansion."""
import json
from pathlib import Path

OUTPUT = Path(__file__).parent / "diagnosis_data.json"

def dx(cat, organ, vitals, modifiers, weights, pe, thresholds, labs, interventions, tc_actions, comorbidity=None):
    return {"category":cat,"organ_system":organ,"vitals":vitals,"vital_modifiers":modifiers,
            "vital_severity_weights":weights,"pe_findings":pe,"critical_pe_thresholds":thresholds,
            "expected_labs":labs,"required_interventions":interventions,"time_critical_actions":tc_actions,
            "comorbidity_modifiers":comorbidity or {}}

def v(hr,sbp,dbp,rr,temp,spo2):
    return {"heart_rate":hr,"systolic_bp":sbp,"diastolic_bp":dbp,"respiratory_rate":rr,"temperature_f":temp,"o2_saturation":spo2}

def lab(mn,mx,unit,direction):
    return {"min":mn,"max":mx,"unit":unit,"direction":direction}

def tc(window,rationale):
    return {"window_minutes":window,"rationale":rationale}

STD={"heart_rate":"multiply","systolic_bp":"decrease","diastolic_bp":"decrease","respiratory_rate":"multiply","temperature_f":"fixed","o2_saturation":"decrease"}

NEW={}

NEW["Upper GI Bleed - Variceal"]=dx("Gastrointestinal","GI",v(118,85,52,22,98.6,95),
    STD,{"heart_rate":10,"systolic_bp":20,"diastolic_bp":15,"o2_saturation":3},
    "Hematemesis (bright red blood or coffee-ground), melena, signs of chronic liver disease (spider angiomata, ascites, jaundice, palmar erythema), splenomegaly, caput medusae",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"hgb":lab(5,10,"g/dL","decreased"),"plt":lab(40,150,"K/uL","decreased"),"pt_inr":lab(1.3,3.0,"INR","elevated"),
     "lactate":lab(2.0,6.0,"mmol/L","elevated"),"bun":lab(20,60,"mg/dL","elevated"),"cr":lab(0.8,2.5,"mg/dL","variable"),
     "alb":lab(1.5,3.0,"g/dL","decreased")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Blood Type and Crossmatch"],
    {"Octreotide":tc(30,"50mcg IV bolus then 50mcg/hr drip; reduces splanchnic blood flow"),
     "IV PPI":tc(30,"Pantoprazole 80mg bolus though primarily for non-variceal; start empirically"),
     "Emergent EGD":tc(720,"Band ligation within 12h; definitive treatment for variceal bleed"),
     "Ceftriaxone":tc(60,"1g IV q24h x 7 days; antibiotic prophylaxis reduces mortality in cirrhotics"),
     "pRBC Transfusion":tc(30,"Target Hgb >7; over-transfusion worsens portal HTN")},
    {"Cirrhosis":{"pt_inr":{"min":1.5,"max":3.5},"plt":{"min":30,"max":100}}})

NEW["Upper GI Bleed - Peptic Ulcer"]=dx("Gastrointestinal","GI",v(110,92,58,20,98.6,96),
    STD,{"heart_rate":10,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":2},
    "Hematemesis or coffee-ground emesis, melena, epigastric tenderness, possible NSAID/aspirin use, H. pylori history; Rockall/Glasgow-Blatchford scores guide urgency",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"hgb":lab(6,12,"g/dL","decreased"),"bun":lab(20,50,"mg/dL","elevated"),"cr":lab(0.6,2.0,"mg/dL","variable"),
     "pt_inr":lab(0.9,1.5,"INR","variable"),"lactate":lab(1.5,4.0,"mmol/L","elevated")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring"],
    {"IV PPI":tc(30,"Pantoprazole 80mg bolus then 8mg/hr drip; reduces rebleeding"),
     "EGD":tc(720,"Within 24h; epinephrine injection + thermal/clip for active bleeding"),
     "pRBC Transfusion":tc(60,"Target Hgb >7 (>8 if CAD)"),
     "H. pylori Testing":tc(0,"Stool antigen or biopsy at EGD; eradication dramatically reduces recurrence")},
    {"NSAID Use":{"risk":"increased ulcer size and bleeding risk"}})

NEW["Lower GI Bleed - Diverticular"]=dx("Gastrointestinal","GI",v(100,105,65,18,98.6,97),
    STD,{"heart_rate":8,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":2},
    "Painless hematochezia (bright red blood per rectum), usually large-volume; typically right-sided diverticula in elderly; 80% stop spontaneously",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"hgb":lab(7,13,"g/dL","decreased"),"bun":lab(10,30,"mg/dL","variable"),"cr":lab(0.6,1.8,"mg/dL","variable"),
     "pt_inr":lab(0.9,1.5,"INR","variable"),"lactate":lab(1.0,3.0,"mmol/L","variable")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring"],
    {"Colonoscopy":tc(0,"After bowel prep if hemodynamically stable; identifies source in 70-80%"),
     "CTA Abdomen":tc(60,"If active brisk bleeding; identifies extravasation for IR embolization"),
     "Interventional Radiology":tc(120,"Angiographic embolization if active bleeding identified on CTA"),
     "Resuscitation":tc(30,"IV crystalloid and pRBC as needed; majority stop spontaneously")},{})

NEW["Acute Pancreatitis - Mild"]=dx("Gastrointestinal","GI",v(95,125,78,18,99.5,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Severe epigastric pain radiating to back, nausea/vomiting, epigastric tenderness without peritoneal signs, mild distension; Ranson criteria, BISAP score for prognostication",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"lipase":lab(200,1500,"U/L","elevated"),"amylase":lab(200,800,"U/L","elevated"),
     "wbc":lab(10,18,"K/uL","elevated"),"alt":lab(30,200,"U/L","variable"),
     "cr":lab(0.6,1.4,"mg/dL","normal"),"ca":lab(8.5,10.5,"mg/dL","normal"),
     "glu":lab(100,200,"mg/dL","variable"),"trig":lab(50,500,"mg/dL","variable")},
    ["IV Access","Fluid Resuscitation","Continuous Monitoring"],
    {"Aggressive IV Fluids":tc(30,"LR at 5-10mL/kg/hr initial; goal-directed; reduces necrosis risk"),
     "Pain Management":tc(30,"IV hydromorphone or fentanyl; meperidine no longer preferred"),
     "NPO Initially":tc(0,"Start clear liquid diet when pain improving; early feeding improves outcomes"),
     "RUQ Ultrasound":tc(240,"Evaluate for gallstones as etiology; cholecystectomy during same admission if gallstone pancreatitis")},{})

NEW["Acute Pancreatitis - Severe/Necrotizing"]=dx("Gastrointestinal","GI",v(120,88,55,24,101.5,93),
    STD,{"heart_rate":12,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":4},
    "Severe epigastric pain, peritoneal signs, Cullen sign (periumbilical ecchymosis), Grey Turner sign (flank ecchymosis), SIRS/shock, third-spacing with massive fluid losses",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"lipase":lab(500,10000,"U/L","elevated"),"wbc":lab(15,30,"K/uL","elevated"),"cr":lab(1.2,4.0,"mg/dL","elevated"),
     "lactate":lab(3.0,8.0,"mmol/L","elevated"),"ca":lab(6.0,8.5,"mg/dL","decreased"),
     "hct":lab(40,55,"%","elevated"),"bun":lab(25,60,"mg/dL","elevated"),
     "glu":lab(150,350,"mg/dL","elevated"),"ldh":lab(300,1000,"U/L","elevated")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Continuous Monitoring","Foley Catheter"],
    {"Aggressive IV Fluids":tc(15,"Goal-directed resuscitation; may need 250-500mL/hr initially"),
     "CT Abdomen with Contrast":tc(72,"At 72h to assess necrosis extent; not needed initially"),
     "ICU Admission":tc(60,"Organ failure defines severe pancreatitis per revised Atlanta"),
     "Antibiotics":tc(0,"Only if infected necrosis suspected (fever, gas in collection); imipenem"),
     "Nutrition":tc(0,"Enteral via NJ tube preferred over TPN if unable to eat >5-7 days")},
    {"Alcohol Use":{"risk":"most common etiology in males"},"Gallstones":{"risk":"most common overall etiology"}})

NEW["Acute Cholecystitis"]=dx("Gastrointestinal","GI/Hepatobiliary",v(95,135,82,18,100.5,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "RUQ pain radiating to right scapula, positive Murphy sign, RUQ guarding, mild jaundice possible; fever suggests complicated (empyema, perforation, gangrenous)",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"wbc":lab(11,18,"K/uL","elevated"),"alt":lab(20,80,"U/L","variable"),"ast":lab(20,60,"U/L","variable"),
     "alk_phos":lab(50,150,"U/L","variable"),"tbili":lab(0.5,3.0,"mg/dL","variable"),
     "lipase":lab(10,200,"U/L","variable"),"crp":lab(1.0,10.0,"mg/dL","elevated")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"RUQ Ultrasound":tc(120,"Gallstones + wall thickening >3mm + pericholecystic fluid + sonographic Murphy sign"),
     "IV Antibiotics":tc(120,"Piperacillin-tazobactam or ceftriaxone + metronidazole"), 
     "Surgical Consult":tc(240,"Early cholecystectomy within 72h; better outcomes than delayed"),
     "HIDA Scan":tc(0,"If US equivocal; sensitivity >95% for acute cholecystitis")},{})

NEW["Acute Cholangitis"]=dx("Gastrointestinal","GI/Hepatobiliary",v(108,95,58,22,103.0,95),
    STD,{"heart_rate":12,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":3},
    "Charcot triad: RUQ pain, fever, jaundice (50-70%); Reynolds pentad adds AMS and hypotension (septic cholangitis); biliary colic history",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"wbc":lab(15,30,"K/uL","elevated"),"tbili":lab(3.0,15.0,"mg/dL","elevated"),
     "alk_phos":lab(200,800,"U/L","elevated"),"ggt":lab(100,500,"U/L","elevated"),
     "alt":lab(50,500,"U/L","elevated"),"lactate":lab(2.0,6.0,"mmol/L","elevated"),
     "blood_cx":lab(1,1,"positive","elevated")},
    ["IV Access","Antibiotics","Fluid Resuscitation","Continuous Monitoring"],
    {"IV Antibiotics":tc(60,"Piperacillin-tazobactam 4.5g q6h; cover gram-neg rods and anaerobes"),
     "Biliary Decompression":tc(720,"ERCP within 24-48h; emergent within 12h if septic/Reynolds pentad"),
     "Blood Cultures":tc(30,"Before antibiotics; E. coli, Klebsiella, Enterococcus most common"),
     "RUQ Ultrasound":tc(120,"CBD dilation >6mm (>8mm post-cholecystectomy) suggests obstruction")},{})

NEW["Acute Appendicitis"]=dx("Gastrointestinal","GI",v(95,128,78,18,100.0,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Periumbilical pain migrating to RLQ (McBurney point), anorexia, nausea, positive Rovsing/psoas/obturator signs, low-grade fever; guarding and rebound suggest perforation",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(11,18,"K/uL","elevated"),"crp":lab(1.0,10.0,"mg/dL","elevated"),
     "ua":lab(0,5,"wbc/HPF","normal"),"lipase":lab(10,60,"U/L","normal")},
    ["IV Access","Continuous Monitoring"],
    {"CT Abdomen/Pelvis":tc(120,"With IV contrast; >95% sensitivity; dilated appendix >6mm, periappendiceal fat stranding"),
     "Surgical Consult":tc(240,"Laparoscopic appendectomy; <24h if uncomplicated"),
     "NPO":tc(30,"Hold oral intake pending surgical evaluation"),
     "IV Antibiotics":tc(240,"Cefoxitin or ertapenem if perforation suspected; preop prophylaxis for uncomplicated")},{})

NEW["Perforated Appendicitis with Abscess"]=dx("Gastrointestinal","GI",v(110,105,65,22,102.5,96),
    STD,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":2},
    "RLQ pain (may be diffuse if free perforation), high fever, tachycardia, diffuse peritonitis or palpable RLQ mass, toxic appearance",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"wbc":lab(15,28,"K/uL","elevated"),"crp":lab(10,30,"mg/dL","elevated"),
     "lactate":lab(2.0,5.0,"mmol/L","elevated"),"cr":lab(0.6,2.0,"mg/dL","variable")},
    ["IV Access","Antibiotics","Fluid Resuscitation","Continuous Monitoring"],
    {"CT Abdomen/Pelvis":tc(60,"Perforated appendix with abscess, free fluid, or phlegmon"),
     "IV Antibiotics":tc(60,"Broad-spectrum: piperacillin-tazobactam or meropenem"),
     "IR Drainage":tc(240,"Percutaneous drainage if abscess >3cm; antibiotics + interval appendectomy in 6-8 weeks"),
     "Surgical Consult":tc(120,"Emergent OR if diffuse peritonitis or failed non-operative management")},{})

NEW["Small Bowel Obstruction"]=dx("Gastrointestinal","GI",v(100,120,75,18,98.6,97),
    STD,{"heart_rate":8,"systolic_bp":10,"diastolic_bp":8,"o2_saturation":2},
    "Colicky abdominal pain, vomiting (bilious→ feculent in distal SBO), abdominal distension, high-pitched tinkling bowel sounds, prior surgical history (adhesions #1 cause)",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"wbc":lab(8,15,"K/uL","variable"),"bmp":lab(1,1,"","variable"),"lactate":lab(1.0,3.0,"mmol/L","variable"),
     "cr":lab(0.6,2.0,"mg/dL","variable"),"k":lab(2.8,4.5,"mEq/L","decreased")},
    ["IV Access","NG Tube Decompression","Continuous Monitoring"],
    {"CT Abdomen/Pelvis":tc(120,"Transition point, small bowel dilation >3cm, decompressed distal bowel"),
     "NG Tube":tc(60,"Salem sump to low intermittent suction; decompression and vomiting relief"),
     "IV Fluid Resuscitation":tc(30,"Replace large third-space losses; monitor UOP"),
     "Surgical Consult":tc(240,"Operative if complete obstruction, strangulation (fever, peritonitis, elevated lactate), or failure to resolve in 48-72h")},{})

NEW["Large Bowel Obstruction"]=dx("Gastrointestinal","GI",v(90,125,78,18,98.6,97),
    STD,{"heart_rate":8,"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Progressive abdominal distension, obstipation (no gas or stool), crampy pain, vomiting (late finding), tympanic abdomen; colon cancer most common cause",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"wbc":lab(8,18,"K/uL","variable"),"cr":lab(0.6,2.0,"mg/dL","variable"),
     "lactate":lab(1.0,4.0,"mmol/L","variable"),"cea":lab(0,20,"ng/mL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"CT Abdomen/Pelvis":tc(120,"Dilated colon proximal to transition point; evaluate for cecal diameter >12cm (perforation risk)"),
     "Surgical Consult":tc(120,"Emergent if cecal dilation >12cm, perforation, or peritonitis"),
     "NG Tube":tc(60,"Decompression if vomiting"),
     "Rectal Tube/Sigmoidoscopy":tc(240,"For sigmoid volvulus decompression if no peritonitis")},{})

NEW["Sigmoid Volvulus"]=dx("Gastrointestinal","GI",v(95,115,72,18,98.6,97),
    STD,{"heart_rate":8,"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Elderly, institutionalized, psychiatric patients on anticholinergics; massive abdominal distension, obstipation, 'coffee bean sign' on XR, omega loop sign on CT",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"wbc":lab(8,18,"K/uL","variable"),"lactate":lab(1.0,4.0,"mmol/L","variable"),
     "cr":lab(0.6,2.0,"mg/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Abdominal XR":tc(60,"Classic coffee-bean / bent inner-tube sign; ahaustral dilated sigmoid"),
     "Sigmoidoscopy":tc(240,"Endoscopic detorsion first-line if no peritonitis; successful in 70-80%"),
     "Rectal Tube":tc(240,"After detorsion to maintain decompression"),
     "Surgical Consult":tc(120,"Sigmoid colectomy for recurrence, failed detorsion, or gangrenous bowel")},{})

NEW["Cecal Volvulus"]=dx("Gastrointestinal","GI",v(100,110,68,20,98.6,96),
    STD,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":2},
    "Right-sided abdominal distension and pain, younger than sigmoid volvulus (30-60yrs), dilated cecum displaced to LUQ on imaging; endoscopic detorsion usually NOT effective",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"wbc":lab(10,20,"K/uL","elevated"),"lactate":lab(1.5,5.0,"mmol/L","elevated"),
     "cr":lab(0.6,2.0,"mg/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"CT Abdomen":tc(60,"Whirl sign, dilated cecum >10cm, ectopic cecum"),
     "Surgical Consult":tc(120,"Right hemicolectomy is definitive treatment; cecopexy if viable bowel"),
     "IV Fluid Resuscitation":tc(30,"Aggressive hydration for third-spacing")},{})

NEW["Mesenteric Ischemia - Acute"]=dx("Gastrointestinal","GI/Vascular",v(115,95,58,22,98.6,96),
    STD,{"heart_rate":12,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "PAIN OUT OF PROPORTION TO EXAM (classic); severe periumbilical pain, bloody diarrhea (late), metabolic acidosis, AF history (SMA embolism most common); gut feeling of impending doom",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"lactate":lab(3.0,10.0,"mmol/L","elevated"),"wbc":lab(15,30,"K/uL","elevated"),
     "hco3":lab(12,20,"mEq/L","decreased"),"amylase":lab(100,500,"U/L","elevated"),
     "ldh":lab(300,1000,"U/L","elevated"),"d_dimer":lab(500,10000,"ng/mL","elevated"),
     "abg_ph":lab(7.15,7.35,"","decreased")},
    ["IV Access","Fluid Resuscitation","Continuous Monitoring"],
    {"CTA Abdomen":tc(60,"EMERGENT; filling defect in SMA/SMV; bowel wall non-enhancement, pneumatosis"),
     "Surgical Consult":tc(60,"Emergent laparotomy for peritonitis or bowel necrosis"),
     "Heparin Drip":tc(60,"Anticoagulation for thrombotic or embolic causes"),
     "Broad-Spectrum Antibiotics":tc(60,"Bacterial translocation through ischemic gut wall")},
    {"Atrial Fibrillation":{"risk":"SMA embolism 50% of acute mesenteric ischemia"}})

NEW["Mesenteric Ischemia - Chronic"]=dx("Gastrointestinal","GI/Vascular",v(85,135,82,16,98.6,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Postprandial pain (intestinal angina) 15-30min after eating, food fear, weight loss, PVD history; abdominal bruit; 2 of 3 mesenteric vessels must be stenosed for symptoms",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"alb":lab(2.0,3.5,"g/dL","decreased"),"cr":lab(0.6,1.8,"mg/dL","variable"),
     "lipid_panel":lab(150,300,"mg/dL","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"CTA Abdomen":tc(240,"Mesenteric artery stenosis/occlusion; collateral vessels may be present"),
     "Mesenteric Angiography":tc(0,"Gold standard; also interventional (stenting/angioplasty)"),
     "Nutrition":tc(0,"Small frequent meals; nutritional optimization before intervention")},{})

NEW["Ischemic Colitis"]=dx("Gastrointestinal","GI/Vascular",v(90,115,72,18,98.6,97),
    STD,{"heart_rate":8,"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Crampy left-sided abdominal pain followed by bloody diarrhea within 24h; splenic flexure and rectosigmoid junction (watershed areas) most commonly affected",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"wbc":lab(10,18,"K/uL","elevated"),"lactate":lab(1.5,4.0,"mmol/L","variable"),
     "hgb":lab(10,14,"g/dL","variable"),"ldh":lab(200,500,"U/L","variable")},
    ["IV Access","Continuous Monitoring"],
    {"CT Abdomen":tc(120,"Bowel wall thickening in watershed distribution; thumbprinting"),
     "Colonoscopy":tc(0,"Within 48h; mucosal edema, hemorrhage, ulceration in segmental pattern"),
     "Supportive Care":tc(30,"Bowel rest, IV fluids, serial abdominal exams; 80% resolve without surgery"),
     "Surgical Consult":tc(120,"For peritonitis, pneumatosis, portal venous gas, or perforation")},{})

NEW["Acute Liver Failure"]=dx("Gastrointestinal","GI/Hepatic",v(105,90,55,22,98.6,95),
    STD,{"heart_rate":10,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "Coagulopathy (INR ≥1.5) + encephalopathy in patient WITHOUT pre-existing liver disease; jaundice, RUQ tenderness, cerebral edema, signs of coagulopathy, asterixis early",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"pt_inr":lab(1.5,6.0,"INR","elevated"),"tbili":lab(5.0,30.0,"mg/dL","elevated"),
     "ast":lab(200,10000,"U/L","elevated"),"alt":lab(200,10000,"U/L","elevated"),
     "ammonia":lab(50,300,"mcg/dL","elevated"),"glu":lab(30,100,"mg/dL","decreased"),
     "lactate":lab(3.0,10.0,"mmol/L","elevated"),"cr":lab(1.0,4.0,"mg/dL","elevated"),
     "ph":lab(7.15,7.35,"","decreased")},
    ["IV Access","Continuous Monitoring","ICU"],
    {"N-Acetylcysteine":tc(60,"21-hour IV protocol; improves survival even in non-acetaminophen ALF"),
     "Intracranial Pressure Monitoring":tc(120,"For grade 3-4 encephalopathy; target ICP <20"),
     "Liver Transplant Evaluation":tc(120,"Apply King's College Criteria; list if criteria met"),
     "Glucose Monitoring":tc(60,"Q1h; D10 drip for hypoglycemia; impaired gluconeogenesis"),
     "Lactulose":tc(60,"For encephalopathy; although controversial in ALF due to ileus risk")},
    {"Acetaminophen OD":{"alt":{"min":3000,"max":10000},"pt_inr":{"min":2.0,"max":8.0}}})

NEW["Hepatic Encephalopathy"]=dx("Gastrointestinal","GI/Hepatic",v(90,108,65,18,98.6,96),
    STD,{"heart_rate":8,"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Altered mental status in cirrhotic patient, asterixis (flapping tremor), fetor hepaticus, constructional apraxia, day-night reversal; precipitants: GI bleed, infection, constipation, meds",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"ammonia":lab(50,200,"mcg/dL","elevated"),"cr":lab(0.8,3.0,"mg/dL","variable"),
     "na":lab(125,140,"mEq/L","variable"),"glu":lab(60,200,"mg/dL","variable"),
     "pt_inr":lab(1.3,3.0,"INR","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"Lactulose":tc(60,"30mL PO/NG q2h titrate to 3-4 stools/day; mainstay of treatment"),
     "Rifaximin":tc(240,"550mg BID; adjunct to lactulose for relapse prevention"),
     "Identify Precipitant":tc(120,"GI bleed, infection/SBP, electrolyte abnormalities, constipation, medications, non-compliance"),
     "Infection Workup":tc(120,"SBP can precipitate HE; diagnostic paracentesis if ascites present")},
    {"Cirrhosis":{"pt_inr":{"min":1.5,"max":3.5}}})

NEW["Spontaneous Bacterial Peritonitis"]=dx("Gastrointestinal","GI/Hepatic",v(105,95,58,20,101.5,96),
    STD,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":2},
    "Fever, abdominal pain, worsening ascites, encephalopathy in cirrhotic patient; may be subtle – always suspect in decompensating cirrhotic",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"ascitic_pmn":lab(250,5000,"cells/uL","elevated"),"wbc":lab(10,22,"K/uL","elevated"),
     "cr":lab(1.0,3.0,"mg/dL","elevated"),"tbili":lab(3.0,15.0,"mg/dL","elevated"),
     "pt_inr":lab(1.5,3.5,"INR","elevated"),"lactate":lab(2.0,5.0,"mmol/L","elevated")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"Diagnostic Paracentesis":tc(120,"PMN >250/uL is diagnostic; do NOT delay for coagulopathy"),
     "Cefotaxime":tc(120,"2g IV q8h x 5 days; or ceftriaxone 2g IV q24h"),
     "IV Albumin":tc(360,"1.5g/kg day 1 + 1g/kg day 3; reduces mortality and hepatorenal syndrome"),
     "Ascitic Fluid Culture":tc(120,"Inoculate blood culture bottles at bedside; improves yield")},
    {"Cirrhosis":{"risk":"required underlying condition"}})

NEW["Esophageal Perforation (Boerhaave)"]=dx("Gastrointestinal","GI",v(120,90,55,24,100.5,93),
    STD,{"heart_rate":12,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":4},
    "Mackler triad: vomiting then chest pain then subcutaneous emphysema; left-sided chest pain after forceful vomiting/retching; Hamman crunch on auscultation; mediastinitis",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"wbc":lab(12,25,"K/uL","elevated"),"lactate":lab(2.0,6.0,"mmol/L","elevated"),
     "amylase":lab(100,500,"U/L","elevated"),"cr":lab(0.6,2.0,"mg/dL","variable")},
    ["IV Access","Antibiotics","Fluid Resuscitation","Continuous Monitoring"],
    {"CT Chest with Oral Contrast":tc(60,"Pneumomediastinum, pleural effusion, esophageal leak, mediastinal air"),
     "Thoracic Surgery Consult":tc(60,"Emergent operative repair within 24h dramatically improves survival"),
     "Broad-Spectrum Antibiotics":tc(30,"Cover oral flora and gram-negatives; piperacillin-tazobactam + fluconazole"),
     "NPO":tc(1,"Absolute nothing by mouth; NG tube for decompression")},{})

NEW["Mallory-Weiss Tear"]=dx("Gastrointestinal","GI",v(90,120,75,16,98.6,98),
    STD,{"heart_rate":8,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Hematemesis after forceful vomiting/retching; partial-thickness mucosal tear at GEJ; typically self-limited; alcohol use, bulimia, severe retching as risk factors",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"hgb":lab(10,15,"g/dL","decreased"),"bun":lab(10,25,"mg/dL","variable"),
     "pt_inr":lab(0.9,1.3,"INR","normal")},
    ["IV Access","Continuous Monitoring"],
    {"EGD":tc(720,"If continued bleeding; epinephrine injection or endoclip; 90% stop spontaneously"),
     "IV PPI":tc(60,"Pantoprazole 40mg IV BID"),
     "Observation":tc(0,"Most resolve without intervention; monitor for rebleed")},{})

NEW["Acute Gastritis/Gastropathy"]=dx("Gastrointestinal","GI",v(85,128,78,16,98.6,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Epigastric pain, nausea, early satiety; may have hematemesis if erosive; NSAID, alcohol, stress-related mucosal disease in ICU patients",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"hgb":lab(10,16,"g/dL","variable"),"h_pylori":lab(1,1,"","variable"),"cr":lab(0.6,1.2,"mg/dL","normal")},
    ["IV Access","Continuous Monitoring"],
    {"PPI":tc(120,"Omeprazole 40mg IV BID; acid suppression first-line"),
     "H. pylori Testing":tc(0,"Stool antigen or breath test; treat if positive"),
     "Remove Offending Agent":tc(30,"Stop NSAIDs, alcohol, aspirin if possible")},{})

NEW["Peptic Ulcer Disease - Perforation"]=dx("Gastrointestinal","GI",v(115,95,58,22,99.5,95),
    STD,{"heart_rate":12,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "Sudden severe epigastric pain ('knife-stab'), rigid board-like abdomen, rebound tenderness, absent bowel sounds, free air under diaphragm on upright CXR",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"wbc":lab(12,25,"K/uL","elevated"),"lactate":lab(2.0,6.0,"mmol/L","elevated"),
     "amylase":lab(50,300,"U/L","variable"),"cr":lab(0.6,2.0,"mg/dL","variable")},
    ["IV Access","Antibiotics","Fluid Resuscitation","Continuous Monitoring"],
    {"Upright CXR or CT":tc(30,"Free air (pneumoperitoneum) confirms perforation"),
     "Surgical Consult":tc(60,"Emergent laparotomy / laparoscopic repair; Graham patch"),
     "IV Antibiotics":tc(30,"Cover gram-negatives and anaerobes: piperacillin-tazobactam"),
     "NPO + NG Tube":tc(15,"Decompression and prevent further contamination"),
     "IV PPI":tc(30,"High-dose pantoprazole 80mg bolus")},{})

NEW["Acute Diverticulitis - Uncomplicated"]=dx("Gastrointestinal","GI",v(88,130,80,16,100.5,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "LLQ pain (rarely right-sided), fever, localized LLQ tenderness with guarding, elevated WBC; left-sided in Western nations, right-sided in Asians",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(11,18,"K/uL","elevated"),"crp":lab(2.0,10.0,"mg/dL","elevated"),
     "cr":lab(0.6,1.4,"mg/dL","normal"),"ua":lab(0,5,"wbc/HPF","normal")},
    ["IV Access","Continuous Monitoring"],
    {"CT Abdomen/Pelvis":tc(120,"Pericolonic fat stranding, colonic wall thickening, diverticula; Hinchey classification"),
     "IV Antibiotics":tc(120,"Ciprofloxacin + metronidazole or piperacillin-tazobactam"),
     "Bowel Rest":tc(0,"Clear liquids advancing as tolerated; some evidence supports diet with uncomplicated"),
     "Colonoscopy":tc(0,"6-8 weeks after resolution to rule out underlying malignancy")},{})

NEW["Acute Diverticulitis - Complicated (Abscess/Perforation)"]=dx("Gastrointestinal","GI",v(110,98,60,22,102.5,95),
    STD,{"heart_rate":10,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "Severe LLQ pain, diffuse peritonitis if free perforation, palpable mass if abscess, septic appearance, high fever; Hinchey III-IV",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"wbc":lab(15,28,"K/uL","elevated"),"lactate":lab(2.0,6.0,"mmol/L","elevated"),
     "crp":lab(10,30,"mg/dL","elevated"),"cr":lab(0.8,2.5,"mg/dL","variable")},
    ["IV Access","Antibiotics","Fluid Resuscitation","Continuous Monitoring"],
    {"CT Abdomen/Pelvis":tc(60,"Abscess, free air, free fluid; Hinchey staging"),
     "IV Antibiotics":tc(30,"Broad-spectrum: piperacillin-tazobactam or meropenem"),
     "IR Drainage":tc(240,"Percutaneous for abscess >3cm; bridge to elective surgery"),
     "Surgical Consult":tc(120,"Emergent Hartmann procedure for Hinchey III/IV (free perforation)")},{})

NEW["Toxic Megacolon"]=dx("Gastrointestinal","GI",v(115,88,55,22,102.5,94),
    STD,{"heart_rate":12,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "Severe abdominal distension and pain, fever, tachycardia, bloody diarrhea, altered mental status in IBD flare or C. diff; transverse colon dilation >6cm on XR",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"wbc":lab(15,30,"K/uL","elevated"),"hgb":lab(8,12,"g/dL","decreased"),"k":lab(2.5,4.0,"mEq/L","decreased"),
     "alb":lab(1.5,3.0,"g/dL","decreased"),"lactate":lab(2.0,6.0,"mmol/L","elevated"),
     "c_diff_toxin":lab(1,1,"positive","elevated")},
    ["IV Access","Antibiotics","Fluid Resuscitation","Continuous Monitoring"],
    {"Abdominal XR":tc(30,"Transverse colon >6cm; haustral loss; serial XR q12h"),
     "IV Corticosteroids":tc(60,"Methylprednisolone 60mg/day if IBD-related; contraindicated in C. diff"),
     "IV Vancomycin + Metronidazole":tc(30,"For C. diff toxic megacolon"),
     "Surgical Consult":tc(120,"Subtotal colectomy if no improvement in 24-72h, perforation, or hemorrhage"),
     "NPO + NG Tube":tc(30,"Bowel rest and decompression")},{})

NEW["C. difficile Colitis - Fulminant"]=dx("Gastrointestinal","GI/Infectious",v(110,92,58,20,102.0,95),
    STD,{"heart_rate":10,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "Profuse watery diarrhea (may paradoxically decrease with ileus), abdominal distension, severe tenderness, WBC >15 or rising Cr; recent antibiotics/hospitalization",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"wbc":lab(15,40,"K/uL","elevated"),"cr":lab(1.5,4.0,"mg/dL","elevated"),
     "lactate":lab(2.0,6.0,"mmol/L","elevated"),"alb":lab(1.5,3.0,"g/dL","decreased"),
     "c_diff_toxin":lab(1,1,"positive","elevated")},
    ["IV Access","Fluid Resuscitation","Continuous Monitoring"],
    {"PO Vancomycin":tc(30,"500mg PO/NG q6h; first-line for fulminant C. diff"),
     "IV Metronidazole":tc(30,"500mg IV q8h; adjunctive for fulminant disease"),
     "Vancomycin Retention Enema":tc(120,"500mg in 100mL NS PR q6h if ileus (poor oral delivery to colon)"),
     "Surgical Consult":tc(240,"Subtotal colectomy for refractory disease, toxic megacolon, perforation, or WBC >20 + lactate >5"),
     "CT Abdomen":tc(60,"Colonic wall thickening, pericolonic stranding, ascites; evaluate for megacolon")},{})

NEW["Acute Hepatitis - Viral"]=dx("Gastrointestinal","GI/Hepatic",v(85,125,78,16,99.5,97),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Jaundice, RUQ pain, nausea/anorexia, malaise, dark urine, clay-colored stools, hepatomegaly, fever in prodrome; HAV fecal-oral, HBV/HCV blood-borne",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"ast":lab(200,3000,"U/L","elevated"),"alt":lab(300,5000,"U/L","elevated"),
     "tbili":lab(3.0,20.0,"mg/dL","elevated"),"alk_phos":lab(100,300,"U/L","elevated"),
     "pt_inr":lab(0.9,1.5,"INR","variable"),"alb":lab(3.0,4.5,"g/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Hepatitis Panel":tc(120,"HAV IgM, HBsAg, HBcAb IgM, HCV Ab + RNA"),
     "PT/INR Monitoring":tc(120,"Rising INR suggests impending liver failure → transfer to transplant center"),
     "Supportive Care":tc(0,"Hydration, antiemetics, avoid hepatotoxins"),
     "Acetaminophen Level":tc(120,"Rule out concomitant acetaminophen toxicity")},{})

NEW["Achalasia"]=dx("Gastrointestinal","GI",v(82,130,80,16,98.6,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Progressive dysphagia to BOTH solids AND liquids (mechanical is solids first), regurgitation of undigested food, chest pain, weight loss, aspiration pneumonia risk",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(5,11,"K/uL","normal"),"cr":lab(0.6,1.2,"mg/dL","normal"),"alb":lab(3.0,4.5,"g/dL","variable")},
    ["Continuous Monitoring"],
    {"Barium Swallow":tc(0,"Bird's beak narrowing at GEJ, dilated esophageal body"),
     "EGD":tc(0,"Rule out pseudoachalasia (cancer at GEJ)"),
     "Esophageal Manometry":tc(0,"Gold standard; aperistalsis + failure of LES relaxation"),
     "Heller Myotomy or POEM":tc(0,"Definitive surgical treatment; Botox injection as bridge")},{})

NEW["Ogilvie Syndrome (Acute Colonic Pseudo-obstruction)"]=dx("Gastrointestinal","GI",v(90,120,75,18,98.6,97),
    STD,{"heart_rate":8,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Massive colonic distension WITHOUT mechanical obstruction; post-operative, critically ill, or elderly patients; cecal dilation >12cm = perforation risk",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"wbc":lab(8,15,"K/uL","variable"),"k":lab(2.8,4.5,"mEq/L","decreased"),
     "mg":lab(1.2,2.0,"mg/dL","variable"),"ca":lab(7.5,10.0,"mg/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Abdominal XR/CT":tc(60,"Diffuse colonic dilation; CT to exclude mechanical obstruction"),
     "Neostigmine":tc(240,"2mg IV over 3-5min with cardiac monitoring and atropine at bedside; 90% response rate"),
     "Colonoscopic Decompression":tc(0,"If neostigmine fails; decompression tube placement"),
     "Correct Electrolytes":tc(60,"Hypokalemia, hypomagnesemia, hypocalcemia worsen ileus"),
     "Surgical Consult":tc(120,"Cecostomy tube or subtotal colectomy if refractory/perforated")},{})

NEW["Hepatorenal Syndrome"]=dx("Gastrointestinal","GI/Renal",v(105,80,50,20,98.6,95),
    STD,{"heart_rate":10,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":3},
    "Progressive oliguria in decompensating cirrhotic with refractory ascites; diagnosis of exclusion; bland urine sediment, UNa <10, normal kidney on US",
    {"o2_saturation_below":90,"systolic_bp_below":65},
    {"cr":lab(1.5,5.0,"mg/dL","elevated"),"na":lab(120,135,"mEq/L","decreased"),
     "tbili":lab(5.0,25.0,"mg/dL","elevated"),"pt_inr":lab(1.5,4.0,"INR","elevated"),
     "una":lab(1,10,"mEq/L","decreased"),"alb":lab(1.5,2.5,"g/dL","decreased")},
    ["IV Access","Continuous Monitoring","Foley Catheter"],
    {"IV Albumin":tc(120,"1g/kg/day (max 100g) x 2 days; volume expansion test"),
     "Octreotide + Midodrine":tc(240,"Splanchnic vasoconstriction + increase MAP; or norepinephrine drip in ICU"),
     "Terlipressin":tc(240,"Vasopressin analog; approved for HRS in many countries; improves renal function"),
     "Liver Transplant Evaluation":tc(0,"Definitive treatment; prognoses very poor without transplant"),
     "Stop Diuretics":tc(30,"Discontinue lactulose? Discontinue all diuretics")},
    {"Cirrhosis":{"risk":"required underlying condition"}})

NEW["GI Foreign Body Ingestion"]=dx("Gastrointestinal","GI",v(88,130,80,18,98.6,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":2},
    "Dysphagia, drooling, chest/abdominal pain, refusal to eat (pediatric); button battery and magnet ingestion are emergencies; sharp objects risk perforation",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(6,12,"K/uL","normal"),"cr":lab(0.6,1.4,"mg/dL","normal")},
    ["IV Access","Continuous Monitoring"],
    {"XR Neck/Chest/Abdomen":tc(60,"Identify location, type, number of objects"),
     "Emergent EGD":tc(120,"Required for: button battery in esophagus, sharp objects, food impaction >24h, magnets"),
     "Button Battery Protocol":tc(1,"Esophageal button battery = immediate removal; can cause perforation/fistula in 2h; honey q10min while awaiting removal"),
     "Observation":tc(0,"Blunt objects past pylorus → serial XR; most pass spontaneously in 4-6 days")},{})

NEW["Acute Gastroenteritis - Severe Dehydration"]=dx("Gastrointestinal","GI/Infectious",v(110,90,55,20,100.5,97),
    STD,{"heart_rate":10,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":2},
    "Profuse watery diarrhea and/or vomiting, dry mucous membranes, decreased skin turgor, orthostasis, sunken eyes, delayed capillary refill, confusion in severe cases",
    {"o2_saturation_below":92,"systolic_bp_below":75},
    {"bun":lab(25,60,"mg/dL","elevated"),"cr":lab(1.2,3.0,"mg/dL","elevated"),
     "na":lab(130,155,"mEq/L","variable"),"k":lab(2.5,4.5,"mEq/L","decreased"),
     "hco3":lab(15,24,"mEq/L","decreased"),"wbc":lab(6,15,"K/uL","variable"),
     "lactate":lab(2.0,5.0,"mmol/L","elevated")},
    ["IV Access","Fluid Resuscitation","Continuous Monitoring"],
    {"IV Fluid Resuscitation":tc(30,"NS or LR bolus 20mL/kg; repeat as needed for perfusion"),
     "Electrolyte Correction":tc(60,"Replace K, Mg, correct metabolic acidosis"),
     "Stool Studies":tc(120,"Culture, C. diff, O&P, viral panel if immunocompromised"),
     "Antiemetics":tc(30,"Ondansetron 4mg IV to enable oral rehydration")},{})

with open(OUTPUT) as f:
    data = json.load(f)
added = 0
for name, entry in NEW.items():
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
print(f"Added {added} GI diagnoses. Total: {len(data['diagnoses'])}")
for c in sorted(cats):
    print(f"  {c}: {len(cats[c])}")

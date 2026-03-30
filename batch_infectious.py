#!/usr/bin/env python3
"""Batch 5: Infectious disease diagnoses expansion."""
import json
from pathlib import Path

OUTPUT = Path(__file__).parent / "diagnosis_data.json"

def dx(cat,organ,vitals,modifiers,weights,pe,thresholds,labs,interventions,tc_actions,comorbidity=None):
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

NEW["Sepsis - qSOFA Positive"]=dx("Infectious","Infectious/Multi-System",v(112,88,55,24,102.5,94),
    STD,{"heart_rate":12,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":3},
    "Altered mental status, tachypnea >=22, SBP <=100; suspected infection; may have localizing signs of source (pneumonia, UTI, cellulitis, intra-abdominal)",
    {"o2_saturation_below":88,"systolic_bp_below":65},
    {"wbc":lab(2,25,"K/uL","variable"),"lactate":lab(2.0,8.0,"mmol/L","elevated"),"cr":lab(1.2,4.0,"mg/dL","elevated"),
     "plt":lab(50,250,"K/uL","decreased"),"tbili":lab(1.0,5.0,"mg/dL","elevated"),
     "procalcitonin":lab(0.5,50.0,"ng/mL","elevated"),"inr":lab(1.2,2.5,"INR","elevated")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Antibiotics","Continuous Monitoring"],
    {"Blood Cultures":tc(30,"Before antibiotics; 2 sets from different sites"),
     "Broad-Spectrum Antibiotics":tc(60,"Within 1h of recognition per Surviving Sepsis Campaign; each hour delay increases mortality 7.6%"),
     "30mL/kg Crystalloid":tc(180,"Within 3h for hypotension or lactate ≥4"),
     "Lactate":tc(60,"If >2 repeat in 2-4h to guide resuscitation; clearance >10%/hr is goal"),
     "Source Control":tc(360,"Identify and drain/debride source within 6-12h")},{})

NEW["Septic Shock"]=dx("Infectious","Infectious/Multi-System",v(125,72,42,28,103.5,91),
    STD,{"heart_rate":15,"systolic_bp":25,"diastolic_bp":18,"o2_saturation":5},
    "Sepsis + vasopressor requirement to maintain MAP >=65 AND lactate >2 despite adequate fluid resuscitation; warm shock (early: warm, flushed) → cold shock (late: cool, mottled)",
    {"o2_saturation_below":85,"systolic_bp_below":60},
    {"lactate":lab(4.0,12.0,"mmol/L","elevated"),"wbc":lab(1,30,"K/uL","variable"),
     "plt":lab(20,100,"K/uL","decreased"),"cr":lab(2.0,6.0,"mg/dL","elevated"),
     "tbili":lab(2.0,10.0,"mg/dL","elevated"),"procalcitonin":lab(2.0,100.0,"ng/mL","elevated"),
     "fibrinogen":lab(100,300,"mg/dL","decreased"),"d_dimer":lab(1000,20000,"ng/mL","elevated")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Vasopressors","Antibiotics","Continuous Monitoring","Arterial Line"],
    {"Broad-Spectrum Antibiotics":tc(60,"WITHIN 1 HOUR; empiric based on suspected source"),
     "Norepinephrine":tc(60,"First-line vasopressor; start if MAP <65 despite fluids; target MAP ≥65"),
     "Vasopressin":tc(120,"Add at 0.03 U/min as second vasopressor; norepi-sparing"),
     "Stress-Dose Steroids":tc(240,"Hydrocortisone 200mg/day if vasopressor-refractory; ADRENAL/APROCCHSS trials"),
     "Central Venous Access":tc(120,"CVC for vasopressor administration; ScvO2 monitoring")},
    {"Immunocompromised":{"wbc":{"min":0.1,"max":5}}})

NEW["Necrotizing Fasciitis"]=dx("Infectious","Infectious/Surgical",v(120,85,52,24,103.0,94),
    STD,{"heart_rate":12,"systolic_bp":20,"diastolic_bp":15,"o2_saturation":3},
    "Pain OUT OF PROPORTION to exam (early), rapidly spreading erythema, skin necrosis, crepitus (gas gangrene), hemorrhagic bullae, fever, LRINEC score ≥6",
    {"o2_saturation_below":88,"systolic_bp_below":65},
    {"wbc":lab(15,35,"K/uL","elevated"),"crp":lab(15,40,"mg/dL","elevated"),"cr":lab(1.5,4.0,"mg/dL","elevated"),
     "na":lab(125,138,"mEq/L","decreased"),"glu":lab(150,350,"mg/dL","elevated"),
     "ck":lab(500,20000,"U/L","elevated"),"lactate":lab(3.0,8.0,"mmol/L","elevated"),
     "hgb":lab(8,13,"g/dL","decreased")},
    ["IV Access x2 Large Bore","Antibiotics","Fluid Resuscitation","Continuous Monitoring"],
    {"Surgical Consult":tc(60,"EMERGENT wide debridement; every hour of delay increases mortality"),
     "IV Antibiotics":tc(30,"Vancomycin + piperacillin-tazobactam + clindamycin (toxin suppression)"),
     "CT/MRI":tc(60,"Gas tracking along fascial planes; but NEVER delay OR for imaging"),
     "Serial Debridement":tc(0,"Return to OR in 24-48h for re-exploration; average 3-4 debridements"),
     "ICU Admission":tc(60,"High mortality; often requires vasopressors, ventilation")},
    {"Diabetes":{"glu":{"min":200,"max":500}}})

NEW["Endocarditis - Acute"]=dx("Infectious","Infectious/Cardiovascular",v(110,100,62,20,103.0,95),
    STD,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":3},
    "Fever, new or changing murmur, Janeway lesions (painless palms/soles), Osler nodes (painful fingertips), Roth spots (retinal hemorrhages), splinter hemorrhages, splenomegaly",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"wbc":lab(12,25,"K/uL","elevated"),"esr":lab(40,100,"mm/hr","elevated"),"crp":lab(5,25,"mg/dL","elevated"),
     "blood_cx":lab(1,1,"positive","elevated"),"cr":lab(0.8,2.5,"mg/dL","variable"),
     "hgb":lab(8,12,"g/dL","decreased"),"rf":lab(1,1,"positive","elevated")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"Blood Cultures":tc(60,"3 sets from different sites before antibiotics; continuous bacteremia hallmark"),
     "TTE/TEE":tc(240,"TEE preferred (>90% sensitivity for vegetations); TTE first if available immediately"),
     "IV Antibiotics":tc(60,"Empiric: vancomycin + cefepime; MSSA: nafcillin; 4-6 week course per AHA"),
     "Surgical Consult":tc(240,"Urgent for HF from valve destruction, uncontrolled infection, large vegetation (>10mm), embolic events")},
    {"IVDU":{"risk":"right-sided; Staph aureus; tricuspid valve"},"Prosthetic Valve":{"risk":"higher mortality; broader empiric coverage"}})

NEW["Endocarditis - Subacute"]=dx("Infectious","Infectious/Cardiovascular",v(90,118,72,18,100.5,97),
    STD,{"heart_rate":8,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Insidious fever, weight loss, night sweats, new murmur; peripheral stigmata more common than acute; Viridans strep typical; preexisting valve disease",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(8,15,"K/uL","variable"),"esr":lab(30,80,"mm/hr","elevated"),"crp":lab(2,15,"mg/dL","elevated"),
     "blood_cx":lab(1,1,"positive","elevated"),"hgb":lab(9,12,"g/dL","decreased"),
     "rf":lab(1,1,"positive","elevated"),"cr":lab(0.8,2.0,"mg/dL","variable")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"Blood Cultures x3":tc(120,"3 sets from different sites over 24h before antibiotics if stable"),
     "TTE then TEE":tc(240,"Modified Duke criteria; vegetations, abscess, new regurgitation"),
     "IV Antibiotics":tc(240,"May wait 24h for culture results if clinically stable; targeted therapy preferred"),
     "Embolic Workup":tc(0,"Brain MRI, abdominal CT for splenic abscess, retinal exam")},{})

NEW["Pyelonephritis - Complicated"]=dx("Infectious","Infectious/Renal",v(108,98,60,22,103.5,96),
    STD,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":2},
    "Fever, flank pain, CVA tenderness, rigors; complicated: obstruction, abscess, pregnancy, male, immunocompromised, catheter-associated; may progress to urosepsis",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"wbc":lab(15,28,"K/uL","elevated"),"ua_wbc":lab(10,100,"/HPF","elevated"),"ua_nitrite":lab(1,1,"positive","elevated"),
     "cr":lab(1.0,3.0,"mg/dL","elevated"),"lactate":lab(1.5,4.0,"mmol/L","elevated"),
     "blood_cx":lab(1,1,"positive","elevated"),"procalcitonin":lab(0.5,10.0,"ng/mL","elevated")},
    ["IV Access","Antibiotics","Fluid Resuscitation","Continuous Monitoring"],
    {"Urine Culture":tc(60,"Before antibiotics; guides de-escalation"),
     "IV Antibiotics":tc(60,"Ceftriaxone 2g IV or fluoroquinolone; add vancomycin if MRSA risk"),
     "Renal Ultrasound/CT":tc(120,"Evaluate for hydronephrosis, perinephric abscess, obstructing stone"),
     "Blood Cultures":tc(60,"If septic; E. coli most common organism"),
     "Urology Consult":tc(240,"If obstructing stone with infection → emergent decompression (stent or nephrostomy)")},
    {"Diabetes":{"glu":{"min":150,"max":350},"cr":{"min":1.0,"max":3.0}}})

NEW["Peritonsillar Abscess"]=dx("Infectious","Infectious/ENT",v(100,135,82,18,101.5,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Severe sore throat (usually unilateral), trismus, hot potato voice, uvular deviation, peritonsillar bulging, drooling, fever; most common deep space neck infection",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(12,22,"K/uL","elevated"),"crp":lab(2,15,"mg/dL","elevated")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"Needle Aspiration or I&D":tc(120,"Needle aspiration first; I&D if fails; both diagnostic and therapeutic"),
     "IV Antibiotics":tc(120,"Ampicillin-sulbactam or clindamycin; cover GAS and oropharyngeal anaerobes"),
     "IV Dexamethasone":tc(120,"Single dose reduces pain and trismus; speeds recovery"),
     "Airway Assessment":tc(15,"Rare airway compromise but must assess; have difficult airway equipment ready")},{})

NEW["Ludwig Angina"]=dx("Infectious","Infectious/ENT",v(110,125,78,22,102.5,94),
    STD,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":4},
    "Submandibular space infection; floor of mouth elevation, tongue protrusion, woody induration of submandibular area, drooling, stridor; AIRWAY EMERGENCY; dental source typical",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"wbc":lab(15,28,"K/uL","elevated"),"crp":lab(5,25,"mg/dL","elevated"),"lactate":lab(1.5,4.0,"mmol/L","elevated")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"Airway Management":tc(15,"PRIMARY CONCERN; fiberoptic intubation or surgical airway may be needed; DO NOT attempt blind intubation"),
     "CT Neck with Contrast":tc(60,"Evaluate extent, drainable collection, mediastinal extension"),
     "IV Antibiotics":tc(30,"Ampicillin-sulbactam + metronidazole; or penicillin + metronidazole + ceftriaxone"),
     "Surgical Consult":tc(120,"Surgical drainage if abscess; may need tooth extraction"),
     "Dexamethasone":tc(60,"IV steroids to reduce edema and improve airway")},{})

NEW["Retropharyngeal Abscess"]=dx("Infectious","Infectious/ENT",v(115,110,68,24,103.0,94),
    STD,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":4},
    "Severe neck pain/stiffness (mimics meningitis), dysphagia, drooling, muffled voice, neck hyperextension/torticollis; children <5y most common; adult variant from spinal procedures or foreign body",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"wbc":lab(15,28,"K/uL","elevated"),"crp":lab(5,20,"mg/dL","elevated")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"Lateral Neck XR":tc(60,"Prevertebral soft tissue widening >7mm at C2 or >14mm at C6 (children)"),
     "CT Neck with Contrast":tc(60,"Ring-enhancing collection in retropharyngeal space; evaluate mediastinal extension"),
     "Airway Management":tc(15,"Highest priority; stridor or respiratory distress → secure airway"),
     "Surgical Drainage":tc(240,"Transoral or external approach depending on extent; ENT consult"),
     "IV Antibiotics":tc(30,"Ampicillin-sulbactam or clindamycin; cover GAS, oral anaerobes, Staph")},{})

NEW["Epiglottitis - Adult"]=dx("Infectious","Infectious/ENT",v(105,130,80,22,102.0,95),
    STD,{"heart_rate":10,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":3},
    "Severe sore throat, dysphagia, drooling, muffled hot-potato voice, sitting upright leaning forward (tripod/sniffing position), stridor; BROADER differential in adults than children",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"wbc":lab(12,22,"K/uL","elevated"),"crp":lab(3,15,"mg/dL","elevated"),
     "blood_cx":lab(1,1,"positive","variable")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"Airway Assessment":tc(5,"DO NOT lay patient flat; prepare for difficult airway; ENT at bedside"),
     "Lateral Neck XR":tc(30,"Thumbprint sign (swollen epiglottis); but DO NOT delay management for imaging"),
     "Nasolaryngoscopy":tc(30,"Direct visualization; cherry-red swollen epiglottis; in controlled environment"),
     "IV Antibiotics":tc(30,"Ceftriaxone 2g + dexamethasone; cover H. flu, Strep, Staph"),
     "Intubation Readiness":tc(5,"Have surgical airway tray ready; awake fiberoptic preferred if needed")},{})

NEW["Cellulitis - Severe / Purulent"]=dx("Infectious","Infectious/Skin",v(95,125,78,18,101.5,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Expanding erythema with warmth, tenderness, induration; purulent = abscess/MRSA likely; red streaking (lymphangitis), regional lymphadenopathy; demarcate borders with marking pen",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(11,20,"K/uL","elevated"),"crp":lab(2,15,"mg/dL","elevated"),"cr":lab(0.6,1.5,"mg/dL","normal"),
     "blood_cx":lab(0,1,"positive","variable"),"ck":lab(50,500,"U/L","variable")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"I&D if Abscess":tc(120,"Incision and drainage is MOST IMPORTANT intervention for purulent cellulitis"),
     "IV Antibiotics":tc(120,"Purulent: vancomycin or daptomycin (MRSA coverage); non-purulent: cefazolin or ceftriaxone (beta-hemolytic strep)"),
     "Mark Borders":tc(30,"Draw on skin with marker to track progression vs regression"),
     "Blood Cultures":tc(120,"If systemic signs (fever, rigors, tachycardia)"),
     "Ultrasound":tc(60,"Bedside US detects abscess with 90% sensitivity; guides I&D")},{})

NEW["Osteomyelitis - Acute"]=dx("Infectious","Infectious/MSK",v(95,125,78,18,101.0,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Localized bone pain, fever, swelling, erythema over bone; pediatric: long bone metaphysis (hematogenous); adult: vertebral body or contiguous spread from wound/surgery; diabetic foot",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(11,20,"K/uL","elevated"),"esr":lab(40,100,"mm/hr","elevated"),
     "crp":lab(3,20,"mg/dL","elevated"),"blood_cx":lab(0,1,"positive","variable")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"MRI":tc(240,"Most sensitive (90%) and specific (82%) imaging modality; marrow edema, periosteal reaction"),
     "Blood Cultures":tc(60,"Positive in 50% of hematogenous osteomyelitis; send before antibiotics"),
     "Bone Biopsy/Culture":tc(0,"Gold standard for organism identification; guides targeted therapy"),
     "IV Antibiotics":tc(120,"Empiric: vancomycin (MRSA) + ceftriaxone; total 4-6 weeks IV therapy"),
     "Surgical Consult":tc(0,"Debridement if abscess, sequestrum, or failed medical therapy")},
    {"Diabetes":{"risk":"diabetic foot osteomyelitis; probe-to-bone test 66% PPV"}})

NEW["Septic Arthritis"]=dx("Infectious","Infectious/MSK",v(100,120,75,18,102.0,97),
    STD,{"heart_rate":8,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Hot, swollen, erythematous joint with SEVERE pain on passive ROM; monoarticular (usually knee); inability to bear weight; Staph aureus most common; gonococcal in young sexually active",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(10,18,"K/uL","elevated"),"esr":lab(30,80,"mm/hr","elevated"),"crp":lab(3,15,"mg/dL","elevated"),
     "synovial_wbc":lab(50000,200000,"cells/uL","elevated"),"uric_acid":lab(3.0,8.0,"mg/dL","normal")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"Arthrocentesis":tc(120,"MANDATORY; synovial WBC >50K highly suggestive; gram stain, culture, crystal analysis to exclude gout"),
     "IV Antibiotics":tc(120,"Vancomycin (MRSA coverage) + ceftriaxone; narrow when cultures return"),
     "Orthopedic Consult":tc(240,"Surgical drainage/lavage especially for hip or prosthetic joint; serial aspirations for other joints"),
     "Blood Cultures":tc(60,"Often positive; particularly in non-gonococcal septic arthritis")},{})

NEW["Tetanus"]=dx("Infectious","Infectious/Neurological",v(110,160,95,22,101.0,95),
    {**STD,"systolic_bp":"multiply","diastolic_bp":"multiply"},{"heart_rate":10,"systolic_bp":10,"diastolic_bp":8,"o2_saturation":3},
    "Trismus (lockjaw), risus sardonicus (sardonic smile), opisthotonus, generalized muscle rigidity and spasms, autonomic instability; wound may be minor/unrecognized; unvaccinated",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"ck":lab(200,10000,"U/L","elevated"),"wbc":lab(8,15,"K/uL","variable"),
     "cr":lab(0.8,3.0,"mg/dL","variable"),"k":lab(4.0,6.5,"mEq/L","elevated")},
    ["IV Access","Continuous Monitoring","ICU"],
    {"Tetanus Immune Globulin":tc(60,"TIG 500 IU IM; neutralizes unbound toxin"),
     "Wound Debridement":tc(120,"Remove necrotic tissue; reduce toxin production"),
     "Metronidazole":tc(60,"500mg IV q6h x 10 days; kills C. tetani (alternative: penicillin G)"),
     "Benzodiazepines":tc(30,"Diazepam 10mg IV q1h PRN for spasm control; may need continuous infusion"),
     "Intubation Prep":tc(30,"Laryngospasm/respiratory failure may require RSI; avoid succinylcholine")},{})

NEW["Rabies - Symptomatic"]=dx("Infectious","Infectious/Neurological",v(115,140,85,22,101.5,95),
    {**STD,"systolic_bp":"multiply"},{"heart_rate":10,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":3},
    "Prodrome: paresthesias at bite site, fever, malaise → Furious (80%): hydrophobia, aerophobia, agitation, hallucinations, autonomic instability → Paralytic (20%): ascending paralysis like GBS",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"wbc":lab(8,15,"K/uL","variable"),"csf_wbc":lab(5,50,"cells/uL","elevated"),
     "csf_protein":lab(50,200,"mg/dL","elevated")},
    ["IV Access","Continuous Monitoring","ICU"],
    {"Milwaukee Protocol":tc(0,"Therapeutic coma attempt; <20% survival even with treatment; nearly 100% fatal once symptomatic"),
     "ICU Supportive Care":tc(60,"Mechanical ventilation, sedation, autonomic stabilization"),
     "Contact Precautions":tc(1,"Patient saliva is infectious"),
     "Post-Exposure Prophylaxis for Contacts":tc(120,"Any healthcare worker with mucous membrane/wound exposure to saliva")},{})

NEW["Malaria - Severe (P. falciparum)"]=dx("Infectious","Infectious/Hematologic",v(115,88,55,24,104.0,93),
    STD,{"heart_rate":12,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":4},
    "High fever with rigors (periodicity may be absent in falciparum), AMS/cerebral malaria, severe anemia, ARDS, hypoglycemia, metabolic acidosis, DIC; travel to endemic area",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"hgb":lab(4,10,"g/dL","decreased"),"plt":lab(20,100,"K/uL","decreased"),"cr":lab(1.5,5.0,"mg/dL","elevated"),
     "glu":lab(30,80,"mg/dL","decreased"),"tbili":lab(3.0,15.0,"mg/dL","elevated"),
     "lactate":lab(3.0,8.0,"mmol/L","elevated"),"ldh":lab(300,2000,"U/L","elevated"),
     "parasitemia":lab(2,50,"%","elevated")},
    ["IV Access","Continuous Monitoring","ICU"],
    {"IV Artesunate":tc(60,"First-line for severe malaria (2.4mg/kg IV at 0, 12, 24h then daily); superior to quinine"),
     "Exchange Transfusion":tc(240,"Consider if parasitemia >10% or cerebral malaria with high burden"),
     "Glucose Monitoring":tc(60,"Q4h; hypoglycemia from parasite consumption and quinine effect"),
     "Supportive Care":tc(30,"Fluid resuscitation (careful - ARDS risk), seizure management, transfusion for Hgb <7")},{})

NEW["Toxic Shock Syndrome - Staphylococcal"]=dx("Infectious","Infectious/Multi-System",v(125,75,45,26,104.0,92),
    STD,{"heart_rate":15,"systolic_bp":22,"diastolic_bp":18,"o2_saturation":4},
    "Fever ≥102°F, diffuse macular rash (sunburn-like), desquamation 1-2 weeks later (especially palms/soles), hypotension, multiorgan involvement (≥3 organ systems); menstrual or wound associated",
    {"o2_saturation_below":85,"systolic_bp_below":60},
    {"wbc":lab(12,28,"K/uL","elevated"),"cr":lab(2.0,5.0,"mg/dL","elevated"),
     "ck":lab(500,10000,"U/L","elevated"),"ast":lab(100,1000,"U/L","elevated"),
     "plt":lab(40,100,"K/uL","decreased"),"tbili":lab(2.0,8.0,"mg/dL","elevated"),
     "lactate":lab(4.0,10.0,"mmol/L","elevated")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Vasopressors","Antibiotics","Continuous Monitoring"],
    {"Aggressive IV Fluids":tc(30,"Massive capillary leak; may need 10-20L/day"),
     "Remove Foreign Body":tc(30,"Remove tampon, wound packing, or retained foreign body immediately"),
     "IV Antibiotics":tc(30,"Vancomycin + clindamycin (toxin suppression is key; clindamycin inhibits toxin production even if resistant)"),
     "Source Control":tc(60,"Wound debridement if wound TSS"),
     "IVIG":tc(240,"2g/kg single dose; neutralizes TSST-1 and other superantigens; consider for refractory cases")},{})

NEW["Toxic Shock Syndrome - Streptococcal"]=dx("Infectious","Infectious/Multi-System",v(122,78,48,26,103.5,91),
    STD,{"heart_rate":15,"systolic_bp":22,"diastolic_bp":18,"o2_saturation":4},
    "Severe pain at infection site (often necrotizing fasciitis), rapidly progressive shock, multiorgan failure; NO rash (vs staphylococcal); GAS bacteremia in 60%",
    {"o2_saturation_below":85,"systolic_bp_below":60},
    {"wbc":lab(2,30,"K/uL","variable"),"cr":lab(2.0,6.0,"mg/dL","elevated"),
     "ck":lab(1000,50000,"U/L","elevated"),"lactate":lab(4.0,12.0,"mmol/L","elevated"),
     "plt":lab(20,80,"K/uL","decreased"),"alb":lab(1.5,2.5,"g/dL","decreased")},
    ["IV Access x2 Large Bore","Fluid Resuscitation","Vasopressors","Antibiotics","Continuous Monitoring"],
    {"IV Antibiotics":tc(30,"Penicillin G + clindamycin; clindamycin Eagle effect — more effective than penicillin alone at high inoculum"),
     "Surgical Debridement":tc(60,"Emergent; often necrotizing fasciitis; wide debridement critical"),
     "IVIG":tc(240,"1-2g/kg; neutralizes streptococcal superantigens"),
     "ICU Care":tc(60,"Vasopressors, mechanical ventilation, CRRT for renal failure often required")},{})

NEW["Herpes Simplex Encephalitis"]=dx("Infectious","Infectious/Neurological",v(100,130,80,18,102.5,96),
    STD,{"heart_rate":8,"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Fever, headache, altered mental status, bizarre behavior, olfactory/gustatory hallucinations, temporal lobe seizures, focal neurological deficits; HSV-1 in adults, HSV-2 in neonates",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"csf_wbc":lab(10,500,"cells/uL","elevated"),"csf_protein":lab(50,200,"mg/dL","elevated"),
     "csf_glucose":lab(40,80,"mg/dL","normal"),"csf_rbc":lab(10,500,"cells/uL","elevated"),
     "wbc":lab(8,15,"K/uL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"IV Acyclovir":tc(60,"10mg/kg IV q8h x 14-21 days; START EMPIRICALLY — do NOT wait for HSV PCR results; reduces mortality from 70% to 20%"),
     "LP with HSV PCR":tc(120,"CSF HSV PCR 96% sensitive after 72h; may be negative early — repeat in 3-7 days if high suspicion"),
     "MRI Brain":tc(120,"Temporal lobe edema/hemorrhage; most sensitive imaging"),
     "EEG":tc(240,"Periodic lateralized epileptiform discharges (PLEDs) from temporal lobe"),
     "Seizure Management":tc(30,"Levetiracetam for temporal lobe seizures")},{})

NEW["Tuberculosis - Active Pulmonary"]=dx("Infectious","Infectious/Respiratory",v(95,120,75,20,100.5,95),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":3},
    "Chronic cough >2 weeks, hemoptysis, night sweats, weight loss, fever; upper lobe cavitation on CXR; immigrants, homeless, incarcerated, HIV, healthcare workers",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"wbc":lab(8,15,"K/uL","variable"),"esr":lab(30,80,"mm/hr","elevated"),"crp":lab(2,10,"mg/dL","elevated"),
     "hgb":lab(10,14,"g/dL","variable"),"alb":lab(2.5,4.0,"g/dL","variable"),
     "alt":lab(10,50,"U/L","normal")},
    ["Airborne Isolation","IV Access","Continuous Monitoring"],
    {"Airborne Isolation":tc(1,"IMMEDIATE N95 respirator + negative pressure room; highest priority"),
     "AFB Smear and Culture":tc(60,"3 sputum specimens (8h apart); nucleic acid amplification test (NAAT) for rapid confirmation"),
     "CXR":tc(60,"Upper lobe infiltrates, cavitation, lymphadenopathy; miliary pattern if disseminated"),
     "RIPE Therapy":tc(240,"Rifampin + Isoniazid + Pyrazinamide + Ethambutol x 2 months, then RH x 4 months"),
     "Public Health Notification":tc(240,"Mandatory reporting; contact investigation")},
    {"HIV":{"risk":"50-fold increased risk; atypical CXR in advanced HIV"}})

NEW["Tuberculosis - Miliary/Disseminated"]=dx("Infectious","Infectious/Multi-System",v(110,100,62,22,102.0,92),
    STD,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":5},
    "Fever, weight loss, hepatosplenomegaly, pancytopenia, diffuse miliary pattern on CXR (1-3mm nodules throughout both lungs), choroidal tubercles on fundoscopy; immunocompromised host",
    {"o2_saturation_below":85,"systolic_bp_below":75},
    {"wbc":lab(3,12,"K/uL","variable"),"hgb":lab(7,11,"g/dL","decreased"),"plt":lab(50,200,"K/uL","decreased"),
     "alt":lab(30,200,"U/L","elevated"),"alk_phos":lab(100,400,"U/L","elevated"),
     "ldh":lab(200,800,"U/L","elevated"),"alb":lab(2.0,3.5,"g/dL","decreased")},
    ["Airborne Isolation","IV Access","Continuous Monitoring"],
    {"Airborne Isolation":tc(1,"Immediate isolation"),
     "RIPE Therapy":tc(120,"Start empirically if miliary pattern; often before culture confirmation"),
     "Blood/Bone Marrow Culture":tc(120,"Higher yield than sputum in miliary TB"),
     "Corticosteroids":tc(240,"Dexamethasone if TB meningitis suspected; reduces mortality"),
     "HIV Testing":tc(120,"Miliary TB frequently presents in advanced HIV; CD4 count critical")},
    {"HIV":{"risk":"commonest cause of miliary TB"}})

NEW["Influenza - Severe/Complicated"]=dx("Infectious","Infectious/Respiratory",v(108,105,65,24,103.5,91),
    STD,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":5},
    "High fever, myalgias, cough, dyspnea, tachypnea; complications: primary viral pneumonia, secondary bacterial pneumonia, myocarditis, rhabdomyolysis, encephalitis; risk groups: elderly, pregnant, immunocompromised",
    {"o2_saturation_below":88,"systolic_bp_below":75},
    {"wbc":lab(3,12,"K/uL","variable"),"crp":lab(2,15,"mg/dL","elevated"),
     "procalcitonin":lab(0.1,2.0,"ng/mL","variable"),"ck":lab(100,5000,"U/L","variable"),
     "cr":lab(0.6,2.0,"mg/dL","variable"),"troponin":lab(0,0.5,"ng/mL","variable")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring"],
    {"Oseltamivir":tc(48,"75mg BID x 5 days; most benefit within 48h of symptoms but give even if late in severe disease"),
     "Respiratory Support":tc(30,"HFNC, BiPAP, or intubation as needed for respiratory failure"),
     "Bacterial Superinfection Evaluation":tc(120,"Blood/sputum cultures; procalcitonin trending; add antibiotics if secondary pneumonia suspected"),
     "Droplet + Contact Precautions":tc(1,"Standard infection prevention; airborne for aerosol-generating procedures")},{})

NEW["COVID-19 - Severe Pneumonia"]=dx("Infectious","Infectious/Respiratory",v(105,110,68,26,102.0,88),
    STD,{"heart_rate":10,"systolic_bp":10,"diastolic_bp":8,"o2_saturation":8},
    "Hypoxemia (often 'happy hypoxia' initially), dyspnea, bilateral ground-glass opacities, prone positioning helps, cytokine storm features; hypercoagulable; ARDS progression",
    {"o2_saturation_below":85,"systolic_bp_below":75},
    {"wbc":lab(4,11,"K/uL","variable"),"lymphocytes":lab(0.5,1.5,"K/uL","decreased"),
     "crp":lab(5,25,"mg/dL","elevated"),"d_dimer":lab(500,10000,"ng/mL","elevated"),
     "ferritin":lab(500,5000,"ng/mL","elevated"),"ldh":lab(300,1000,"U/L","elevated"),
     "il6":lab(10,500,"pg/mL","elevated"),"troponin":lab(0,0.5,"ng/mL","variable")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring"],
    {"Dexamethasone":tc(120,"6mg/day x 10 days; benefit ONLY if requiring O2 (RECOVERY trial); reduces mortality"),
     "Prone Positioning":tc(30,"16h/day prone; improves V/Q matching and oxygenation; reduces intubation"),
     "Anticoagulation":tc(120,"Prophylactic enoxaparin for non-ICU; therapeutic for ICU patients (per ATTACC/REMAP-CAP)"),
     "Tocilizumab":tc(240,"If CRP >75 and on O2 within 24h of ICU admission; IL-6 receptor blocker"),
     "HFNC/NIV":tc(30,"High-flow nasal cannula superior to standard O2 for avoiding intubation")},{})

NEW["Fournier Gangrene"]=dx("Infectious","Infectious/Surgical",v(120,82,50,24,103.5,93),
    STD,{"heart_rate":15,"systolic_bp":22,"diastolic_bp":15,"o2_saturation":4},
    "Necrotizing fasciitis of perineum/genitalia; severe perineal/scrotal pain, swelling, crepitus, rapid progression, foul smell, skin necrosis; diabetic and immunocompromised at risk",
    {"o2_saturation_below":85,"systolic_bp_below":60},
    {"wbc":lab(15,35,"K/uL","elevated"),"lactate":lab(4.0,10.0,"mmol/L","elevated"),
     "cr":lab(1.5,4.0,"mg/dL","elevated"),"na":lab(125,138,"mEq/L","decreased"),
     "glu":lab(200,500,"mg/dL","elevated"),"hgb":lab(8,13,"g/dL","decreased")},
    ["IV Access x2 Large Bore","Antibiotics","Fluid Resuscitation","Vasopressors","Continuous Monitoring"],
    {"Emergent Surgical Debridement":tc(60,"MOST CRITICAL intervention; wide radical debridement; mortality directly correlates with time to OR"),
     "IV Antibiotics":tc(30,"Vancomycin + piperacillin-tazobactam + clindamycin; polymicrobial infection"),
     "ICU Admission":tc(60,"High mortality (20-40%); frequent return to OR for re-debridement"),
     "CT Pelvis":tc(60,"Gas tracking, extent of disease; but NEVER delay OR for imaging if clinical diagnosis clear")},
    {"Diabetes":{"glu":{"min":250,"max":600},"cr":{"min":1.5,"max":4.0}}})

NEW["Lyme Disease - Acute Disseminated"]=dx("Infectious","Infectious/Multi-System",v(75,125,78,16,100.0,98),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Multiple erythema migrans lesions, facial nerve palsy (bilateral pathognomonic), AV block (PR prolongation, complete heart block), meningitis, migratory arthralgias; tick exposure history",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(6,12,"K/uL","normal"),"esr":lab(20,60,"mm/hr","elevated"),
     "lyme_igg_igm":lab(1,1,"positive","elevated"),"alt":lab(20,80,"U/L","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Lyme Serology":tc(120,"Two-tier testing: EIA/IFA then Western blot if positive; may be negative in first 2 weeks"),
     "ECG":tc(30,"PR prolongation or high-degree AV block (Lyme carditis); may need temporary pacer"),
     "LP":tc(0,"If meningitis suspected; Lyme CSF antibody index"),
     "Doxycycline":tc(120,"100mg BID x 21-28 days for disseminated; IV ceftriaxone for meningitis or 3rd degree AVB")},{})

NEW["Rocky Mountain Spotted Fever"]=dx("Infectious","Infectious/Multi-System",v(110,95,58,22,104.0,94),
    STD,{"heart_rate":10,"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "Fever, headache, myalgia then classic petechial rash starting ankles/wrists → spreading centrIPETally (palms & soles involved); tick exposure (Dermacentor); 20% mortality if untreated",
    {"o2_saturation_below":88,"systolic_bp_below":75},
    {"wbc":lab(6,15,"K/uL","variable"),"plt":lab(50,150,"K/uL","decreased"),"na":lab(125,138,"mEq/L","decreased"),
     "alt":lab(30,200,"U/L","elevated"),"cr":lab(0.8,3.0,"mg/dL","variable"),
     "hgb":lab(10,14,"g/dL","variable")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"Doxycycline":tc(60,"100mg BID for ALL ages including children; START immediately on clinical suspicion — do NOT wait for serology"),
     "Supportive Care":tc(30,"Aggressive fluid resuscitation for capillary leak; platelets for active bleeding only"),
     "Serology":tc(0,"Antibody rise takes 7-10 days; treatment must begin empirically; PCR available")},{})

NEW["Dengue - Severe (Dengue Hemorrhagic Fever)"]=dx("Infectious","Infectious/Hematologic",v(115,85,52,22,103.5,94),
    STD,{"heart_rate":12,"systolic_bp":18,"diastolic_bp":12,"o2_saturation":3},
    "Fever, severe abdominal pain, persistent vomiting, mucosal bleeding, rapid hematocrit rise (hemoconcentration), pleural effusions, ascites; WARNING SIGNS present in defervescence phase",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"plt":lab(10,50,"K/uL","decreased"),"hct":lab(40,55,"%","elevated"),"ast":lab(200,5000,"U/L","elevated"),
     "alt":lab(100,3000,"U/L","elevated"),"alb":lab(2.0,3.5,"g/dL","decreased"),
     "pt_inr":lab(1.2,2.5,"INR","elevated")},
    ["IV Access","Fluid Resuscitation","Continuous Monitoring"],
    {"IV Crystalloid":tc(30,"5-10mL/kg/hr LR; reduce as hematocrit falls; AVOID over-resuscitation (effusions)"),
     "Serial Hematocrit":tc(60,"Q4-6h; rising Hct = ongoing plasma leak; falling Hct may = hemorrhage"),
     "Platelet Monitoring":tc(60,"Transfuse only for active bleeding or <10K; prophylactic transfusion NOT recommended"),
     "Avoid NSAIDs/Aspirin":tc(1,"Increased bleeding risk; use acetaminophen only for fever")},{})

NEW["Pneumonia - Healthcare-Associated/Ventilator-Associated"]=dx("Infectious","Infectious/Respiratory",v(105,110,68,22,102.0,92),
    STD,{"heart_rate":10,"systolic_bp":12,"diastolic_bp":8,"o2_saturation":5},
    "New infiltrate + purulent secretions, fever or leukocytosis in hospitalized/ventilated patient ≥48h; MDR risk: Pseudomonas, MRSA, Acinetobacter, ESBL-producing organisms",
    {"o2_saturation_below":88,"systolic_bp_below":75},
    {"wbc":lab(12,25,"K/uL","elevated"),"procalcitonin":lab(0.5,10.0,"ng/mL","elevated"),
     "cr":lab(0.6,2.0,"mg/dL","variable"),"lactate":lab(1.5,4.0,"mmol/L","elevated"),
     "sputum_cx":lab(1,1,"positive","elevated")},
    ["IV Access","Antibiotics","Oxygen Therapy","Continuous Monitoring"],
    {"Respiratory Culture":tc(120,"Quantitative tracheal aspirate or BAL; before new antibiotics"),
     "Broad-Spectrum Antibiotics":tc(60,"Anti-pseudomonal beta-lactam + vancomycin or linezolid (MRSA); double gram-neg if MDR risk"),
     "De-escalation":tc(0,"Narrow based on culture + sensitivities within 48-72h; shorter courses (7 days) if improving"),
     "CXR":tc(60,"New or progressive infiltrate; daily in ventilated patients")},{})

NEW["Catheter-Related Bloodstream Infection"]=dx("Infectious","Infectious",v(102,115,72,18,102.5,97),
    STD,{"heart_rate":8,"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Fever, rigors, exit site erythema/purulence, bacteremia with no other identified source in patient with central line; differential time to positivity (CVC blood+ ≥2h before peripheral)",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"wbc":lab(11,22,"K/uL","elevated"),"blood_cx":lab(1,1,"positive","elevated"),
     "procalcitonin":lab(0.5,5.0,"ng/mL","elevated"),"cr":lab(0.6,1.5,"mg/dL","normal")},
    ["IV Access (peripheral)","Antibiotics","Continuous Monitoring"],
    {"Blood Cultures":tc(60,"Paired: one from CVC + one peripheral; differential time to positivity"),
     "Remove CVC":tc(240,"Remove line for S. aureus, Candida, or clinical deterioration; exchange over wire for some gram-negatives"),
     "IV Antibiotics":tc(60,"Vancomycin empirically; add gram-negative coverage if septic; duration based on organism"),
     "TTE/TEE":tc(0,"For S. aureus bacteremia — always rule out endocarditis; 25% have vegetation")},{})

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
print(f"Added {added} infectious diagnoses. Total: {len(data['diagnoses'])}")
for c in sorted(cats):
    print(f"  {c}: {len(cats[c])}")

#!/usr/bin/env python3
"""Batch 3: Neurological diagnoses expansion."""
import json
from pathlib import Path

OUTPUT = Path(__file__).parent / "diagnosis_data.json"

def dx(category, organ, vitals, modifiers, weights, pe, thresholds, labs, interventions, time_critical, comorbidity_mods=None):
    return {"category": category, "organ_system": organ, "vitals": vitals, "vital_modifiers": modifiers,
            "vital_severity_weights": weights, "pe_findings": pe, "critical_pe_thresholds": thresholds,
            "expected_labs": labs, "required_interventions": interventions, "time_critical_actions": time_critical,
            "comorbidity_modifiers": comorbidity_mods or {}}

def v(hr, sbp, dbp, rr, temp, spo2):
    return {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp, "respiratory_rate": rr, "temperature_f": temp, "o2_saturation": spo2}

def lab(mn, mx, unit, direction):
    return {"min": mn, "max": mx, "unit": unit, "direction": direction}

def tc(window, rationale):
    return {"window_minutes": window, "rationale": rationale}

STD = {"heart_rate": "multiply", "systolic_bp": "decrease", "diastolic_bp": "decrease",
       "respiratory_rate": "multiply", "temperature_f": "fixed", "o2_saturation": "decrease"}
CUSHING = {**STD, "heart_rate": "inverse", "systolic_bp": "multiply", "respiratory_rate": "inverse"}

NEW = {}

# ── Ischemic Stroke variants ──
NEW["Ischemic Stroke - MCA"] = dx("Neurological","Neurological",v(88,165,95,16,98.6,97),
    {**STD,"systolic_bp":"multiply"},{"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Contralateral hemiparesis (face/arm>leg), aphasia if dominant hemisphere, hemineglect if non-dominant, gaze deviation toward lesion",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"glu":lab(80,200,"mg/dL","variable"),"pt_inr":lab(0.9,1.3,"INR","normal"),"plt":lab(100,400,"K/uL","normal"),
     "cr":lab(0.6,1.4,"mg/dL","normal"),"troponin":lab(0,0.04,"ng/mL","normal")},
    ["IV Access","Continuous Monitoring","Oxygen Therapy"],
    {"CT Head":tc(25,"Non-contrast CT to rule out hemorrhage before tPA"),"tPA Administration":tc(270,"Alteplase 0.9mg/kg IV within 4.5h of symptom onset per AHA/ASA guidelines"),
     "NIH Stroke Scale":tc(10,"Quantify deficit severity; guides treatment decisions"),"Thrombectomy Eval":tc(360,"LVO on CTA → mechanical thrombectomy up to 24h per DAWN/DEFUSE3")},
    {"Atrial Fibrillation":{"risk":"cardioembolic source"}})

NEW["Ischemic Stroke - Posterior Circulation"] = dx("Neurological","Neurological",v(85,160,92,16,98.6,97),
    {**STD,"systolic_bp":"multiply"},{"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Vertigo, diplopia, dysarthria, ataxia, crossed findings (ipsilateral cranial nerve + contralateral motor), possible locked-in syndrome",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"glu":lab(80,200,"mg/dL","variable"),"pt_inr":lab(0.9,1.3,"INR","normal"),"plt":lab(100,400,"K/uL","normal"),"cr":lab(0.6,1.4,"mg/dL","normal")},
    ["IV Access","Continuous Monitoring","Oxygen Therapy"],
    {"CT Head":tc(25,"Non-contrast CT; may miss early posterior fossa infarcts"),"MRI Brain":tc(60,"DWI most sensitive for posterior circulation stroke"),
     "CTA Head/Neck":tc(30,"Evaluate vertebrobasilar system for occlusion"),"tPA":tc(270,"Same window as anterior circulation if no contraindications")},{})

NEW["Lacunar Stroke"] = dx("Neurological","Neurological",v(82,175,100,16,98.6,98),
    {**STD,"systolic_bp":"multiply"},{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Pure motor hemiparesis OR pure sensory loss OR ataxic hemiparesis OR dysarthria-clumsy hand; no cortical signs (no aphasia, neglect, visual field cuts)",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"glu":lab(100,250,"mg/dL","variable"),"hba1c":lab(6.0,12.0,"%","elevated"),"cr":lab(0.8,2.0,"mg/dL","variable"),
     "lipid_panel":lab(200,350,"mg/dL","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"CT Head":tc(25,"Rule out hemorrhage"),"MRI Brain":tc(120,"DWI to confirm small deep infarct"),
     "BP Management":tc(60,"Permissive hypertension acutely; long-term target <130/80")},{})

NEW["Hemorrhagic Stroke - ICH"] = dx("Neurological","Neurological",v(92,195,110,18,98.6,96),
    {**STD,"systolic_bp":"multiply"},{"systolic_bp":12,"diastolic_bp":8,"o2_saturation":3},
    "Sudden headache, vomiting, progressive focal deficit, decreased consciousness, possible seizure; signs reflect location (basal ganglia, thalamus, cerebellum, pons)",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"pt_inr":lab(0.9,4.0,"INR","variable"),"plt":lab(50,400,"K/uL","variable"),"cr":lab(0.6,2.0,"mg/dL","variable"),
     "glu":lab(100,250,"mg/dL","elevated"),"troponin":lab(0,0.5,"ng/mL","variable")},
    ["IV Access","Continuous Monitoring","Oxygen Therapy"],
    {"CT Head":tc(15,"Emergent; hyperdense lesion confirms ICH"),"BP Control":tc(30,"Target SBP <140 per INTERACT2; IV nicardipine or clevidipine"),
     "Coagulopathy Reversal":tc(30,"PCC for warfarin, idarucizumab for dabigatran, andexanet for Xa inhibitors"),
     "Neurosurgery Consult":tc(60,"For cerebellar ICH >3cm, hydrocephalus, or herniation")},
    {"Anticoagulation":{"pt_inr":{"min":2.0,"max":5.0}}})

NEW["Cerebellar Stroke"] = dx("Neurological","Neurological",v(78,170,95,16,98.6,97),
    {**STD,"systolic_bp":"multiply"},{"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Sudden vertigo, vomiting, severe ataxia, dysarthria, nystagmus, inability to walk; DANGER: rapid deterioration from brainstem compression or obstructive hydrocephalus",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"glu":lab(80,200,"mg/dL","variable"),"pt_inr":lab(0.9,1.3,"INR","normal"),"plt":lab(100,400,"K/uL","normal")},
    ["IV Access","Continuous Monitoring"],
    {"CT Head":tc(15,"Emergent; evaluate posterior fossa and fourth ventricle"),"Neurosurgery Consult":tc(30,"Emergent for decompressive craniectomy or EVD if hydrocephalus"),
     "Serial Neuro Checks":tc(15,"Q15min — rapid deterioration is hallmark of cerebellar stroke")},{})

NEW["Transient Ischemic Attack"] = dx("Neurological","Neurological",v(82,155,88,16,98.6,98),
    {**STD,"systolic_bp":"multiply"},{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Resolved focal neurological deficit (was present <24h), normal exam now; ABCD2 score determines risk of subsequent stroke",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"glu":lab(80,200,"mg/dL","variable"),"lipid_panel":lab(150,300,"mg/dL","variable"),"hba1c":lab(5.0,10.0,"%","variable"),
     "pt_inr":lab(0.9,1.3,"INR","normal"),"troponin":lab(0,0.04,"ng/mL","normal")},
    ["IV Access","Continuous Monitoring"],
    {"MRI Brain":tc(240,"DWI to rule out completed infarct"),"CTA Head/Neck":tc(120,"Evaluate for carotid stenosis"),
     "Dual Antiplatelet":tc(60,"ASA + clopidogrel for 21 days if ABCD2 ≥4 per POINT trial"),
     "Cardiac Monitoring":tc(240,"Telemetry x 24h minimum; extended if AF suspected")},{})

NEW["Subdural Hematoma - Acute"] = dx("Neurological","Neurological",v(70,165,95,14,98.6,96),
    CUSHING,{"heart_rate":8,"systolic_bp":10,"respiratory_rate":3,"o2_saturation":3},
    "Progressive headache, contralateral hemiparesis, ipsilateral pupil dilation, declining consciousness; crescent-shaped hyperdensity on CT crossing suture lines",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"pt_inr":lab(0.9,4.0,"INR","variable"),"plt":lab(50,400,"K/uL","variable"),"hgb":lab(10,16,"g/dL","normal"),
     "na":lab(135,148,"mEq/L","normal")},
    ["IV Access","Continuous Monitoring"],
    {"CT Head":tc(15,"Emergent; crescent-shaped hyperdensity"),"Neurosurgery Consult":tc(30,"Craniotomy for SDH >10mm or midline shift >5mm"),
     "Coagulopathy Reversal":tc(30,"Reverse anticoagulation immediately if applicable"),
     "ICP Management":tc(15,"HOB 30°, mannitol or hypertonic saline if herniation signs")},
    {"Anticoagulation":{"pt_inr":{"min":2.0,"max":5.0}},"Elderly":{"plt":{"min":50,"max":150}}})

NEW["Subdural Hematoma - Chronic"] = dx("Neurological","Neurological",v(75,145,85,16,98.6,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Insidious headache weeks after minor trauma, cognitive decline, gait instability, subtle hemiparesis; elderly on anticoagulants; crescent-shaped iso/hypodensity on CT",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"pt_inr":lab(0.9,4.0,"INR","variable"),"plt":lab(50,300,"K/uL","variable"),"na":lab(130,148,"mEq/L","variable"),
     "cr":lab(0.6,2.0,"mg/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"CT Head":tc(60,"Iso or hypodense crescent; may have mixed density if rebleed"),"Neurosurgery Consult":tc(120,"Burr hole drainage for symptomatic cases"),
     "Coagulopathy Correction":tc(60,"Hold/reverse anticoagulation")},{})

NEW["Cerebral Venous Thrombosis"] = dx("Neurological","Neurological",v(90,140,85,16,98.6,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Headache (often progressive over days), papilledema, focal deficits, seizures; consider in young women on OCPs, postpartum, or with hypercoagulable states",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"d_dimer":lab(500,5000,"ng/mL","elevated"),"pt_inr":lab(0.9,1.3,"INR","normal"),"plt":lab(150,400,"K/uL","normal"),
     "cr":lab(0.6,1.2,"mg/dL","normal")},
    ["IV Access","Continuous Monitoring"],
    {"CT Venogram or MRV":tc(120,"Gold standard; empty delta sign on contrast CT"),"Anticoagulation":tc(240,"Heparin drip even with hemorrhagic infarction per AHA guidelines"),
     "Seizure Management":tc(30,"Levetiracetam if seizures; CVT has high seizure incidence")},{})

NEW["Brain Abscess"] = dx("Neurological","Neurological/Infectious",v(95,130,78,18,101.5,96),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Headache, fever, focal neurological deficit, seizures; triad present in <50% of cases; ring-enhancing lesion on CT/MRI",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"wbc":lab(10,25,"K/uL","elevated"),"crp":lab(2.0,20.0,"mg/dL","elevated"),"esr":lab(30,100,"mm/hr","elevated"),
     "cr":lab(0.6,1.4,"mg/dL","normal"),"na":lab(135,148,"mEq/L","normal")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"CT/MRI Brain":tc(60,"Ring-enhancing lesion with surrounding edema"),"IV Antibiotics":tc(60,"Empiric: ceftriaxone + metronidazole +/- vancomycin; 6-8 week course"),
     "Neurosurgery Consult":tc(120,"Aspiration/excision if >2.5cm or causing mass effect"),
     "Seizure Prophylaxis":tc(60,"Levetiracetam for supratentorial abscesses")},{})

NEW["Meningitis - Bacterial"] = dx("Neurological","Neurological/Infectious",v(115,95,58,22,103.5,95),
    STD,{"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "Fever, headache, nuchal rigidity, photophobia, altered mental status, positive Kernig and Brudzinski signs, petechial rash if meningococcal",
    {"o2_saturation_below":90,"systolic_bp_below":75},
    {"wbc":lab(15,35,"K/uL","elevated"),"lactate":lab(2.0,6.0,"mmol/L","elevated"),
     "csf_wbc":lab(100,10000,"cells/uL","elevated"),"csf_protein":lab(100,500,"mg/dL","elevated"),
     "csf_glucose":lab(10,40,"mg/dL","decreased"),"cr":lab(0.6,2.0,"mg/dL","variable")},
    ["IV Access","Antibiotics","Fluid Resuscitation","Continuous Monitoring"],
    {"IV Antibiotics":tc(30,"Vancomycin + ceftriaxone STAT; do NOT delay for LP if unstable"),
     "Dexamethasone":tc(30,"0.15mg/kg IV before or with first antibiotic dose; reduces mortality in pneumococcal"),
     "Lumbar Puncture":tc(60,"After CT if indicated; opening pressure, cell count, protein, glucose, gram stain, culture"),
     "Blood Cultures":tc(30,"Before antibiotics if possible; but NEVER delay antibiotics for cultures")},
    {"Immunocompromised":{"wbc":{"min":5,"max":15}}})

NEW["Meningitis - Viral"] = dx("Neurological","Neurological/Infectious",v(100,120,75,18,101.5,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Headache, fever, mild nuchal rigidity, photophobia; generally less toxic-appearing than bacterial; normal mental status typically preserved",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(8,15,"K/uL","variable"),"csf_wbc":lab(10,500,"cells/uL","elevated"),
     "csf_protein":lab(50,150,"mg/dL","elevated"),"csf_glucose":lab(40,80,"mg/dL","normal"),
     "cr":lab(0.6,1.2,"mg/dL","normal")},
    ["IV Access","Continuous Monitoring"],
    {"Lumbar Puncture":tc(60,"Lymphocytic pleocytosis, normal glucose distinguishes from bacterial"),
     "HSV PCR":tc(120,"Send on all viral meningitis CSF; acyclovir if HSV suspected"),
     "Supportive Care":tc(30,"IV fluids, analgesics, antiemetics; most cases self-limited")},{})

NEW["Normal Pressure Hydrocephalus"] = dx("Neurological","Neurological",v(78,140,82,16,98.6,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Classic triad: gait apraxia (magnetic gait), urinary incontinence, dementia; 'wet, wacky, wobbly'; gait abnormality typically earliest and most prominent",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"na":lab(135,148,"mEq/L","normal"),"cr":lab(0.6,2.0,"mg/dL","variable"),"tsh":lab(0.4,4.0,"mIU/L","normal"),
     "b12":lab(200,900,"pg/mL","normal")},
    ["Continuous Monitoring"],
    {"CT/MRI Brain":tc(240,"Ventriculomegaly out of proportion to sulcal atrophy"),
     "Large Volume LP":tc(240,"Remove 30-50mL CSF; assess gait improvement post-tap (positive predictor for shunt)"),
     "Neurosurgery Consult":tc(0,"VP shunt placement for responders")},{})

NEW["Myasthenia Gravis Crisis"] = dx("Neurological","Neurological/Neuromuscular",v(100,135,82,22,98.6,94),
    STD,{"systolic_bp":10,"diastolic_bp":5,"o2_saturation":4},
    "Rapidly progressive weakness, respiratory failure, dyspnea, weak cough, dysphagia, ptosis, diplopia, nasal speech; NIF worsening",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"wbc":lab(6,12,"K/uL","normal"),"cr":lab(0.6,1.4,"mg/dL","normal"),
     "k":lab(3.5,5.0,"mEq/L","normal"),"abg_pco2":lab(35,60,"mmHg","variable")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring"],
    {"NIF/VC Monitoring":tc(15,"NIF <-20 or VC <1L or declining → intubate; check q2h"),
     "IVIG or Plasmapheresis":tc(240,"Both equally effective; IVIG 0.4g/kg/day x 5 days"),
     "Hold Cholinesterase Inhibitors":tc(30,"May worsen secretions and confound respiratory assessment in crisis"),
     "Intubation":tc(30,"Avoid succinylcholine (resistance) and aminoglycosides (worsen NMJ)")},{})

NEW["Multiple Sclerosis - Acute Relapse"] = dx("Neurological","Neurological",v(82,125,78,16,98.6,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "New or worsening neurological symptoms >24h: optic neuritis (painful vision loss), transverse myelitis, brainstem syndrome; Uhthoff phenomenon (heat worsening)",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(6,12,"K/uL","normal"),"cr":lab(0.6,1.2,"mg/dL","normal"),
     "csf_wbc":lab(0,50,"cells/uL","variable"),"csf_protein":lab(15,60,"mg/dL","normal")},
    ["IV Access","Continuous Monitoring"],
    {"MRI Brain/Spine":tc(240,"Gadolinium-enhancing lesions confirm acute inflammation; dissemination in space and time"),
     "IV Methylprednisolone":tc(240,"1g IV daily x 3-5 days; hastens recovery from relapse"),
     "Plasmapheresis":tc(0,"If steroid-refractory severe relapse; 5-7 exchanges")},{})

NEW["Trigeminal Neuralgia"] = dx("Neurological","Neurological",v(90,155,90,18,98.6,98),
    {**STD,"systolic_bp":"multiply"},{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Sudden severe lancinating facial pain in V2/V3 distribution, triggered by chewing/touching/wind; unilateral; pain-free intervals between attacks",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(6,12,"K/uL","normal"),"cr":lab(0.6,1.4,"mg/dL","normal"),"esr":lab(0,30,"mm/hr","normal")},
    ["IV Access","Continuous Monitoring"],
    {"MRI Brain":tc(0,"Rule out structural cause: tumor, MS plaque, vascular compression"),
     "Carbamazepine":tc(60,"200mg BID titrate up; first-line treatment; check Na and CBC at baseline"),
     "Pain Management":tc(30,"Acute: IV phenytoin or lidocaine infusion for status trigeminus")},{})

NEW["Bell Palsy"] = dx("Neurological","Neurological",v(80,130,80,16,98.6,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Acute unilateral facial paralysis involving forehead (LMN pattern); difficulty closing eye, drooping mouth, loss of nasolabial fold; hyperacusis, taste changes",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(6,12,"K/uL","normal"),"glu":lab(70,200,"mg/dL","variable"),"cr":lab(0.6,1.4,"mg/dL","normal"),
     "esr":lab(0,30,"mm/hr","normal")},
    ["Continuous Monitoring"],
    {"CT/MRI":tc(0,"Only if atypical features suggesting stroke or tumor; not routine"),
     "Prednisone":tc(72,"60-80mg/day x 7 days with taper; best if started within 72h of onset"),
     "Eye Protection":tc(24,"Artificial tears, eye patch at night to prevent corneal exposure keratopathy")},{})

NEW["Cauda Equina Syndrome"] = dx("Neurological","Neurological/MSK",v(90,130,80,16,98.6,98),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Low back pain, bilateral leg weakness, saddle anesthesia, bowel/bladder dysfunction (urinary retention most sensitive), decreased rectal tone, bilateral absent ankle reflexes",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(6,15,"K/uL","variable"),"cr":lab(0.6,1.4,"mg/dL","normal"),"esr":lab(0,50,"mm/hr","variable"),
     "crp":lab(0,5.0,"mg/dL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"MRI Lumbar Spine":tc(120,"EMERGENT; compression of cauda equina nerve roots"),
     "Neurosurgery Consult":tc(120,"Emergent surgical decompression within 24-48h for best outcomes"),
     "Foley Catheter":tc(60,"Urinary retention is common and may require catheterization"),
     "Post-Void Residual":tc(30,">200mL post-void residual is highly suggestive")},{})

NEW["Wernicke Encephalopathy"] = dx("Neurological","Neurological",v(100,110,68,18,98.6,98),
    STD,{"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Classic triad (all three present in <33%): confusion/AMS, ophthalmoplegia (lateral rectus palsy, nystagmus), gait ataxia; malnourished/alcoholic patient",
    {"o2_saturation_below":92,"systolic_bp_below":80},
    {"mg":lab(0.8,1.5,"mg/dL","decreased"),"glu":lab(50,150,"mg/dL","variable"),
     "thiamine":lab(0,30,"nmol/L","decreased"),"ast":lab(30,200,"U/L","elevated"),
     "alt":lab(20,100,"U/L","elevated"),"alb":lab(2.0,3.5,"g/dL","decreased")},
    ["IV Access","Continuous Monitoring"],
    {"IV Thiamine":tc(30,"500mg IV TID x 3 days; give BEFORE glucose to prevent precipitation of Wernicke"),
     "Magnesium Repletion":tc(60,"Thiamine cannot be utilized without adequate magnesium"),
     "Glucose":tc(30,"Only AFTER thiamine administration; D50 if hypoglycemic")},
    {"Alcohol Use":{"ast":{"min":50,"max":300},"mg":{"min":0.5,"max":1.2}}})

NEW["Central Cord Syndrome"] = dx("Neurological","Neurological/MSK",v(72,115,72,16,98.6,97),
    STD,{"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Upper extremity weakness greater than lower (cape distribution), bladder dysfunction, variable sensory loss below level; typically hyperextension injury in elderly with cervical spondylosis",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"hgb":lab(10,16,"g/dL","normal"),"cr":lab(0.6,2.0,"mg/dL","variable"),"lactate":lab(1.0,3.0,"mmol/L","variable")},
    ["IV Access","Continuous Monitoring"],
    {"C-Spine MRI":tc(120,"Emergent to evaluate cord compression and edema"),
     "C-Spine Immobilization":tc(1,"Immediate; rigid collar until imaging clears"),
     "MAP Target":tc(30,"Maintain MAP >85 for spinal cord perfusion per AANS"),
     "Neurosurgery Consult":tc(120,"Surgical decompression if significant cord compression")},{})

NEW["Anterior Cord Syndrome"] = dx("Neurological","Neurological/MSK",v(68,85,52,14,97.5,95),
    {**STD,"heart_rate":"inverse"},{"heart_rate":8,"systolic_bp":18,"o2_saturation":3},
    "Bilateral motor paralysis and loss of pain/temperature below lesion level; preserved proprioception and vibration (posterior columns spared); worst prognosis of incomplete SCI syndromes",
    {"o2_saturation_below":88,"systolic_bp_below":70},
    {"hgb":lab(8,16,"g/dL","variable"),"lactate":lab(1.5,5.0,"mmol/L","elevated"),"cr":lab(0.6,2.0,"mg/dL","variable")},
    ["IV Access","Fluid Resuscitation","Continuous Monitoring"],
    {"MRI Spine":tc(120,"Emergent; evaluate anterior spinal artery territory infarction vs compression"),
     "MAP Target":tc(30,"MAP >85 mmHg with pressors if needed"),
     "Surgical Consult":tc(120,"Consider emergent decompression if compressive etiology")},{})

NEW["Brown-Sequard Syndrome"] = dx("Neurological","Neurological/MSK",v(88,120,75,18,98.6,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Hemisection pattern: ipsilateral motor loss and proprioception loss, contralateral pain/temperature loss below lesion level; best prognosis of incomplete SCI syndromes",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"hgb":lab(8,16,"g/dL","variable"),"cr":lab(0.6,1.4,"mg/dL","normal"),"lactate":lab(1.0,3.0,"mmol/L","variable")},
    ["IV Access","Continuous Monitoring"],
    {"MRI Spine":tc(120,"Confirm hemisection pattern; evaluate for penetrating vs blunt etiology"),
     "C-Spine Immobilization":tc(1,"Immediate stabilization"),
     "Neurosurgery Consult":tc(120,"Surgical exploration if penetrating injury")},{})

NEW["Cerebral Aneurysm - Unruptured Symptomatic"] = dx("Neurological","Neurological",v(85,145,88,16,98.6,97),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Sentinel headache (warning leak), cranial nerve palsy (CN III with posterior communicating aneurysm → ptosis, mydriasis), visual symptoms",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(6,12,"K/uL","normal"),"cr":lab(0.6,1.4,"mg/dL","normal"),"pt_inr":lab(0.9,1.3,"INR","normal")},
    ["IV Access","Continuous Monitoring"],
    {"CTA Head":tc(60,"Identify aneurysm location and morphology"),
     "Neurosurgery/Neurointerventional Consult":tc(120,"Discuss clipping vs coiling based on aneurysm characteristics"),
     "BP Control":tc(30,"Avoid hypertension; target SBP <140 given rupture risk"),
     "Admission":tc(60,"Close monitoring; any new headache could represent rupture")},{})

NEW["Hydrocephalus - Acute"] = dx("Neurological","Neurological",v(58,170,98,12,98.6,96),
    CUSHING,{"heart_rate":10,"systolic_bp":10,"respiratory_rate":3,"o2_saturation":3},
    "Headache, vomiting, papilledema, upgaze palsy (setting sun sign), Cushing response (late), decreased consciousness; causes: tumor obstructing CSF, post-hemorrhagic, post-infectious",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"na":lab(135,155,"mEq/L","variable"),"cr":lab(0.6,2.0,"mg/dL","variable"),"wbc":lab(6,15,"K/uL","variable")},
    ["IV Access","Continuous Monitoring"],
    {"CT Head":tc(15,"Emergent; ventriculomegaly, periventricular edema, identify obstructive cause"),
     "EVD Placement":tc(60,"Emergent external ventricular drain by neurosurgery"),
     "ICP Management":tc(15,"HOB 30°, mannitol or 23.4% saline for acute herniation"),
     "Neurosurgery Consult":tc(30,"Emergent for EVD; definitive VP shunt or ETV later")},{})

NEW["Cerebral Edema"] = dx("Neurological","Neurological",v(60,175,100,10,98.6,95),
    CUSHING,{"heart_rate":10,"systolic_bp":10,"respiratory_rate":4,"o2_saturation":3},
    "Progressive obtundation, pupil asymmetry, posturing (decorticate→decerebrate), Cushing triad, cerebral herniation syndromes (uncal, central, tonsillar)",
    {"o2_saturation_below":88,"systolic_bp_below":75},
    {"na":lab(135,160,"mEq/L","variable"),"glu":lab(80,250,"mg/dL","variable"),
     "serum_osm":lab(280,320,"mOsm/kg","variable"),"cr":lab(0.6,3.0,"mg/dL","variable")},
    ["IV Access","Continuous Monitoring","Intubation","Oxygen Therapy"],
    {"Hyperosmolar Therapy":tc(15,"Mannitol 1g/kg or 23.4% NaCl 30mL for acute herniation"),
     "Intubation":tc(15,"Target PaCO2 35-40; brief hyperventilation to 30-35 ONLY for active herniation"),
     "CT Head":tc(15,"Identify cause and degree of shift"),
     "Neurosurgery Consult":tc(30,"Decompressive craniectomy if refractory; EVD for hydrocephalus")},{})

NEW["Pseudotumor Cerebri"] = dx("Neurological","Neurological",v(82,130,82,16,98.6,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Headache (worse with Valsalva, positional), papilledema, visual obscurations, pulsatile tinnitus, CN VI palsy; obese woman of childbearing age typical",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(6,12,"K/uL","normal"),"cr":lab(0.6,1.2,"mg/dL","normal"),"tsh":lab(0.4,4.0,"mIU/L","normal"),
     "csf_opening_pressure":lab(25,60,"cmH2O","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"MRI/MRV Brain":tc(240,"Rule out venous sinus thrombosis and structural causes; empty sella, tortuous optic nerves"),
     "Lumbar Puncture":tc(240,"Diagnostic AND therapeutic; elevated opening pressure with normal CSF composition"),
     "Acetazolamide":tc(240,"250-500mg BID; reduces CSF production; first-line medical therapy"),
     "Ophthalmology Consult":tc(240,"Formal visual field testing; monitor for progressive visual loss")},{})

NEW["Myasthenic Crisis vs Cholinergic Crisis"] = dx("Neurological","Neurological/Neuromuscular",v(105,125,78,24,98.6,92),
    STD,{"systolic_bp":10,"diastolic_bp":5,"o2_saturation":5},
    "Respiratory failure + weakness; DIFFERENTIATING: Myasthenic=dry, dilated pupils, worse with activity; Cholinergic=SLUDGE (salivation, lacrimation, urination, diarrhea, miosis), excess secretions",
    {"o2_saturation_below":85,"systolic_bp_below":80},
    {"wbc":lab(6,12,"K/uL","normal"),"cr":lab(0.6,1.4,"mg/dL","normal"),
     "k":lab(3.5,5.0,"mEq/L","normal"),"abg_pco2":lab(40,65,"mmHg","elevated")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring"],
    {"NIF/VC":tc(15,"NIF <-20 or VC <15mL/kg → intubate; trending is key"),
     "Edrophonium Test":tc(30,"2mg test dose → if improves = myasthenic crisis; if worsens = cholinergic crisis (rarely done now)"),
     "Hold All Cholinesterase Inhibitors":tc(15,"Stop pyridostigmine during crisis evaluation"),
     "IVIG or Plasmapheresis":tc(240,"Start definitive immunotherapy once myasthenic crisis confirmed")},{})

NEW["Spinal Epidural Abscess"] = dx("Neurological","Neurological/Infectious",v(105,120,75,18,102.0,96),
    STD,{"systolic_bp":10,"diastolic_bp":5,"o2_saturation":2},
    "Progressive back pain, fever, focal neurological deficit; classic triad: fever + spinal pain + neuro deficit (present <15% of cases); IVDU and diabetes are major risk factors",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"wbc":lab(12,28,"K/uL","elevated"),"esr":lab(50,120,"mm/hr","elevated"),"crp":lab(5.0,25.0,"mg/dL","elevated"),
     "cr":lab(0.6,2.0,"mg/dL","variable"),"blood_cx":lab(1,1,"positive","elevated")},
    ["IV Access","Antibiotics","Continuous Monitoring"],
    {"MRI Spine with Contrast":tc(120,"Most sensitive; gadolinium-enhancing epidural collection"),
     "IV Antibiotics":tc(60,"Vancomycin + cefepime or meropenem; MRSA coverage essential"),
     "Neurosurgery Consult":tc(120,"Emergent surgical drainage if neurological deficits present or progressing"),
     "Blood Cultures":tc(60,"Before antibiotics; Staph aureus most common organism")},
    {"IVDU":{"risk":"MRSA, endocarditis workup"},"Diabetes":{"glu":{"min":150,"max":400}}})

NEW["Acute Disseminated Encephalomyelitis"] = dx("Neurological","Neurological",v(105,115,72,18,101.0,96),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Polyfocal neurological deficits days after viral illness or vaccination; encephalopathy, bilateral optic neuritis, transverse myelitis, cerebellar signs; predominantly pediatric",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"wbc":lab(8,18,"K/uL","variable"),"csf_wbc":lab(10,200,"cells/uL","elevated"),
     "csf_protein":lab(50,150,"mg/dL","elevated"),"crp":lab(1.0,10.0,"mg/dL","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"MRI Brain/Spine":tc(120,"Large, bilateral, fluffy white matter lesions; may enhance with gadolinium"),
     "IV Methylprednisolone":tc(240,"30mg/kg/day (max 1g) x 3-5 days; first-line"),
     "IVIG":tc(0,"If steroid-refractory; 2g/kg over 2-5 days"),
     "Plasmapheresis":tc(0,"Third-line if no response")},{})

NEW["Tension Headache"] = dx("Neurological","Neurological",v(78,130,80,16,98.6,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Bilateral pressing/tightening headache, mild-moderate intensity, not aggravated by physical activity; no nausea/photophobia/phonophobia (≤1 of these); pericranial tenderness",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(5,11,"K/uL","normal"),"cr":lab(0.6,1.2,"mg/dL","normal")},
    ["Continuous Monitoring"],
    {"Clinical Diagnosis":tc(0,"History-based; no imaging needed unless red flags present"),
     "Analgesics":tc(30,"NSAIDs or acetaminophen first-line; avoid opioids and barbiturates"),
     "Red Flag Assessment":tc(15,"Thunderclap onset, fever, focal deficits, papilledema → further workup")},{})

NEW["Migraine - Acute Severe"] = dx("Neurological","Neurological",v(85,140,85,16,98.6,98),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":1},
    "Unilateral throbbing headache, nausea/vomiting, photophobia, phonophobia, worse with activity; may have aura (visual most common); status migrainosus if >72h",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(5,12,"K/uL","normal"),"cr":lab(0.6,1.2,"mg/dL","normal"),"mg":lab(1.5,2.5,"mg/dL","normal")},
    ["IV Access","Continuous Monitoring"],
    {"IV Antiemetic":tc(15,"Metoclopramide 10mg or prochlorperazine 10mg IV; dual action as both antiemetic and abortive"),
     "IV Ketorolac":tc(30,"30mg IV; effective abortive; avoid in renal disease"),
     "IV Magnesium":tc(30,"2g IV over 15min especially if with aura"),
     "CT Head":tc(60,"Only if first/worst headache, thunderclap onset, focal deficits, or red flags")},{})

NEW["Cluster Headache - Acute"] = dx("Neurological","Neurological",v(88,145,88,18,98.6,98),
    {**STD,"systolic_bp":"multiply"},{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "Severe unilateral periorbital pain, ipsilateral lacrimation, conjunctival injection, ptosis, miosis, nasal congestion/rhinorrhea; patient restless/agitated (opposite of migraine)",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"wbc":lab(5,12,"K/uL","normal"),"cr":lab(0.6,1.2,"mg/dL","normal")},
    ["Oxygen Therapy","Continuous Monitoring"],
    {"High-Flow Oxygen":tc(5,"100% O2 at 12-15 L/min via NRB x 15min; first-line treatment; 78% response rate"),
     "Subcutaneous Sumatriptan":tc(15,"6mg SC; fastest pharmacologic abortive; contraindicated in CAD"),
     "Verapamil":tc(0,"First-line preventive during cluster period; 240-960mg/day with ECG monitoring")},{})

NEW["Seizure - New Onset"] = dx("Neurological","Neurological",v(110,155,90,20,99.0,95),
    {**STD,"systolic_bp":"multiply"},{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":3},
    "Witnessed tonic-clonic activity, post-ictal confusion and drowsiness, tongue laceration, incontinence; postictal Todd paralysis may mimic stroke",
    {"o2_saturation_below":88,"systolic_bp_below":80},
    {"glu":lab(60,250,"mg/dL","variable"),"na":lab(125,148,"mEq/L","variable"),"ca":lab(7.5,10.5,"mg/dL","variable"),
     "mg":lab(1.2,2.5,"mg/dL","variable"),"k":lab(3.0,5.5,"mEq/L","variable"),
     "wbc":lab(8,18,"K/uL","variable"),"lactate":lab(2.0,8.0,"mmol/L","elevated"),
     "prolactin":lab(20,100,"ng/mL","elevated"),"ck":lab(100,5000,"U/L","elevated")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring"],
    {"POC Glucose":tc(5,"Immediate; hypoglycemia is reversible cause"),
     "CT Head":tc(60,"Non-contrast to rule out structural/hemorrhagic cause"),
     "BMP":tc(30,"Electrolyte derangement workup: Na, Ca, Mg, glucose"),
     "EEG":tc(0,"Routine outpatient if first unprovoked seizure; urgent if concern for NCSE")},
    {"Alcohol Use":{"mg":{"min":0.8,"max":1.5},"glu":{"min":40,"max":80}}})

NEW["Non-Convulsive Status Epilepticus"] = dx("Neurological","Neurological",v(90,140,85,16,98.6,96),
    STD,{"systolic_bp":8,"diastolic_bp":5,"o2_saturation":2},
    "Altered mental status without obvious motor seizure activity; subtle signs: eye deviation, nystagmus, facial twitching, automatisms; diagnosis REQUIRES EEG",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"glu":lab(70,200,"mg/dL","variable"),"na":lab(128,148,"mEq/L","variable"),"ammonia":lab(20,100,"mcg/dL","variable"),
     "wbc":lab(6,15,"K/uL","variable"),"lactate":lab(1.0,4.0,"mmol/L","variable")},
    ["IV Access","Continuous Monitoring"],
    {"Continuous EEG":tc(60,"ONLY way to diagnose NCSE; should be obtained urgently for unexplained AMS"),
     "Benzodiazepine Trial":tc(15,"Lorazepam 0.1mg/kg IV; clinical and EEG improvement confirms diagnosis"),
     "Metabolic Workup":tc(30,"BMP, ammonia, hepatic panel, tox screen; rule out mimics"),
     "Antiepileptic Loading":tc(60,"Levetiracetam 60mg/kg or valproate 40mg/kg IV after benzo trial")},{})

NEW["Temporal Arteritis"] = dx("Neurological","Neurological/Rheumatologic",v(82,140,85,16,99.5,98),
    STD,{"systolic_bp":5,"diastolic_bp":3,"o2_saturation":1},
    "New headache in patient >50, temporal artery tenderness with decreased pulsation, jaw claudication, visual symptoms (amaurosis fugax → permanent blindness), scalp tenderness, PMR symptoms",
    {"o2_saturation_below":92,"systolic_bp_below":85},
    {"esr":lab(50,120,"mm/hr","elevated"),"crp":lab(3.0,25.0,"mg/dL","elevated"),
     "plt":lab(300,600,"K/uL","elevated"),"hgb":lab(9,13,"g/dL","decreased"),
     "alk_phos":lab(80,200,"U/L","elevated")},
    ["IV Access","Continuous Monitoring"],
    {"High-Dose Prednisone":tc(60,"1mg/kg/day (max 60mg); START IMMEDIATELY — do NOT wait for biopsy; visual loss is irreversible"),
     "Temporal Artery Biopsy":tc(336,"Within 2 weeks of steroid start; skip lesions → need adequate length (>1cm)"),
     "Ophthalmology Consult":tc(120,"Urgent if visual symptoms; fundoscopy for optic disc pallor"),
     "IV Methylprednisolone":tc(30,"1g IV x 3 days if visual loss already present; then oral prednisone")},{})

NEW["Autonomic Dysreflexia"] = dx("Neurological","Neurological",v(55,210,120,14,98.6,96),
    {**STD,"heart_rate":"inverse","systolic_bp":"multiply","diastolic_bp":"multiply"},
    {"heart_rate":10,"systolic_bp":10,"diastolic_bp":8,"o2_saturation":2},
    "In SCI patients at T6 or above: severe paroxysmal hypertension, reflex bradycardia, pounding headache, flushing/sweating above lesion level, piloerection, nasal congestion",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"cr":lab(0.6,3.0,"mg/dL","variable"),"k":lab(3.5,5.5,"mEq/L","variable"),"ua_wbc":lab(0,50,"/HPF","variable")},
    ["Continuous Monitoring"],
    {"Sit Patient Up":tc(1,"Immediately sit patient upright to use orthostatic effects to lower BP"),
     "Identify Noxious Stimulus":tc(10,"Most common: bladder distension (blocked catheter) → straight cath or flush; fecal impaction → disimpact with lidocaine jelly"),
     "Nifedipine":tc(15,"10mg bite-and-swallow or nitropaste 1 inch above lesion if SBP >150 after stimulus removed"),
     "Loosen Clothing":tc(2,"Remove any tight clothing, abdominal binders, compression stockings below level of injury")},{})

NEW["Posterior Reversible Encephalopathy Syndrome"] = dx("Neurological","Neurological",v(90,195,115,18,98.6,96),
    {**STD,"systolic_bp":"multiply","diastolic_bp":"multiply"},{"systolic_bp":10,"diastolic_bp":8,"o2_saturation":2},
    "Headache, altered mental status, seizures, visual disturbances (cortical blindness), associated with severe hypertension, eclampsia, immunosuppressants, renal failure",
    {"o2_saturation_below":90,"systolic_bp_below":80},
    {"cr":lab(0.8,4.0,"mg/dL","variable"),"na":lab(130,148,"mEq/L","variable"),
     "plt":lab(50,300,"K/uL","variable"),"ldh":lab(200,1000,"U/L","variable")},
    ["IV Access","Continuous Monitoring"],
    {"MRI Brain":tc(120,"FLAIR hyperintensity in posterior parieto-occipital white matter; DWI typically negative (vasogenic not cytotoxic edema)"),
     "BP Control":tc(30,"Gradual reduction; target 25% reduction in first few hours"),
     "Seizure Management":tc(30,"Levetiracetam or lorazepam; magnesium if eclampsia-related"),
     "Remove Offending Agent":tc(60,"Stop cyclosporine, tacrolimus, or other causative immunosuppressant if applicable")},{})

NEW["Amyotrophic Lateral Sclerosis - Respiratory Crisis"] = dx("Neurological","Neurological/Neuromuscular",v(100,130,80,24,98.6,90),
    STD,{"systolic_bp":10,"diastolic_bp":5,"o2_saturation":5},
    "Progressive dyspnea, weak cough, inability to clear secretions, orthopnea, morning headaches (CO2 retention), mixed UMN/LMN signs, fasciculations, bulbar weakness",
    {"o2_saturation_below":85,"systolic_bp_below":80},
    {"abg_pco2":lab(45,70,"mmHg","elevated"),"hco3":lab(28,38,"mEq/L","elevated"),
     "cr":lab(0.3,0.8,"mg/dL","decreased"),"alb":lab(2.5,4.0,"g/dL","variable")},
    ["IV Access","Oxygen Therapy","Continuous Monitoring"],
    {"NIF/VC Assessment":tc(15,"FVC <50% predicted or NIF <-40 → discuss BiPAP; <25% → discuss tracheostomy"),
     "BiPAP Initiation":tc(30,"Non-invasive ventilation improves survival and quality of life"),
     "Advance Directive Discussion":tc(0,"CRITICAL: establish goals of care regarding intubation before crisis"),
     "Secretion Management":tc(30,"Cough assist device, glycopyrrolate for secretions, suction PRN")},{})

NEW["Parkinson Disease - Acute Akinetic Crisis"] = dx("Neurological","Neurological",v(110,90,55,22,103.5,94),
    STD,{"systolic_bp":15,"diastolic_bp":10,"o2_saturation":3},
    "Severe rigidity, hyperthermia, autonomic instability, dysphagia/aspiration risk, rhabdomyolysis; triggered by sudden withdrawal or reduction of dopaminergic medications; resembles NMS",
    {"o2_saturation_below":88,"systolic_bp_below":75},
    {"ck":lab(500,50000,"U/L","elevated"),"cr":lab(1.0,5.0,"mg/dL","elevated"),
     "wbc":lab(10,20,"K/uL","elevated"),"k":lab(4.0,7.0,"mEq/L","elevated"),
     "lactate":lab(2.0,8.0,"mmol/L","elevated")},
    ["IV Access","Fluid Resuscitation","Continuous Monitoring"],
    {"Resume Dopaminergic Meds":tc(30,"NG tube administration of levodopa/carbidopa if unable to swallow"),
     "IV Fluids":tc(30,"Aggressive NS to prevent rhabdomyolysis-induced AKI"),
     "Active Cooling":tc(15,"If hyperthermic; same approach as NMS"),
     "Dantrolene":tc(60,"1-2.5mg/kg IV if severe rigidity and hyperthermia unresponsive to dopaminergic therapy")},{})

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
print(f"Added {added} neurological diagnoses. Total: {len(data['diagnoses'])}")
for c in sorted(cats):
    print(f"  {c}: {len(cats[c])}")

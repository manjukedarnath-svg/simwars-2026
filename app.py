from flask import Flask, request, send_file, render_template_string, jsonify, redirect, session
import io
import os
import sqlite3
from docx import Document

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'scores.db'))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS scores
                        (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()

init_db()

def _get_weasyprint():
    try:
        from weasyprint import HTML as WeasyHTML
        return WeasyHTML
    except Exception:
        return None

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'simwars-2026-change-me')

ORGANISER_PASSWORD = '@MSPtrio2023sim'
JUDGE_PASSWORD = '@SIMblore2014'

UNLOCK_TEMPLATE = '''
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>SimWars — Enter Password</title>
<style>
body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f172a;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;}
.card{background:#1e293b;padding:32px 36px;border-radius:14px;max-width:360px;width:90%;box-shadow:0 10px 40px rgba(0,0,0,.4);}
h1{font-size:1.1rem;margin:0 0 6px;}
p{color:#94a3b8;font-size:0.85rem;margin:0 0 18px;}
input{width:100%;box-sizing:border-box;padding:10px 12px;border-radius:8px;border:1px solid #334155;background:#0f172a;color:#fff;font-size:0.95rem;margin-bottom:12px;}
button{width:100%;padding:10px;border:none;border-radius:8px;background:#7C3AED;color:#fff;font-weight:700;cursor:pointer;font-size:0.9rem;}
.err{color:#f87171;font-size:0.82rem;margin-bottom:10px;}
</style></head>
<body>
<form class="card" method="post">
<h1>🔒 Organisers & Judges Only</h1>
<p>Enter your Organiser or Judge password to continue.</p>
{% if error %}<div class="err">Incorrect password. Try again.</div>{% endif %}
<input type="password" name="password" placeholder="Password" autofocus autocomplete="off">
<button type="submit">Unlock</button>
</form>
</body></html>
'''

def require_role():
    if session.get('role') not in ('organiser', 'judge'):
        return redirect('/unlock?next=' + request.path)
    return None

@app.route('/unlock', methods=['GET', 'POST'])
def unlock():
    next_url = request.args.get('next') or request.form.get('next') or '/library'
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if pw == ORGANISER_PASSWORD:
            session['role'] = 'organiser'
            return redirect(next_url)
        elif pw == JUDGE_PASSWORD:
            session['role'] = 'judge'
            return redirect(next_url)
        return render_template_string(UNLOCK_TEMPLATE, error=True)
    return render_template_string(UNLOCK_TEMPLATE, error=False)

# ============================================
# CASE DATA (All 8 Cases)
# ============================================
CASES = [
    {
        "id": "B1",
        "round": "ROUND ONE",
        "title": "Near Drowning / Submersion with VT Arrest",
        "summary": "12-year-old female (30 kg) was submerged in seawater. Rescuers gave rescue breaths and rushed her to ER. She is unresponsive, hypothermic (35°C), and in Pulseless VT arrest. The team must recognize shockable rhythm, start high-quality CPR, defibrillate, manage hypothermia, and correct hyperkalemia.",
        "background": "12-year-old girl was on a trip with friends in Goa. She was pulled from the water after submersion. She was unresponsive. Rescuers gave a few rescue breaths and rushed her to the ER.",
        "expanded_history": "Previously well, developmentally normal. No known medical conditions.",
        "stages": [
            {"name": "Stage 1: Initial Assessment", "vitals": "HR: 187, RR: 5, BP: Non-recordable, SpO2: 54% (RA), T: 35°C, ECG: Ventricular Tachycardia", "condition": "Unresponsive, wet clothes, cold peripheries. Poor chest rise.", "expected": "Recognize cardioresp. arrest. Call for help. Start BVM with 100% O2. Apply monitors.", "notes": "If BVM started → proceed. If not → rapid desat."},
            {"name": "Stage 2: Pulseless VT", "vitals": "HR: 187, BP: Non-recordable, SpO2: 54%, ECG: VT (no pulse)", "condition": "Pulseless. Cold, clammy.", "expected": "Start high-quality CPR (15:2). Attempt IV/IO access. Prepare defibrillator.", "notes": "CPR coach monitors depth, rate, recoil."},
            {"name": "Stage 3: Critical Decision Point", "vitals": "HR: 187, BP: Non-recordable, SpO2: 54%, ECG: VT", "condition": "Hypothermic. Labs: K 4.5, Na 130, Lactate 6.", "expected": "Branch A (Correct): Defibrillate 2J/kg → Resume CPR → Adrenaline → Fluid bolus (20ml/kg) → Warming measures.\nBranch B (Incorrect): Give Adrenaline without defibrillation OR delay CPR.", "notes": "If Defib + CPR → Stage 4A (ROSC). If Adrenaline first / no shock → Stage 4B."},
            {"name": "Stage 4: Outcome", "vitals": "4A (ROSC): HR 87, BP 84/50, Sinus rhythm. 4B (Arrest): Asystole/Refractory VT.", "condition": "4A: Sinus rhythm, SpO2 92%. 4B: Asystole / Refractory VT.", "expected": "4A: Post-arrest care, continue warming, shift to PICU. 4B: Continue CPR per algorithm.", "notes": "End scenario."}
        ],
        "patient": {"name": "Vaibhavi", "mrn": "5501", "gender": "Female", "age": "12 years", "dob": "15-06-2012", "height": "145 cm", "weight": "30 kg", "cc": "Unresponsive after drowning", "hpi": "Submerged in seawater, pulled out by rescuers. Received rescue breaths at site. Rushed to ER.", "pmh": "None. Developmentally normal.", "psh": "None.", "meds": "Nil.", "allergies": "None.", "family": "Trip with friends. No significant family history."},
        "actors": "Lifeguard/Rescuer (optional, can provide handover). Nurse helps with monitors and IV access.",
        "equipment": "Simulator (pediatric), ECG monitor, Pulse oximeter, Defibrillator, BVM, Airway kit, IV/IO supplies, Fluid warmer, Warming blankets, Crash cart."
    },
    {
        "id": "B2",
        "round": "ROUND ONE",
        "title": "PEA Arrest in a Child with Dilated Cardiomyopathy",
        "summary": "11-year-old male with known Dilated Cardiomyopathy (DCM) presents with 2-day history of fever and respiratory distress. He develops Torsades de Pointes and progresses to PEA arrest. The team must recognize Torsades, administer Magnesium sulfate, correct hypokalemia (K 2.5) and hypocalcemia (iCa 0.8), and perform high-quality CPR.",
        "background": "11-year-old male Varsha presents to the Pediatric ER with severe breathing difficulty. He is brought by his parent who gives a history of fever, cough, and cold for 2 days. He has become very dull and his response has decreased.",
        "expanded_history": "Known case of Dilated Cardiomyopathy (DCM) diagnosed 2 years ago. On medications (details not known to parents). Non-compliant with medications recently.",
        "stages": [
            {"name": "Stage 1: Initial Assessment", "vitals": "HR: 180, RR: 10, BP: 84/40, SpO2: 77% (RA), ECG: Sinus tach with ectopics", "condition": "Drowsy, poor response. Tachypneic. Fever (T 98.5°F).", "expected": "Recognize cardiogenic shock / pre-arrest. Start BVM. Apply monitors. Obtain IV access.", "notes": "If BVM started → proceed. If not → rapid deterioration."},
            {"name": "Stage 2: Decompensation (Torsades/PEA)", "vitals": "HR: 178, RR: 6, BP: 77/50, SpO2: 84%, ECG: Torsades", "condition": "Unresponsive. Flaring. No pulse.", "expected": "Start high-quality CPR. Recognize Torsades without pulse.", "notes": "CPR quality monitored."},
            {"name": "Stage 3: Critical Decision Point", "vitals": "HR: 45, BP: 70/45, SpO2: 78%, ECG: PEA", "condition": "Labs: K 2.5, iCa 0.8.", "expected": "Branch A (Correct): Give Magnesium sulfate 50mg/kg IV + Fluid bolus → Continue CPR → Correct hypokalemia & hypocalcemia.\nBranch B (Incorrect): Give unsynchronized shock OR Adrenaline without Mg.", "notes": "If Mg + CPR → Stage 4A (ROSC). If no Mg / only shock → Stage 4B (Asystole)."},
            {"name": "Stage 4: Outcome", "vitals": "4A (ROSC): HR 87, BP 84/50, Sinus rhythm. 4B (Arrest): Asystole.", "condition": "4A: Sinus rhythm, SpO2 92%. 4B: Asystole.", "expected": "4A: Stabilize, shift to PICU. 4B: Continue CPR per algorithm.", "notes": "End scenario."}
        ],
        "patient": {"name": "Varsha", "mrn": "5525", "gender": "Male", "age": "11 years", "dob": "05-11-2013", "height": "140 cm", "weight": "30 kg", "cc": "Breathing difficulty and dullness", "hpi": "Fever and cough for 2 days. Progressive dullness and decreased response.", "pmh": "Dilated Cardiomyopathy (DCM), diagnosed 2 years ago.", "psh": "None.", "meds": "Unknown (parents non-compliant).", "allergies": "None.", "family": "Parents present."},
        "actors": "Parent provides limited history. Nurse assists with CPR and medications.",
        "equipment": "Simulator (pediatric), ECG monitor, Defibrillator, BVM, IV/IO supplies, Magnesium sulfate, Calcium gluconate, Crash cart."
    },
    {
        "id": "B3",
        "round": "ROUND ONE",
        "title": "Electrocution with VT Arrest",
        "summary": "13-year-old male (30 kg) found unconscious at a construction site after electrical injury. He has burn marks on his right hand and left leg. He is in Pulseless VT arrest with severe hyperkalemia (K 7.5). The team must recognize hyperkalemia, administer Calcium, defibrillate, and manage the burn injury.",
        "background": "13-year-old boy was found unconscious at a construction site. Ambulance crew gave some CPR and brought him to the ER. He has shallow, irregular breaths.",
        "expanded_history": "Sustained burn injury on the right hand and left leg – likely from an electrical wire. No known medical conditions.",
        "stages": [
            {"name": "Stage 1: Initial Assessment", "vitals": "HR: 150, RR: 5, BP: 70/36, SpO2: 75% (RA), ECG: Sinus tach with peaked T, PVCs", "condition": "Unresponsive. Burns on hand/leg. Poor GCS.", "expected": "Recognize electrical injury + hyperkalemia. Start BVM. Apply monitors. Fluid bolus.", "notes": "If BVM + fluid bolus started → Stage 2. If not → Asystole (4B)."},
            {"name": "Stage 2: Pulseless VT", "vitals": "HR: 177, RR: 8, BP: 88/67, SpO2: 92%, ECG: VT", "condition": "Pulseless. No pulses.", "expected": "Start high-quality CPR. Recognize shockable rhythm.", "notes": "CPR quality monitored."},
            {"name": "Stage 3: Critical Decision Point", "vitals": "HR: 177, BP: 88/67, SpO2: 92%, ECG: VT", "condition": "Hyperkalemia. Labs: K 7.5, pH 7.02, Lactate 6. Repeat: pH 7.00, Lactate 9.", "expected": "Branch A (Correct): Defibrillate 2J/kg → Resume CPR → Calcium gluconate → Insulin/Glucose → Bicarbonate.\nBranch B (Incorrect): Give Adrenaline without Calcium / no defibrillation.", "notes": "If Defib + Calcium → 4A. If Adrenaline first / no Ca → 4B."},
            {"name": "Stage 4: Outcome", "vitals": "4A (ROSC): HR 150, BP 80/45, Sinus rhythm. 4B (Arrest): Refractory VT.", "condition": "4A: Sinus rhythm, SpO2 92%. 4B: Refractory VT/Asystole.", "expected": "4A: Stabilize, treat burns, shift to PICU. 4B: Continue CPR.", "notes": "End scenario."}
        ],
        "patient": {"name": "Arush", "mrn": "5526", "gender": "Male", "age": "13 years", "dob": "20-08-2011", "height": "150 cm", "weight": "30 kg", "cc": "Unconscious after electrical injury", "hpi": "Found at construction site. Electrical wire contact.", "pmh": "None.", "psh": "None.", "meds": "Nil.", "allergies": "None.", "family": "Construction site worker."},
        "actors": "Ambulance crew provides handover. Nurse assists with IV/IO and medications.",
        "equipment": "Simulator (pediatric), ECG monitor, Defibrillator, BVM, IV/IO supplies, Calcium gluconate, Insulin, Dextrose, Bicarbonate, Burn dressings, Crash cart."
    },
    {
        "id": "B4",
        "round": "ROUND ONE",
        "title": "Refractory Status Epilepticus with Respiratory Arrest",
        "summary": "12-year-old female with high-grade fever and seizures. She received Lorazepam and Leviteracetam at a local hospital but continues seizing. She develops respiratory arrest and PEA. The team must manage status epilepticus, recognize raised ICP (pupillary changes), and provide anticonvulsants, 3% NaCl/Mannitol, and intubation.",
        "background": "12-year-old Sita was brought in with active generalized seizures. She has been seizing on and off for the last 1 hour. Referred from an outside hospital.",
        "expanded_history": "Previously well. Recent trip to native place (Matheran). High-grade fever for 1 day. Seizures started at home. Received Lorazepam, Phosphenytoin, and Leviteracetam at local hospital.",
        "stages": [
            {"name": "Stage 1: Initial Assessment", "vitals": "HR: 176, RR: 12, BP: 108/60, T: 103°F, SpO2: 74% (RA), ECG: Sinus tach", "condition": "Active seizures, pooling of oral secretions. Gurgling sounds. Stridor.", "expected": "Recognize Status Epilepticus. Call for help. Start BVM. Suction airway. Apply monitors.", "notes": "If BVM started → SpO2 improves. If not → resp. arrest (Stage 2)."},
            {"name": "Stage 2: Respiratory Arrest / PEA", "vitals": "HR: 54, RR: 0 (on BMV), BP: 60/40, SpO2: 78%, ECG: PEA", "condition": "Unconscious. Not responding. PEA on ECG. Pupils equal initially.", "expected": "Start CPR. Administer 1st line anticonvulsant (Lorazepam). Prepare for intubation.", "notes": "If CPR started + anticonvulsant → proceed. If delay → 4B."},
            {"name": "Stage 3: Critical Decision Point", "vitals": "HR: 22, RR: 0, BP: NR, SpO2: NR, ECG: PEA/Asystole", "condition": "Pupils become unequal → Raised ICP. Labs: Na 125, Lactate 6.", "expected": "Branch A (Correct): Give 3% NaCl / Mannitol → Continue anticonvulsants (Phenobarb/Valproate) → RSI intubation → Head elevation.\nBranch B (Incorrect): Delay intubation OR fail to recognize raised ICP.", "notes": "If correct ICP measures + intubation → 4A. If delay → 4B."},
            {"name": "Stage 4: Outcome", "vitals": "4A (ROSC): HR 100, BP 90/66, Sinus rhythm. 4B (Arrest): Asystole.", "condition": "4A: Sinus rhythm, intubated, SpO2 95%. 4B: Asystole.", "expected": "4A: Stabilize, continue ICP management, shift to PICU. 4B: Continue CPR.", "notes": "End scenario."}
        ],
        "patient": {"name": "Sita", "mrn": "5527", "gender": "Female", "age": "12 years", "dob": "15-05-2012", "height": "148 cm", "weight": "30 kg", "cc": "Seizures and fever", "hpi": "High-grade fever for 1 day. Seizures started at home. Referred from local hospital after receiving anticonvulsants.", "pmh": "Previously well.", "psh": "None.", "meds": "Nil (received Lorazepam, Phosphenytoin, Leviteracetam at referral).", "allergies": "None.", "family": "Recent trip to native place."},
        "actors": "Mother provides history when asked. Nurse prompts for pupillary check and ICP measures if missed.",
        "equipment": "Simulator (pediatric), ECG monitor, BVM, Suction, IV/IO supplies, Anticonvulsants, Mannitol/3% NaCl, Airway kit, Crash cart."
    },
    {
        "id": "P1",
        "round": "ROUND TWO",
        "title": "Cardiogenic Shock (Fulminant Myocarditis)",
        "summary": "1-year-old previously well child (10 kg) with rapid history of breathing difficulty and signs of progressive shock following a minor upper respiratory illness. Child is in acute cardiogenic shock following fulminant myocarditis. The team must avoid the 'fluid trap' (20ml/kg will cause pulmonary edema), start inotropes (Adrenaline), and perform synchronized cardioversion for VT.",
        "background": "1-year-old girl Sita, previously well, brought with coryza for 4 days, cough for 2 days, decreased feeding and breathing difficulty. Admitted at local hospital for acute bronchiolitis. Referred for respiratory support.",
        "expanded_history": "Previously well. Progressed to chest pain, lethargy, poor feeding. No urine for 7-8 hours. Weight = 10 kg. Elder sibling is a known asthmatic.",
        "stages": [
            {"name": "Stage 1: Initial Assessment", "vitals": "HR: 170, RR: 65, BP: 74/50, SpO2: 88% (RA), ECG: Sinus tach with PVCs", "condition": "Drowsy, grunting. Pale, gallop rhythm. Liver 3cm. Hepatomegaly.", "expected": "Recognize cardiogenic shock (vs. bronchiolitis). Start high-flow O2. Apply monitors. Obtain IV access.", "notes": "Nurse says '20ml/kg fluid?' (fluid trap). If fluid given → worsens (Stage 2)."},
            {"name": "Stage 2: Deterioration", "vitals": "HR: 201, RR: 80, BP: 55/40, SpO2: 92%, ECG: Sinus tach with PVCs", "condition": "Crepitations worsen. Liver 4cm. Gallop louder. Drowsy.", "expected": "Recognize fluid-refractory cardiogenic shock. HALT further fluids. Start inotropes (Adrenaline). Give diuretics (Frusemide).", "notes": "If Adrenaline started → Stage 3. If further fluids → 4B."},
            {"name": "Stage 3: Critical Decision Point", "vitals": "HR: 186, RR: 66, BP: 80/55, SpO2: 88%, ECG: VT with pulse", "condition": "VT with pulse. Labs: pH 7.22, Lactate 8, Na 131, K 5.4.", "expected": "Branch A (Correct): Synchronized cardioversion 0.5J/kg → Continue Adrenaline → Prepare RSI (Ketamine + Rocuronium).\nBranch B (Incorrect): Unsynchronized defibrillation OR Amiodarone without shock.", "notes": "If synchronized shock → 4A. If unsynchronized / no shock → 4B."},
            {"name": "Stage 4: Outcome", "vitals": "4A (Stable): HR 152, BP 85/50, Sinus rhythm. 4B (Arrest): Pulseless VT / Asystole.", "condition": "4A: Sinus rhythm, intubated, SpO2 94%. 4B: Pulseless VT / Asystole.", "expected": "4A: Stabilize, shift to PICU. 4B: Start CPR per algorithm.", "notes": "End scenario."}
        ],
        "patient": {"name": "Sita", "mrn": "5529", "gender": "Female", "age": "1 year", "dob": "20-10-2022", "height": "75 cm", "weight": "10 kg", "cc": "Coryza, cough, increased work of breathing, lethargy, poor feeding, poor urine output", "hpi": "Coryza for 4 days, cough for 2 days. Progressive breathing difficulty. Treated for bronchiolitis at local hospital. No urine for 7-8 hours.", "pmh": "Previously well.", "psh": "None.", "meds": "Nil.", "allergies": "None.", "family": "Elder sibling asthmatic. Parents very concerned."},
        "actors": "Parents very worried. Nurse gives wrong fluid bolus (20ml/kg instead of 10ml/kg) if asked.",
        "equipment": "Simulator (pediatric), ECG monitor, Defibrillator, BVM, IV supplies, Inotropes (Adrenaline), Diuretics, Airway kit, Crash cart."
    },
    {
        "id": "P2",
        "round": "ROUND TWO",
        "title": "Scorpion Sting Envenomation — Acute RV Strain and Diastolic Failure",
        "summary": "10-year-old male (30 kg) develops a scorpion-venom catecholamine storm after a red scorpion sting — acute RV strain with cold shock, clear lungs, and a raised JVP. The team must avoid large fluid boluses and noradrenaline, recognize the envenomation gestalt, and give Prazosin plus an inodilator to unload the RV before it progresses to biventricular failure.",
        "background": "Arjun, 10 years old, 30 kilos, brought in from a village about an hour away. He cried out in severe pain in his left foot around 2 a.m., followed by profuse sweating, vomiting, and frothing at the mouth. He is now very lethargic, breathing fast, and feels cold to the touch. The family saw a small, dark reddish-brown scorpion near his sleeping mat.",
        "expanded_history": "Previously fit and well. No known cardiac or respiratory illness. Lives in a rural area, sleeps on the floor. No known drug allergies. Up to date on routine immunisations. Mother reports excessive salivation (frothing) noted shortly after the sting, and severe, radiating pain from the sting site. No fever, no cough, no diarrhoea. No other family members unwell. No known toxin or drug ingestion. The scorpion was small and dark reddish-brown — consistent with Mesobuthus tamulus (red scorpion), endemic to this region.",
        "stages": [
            {"name": "Stage 1: Initial Assessment (0:00–2:00)", "vitals": "HR: 155, RR: 42, BP: 78/44, SpO2: 89% RA (91% on 15L NRB), CRT: 5s, GCS: 12 (E3 V4 M5)", "condition": "Cold, clammy, profuse diaphoresis. Pinpoint pupils. Sting mark + local erythema, left sole. Priapism noted. Hypersalivation (frothing). Clear lung fields. Elevated JVP. Tachycardic, loud P2, no murmur.", "expected": "Rapid ABCDE; identify low-output shock with clear lungs + raised JVP within the first minute. Recognize the envenomation gestalt: sting history + diaphoresis + priapism + hypersalivation + pinpoint pupils. Verbalize this is NOT septic or hypovolaemic shock. Request bedside POCUS (cardiac + lung) to confirm RV strain. Actively avoid a large (20ml/kg) fluid bolus — at most a small cautious test-dose with immediate reassessment.", "notes": "Shock is driven by a catecholamine (alpha-adrenergic) storm causing pulmonary vasoconstriction and acute RV strain — a reflexive large fluid bolus over-distends the RV and drops cardiac output further. Nurse prompt 0:30: 'His BP is very low, doctor. Should I open the fluids and give a 20ml/kg bolus?' — correct answer is caution/avoid."},
            {"name": "Stage 2: Inodilator / Antidote Window (2:00–5:00)", "vitals": "HR: 165, BP: 80/42, SpO2: 90% NRB, ECG: sinus tach, right-axis deviation, incomplete RBBB, T-wave inversions V1-V3", "condition": "Deteriorating shock from ongoing catecholamine storm — RV diastolic overload, LV still unaffected. POCUS (if requested): RV severely dilated (RV/LV ratio >1.5), D-shaped septum in diastole, IVC plethoric (<50% collapse), LV EF ~60%, no effusion. Lung POCUS: early B-lines.", "expected": "Diagnose catecholamine storm from red scorpion sting. Start Dobutamine 5-10mcg/kg/min or Milrinone — NOT noradrenaline or dopamine. Give Prazosin 30mcg/kg/dose (~1mg for 30kg) orally/NG, repeated per protocol. Do NOT give atropine for secretions.", "notes": "Noradrenaline here worsens pulmonary vasoconstriction and RV afterload and can precipitate collapse — avoid. Prazosin is the definitive bridge: counteracts the venom's alpha-effect and unloads the RV. Early inodilator + Prazosin → tracks to Stage 4A. Fluid bolus/noradrenaline/delayed Prazosin → tracks toward 4B/5. Nurse prompt 3:00: 'His heart rate is climbing and BP isn't improving. Should I draw up the Noradrenaline infusion?' — correct answer is NO."},
            {"name": "Stage 3: Scripted Deterioration (≈5:30)", "vitals": "Good branch: SpO2 dips to ~90%, recovers to 94% within 90s; HR peaks 178 then settles; BP holds ~90/58. Poor branch: HR falls to ~50 (agonal bradycardia) → PEA; BP/SpO2 unrecordable.", "condition": "Scripted deterioration fires for every team at ≈5:30, but severity is branch-dependent — a brief self-limiting dip for teams who blocked the catecholamine surge early, versus a bradycardic arrest (PEA) for teams who didn't.", "expected": "Branch A (Correct): Recognize this as the same catecholamine/RV process, not a new diagnosis. Escalate oxygen/airway support; if desaturating, prepare careful RSI (avoid ketamine's sympathomimetic push — favour etomidate or cautious reduced-dose induction; avoid heavy propofol/midazolam which risks profound hypotension). No arrest.\nBranch B (Incorrect): Fails to escalate support / arrests → PEA → start high-quality CPR, IV/IO adrenaline 0.01mg/kg every 3-5 min, reversible-causes review focused on RV failure/afterload (not hypovolaemia), avoid fluid boluses during CPR.", "notes": "Not branch-neutral — outcome is the direct consequence of Stage 1-2 management. Good branch → Stage 4A without CPR. Poor branch → CPR/ROSC → Stage 4B. No ROSC after 2 rounds → Stage 5 (capped). Nurse prompt 5:00: 'His oxygen saturation is dropping and he's losing consciousness. Do you want me to get the intubation trolley?' — correct answer is yes, with a hemodynamically cautious plan. Nurse prompt 7:00: 'Do you want me to call PICU and arrange a bed?' — correct answer is YES, with explicit dose handover."},
            {"name": "Stage 4: Outcome", "vitals": "4A (Stabilised — Isolated RV Strain): HR 120 sinus, BP 102/64 on Dobutamine, SpO2 94% NRB, CRT 3s, GCS 14-15. 4B (Post-ROSC — Combined Biventricular Failure): HR 130 post-ROSC, BP 88/54 on Dobutamine ± 2nd agent, SpO2 90% high-flow/NRB, GCS 10-12.", "condition": "4A: Sweating/priapism resolving; lungs clear with minimal basal crackles. Echo: improving RV size/function; LV never involved (EF preserved). 4B: Echo shows RV still dilated AND new LV hypokinesia — EF fallen to ~35-40%. Bibasal crackles — evolving pulmonary oedema.", "expected": "4A: Continue Dobutamine/Milrinone and oral/NG Prazosin maintenance. Consider Scorpion Antivenom (AScV) 1 vial IV over 30 min if available. PICU referral with explicit inotrope/alpha-blocker doses and transfer plan. Cardiology review at 24h. Structured SBAR handover.\n4B: Continue/escalate inotropic support (avoid pure alpha-agonists). Discuss ECMO referral if refractory. Urgent PICU transfer with explicit dosing. Post-arrest care bundle: temperature control, glucose, avoid hyperoxia. Honest family communication.", "notes": "End scenario. 4A: isolated RV strain recognized and treated before biventricular failure. 4B: reflects the real-world consequence of delayed recognition, fluid overload, or pressor misuse."},
            {"name": "Stage 5: Rescue (capped)", "vitals": "Refractory PEA/asystole despite 2 rounds of CPR + adrenaline.", "condition": "Persistent catecholamine-driven cardiovascular collapse, unresponsive to measures attempted so far.", "expected": "Continue high-quality CPR. Repeat adrenaline boluses. Consider bilateral needle decompression to exclude tension physiology. Consider ECMO if available.", "notes": "Automatic −10 Domain I penalty. Capped 45 seconds, then scripted stabilisation into Stage 4B."}
        ],
        "patient": {"name": "Arjun", "mrn": "5530", "gender": "Male", "age": "10 years", "dob": "12-04-2016", "height": "138 cm", "weight": "30 kg", "cc": "Sudden severe pain and swelling after scorpion sting; cold shock", "hpi": "Cried out in severe pain in his left foot around 2 a.m., followed by profuse sweating, vomiting, and frothing at the mouth. Now lethargic, breathing fast, and cold to touch. Family saw a small, dark reddish-brown scorpion near his sleeping mat.", "pmh": "Previously fit and well. No known cardiac or respiratory illness. No known drug allergies. Up to date on immunisations.", "psh": "None.", "meds": "Nil.", "allergies": "None known.", "family": "Mother present at bedside — frightened, provides history on request."},
        "actors": "Mother (confederate) — frightened, provides history on request, escalates if ignored, never obstructs care.",
        "equipment": "Simulator (pediatric), ECG monitor, Pulse oximeter, POCUS probe with propped cardiac/lung images (RV dilation, D-sign, plethoric IVC; branch-dependent CXRs), BVM, Airway/RSI kit, IV/IO supplies, Inotrope infusion pump (Dobutamine/Milrinone), Oral/NG Prazosin syringe prop, Scorpion antivenom (AScV) vial prop, Defibrillator/monitor, Crash cart."
    },
    {
        "id": "P3",
        "round": "ROUND TWO",
        "title": "Acute Severe Asthma with Pneumothorax",
        "summary": "3-year-old known asthmatic (parents stopped inhalers due to steroid phobia) presents in acute severe asthma. He deteriorates, requires intubation, and develops a right-sided pneumothorax post-intubation. The team must manage the asthma, recognize the pneumothorax, and perform needle decompression/chest tube insertion.",
        "background": "3-year-old male Arun presents with severe breathing difficulty. Parent gives history of 2-day fever and cough that worsened abruptly. Father has been giving home nebulisations for 24 hours (3 doses of Salbutamol). Child is in marked distress, cannot finish a sentence, and is moderately agitated.",
        "expanded_history": "Known case of Asthma diagnosed 1 year ago. Started on MDIs but parents stopped after 3 months due to steroid phobia. On homeopathy and home nebulisations since then. Parents are very agitated and do not believe in allopathy.",
        "stages": [
            {"name": "Stage 1: Initial Assessment", "vitals": "HR: 140, RR: 50, BP: 88/60, SpO2: 87% (RA), ECG: Sinus tach", "condition": "Agitated, cannot speak. Severe retractions, nasal flaring, wheeze.", "expected": "Recognize acute severe asthma. Start high-flow O2. Apply monitors. Start continuous Salbutamol + Ipratropium nebulizations.", "notes": "Parents angry (anti-allopathy). Nurse not pediatric-trained."},
            {"name": "Stage 2: Deterioration", "vitals": "HR: 166-170, RR: 62, BP: 84/50, SpO2: 84%, ECG: Sinus tach", "condition": "Drowsy, moaning. Quiet wheezes.", "expected": "Give IV steroids (Methylprednisolone 2mg/kg). Give Magnesium sulfate (50mg/kg). Consider Aminophylline/Terbutaline. Call PICU.", "notes": "If nebulizers + steroids + Mg given → Stage 3. If delayed → worsening."},
            {"name": "Stage 3: Critical Decision Point", "vitals": "HR: 99, RR: 16, BP: 80/45, SpO2: 78% (NIV), ECG: Sinus tach", "condition": "Minimal air entry. Labs: pH 7.10, PCO2 72, Lactate 5.", "expected": "Branch A (Correct): RSI intubation (Ketamine + Rocuronium) → Recognize right-sided pneumothorax (decreased air entry, hyper-resonance) → Needle decompression → Chest tube.\nBranch B (Incorrect): Delay intubation (>60 sec) OR fail to recognize pneumothorax.", "notes": "If correct intubation + pneumothorax drainage → 4A. If delayed / missed → 4B."},
            {"name": "Stage 4: Outcome", "vitals": "4A (Stable): HR 120, BP 90/50, Sinus rhythm. 4B (Arrest): Asystole / Tension pneumothorax.", "condition": "4A: Intubated, chest tube in situ, SpO2 93%. 4B: Asystole / Tension pneumo.", "expected": "4A: Stabilize, shift to PICU. 4B: Start CPR + needle decompression.", "notes": "End scenario."}
        ],
        "patient": {"name": "Arun", "mrn": "5531", "gender": "Male", "age": "3 years", "dob": "20-10-2020", "height": "89 cm", "weight": "10 kg", "cc": "Increased work of breathing", "hpi": "URI past few days. Worsened abruptly with severe cough. Home nebulisations ×3.", "pmh": "Diagnosed Asthma 1 year ago. Recurrent wheezy episodes. Started on MDIs, stopped after 3 months.", "psh": "None.", "meds": "Duolin home nebulisation.", "allergies": "None.", "family": "Parents very anxious, angry, and do not believe in allopathy."},
        "actors": "Parents very anxious and angry; provide some history if asked; over-dramatic. ER nurses not pediatric-trained.",
        "equipment": "Simulator (pediatric), ECG monitor, BVM, Nebulizers, Steroids, Magnesium, Airway kit, Needle decompression kit, Chest tube kit, Crash cart."
    },
    {
        "id": "P4",
        "round": "ROUND TWO",
        "title": "Refractory Septic Shock (Physiologically Difficult Airway)",
        "summary": "3-year-old female (15 kg) with refractory septic shock. She has zero physiologic reserve. The team must 'resuscitate before intubating,' avoid Propofol/Midazolam (use Ketamine + Rocuronium), prepare push-dose Epinephrine, and manage the post-intubation crash (reducing PEEP, giving push-dose Epi, fluid bolus).",
        "background": "3-year-old female Maya, previously healthy, presents with 3-day history of high fever, vomiting, and lethargy. Brought to the ED an hour ago and received 1×20ml/kg normal saline bolus. Now transferring to PICU.",
        "expanded_history": "Previously healthy. No known allergies. Parents describe progressive lethargy and poor feeding.",
        "stages": [
            {"name": "Stage 1: Initial Assessment", "vitals": "HR: 195, RR: 55, BP: 62/30, SpO2: 89% (NRB), ECG: Sinus tach", "condition": "Mottled, grunting. Cold extremities. Altered.", "expected": "Recognize fluid-refractory septic shock. Start high-flow O2. Apply monitors. Obtain 2nd IV/IO access. Give 2nd fluid bolus (10-20ml/kg).", "notes": "If 2nd fluid + inotrope → Stage 2. If focus on airway only → worsening."},
            {"name": "Stage 2: Recognition of Difficult Airway", "vitals": "HR: 185, BP: 68/35 (with vasoactives), SpO2: 92% (HFNC), ECG: Sinus tach", "condition": "Tiring.", "expected": "Start peripheral vasoactive infusion (Epinephrine/Norepinephrine). Recognize 'physiologically difficult airway'.", "notes": "Pre-oxygenate maximally. Prepare push-dose Epinephrine syringes."},
            {"name": "Stage 3: Critical Decision Point (Intubation)", "vitals": "HR: 185, BP: 68/35, SpO2: 92%, ECG: Sinus tach", "condition": "Labs: pH 7.12, Lactate 6.5. RT suggests Propofol/Fentanyl (trap).", "expected": "Branch A (Correct): Use Ketamine (1-2mg/kg) + Rocuronium (avoid Propofol/Midaz/Fentanyl) → Prepare push-dose Epi → Post-intubation: BP crashes → Push-dose Epi → Reduce PEEP → Fluid bolus.\nBranch B (Incorrect): Use Propofol/Midazolam OR fail to prepare push-dose Epi.", "notes": "If Ketamine + push-dose Epi → 4A. If Propofol / no push-dose → 4B (PEA)."},
            {"name": "Stage 4: Outcome", "vitals": "4A (Stable): HR 160, BP 75/40, Sinus rhythm. 4B (Arrest): PEA arrest.", "condition": "4A: Intubated, on inotropes, SpO2 94%. 4B: PEA / Cardiac arrest.", "expected": "4A: Stabilize, shift to PICU. 4B: Start CPR, give Adrenaline per PALS.", "notes": "End scenario."}
        ],
        "patient": {"name": "Maya", "mrn": "5532", "gender": "Female", "age": "3 years", "dob": "15-08-2020", "height": "90 cm", "weight": "15 kg", "cc": "Fever, vomiting, lethargy, breathing difficulty", "hpi": "3-day history of high fever, vomiting, and lethargy. Received 1×20ml/kg bolus in ED.", "pmh": "Previously healthy.", "psh": "None.", "meds": "Nil.", "allergies": "None.", "family": "Parents concerned."},
        "actors": "RT suggests using Propofol and Fentanyl (testing pharmacological discipline). Nurse asks if intubation meds should be pushed (tests pre-intubation briefing).",
        "equipment": "Simulator (pediatric), ECG monitor, BVM, HFNC/NIV, IV/IO supplies, Ketamine, Rocuronium, Push-dose Epinephrine syringes, Inotropes, Airway kit, Crash cart."
    },
    {
        "id": "SF1",
        "round": "SEMI-FINALS",
        "title": "The Quiet Head — Dual Paediatric Trauma",
        "summary": "Two siblings arrive simultaneously after a high-speed RTA. Ananya Rao (7y, 24kg) is initially talking — the classic lucid interval of an expanding right temporal extradural haematoma. Vihaan Rao (18mo, 10kg) cries loudly with a femoral fracture and trace FAST finding, but is haemodynamically stable. The team must simultaneously manage both patients, resist false reassurance from Ananya's initial calm presentation, read the outside CT report rather than accepting the father's verbal account, and escalate the neurological emergency in time.",
        "background": "You are the paediatric trauma team on duty. Two siblings from a high-speed RTA arrive simultaneously. Ananya (7y) had brief LOC, vomited once, and is increasingly sleepy. Vihaan (18mo) has no LOC but cries persistently with a deformed right leg. IV access in both pre-hospital. CT brain done outside — report with father.",
        "expanded_history": "Ananya Rao (7y, 24kg): Restrained rear-seat passenger. Head struck right window. Brief LOC then recovery. Hidden diagnosis: right temporal extradural haematoma, temporal bone fracture, mild pulmonary contusion, closed distal radius fracture.\n\nVihaan Rao (18mo, 10kg): Child restraint partially detached. No LOC. Persistent crying. Hidden diagnosis: closed right femoral shaft fracture, trace perihepatic free fluid on FAST.",
        "stages": [
            {"name": "Stage 1: Act I — Golden Minute (0:00–4:00)", "vitals": "Ananya: HR 118, RR 28, BP 112/72, SpO2 97% NRB, GCS 13, Pupils 3mm equal, Vihaan: HR 168, RR 42, BP 96/60, SpO2 96%", "condition": "Ananya: Lying quietly. Responds slowly. Blood over right temporal scalp. Right wrist swollen. Lucid interval — no deterioration yet.\n\nVihaan: Crying loudly. Right leg held still. Seatbelt bruising abdomen. FAST: minimal perihepatic free fluid — haemodynamically stable.", "expected": "Designate team leader · Allocate sub-group to each child · Simultaneous ABCDE on both · Monitors on both · C-spine maintained for Ananya · Baseline GCS and pupils documented for Ananya · Trauma bloods for both · FAST for Vihaan · Recognise mechanism-based red flags from handover (Ananya: LOC, vomiting, increasing sleepiness)", "notes": "Deliberate calm opening — the lucid interval must tempt false reassurance. No deterioration in this window. Nurse prompt 3:00 if bloods not sent. Vihaan's FAST: minimal free fluid = calibrated response required (surgical consult + serial exam, not theatre)."},
            {"name": "Stage 2: Reassessment — GCS Trend + Parents Arrive (4:00–5:30)", "vitals": "Ananya: HR 100, BP 132/82, GCS 11 (E2V4M5), Pupils R4mm sluggish L3mm, Vihaan: HR 148, BP 96/60, SpO2 96%", "condition": "Ananya: GCS 13→11. Right pupil 4mm sluggish — anisocoria developing. BP rises (early Cushing). Father arrives 5:00 at Ananya's bay with outside CT report and X-rays.\n\nVihaan: Stable after analgesia and fluids. Mother arrives 5:00 at Vihaan's bay.", "expected": "Recognise GCS trend (not a single reading) · Identify new anisocoria · Read CT report directly — do not accept father's verbal account ('they said it was normal') · CT actually says: small right temporal extradural collection, recommend repeat imaging if neurological deterioration · Activate neurosurgery immediately · Prepare RSI airway equipment · Calibrated response to Vihaan's trace FAST: surgical consult + serial exam", "notes": "Nurse prompt 4:30: 'Who needs the USG machine first — Ananya or Vihaan?' One machine only — forces explicit resource decision. Father (5:00): 'She was talking all the way. The scan was normal. Why is she becoming sleepy?' The trap is accepting the verbal account rather than reading the document."},
            {"name": "Stage 3: Scripted Acute Event — Seizure (5:30–8:00)", "vitals": "Ananya: HR 48, BP 138/90, GCS 6, Pupils R6mm fixed L3mm reactive, Irregular respirations", "condition": "Ananya seizes at 5:30 — scripted and unpreventable for both teams.\nBranch A (correct): RSI + ICP management → Stage 3 impending herniation (reversible).\nBranch B (delayed): No airway or ICP treatment → Stage 3B established herniation (GCS 3, apnoeic).", "expected": "Branch A (Correct): Airway · O2 · Suction · Benzodiazepine · Recognise Cushing response (bradycardia HR 48, rising BP, irregular respirations, fixed pupil) · RSI intubation with C-spine · 3% hypertonic saline 3–5 mL/kg · ETCO2 35–40 post-intubation · Head elevation 30° · Activate neurosurgery.\nBranch B (Incorrect): Delay intubation OR miss raised ICP signs → progresses to Stage 3B", "notes": "Seizure fires regardless of team performance. Do not score a prevention pathway. Father at Ananya's bay: 'She was talking 10 minutes ago — why does she need a breathing tube?' One team member communicates; leader does not stop managing patient. Cushing bradycardia (HR 48) is correct physiology, not an operator error. Stage 5 cap: 60 seconds, scripted stabilisation to Stage 3B, −10 penalty."},
            {"name": "Stage 4: Stabilised / Endgame (8:00–15:00)", "vitals": "Ananya: HR 91, BP 132/72, SpO2 97%, Intubated, Pupils R fixed L reactive, Vihaan: HR 138, BP 96/58, Splinted", "condition": "Ananya: Intubated, AED given, neuroprotection performed. Right pupil still fixed — requires surgical evacuation (not a failure of medical management).\n\nVihaan: Pain controlled, femur splinted, surgical review arranged.", "expected": "Confirm ETT placement · Continue sedation, maintain normocapnia · Prepare urgent neurosurgery transfer for Ananya · Arrange surgical review for Vihaan's abdominal injury and femur · Clear SBAR handover for both children", "notes": "Fixed pupil persists despite correct medical stabilisation — full recovery requires surgical evacuation. Do not let teams read unchanged pupil as failure. Tiebreaker: 'One CT scanner, one theatre. Justify the order of use for both children, and state what would change that order.'"}
        ],
        "patient": {"name": "Ananya Rao + Vihaan Rao", "mrn": "SF-01 / SF-02", "gender": "Female + Male", "age": "7 years + 18 months", "dob": "High-speed RTA — restrained rear-seat passengers", "height": "Ananya ~24 kg · Vihaan ~10 kg", "weight": "Dual-patient round — 15:00 hard stop", "cc": "Head injury (Ananya) + multiple trauma (Vihaan)", "hpi": "Ananya: Head struck right window, brief LOC, vomited once, increasingly sleepy. Vihaan: Child restraint partially detached, persistent crying, right leg deformed.", "pmh": "Both previously well.", "psh": "None.", "meds": "Nil.", "allergies": "None.", "family": "Father arrives 5:00 at Ananya's bay with outside CT report. Mother arrives 5:00 at Vihaan's bay."},
        "actors": "Ambulance Crews 1 and 2 (hand over, step back). One circulating trauma nurse initially. Father with CT report (Ananya's bay, 5:00). Mother (Vihaan's bay, 5:00).",
        "equipment": "Two multiparameter monitors. ONE ultrasound machine (contention is deliberate). Paediatric C-spine collars. Airway trolley + RSI tray. 3% hypertonic saline. AED vial/label. Printed outside CT report prop + X-rays. Toddler femur splint. Paediatric BVM. Crash cart."
    },
    {
        "id": "SF2",
        "round": "SEMI-FINALS",
        "title": "The Loud Wound — Dual Paediatric Trauma",
        "summary": "The deliberate mirror image of SF1. Meera Iyer (8y, 26kg) arrives quiet — a grade IV splenic laceration with evolving haemorrhagic shock, misread by paramedics as stable. Diya Iyer (3y, 14kg) arrives with a visibly blood-soaked scalp dressing requiring two changes en route — but is neurologically and haemodynamically intact. The team must resist the pull of the more dramatic presentation, correctly interpret a positive FAST in an unstable child as an indication for surgery not CT, and activate massive transfusion.",
        "background": "You are the paediatric trauma team. Two siblings from a high-speed T-bone collision arrive simultaneously. Diya (3y) has a visibly blood-soaked scalp dressing. Meera (8y) is quiet — crew 'weren't as worried about her.' Both were restrained rear-seat passengers.",
        "expanded_history": "Meera Iyer (8y, 26kg): Seatbelt mark across abdomen. Quiet throughout transport. Crew misread as stable. Hidden: grade IV splenic laceration, progressive haemoperitoneum, Class II→III haemorrhagic shock, closed right femoral shaft fracture.\n\nDiya Iyer (3y, 14kg): Head struck side window. No LOC. Scalp bled briskly, dressing changed twice en route. Hidden: scalp laceration with subgaleal haematoma — NO skull fracture, NO intracranial injury, NO other injuries.",
        "stages": [
            {"name": "Stage 1: Act I — Both Arrive (0:00–4:00)", "vitals": "Meera: HR 138, RR 30, BP 100/68, SpO2 98%, CRT 3s, Pulse pressure narrow, Diya: HR 130, RR 28, BP 94/60, SpO2 99%, GCS 15", "condition": "Meera: Quiet, seatbelt bruising abdomen and right thigh. Pale, cool peripheries, narrowing pulse pressure — compensated shock.\n\nDiya: Crying loudly. Scalp dressing visibly blood-soaked. Large boggy swelling underneath. Alert, moving all limbs normally.", "expected": "Designate leader · Resist initial pull toward Diya (visible blood is disproportionate to clinical significance) · Allocate sub-group to each child · Recognise Meera's narrow pulse pressure as compensated shock · Two large-bore IV access on Meera · Type-and-crossmatch urgently for both · FAST for Meera · Firm direct pressure/pressure dressing for Diya's scalp · Analgesia for both", "notes": "The volume of visible blood from Diya is disproportionate to clinical significance — the scalp is highly vascular. FAST is not indicated for Diya (no abdominal mechanism) — requesting it is a resource error, not a safety error. Nurse prompt 3:00: 'Shall I send trauma bloods and crossmatch for both children?'"},
            {"name": "Stage 2: Reassessment — Shock Trend + Parents Arrive (4:00–5:30)", "vitals": "Meera: HR 156, RR 34, BP 92/60, SpO2 97%, CRT 3–4s, GCS 14, FAST positive, Diya: HR 116, RR 24, BP 98/62, GCS 15", "condition": "Meera: Rising HR, narrowing pulse pressure. GCS 14 — becoming drowsy. Abdomen more distended and tense. Reduced pain reporting = altered sensorium, NOT improvement. FAST: significant free fluid in Morrison's pouch, splenorenal recess and pelvis.\n\nDiya: Bleeding controlled. Settling. GCS 15 throughout. Father arrives 5:00 at Meera's bay — initially reassured because she looks quieter.", "expected": "Recognise falling pulse pressure + rising HR as progression · Do NOT mistake Meera's reduced pain reporting for improvement · Positive FAST in haemodynamically unstable child = urgent surgery/IR, NOT CT · Escalate from crystalloid to blood products · Activate MTP (PRBC:FFP:platelets 1:1:1) · TXA 15 mg/kg over ~10 min · Active warming · Urgent surgical review · Continue Diya's wound management without diverting team resources from Meera", "notes": "Nurse prompt 4:30: 'Diya's dressing has soaked through again — do you want more gauze, or should I get help?' Deliberate pull toward the louder patient. CT request for Meera is the trap — answer delivered neutrally: 'Scanner is free, ten minutes. Do you want her to go?' A positive FAST in an unstable child means theatre or IR, not CT."},
            {"name": "Stage 3: Acute Event — Haematemesis + Decompensation (5:30–8:00)", "vitals": "Meera: HR 168, RR 38, BP 78/48, SpO2 94%, CRT 4s, GCS 11, Abdomen tense and distended", "condition": "Blood-tinged vomit + acute BP fall at 5:30 — scripted and unpreventable.\nBranch A (correct): MTP + TXA + surgery/IR activation → progresses to stabilisation.\nBranch B (delayed): CT ordered for unstable child, or team resources diverted to Diya → Stage 3B (pre-arrest: HR 70 paradoxical bradycardia, BP 58/32).", "expected": "Branch A (Correct): Escalate MTP · TXA if not yet given · Second large-bore access · Active warming · Immediate surgical/IR activation for source control · Anticipate airway support as GCS falls · Maintain care continuity for Diya.\nBranch B (Incorrect): Sending haemodynamically unstable Meera to CT OR diverting significant team/product attention to Diya", "notes": "Acute event scripted and unpreventable. Father (5:00, Meera's bay): 'Blood? I thought she was the stable one — what's happening?' Permissive hypotension credited if explicitly justified but never required; paediatric evidence is weak where TBI cannot be excluded. Mother arrives 5:00 at Diya's bay: 'There was so much blood — why is everyone with the other one?' Stage 5 cap: 60 seconds, scripted stabilisation, −10. Resuscitative thoracotomy is NOT indicated in blunt paediatric traumatic arrest."},
            {"name": "Stage 4: Stabilised / Endgame (8:00–15:00)", "vitals": "Meera: HR 118, RR 26, BP 96/60, SpO2 97–100%, Warmed, CRT 2s, Diya: GCS 15, Wound closed, Playful", "condition": "Meera: On MTP, warmed. Abdomen may remain distended — source control requires theatre or IR. Possible intubation if GCS falls further.\n\nDiya: Scalp wound closed (staples or tissue adhesive). GCS 15 throughout. Well, tolerating oral intake.", "expected": "Meera: Confirm ongoing product administration · Active warming · Urgent transfer to theatre or IR · RSI if GCS falls (specify safe induction).\nDiya: Confirm low-risk head-injury criteria met · No neuroimaging without clinical indication · Disposition to ward with safety-net advice.\nBoth: Clear SBAR handover for both children", "notes": "Meera's persistent abdominal distension is expected — source control is surgical or angiographic, not medical. Diya is the deliberate contrast: a well child ready for discharge. Tiebreaker: 'You had a positive FAST in a child with falling pulse pressure. Defend going to theatre rather than CT — and tell us what finding would have made CT the right call.'"}
        ],
        "patient": {"name": "Meera Iyer + Diya Iyer", "mrn": "SF-03 / SF-04", "gender": "Female + Female", "age": "8 years + 3 years", "dob": "High-speed T-bone collision — restrained rear-seat passengers", "height": "Meera ~26 kg · Diya ~14 kg", "weight": "Dual-patient round — 15:00 hard stop", "cc": "Haemorrhagic shock (Meera) + scalp laceration (Diya)", "hpi": "Meera: Seatbelt mark across abdomen. Quiet, misread as stable by crew. Diya: Scalp bled briskly, dressing changed twice en route. Alert and crying since scene.", "pmh": "Both previously well.", "psh": "None.", "meds": "Nil.", "allergies": "None.", "family": "Father arrives 5:00 at Meera's bay. Mother arrives 5:00 at Diya's bay."},
        "actors": "Ambulance Crews 1 and 2 (hand over, step back). One circulating trauma nurse. Father (Meera's bay, 5:00). Mother (Diya's bay, 5:00).",
        "equipment": "Two multiparameter monitors. ONE ultrasound machine (contention deliberate). O-negative blood (2 units in fridge, available immediately). MTP cooler labelled 1:1:1. TXA vial. Fluid warmer + rapid infuser. Scalp wound tray (staples/tissue adhesive) and pressure dressings. Simulated haematemesis delivery for 5:30 (bowl, towels, technician). Warming blanket visible. Two large-bore IV/IO points on Meera. Paediatric femur splint. Crash cart."
    },
    {
        "id": "F1",
        "round": "FINALS",
        "title": "Crashing on the Vent — Severe PARDS with Acute Cor Pulmonale",
        "summary": "Leo (6y, 20kg), day 3 PICU with influenza A pneumonia, is deeply sedated, paralysed, and desaturating on injurious ventilator settings (Pplat 34, ΔP 20). The declared team leader is removed (family emergency) and a substitute arrives — status ambiguous, later asserting seniority at 4:30 with a sepsis anchor. RV failure triggers hard at 4:00. The team must diagnose obstructive/RV-failure shock, halt the fluid bolus through graded assertiveness, request POCUS (D-sign, TAPSE 8mm), unload the lung (reduce MAP/PEEP), start epinephrine, add iNO, and correctly hand over to the returning leader at 9:30 — who must correct the false handover and disclose any fluid given. ECMO mode and rationale demanded at 14:00.",
        "background": "Leo is 6, 20kg, day 3 in PICU with influenza A pneumonia, intubated 24h. Deeply sedated and paralysed. Femoral CVL, right radial arterial line. Now desaturating. Your consultant has been called away — family emergency. The unit is sending someone to cover.",
        "expanded_history": "Previously healthy. Influenza A pneumonia. Ventilator PC-AC: Rate 24, Vt 110mL (5.5mL/kg), PEEP 14, PIP 34, Pplat 34, ΔP 20, Ti 0.8s, MAP 21, FiO2 0.85. ABG (30 min old): pH 7.28, PaCO2 58, PaO2 55, OI 32 → severe PARDS (PALICC-2, 2023). Infusions: fentanyl 2 mcg/kg/h, midazolam 0.1 mg/kg/h, rocuronium 1 mg/kg/h. No vasoactives. Team composition: 4 competitors (1 nurse compulsory + 3 doctors). Declared leader pulled before start; substitute restores count to 4. Confederate second nurse also present.",
        "stages": [
            {"name": "Stage 1: Handover Under Fire (0:00–4:00)", "vitals": "HR 145, BP 88/50, SpO2 82%, CVP 8, Temp 38.1°C, PEEP 14, PIP 34, Pplat 34, ΔP 20, MAP 21, FiO2 0.85", "condition": "Leo desaturating despite high FiO2 and PEEP 14. Pplat 34 / ΔP 20 = injurious ventilation. OI 32 = severe PARDS.\n\nSubstitute arrives 0:30 — status unknown, requests handover. Confederate nurse and RT also present.", "expected": "Structured DOPE (all four elements verbalised) · Identify Pplat 34 / ΔP 20 as excessive — do NOT reflexively escalate PEEP · Declare prone position with safety checklist (ETT depth confirmed and secured, lines managed, roles assigned, who owns the head, eye and pressure protection) — only intervention that improves oxygenation without raising mean airway pressure · Upward handover to substitute: structured, states the problem not just numbers · Task the second nurse", "notes": "ΔP is displayed as components but never calculated aloud by staff — Stage 1 discriminator. Prone declared here with checklist → Tier A crash at 4:00 (recovers on 2 interventions). Holding settings → Tier B. Escalating PEEP ≥16 → Tier C (MAP must be reduced first; pharmacology alone will not rescue). RT prompt at 2:30 if prone not raised: 'He's still 85%. Do you want to think about proning him?'"},
            {"name": "Stage 2: The Crash + Wrong Anchor (4:00–7:00)", "vitals": "Tier B: HR 175, BP 65/35, SpO2 84%, CVP 16, CRT 5s, Cool mottled extremities, Liver 4cm below costal margin", "condition": "RV failure triggers hard at 4:00 — severity per Stage 1 tier. At 4:30 substitute asserts seniority: 'I've been a consultant here five years. He's febrile, hypotensive, tachycardic — this is septic shock. Get fluid in and broaden the antibiotics.' At 5:30 directs confederate nurse: '20 per kilo of saline. Now.' Nurse physically starts the bolus.", "expected": "Branch A (Correct): Halt the fluid bolus with closed-loop confirmation · Name shock as obstructive/RV failure — NOT septic · Request POCUS (D-sign, dilated RV:LV >1, TAPSE 8mm, dilated IVC, small underfilled LV) · Reduce MAP (lower PEEP or Vt) · Epinephrine 0.05–0.1 mcg/kg/min · iNO 20ppm AFTER MAP reduced (no haemodynamic benefit before unloading the lung) · Avoid milrinone bolus (systolic −20).\nBranch B (Incorrect): Accept sepsis frame · Continue fluid → second bolus → PEA arrest", "notes": "Two-challenge rule: an unacknowledged safety concern must be restated. Level 2 (concern + reason) or higher required. The team nurse physically stopping the confederate nurse = highest-gradient act, top of scoring band. Chief Judge signals yield or harden at 7:00 based on challenge level. iNO conditional is the intellectual core: pharmacology cannot rescue mechanical overdistension — oxygenation improves, haemodynamics do not, until MAP is reduced first."},
            {"name": "Stage 3: Resolution + Leader Returns (7:00–11:00)", "vitals": "Post-treatment: HR 158, BP 74/42 (improving with epinephrine), SpO2 87%, CVP 13, iNO running", "condition": "At 7:00: Chief Judge signals yield (if adequately challenged) or harden (one final escalation then holds). At 9:30: Declared leader re-enters cold. Substitute delivers FALSE handover in front of the team: 'He's septic — febrile, hypotensive, we've been resuscitating. I'd keep the fluid going.' Team must correct departing substitute in front of returning leader — and disclose any fluid given.", "expected": "Reduce MAP and accept permissive hypercapnia (pH >7.20) · Epinephrine 0.05–0.1 mcg/kg/min with dose stated aloud · iNO 20ppm · Avoid milrinone bolus · Re-entry handover: correct false version, transmit RV failure diagnosis, disclose any fluid given · Returning leader: ask rather than assume, request CVP trend, restate model back, do NOT restart differential from scratch", "notes": "Vasopressin 0.3–0.5 mU/kg/min: systolic +10, CVP unchanged — expert marker. Milrinone infusion without bolus + BP supported: systolic −5, CVP −2 (acceptable). POCUS delivered unsolicited at 8:00 if never requested. Safety valve: if by 8:00 team has disintegrated, Chief Judge signals early reversion to neutral — no team may score zero on cor pulmonale because they spent 9 minutes losing an argument."},
            {"name": "Stage 4: Endgame — Mother + ECMO Call (11:00–15:00)", "vitals": "HR 155, BP 78/45 (on epinephrine), SpO2 89%, iNO running, Ventilating on reduced settings", "condition": "Substitute exits 11:00. Returning leader owns the room. Mother enters 13:00 — does not leave without an answer: 'Is my son dying?' ECMO team calls 14:00 demanding mode and rationale. Deliberate collision: family conversation and ECMO decision simultaneously. One person cannot cover both.", "expected": "ECMO mode with defensible rationale: V-V (correct hypoxaemia/hypercarbia → lower MAP → unload RV; RV function may recover) OR V-A (refractory shock or arrest) — both earn full credit if justified, unjustified scores 2/6 · Family communication: honest, no jargon, does not abandon patient to talk · Explicit delegation so both can be managed simultaneously", "notes": "Arrest cap: PEA runs 60 seconds only, scripted ROSC, −10. Penalties: fluid ≥10 mL/kg −8 · milrinone bolus at systolic <70 −5 · PEEP ≥18 −5 · prone attempted 4:00–9:00 −4 · PEA arrest −10. Tiebreaker: 'Defend your ECMO mode — V-V or V-A — and what would change your mind?'"}
        ],
        "patient": {"name": "Leo", "mrn": "F1-001", "gender": "Male", "age": "6 years", "dob": "Day 3 PICU — influenza A pneumonia", "height": "~110 cm", "weight": "20 kg", "cc": "Desaturating on mechanical ventilation — severe PARDS", "hpi": "Day 3 PICU. Influenza A pneumonia. Intubated 24h. Deeply sedated and paralysed. Now desaturating on injurious ventilator settings (Pplat 34, ΔP 20, FiO2 0.85).", "pmh": "Previously healthy.", "psh": "None.", "meds": "Fentanyl 2 mcg/kg/h · Midazolam 0.1 mg/kg/h · Rocuronium 1 mg/kg/h.", "allergies": "None.", "family": "Mother enters 13:00. Does not leave without an answer: 'Is my son dying?'"},
        "actors": "Substitute leader (confederate — ambiguous rank, asserts seniority 4:30 with sepsis anchor). Confederate nurse (executes only — physically starts the saline bolus at 5:30; never rescues the team). Respiratory Therapist (scripted prompts only). Mother (13:00). ECMO caller — voice only, 14:00.",
        "equipment": "Paediatric manikin. Ventilator screen showing PEEP, PIP, Pplat, Vt, rate, MAP (operator-editable). Three labelled infusions running. iNO cart with visible flowmeter. 500mL saline pre-spiked on pole (fluid trap must be physically startable). Code cart. Prone supplies visible (gel rolls, foam face support). Pre-recorded POCUS clips: PSAX D-shaped septum, apical 4-chamber dilated RV, M-mode TAPSE 8mm, dilated IVC. Monitor mirrored to main screen — audience must watch CVP climb as BP falls."
    },
    {
        "id": "F2",
        "round": "FINALS",
        "title": "The Tense Abdomen — Severe Dengue with Abdominal Compartment Syndrome",
        "summary": "Rehan (10y, 30kg), dengue day 5 after defervescence (critical phase), arrives after receiving ~70mL/kg crystalloid at a peripheral hospital. He has a tense grossly distended abdomen, anuria for 8 hours, thrombocytopenia (platelets 12), and active GI bleeding. CVP 18 is falsely reassuring — transmitted intra-abdominal pressure, not filling. The catheter is already in situ: IAP measurement (90 seconds, free) reads 26mmHg. The confederate substitute anchors on haemorrhagic shock and orders crystalloid + FFP at 5:30. The team must halt the crystalloid while accepting blood products, decompress the abdomen (therapeutic paracentesis → the only action that restores urine output), and hand over to the returning leader at 9:30.",
        "background": "Rehan is 10, 30kg, day 5 of dengue — NS1 positive, fever settled yesterday. Arriving from a peripheral hospital where he received ~70mL/kg crystalloid over 6 hours for progressive hypotension. Femoral CVL and catheter already placed there. Shocked, abdomen distended, no urine for 8 hours. Father is at the bedside. Your consultant has been called away — family emergency.",
        "expanded_history": "Dengue day 5, critical phase — defervescence yesterday. Peripheral hospital gave ~70mL/kg crystalloid. Femoral CVL, urinary catheter placed there. Vitals: HR 152, BP 78/62 (PP 16), RR 44, SpO2 91% on 6L mask, CRT 4s, CVP 18, Temp 36.6°C. Examination: cool mottled peripheries, grossly distended tense abdomen with pen girth mark from referring hospital, liver 4cm tender, reduced air entry both bases, drowsy but rousable, old melaena. Catheter dry for 8 hours. IAP via catheter: 26mmHg (Grade IV, ACS). Abdominal perfusion pressure = MAP − IAP = 67 − 26 = 41mmHg (target >60).",
        "stages": [
            {"name": "Stage 1: Handover Under Fire (0:00–4:00)", "vitals": "HR 152, BP 78/62, Pulse Pressure 16, RR 44, SpO2 91%, CVP 18, CRT 4s, Lactate 6.2, pH 7.18, Platelets 12", "condition": "Rehan: Decompensated dengue shock, critical phase. Narrow pulse pressure (PP 16) = earliest reliable marker. Grossly distended tense abdomen with pen girth mark from referring hospital. Catheter bag dry for 8 hours. CVP 18 = falsely reassuring (transmitted IAP, not filling). Old melaena. Father present throughout — silent unless addressed.\n\nSubstitute arrives 0:30, status unknown, requests handover.", "expected": "Recognise decompensated dengue shock in critical phase (narrow PP, defervescence, day 5) · Take fluid history: ~70mL/kg already in — register this critical point · Examine the abdomen: tense, note pen girth mark · MEASURE INTRA-ABDOMINAL PRESSURE via catheter already in situ → 26mmHg = Grade IV = Abdominal Compartment Syndrome · Send Hct, coagulation, renal bundle · Recognise AKI + hyperkalaemia (K+ 5.8) · Structured upward handover to substitute · Task the confederate nurse", "notes": "IAP measurement is the discriminating Stage 1 action — 90 seconds, no extra equipment needed. Measuring IAP → Tier A crash at 4:00 (recovers on 2 correct actions). Examining abdomen but no IAP → Tier B. Giving ≥20mL/kg crystalloid before 4:00 → Tier C (decompression required first; blood products alone will not restore BP or urine). Technician prompt at 2:30 if abdomen not examined: 'There's a pen line drawn on his tummy from the other hospital — he's well past it now.'"},
            {"name": "Stage 2: Haematemesis + Half-Right Anchor (4:00–7:00)", "vitals": "Tier B: HR 168, BP 64/50, SpO2 85%, IAP 28, CRT 4s, Hct 48%→31% (repeat 6:00)", "condition": "400mL haematemesis at 4:00 — scripted and unpreventable. Substitute asserts seniority at 4:30: 'I've been a consultant here eight years. He's bleeding, shocked, haematocrit dropping — haemorrhagic shock. Run the fluids and activate massive transfusion.' At 5:30 directs nurse: '20/kg Ringer's wide open AND four units FFP.' Nurse physically starts both. The anchor is half-right: the child genuinely is bleeding and needs blood — what is wrong is the crystalloid, large-volume FFP, and failure to address the abdomen.", "expected": "Branch A (Correct): Halt crystalloid with closed-loop confirmation WHILE accepting blood · Name problem as mechanical — tense abdomen obstructing venous return, not simple hypovolaemia · Refuse large-volume FFP (IAP +2, MAP −5) · Request POCUS: gross ascites, small hyperdynamic LV, dilated non-collapsing IVC (IVC is the deliberate red herring — reads as fluid-replete but reflects compression; small hyperdynamic LV is the honest finding) · Packed cells 10mL/kg.\nBranch B (Incorrect): Accept crystalloid + FFP → MAP falls further, IAP rises, urine production zero → arrest", "notes": "Two-challenge rule applies. Team nurse physically stopping the confederate nurse = ceiling behaviour, top of scoring band. Chief Judge signals yield or harden at 7:00. Furosemide for anuria: no urine produced (renal vein compressed) + MAP −4 = penalty. Noradrenaline raises BP but produces no urine without decompression — vasopressors cannot substitute for mechanical decompression."},
            {"name": "Stage 3: Resolution + Paracentesis + Leader Returns (7:00–11:00)", "vitals": "Post-paracentesis: IAP 26→14, MAP +12, SpO2 +5, Urine 20mL within 10 min, BP improving", "condition": "At 9:30: Declared leader re-enters cold. Substitute delivers FALSE handover: 'He's bleeding out — haemorrhagic shock, we've been filling him. I'd keep the fluid and FFP going.' Team must correct departing substitute in front of returning leader — disclose all crystalloid and FFP given.", "expected": "Packed cells 10mL/kg with dose stated aloud · Platelets for active bleeding with count of 12 (NOT large-volume FFP) · Decompression bundle: NG tube · analgesia + sedation to relax abdominal wall (head of bed ≤30° — raising >30° worsens IAP) · THERAPEUTIC PARACENTESIS (1.2L drained → IAP 26→14, MAP +12, SpO2 +5, urine appears within 10 min) · Re-entry handover: correct false version, transmit mechanical diagnosis, disclose crystalloid/FFP given", "notes": "Paracentesis is the ONLY action that restores urine output — vasopressors alone will not. Paracentesis without platelet/product cover: bleeding at site, −3 penalty, drainage still effective. NG decompression alone: IAP −2, MAP +3. Sedation/analgesia to relax abdominal wall: IAP −3, MAP +4. POCUS delivered unsolicited at 8:00 if never requested. Returning leader: asks rather than assumes, requests urine output and fluid totals, restates model back, does NOT restart differential from scratch."},
            {"name": "Stage 4: Endgame — Father + PICU Call (11:00–15:00)", "vitals": "IAP 14, MAP improving, Urine draining, Platelets transfusing, SpO2 94%", "condition": "Substitute exits 11:00. Returning leader owns room. Father (silent since 0:00) demands answer at 13:00: 'You keep putting things into him and he's getting worse. Is my son going to die?' PICU/retrieval calls 14:00: 'We'll take him. Intubated before transfer or awake? Do you want the surgeons?' Deliberate collision: family conversation + disposition decision simultaneously.", "expected": "Airway decision with rationale: Intubate (rising WOB, splinted diaphragm, active haematemesis — specify ketamine induction + PEEP ≤5, OR decompression first) OR Transfer awake (positive pressure into undecompressed abdomen reduces preload further; decompression flips the decision) — both earn full credit if justified, unjustified scores 2/6 · Surgical/PICU escalation · Family communication: honest, no jargon, does not abandon patient to communicate", "notes": "Penalties: crystalloid ≥20mL/kg after 4:00 −8 · FFP ≥15mL/kg −5 · intubation as first move or PEEP ≥8 −5 · nephrotoxic given −4 · furosemide for anuria −3 · cardiac arrest −10. NSAID/nephrotoxic: creatinine rises on repeat. Arrest cap: 60 seconds, scripted ROSC, −10. Tiebreaker: 'Defend your airway decision — intubate before transfer, or not — and what would change your mind?'"}
        ],
        "patient": {"name": "Rehan", "mrn": "F2-001", "gender": "Male", "age": "10 years", "dob": "Dengue Day 5 — critical phase after defervescence", "height": "~138 cm", "weight": "30 kg", "cc": "Dengue shock — distended abdomen, anuria 8h, active GI bleed", "hpi": "Day 5 dengue. NS1+. Fever settled yesterday (defervescence = critical phase entry). Peripheral hospital gave ~70mL/kg crystalloid over 6h for progressive hypotension. Femoral CVL + catheter placed there. Grossly distended tense abdomen with referring hospital's girth mark. No urine for 8 hours. Old melaena. Now haematemesis.", "pmh": "Previously healthy.", "psh": "None.", "meds": "Nil.", "allergies": "None.", "family": "Father present in room from 0:00 — silent until 13:00 unless addressed. 'You keep putting things into him and he's getting worse. Is my son going to die?'"},
        "actors": "Substitute leader (confederate — ambiguous rank, asserts seniority 4:30 with haemorrhagic shock anchor). Confederate nurse (physically starts crystalloid + FFP at 5:30; never rescues). ED Technician (girth prompt 2:30, IAP reading on request). Father (present 0:00, speaks 13:00). PICU/retrieval caller — voice only, 14:00.",
        "equipment": "Paediatric manikin with distended abdomen prop (drainable reservoir — paracentesis payoff must be visible). Pen girth mark on abdomen. Urinary catheter with IAP manometry setup. Femoral CVL + peripheral cannula. Crystalloid bag pre-spiked and hanging (fluid trap physically present and startable). Blood product boxes labelled. Paracentesis kit staged. Simulated haematemesis for 4:00 (bowl, towels, technician). Pre-recorded POCUS clips: gross ascites, thickened GB wall, bilateral pleural effusions, dilated non-collapsing IVC, small hyperdynamic LV. Catheter bag visible on camera — urine appearing is the reward signal."
    }
]

# ============================================
# ROUND COLORS
# ============================================
ROUND_COLORS = {
    "ROUND ONE": {"accent": "#1a56db", "light": "#ebf5ff", "badge": "#1e40af"},
    "ROUND TWO": {"accent": "#7e3af2", "light": "#f5f3ff", "badge": "#5521b5"},
    "SEMI-FINALS": {"accent": "#0d9488", "light": "#f0fdfa", "badge": "#0f766e"},
    "FINALS": {"accent": "#d97706", "light": "#fffbeb", "badge": "#92400e"},
}

# ============================================
# INDEX PAGE
# ============================================
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SimWars — Case Library</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f1f5f9; color: #1e293b; min-height: 100vh; }

    /* Header */
    .header { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: white; padding: 48px 40px 40px; }
    .header-inner { max-width: 1100px; margin: 0 auto; }
    .header h1 { font-size: 2.4rem; font-weight: 800; letter-spacing: -0.5px; }
    .header p { margin-top: 10px; color: #94a3b8; font-size: 1.05rem; }
    .stats { display: flex; gap: 32px; margin-top: 28px; }
    .stat { }
    .stat-num { font-size: 2rem; font-weight: 700; color: #60a5fa; }
    .stat-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-top: 2px; }

    /* Content */
    .content { max-width: 1100px; margin: 40px auto; padding: 0 40px 60px; }

    /* Round section */
    .round-header { display: flex; align-items: center; gap: 14px; margin: 40px 0 20px; }
    .round-label { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; padding: 5px 14px; border-radius: 20px; }
    .round-one .round-label { background: #dbeafe; color: #1e40af; }
    .round-two .round-label { background: #ede9fe; color: #5521b5; }
    .round-sf .round-label { background: #ccfbf1; color: #0f766e; }
    .round-finals .round-label { background: #fef3c7; color: #92400e; }
    .round-header hr { flex: 1; border: none; border-top: 1.5px solid #e2e8f0; }

    /* Grid */
    .cases-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }

    /* Card */
    .card { background: white; border-radius: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04); overflow: hidden; display: flex; flex-direction: column; transition: transform 0.15s, box-shadow 0.15s; text-decoration: none; color: inherit; }
    .card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
    .card-accent { height: 5px; }
    .round-one .card-accent { background: linear-gradient(90deg, #1a56db, #3b82f6); }
    .round-two .card-accent { background: linear-gradient(90deg, #7e3af2, #a78bfa); }
    .round-sf .card-accent { background: linear-gradient(90deg, #0d9488, #34d399); }
    .round-finals .card-accent { background: linear-gradient(90deg, #d97706, #fbbf24); }
    .card-body { padding: 22px 22px 18px; flex: 1; display: flex; flex-direction: column; }
    .case-id { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin-bottom: 8px; }
    .case-title { font-size: 1rem; font-weight: 700; line-height: 1.4; color: #0f172a; margin-bottom: 10px; }
    .case-summary { font-size: 0.82rem; color: #64748b; line-height: 1.6; flex: 1; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
    .card-footer { padding: 14px 22px; border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
    .patient-chip { font-size: 0.78rem; color: #64748b; }
    .patient-chip strong { color: #334155; }
    .open-btn { font-size: 0.78rem; font-weight: 600; color: #1a56db; text-decoration: none; display: flex; align-items: center; gap: 4px; }
    .round-two .open-btn { color: #7e3af2; }
    .round-sf .open-btn { color: #0d9488; }
    .round-finals .open-btn { color: #d97706; }
    .open-btn::after { content: '→'; }

    /* Results console */
    .rc-wrap { margin-top: 32px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 14px; overflow: hidden; }
    .rc-head { display: flex; align-items: center; justify-content: space-between; padding: 10px 18px 0; }
    .rc-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; color: #94a3b8; }
    .rc-dot { width: 7px; height: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 6px #22c55e; animation: rc-blink 2s infinite; }
    @keyframes rc-blink { 0%,100%{opacity:1} 50%{opacity:.4} }
    .rc-tabs { display: flex; gap: 2px; padding: 8px 18px 0; }
    .rc-tab { font-size: 0.78rem; font-weight: 600; padding: 5px 14px; border-radius: 7px 7px 0 0; cursor: pointer; color: #94a3b8; border: none; background: transparent; }
    .rc-tab.active { background: rgba(255,255,255,0.1); color: white; }
    .rc-body { padding: 14px 18px 18px; min-height: 60px; }
    .rc-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
    .rc-table th { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #64748b; padding: 0 8px 6px; text-align: left; }
    .rc-table th.r { text-align: right; }
    .rc-table td { padding: 5px 8px; color: #e2e8f0; border-top: 1px solid rgba(255,255,255,0.05); }
    .rc-table td.r { text-align: right; font-variant-numeric: tabular-nums; }
    .rc-rank { font-size: 1rem; width: 28px; display: inline-block; }
    .rc-name { font-weight: 700; }
    .rc-sub { font-size: 0.7rem; color: #64748b; }
    .rc-score-big { font-size: 1.05rem; font-weight: 800; color: #fbbf24; }
    .rc-empty { color: #475569; font-size: 0.82rem; padding: 8px 0; }
    .rc-sf-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .rc-sf-round { }
    .rc-sf-label { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #64748b; margin-bottom: 6px; }
    .rc-sf-team { font-size: 0.85rem; font-weight: 700; color: #e2e8f0; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
    .rc-fn-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
    .rc-fn-name { font-size: 0.9rem; font-weight: 700; color: #e2e8f0; }
    .rc-fn-detail { font-size: 0.72rem; color: #64748b; margin-top: 2px; }
    .rc-fn-total { font-size: 1.3rem; font-weight: 800; color: #fbbf24; }
  </style>
</head>
<body>
  <div class="header">
    <div class="header-inner">
      <h1>SimWars Case Library</h1>
      <p>Pediatric Emergency Simulation Scenarios</p>
      <div class="stats">
        <div class="stat"><div class="stat-num">{{ cases|length }}</div><div class="stat-label">Total Cases</div></div>
        <div class="stat"><div class="stat-num">3</div><div class="stat-label">Rounds</div></div>
        <div class="stat"><div class="stat-num">4</div><div class="stat-label">Stages per Case</div></div>
      </div>

      <!-- Live Results Console -->
      <div class="rc-wrap">
        <div class="rc-head">
          <span class="rc-title">Live Results Console</span>
          <span class="rc-dot"></span>
        </div>
        <div class="rc-tabs">
          <button class="rc-tab active" onclick="rcSwitch('prelim',this)">Prelims</button>
          <button class="rc-tab" onclick="rcSwitch('sf',this)">Semi-Finals</button>
          <button class="rc-tab" onclick="rcSwitch('finals',this)">Finals</button>
        </div>
        <div class="rc-body" id="rcBody"><div class="rc-empty">Loading…</div></div>
      </div>
    </div>
  </div>

  <script>
    let rcData = null;
    let rcTab = 'prelim';

    function rcSwitch(tab, btn) {
      rcTab = tab;
      document.querySelectorAll('.rc-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      rcRender();
    }

    function rcRender() {
      const body = document.getElementById('rcBody');
      if (!rcData) { body.innerHTML = '<div class="rc-empty">Loading…</div>'; return; }

      if (rcTab === 'prelim') {
        const teams = rcData.prelim;
        if (!teams.length) { body.innerHTML = '<div class="rc-empty">No prelim scores entered yet.</div>'; return; }
        const medals = ['🥇','🥈','🥉','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣'];
        let h = '<table class="rc-table"><thead><tr><th>#</th><th>Team</th><th class="r">PALS</th><th class="r">BLS</th><th class="r">Combined</th></tr></thead><tbody>';
        teams.forEach((t, i) => {
          const rank = medals[i] || (i+1);
          h += `<tr><td><span class="rc-rank">${rank}</span></td>
            <td><span class="rc-name">${t.name}</span><br><span class="rc-sub">${t.team}</span></td>
            <td class="r">${t.pals.toFixed(0)}</td>
            <td class="r">${t.bls.toFixed(0)}</td>
            <td class="r"><span class="rc-score-big">${t.combined.toFixed(1)}</span></td></tr>`;
        });
        h += '</tbody></table>';
        const w = rcData.weights;
        h += `<div style="font-size:0.68rem;color:#475569;margin-top:8px;">Domain-weighted (BLS ×1.25/×0.8, PALS unweighted) · ${teams.length} of 16 teams scored</div>`;
        body.innerHTML = h;

      } else if (rcTab === 'sf') {
        const sf = rcData.sf;
        const hasNames = Object.values(sf).some(n => n && !['SF1','SF2','SF3','SF4'].includes(n));
        if (!hasNames) { body.innerHTML = '<div class="rc-empty">Semi-Finals teams not assigned yet.</div>'; return; }
        body.innerHTML = `<div class="rc-sf-grid">
          <div class="rc-sf-round">
            <div class="rc-sf-label">Round 1 — "The Quiet Head"</div>
            <div class="rc-sf-team">${sf.sf1 || '—'}</div>
            <div class="rc-sf-team">${sf.sf2 || '—'}</div>
          </div>
          <div class="rc-sf-round">
            <div class="rc-sf-label">Round 2 — "The Loud Wound"</div>
            <div class="rc-sf-team">${sf.sf3 || '—'}</div>
            <div class="rc-sf-team">${sf.sf4 || '—'}</div>
          </div>
        </div>`;

      } else if (rcTab === 'finals') {
        const fn = rcData.finals;
        const hasData = ['fin1','fin2'].some(t => fn[t].total > 0 || !['FIN1','FIN2'].includes(fn[t].name));
        if (!hasData) { body.innerHTML = '<div class="rc-empty">Finals not started yet.</div>'; return; }
        let h = '';
        ['fin1','fin2'].forEach(t => {
          const d = fn[t];
          const s = d.scores;
          h += `<div class="rc-fn-row">
            <div>
              <div class="rc-fn-name">${d.name}</div>
              <div class="rc-fn-detail">
                F1: ${s.F1.clin}/45 clin · ${s.F1.tw}/40 tw · ${s.F1.shared}/15 sr = ${s.F1.total}/100
                &nbsp;·&nbsp;
                F2: ${s.F2.clin}/45 clin · ${s.F2.tw}/40 tw · ${s.F2.shared}/15 sr = ${s.F2.total}/100
              </div>
            </div>
            <div class="rc-fn-total">${d.total}<span style="font-size:0.65rem;font-weight:400;color:#64748b;">/200</span></div>
          </div>`;
        });
        body.innerHTML = h;
      }
    }

    async function rcPoll() {
      try {
        const r = await fetch('/api/results');
        rcData = await r.json();
        rcRender();
      } catch(e) {}
    }

    rcPoll();
    setInterval(rcPoll, 4000);
  </script>

  <div class="content">
    {% for round_name, round_cases in rounds.items() %}
      {% set rclass = 'round-one' if 'ONE' in round_name else ('round-sf' if 'SEMI' in round_name else ('round-finals' if 'FINALS' in round_name else 'round-two')) %}
      <div class="{{ rclass }}">
        <div class="round-header">
          <span class="round-label">{{ round_name }}</span>
          <hr>
        </div>
        <div class="cases-grid">
          {% for case in round_cases %}
          <a class="card {{ rclass }}" href="/case/{{ case.id }}">
            <div class="card-accent"></div>
            <div class="card-body">
              <div class="case-id">Case {{ case.id }}</div>
              <div class="case-title">{{ case.title }}</div>
              <div class="case-summary">{{ case.summary }}</div>
            </div>
            <div class="card-footer">
              <div class="patient-chip">Patient: <strong>{{ case.patient.name }}</strong> &middot; {{ case.patient.age }}</div>
              <span class="open-btn">View</span>
            </div>
          </a>
          {% endfor %}
        </div>
      </div>
    {% endfor %}
  </div>
</body>
</html>
"""

# ============================================
# CASE DETAIL PAGE
# ============================================
CASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ case.id }}: {{ case.title }}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f1f5f9; color: #1e293b; }

    /* Nav bar */
    .topbar { background: #0f172a; padding: 0 32px; display: flex; align-items: center; gap: 20px; height: 52px; position: sticky; top: 0; z-index: 100; }
    .topbar a { color: #94a3b8; font-size: 0.85rem; text-decoration: none; }
    .topbar a:hover { color: white; }
    .topbar .sep { color: #334155; }
    .topbar .case-label { color: #e2e8f0; font-weight: 600; font-size: 0.85rem; }
    .topbar-actions { margin-left: auto; display: flex; gap: 10px; }
    .btn { display: inline-flex; align-items: center; gap: 6px; padding: 7px 16px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; cursor: pointer; text-decoration: none; border: none; }
    .btn-ghost { background: rgba(255,255,255,0.08); color: #cbd5e1; }
    .btn-ghost:hover { background: rgba(255,255,255,0.14); color: white; }
    .btn-primary { background: {{ colors.accent }}; color: white; }
    .btn-primary:hover { opacity: 0.9; }
    .btn-outline { background: transparent; border: 1.5px solid rgba(255,255,255,0.2); color: #cbd5e1; }
    .btn-outline:hover { border-color: rgba(255,255,255,0.4); color: white; }

    /* Hero */
    .hero { background: linear-gradient(135deg, #0f172a 0%, {{ colors.badge }} 100%); color: white; padding: 36px 40px 32px; }
    .hero-inner { max-width: 1100px; margin: 0 auto; }
    .round-badge { display: inline-block; background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.2); color: #e2e8f0; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; padding: 4px 14px; border-radius: 20px; margin-bottom: 14px; }
    .hero h1 { font-size: 1.9rem; font-weight: 800; line-height: 1.3; max-width: 800px; }
    .hero-meta { display: flex; gap: 24px; margin-top: 18px; flex-wrap: wrap; }
    .meta-item { display: flex; flex-direction: column; }
    .meta-label { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 2px; }
    .meta-value { font-size: 0.9rem; font-weight: 600; color: #e2e8f0; }

    /* Body */
    .page-body { max-width: 1100px; margin: 32px auto; padding: 0 40px 60px; display: grid; grid-template-columns: 1fr 320px; gap: 28px; align-items: start; }

    /* Sections */
    .section { background: white; border-radius: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 20px; overflow: hidden; }
    .section-header { padding: 16px 22px; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; gap: 10px; }
    .section-icon { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; flex-shrink: 0; }
    .section-title { font-size: 0.9rem; font-weight: 700; color: #0f172a; }
    .section-body { padding: 20px 22px; }
    .section-body p { font-size: 0.9rem; line-height: 1.7; color: #475569; }

    /* Stages */
    .stage { border: 1.5px solid #e2e8f0; border-radius: 10px; margin-bottom: 14px; overflow: hidden; }
    .stage:last-child { margin-bottom: 0; }
    .stage-header { padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; }
    .stage-num { width: 26px; height: 26px; border-radius: 50%; background: {{ colors.light }}; color: {{ colors.accent }}; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .stage-name { font-size: 0.88rem; font-weight: 700; color: #0f172a; margin-left: 10px; flex: 1; }
    .stage-chevron { color: #94a3b8; font-size: 0.8rem; transition: transform 0.2s; }
    .stage.open .stage-chevron { transform: rotate(180deg); }
    .stage-body { display: none; padding: 0 16px 16px; border-top: 1px solid #f1f5f9; }
    .stage.open .stage-body { display: block; }
    .stage-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; }
    .stage-cell { background: #f8fafc; border-radius: 8px; padding: 12px; }
    .stage-cell-label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 6px; }
    .stage-cell-value { font-size: 0.82rem; color: #334155; line-height: 1.6; }
    .stage-cell.full { grid-column: 1 / -1; }
    .branch-a { background: #f0fdf4; border: 1px solid #bbf7d0; }
    .branch-a .stage-cell-label { color: #16a34a; }
    .branch-b { background: #fff7ed; border: 1px solid #fed7aa; }
    .branch-b .stage-cell-label { color: #ea580c; }

    /* Vitals pills */
    .vitals { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
    .vital-pill { background: {{ colors.light }}; color: {{ colors.badge }}; font-size: 0.75rem; font-weight: 600; padding: 3px 10px; border-radius: 20px; }

    /* Sidebar */
    .sidebar { position: sticky; top: 72px; }
    .info-card { background: white; border-radius: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 16px; overflow: hidden; }
    .info-card-header { padding: 13px 18px; background: {{ colors.light }}; border-bottom: 1px solid #e2e8f0; }
    .info-card-title { font-size: 0.8rem; font-weight: 700; color: {{ colors.badge }}; text-transform: uppercase; letter-spacing: 0.08em; }
    .info-table { width: 100%; padding: 12px 18px; }
    .info-row { display: flex; gap: 8px; padding: 5px 0; border-bottom: 1px solid #f8fafc; font-size: 0.82rem; }
    .info-row:last-child { border-bottom: none; }
    .info-label { color: #94a3b8; font-weight: 600; min-width: 90px; flex-shrink: 0; }
    .info-value { color: #334155; }
    .info-body { padding: 14px 18px; font-size: 0.82rem; color: #475569; line-height: 1.65; }

    /* Download bar */
    .download-bar { background: white; border-radius: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); padding: 16px 18px; }
    .download-title { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 12px; }
    .download-btns { display: flex; flex-direction: column; gap: 8px; }
    .dl-btn { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 8px; text-decoration: none; font-size: 0.83rem; font-weight: 600; border: 1.5px solid #e2e8f0; color: #334155; transition: all 0.15s; }
    .dl-btn:hover { border-color: {{ colors.accent }}; color: {{ colors.accent }}; background: {{ colors.light }}; }
    .dl-icon { font-size: 1rem; }

    /* Investigations console */
    .inv-console { background: #0f172a; border-radius: 14px; padding: 16px; margin-bottom: 16px; }
    .inv-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
    .inv-title::after { content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.07); }
    .inv-types { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 10px; }
    .inv-type-btn { background: rgba(255,255,255,0.06); color: #94a3b8; border: 1px solid rgba(255,255,255,0.08); border-radius: 7px; padding: 6px 4px; font-size: 0.72rem; font-weight: 600; cursor: pointer; text-align: center; transition: 0.15s; }
    .inv-type-btn:hover, .inv-type-btn.active { background: {{ colors.accent }}; color: white; border-color: {{ colors.accent }}; }
    .inv-textarea { width: 100%; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #e2e8f0; font-size: 0.82rem; font-family: 'Courier New', monospace; padding: 10px; resize: vertical; min-height: 90px; outline: none; line-height: 1.5; }
    .inv-textarea:focus { border-color: {{ colors.accent }}; }
    .inv-push-btn { width: 100%; margin-top: 8px; padding: 10px; background: {{ colors.accent }}; color: white; font-size: 0.82rem; font-weight: 700; border: none; border-radius: 8px; cursor: pointer; transition: 0.15s; letter-spacing: 0.03em; }
    .inv-push-btn:hover { filter: brightness(1.1); }
    .inv-push-btn.sent { background: #16a34a; }
    .inv-status { font-size: 0.7rem; color: #22c55e; text-align: center; margin-top: 6px; min-height: 18px; }
    .inv-card-btn { display: block; width: 100%; text-align: left; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 8px 12px; margin-bottom: 6px; cursor: pointer; transition: 0.15s; }
    .inv-card-btn:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.2); }
    .inv-card-label { display: block; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; margin-bottom: 2px; }
    .inv-card-text { display: block; font-size: 0.78rem; color: #cbd5e1; font-family: 'Courier New', monospace; }

    /* Case nav */
    .case-nav { display: flex; gap: 8px; }
    .nav-btn { flex: 1; padding: 9px 12px; background: white; border: 1.5px solid #e2e8f0; border-radius: 8px; text-align: center; text-decoration: none; font-size: 0.78rem; font-weight: 600; color: #64748b; }
    .nav-btn:hover { border-color: {{ colors.accent }}; color: {{ colors.accent }}; }
    .nav-btn.disabled { opacity: 0.4; pointer-events: none; }

    @media (max-width: 768px) {
      .page-body { grid-template-columns: 1fr; }
      .sidebar { position: static; }
      .hero { padding: 28px 20px; }
      .page-body { padding: 0 16px 40px; }
      .stage-grid { grid-template-columns: 1fr; }
      .topbar { padding: 0 16px; }
    }

   @media print {
         .topbar, .topbar-actions, .download-bar, .case-nav, .inv-console { display: none !important; }
         .page-body { display: block !important; }
         .sidebar { position: static !important; margin-top: 24px; }
         .stage-body { display: block !important; }
         .stage-grid { display: block !important; }
         .stage-cell { margin-bottom: 10px; }
       }
  </style>
</head>
<body>
  <!-- Sticky nav -->
  <nav class="topbar">
    <a href="/">← All Cases</a>
    <span class="sep">/</span>
    <span class="case-label">Case {{ case.id }}: {{ case.title[:40] }}{% if case.title|length > 40 %}…{% endif %}</span>
    <div class="topbar-actions">
      <a href="/case/{{ case.id }}?format=pdf" class="btn btn-ghost">⬇ PDF</a>
      <a href="/case/{{ case.id }}?format=docx" class="btn btn-ghost">⬇ DOCX</a>
      <button onclick="window.print()" class="btn btn-outline">🖨 Print</button>
    </div>
  </nav>

  <!-- Hero -->
  <div class="hero">
    <div class="hero-inner">
      <div class="round-badge">{{ case.round }} &middot; Case {{ case.id }}</div>
      <h1>{{ case.title }}</h1>
      <div class="hero-meta">
        <div class="meta-item"><div class="meta-label">Patient</div><div class="meta-value">{{ case.patient.name }}, {{ case.patient.age }}</div></div>
        <div class="meta-item"><div class="meta-label">Weight</div><div class="meta-value">{{ case.patient.weight }}</div></div>
        <div class="meta-item"><div class="meta-label">Gender</div><div class="meta-value">{{ case.patient.gender }}</div></div>
        <div class="meta-item"><div class="meta-label">MRN</div><div class="meta-value">{{ case.patient.mrn }}</div></div>
      </div>
    </div>
  </div>

  <!-- Body -->
  <div class="page-body">
    <div class="main-col">

      <!-- Summary -->
      <div class="section">
        <div class="section-header">
          <div class="section-icon" style="background:{{ colors.light }}">📋</div>
          <div class="section-title">Case Summary</div>
        </div>
        <div class="section-body"><p>{{ case.summary }}</p></div>
      </div>

      <!-- Background -->
      <div class="section">
        <div class="section-header">
          <div class="section-icon" style="background:#fef9c3">📖</div>
          <div class="section-title">Background (given to participants)</div>
        </div>
        <div class="section-body">
          <p>{{ case.background }}</p>
          <p style="margin-top:12px; color:#94a3b8; font-size:0.8rem; font-style:italic;"><strong>If asked:</strong> {{ case.expanded_history }}</p>
        </div>
      </div>

      <!-- Stages -->
      <div class="section">
        <div class="section-header">
          <div class="section-icon" style="background:#fef2f2">🔴</div>
          <div class="section-title">Scenario Stages</div>
        </div>
        <div class="section-body">
          {% for stage in case.stages %}
          <div class="stage open" onclick="toggleStage(this)">
            <div class="stage-header">
              <div class="stage-num">{{ loop.index }}</div>
              <div class="stage-name">{{ stage.name }}</div>
              <span class="stage-chevron">▲</span>
            </div>
            <div class="stage-body">
              <div class="vitals">
                {% for v in stage.vitals.split(', ') %}
                <span class="vital-pill">{{ v }}</span>
                {% endfor %}
              </div>
              <div class="stage-grid">
                <div class="stage-cell">
                  <div class="stage-cell-label">Patient Condition</div>
                  <div class="stage-cell-value">{{ stage.condition }}</div>
                </div>
                <div class="stage-cell">
                  <div class="stage-cell-label">Operator Notes</div>
                  <div class="stage-cell-value">{{ stage.notes }}</div>
                </div>
                {% if 'Branch A' in stage.expected %}
                  {% set parts = stage.expected.split('Branch B') %}
                  {% set partA = parts[0].replace('Branch A (Correct): ', '') %}
                  {% set partB = parts[1].replace(' (Incorrect): ', '') if parts|length > 1 else '' %}
                  <div class="stage-cell full branch-a">
                    <div class="stage-cell-label">✅ Branch A — Correct Interventions</div>
                    <div class="stage-cell-value">{{ partA }}</div>
                  </div>
                  {% if partB %}
                  <div class="stage-cell full branch-b">
                    <div class="stage-cell-label">⚠️ Branch B — Incorrect / Trap</div>
                    <div class="stage-cell-value">{{ partB }}</div>
                  </div>
                  {% endif %}
                {% else %}
                <div class="stage-cell full">
                  <div class="stage-cell-label">Expected Interventions</div>
                  <div class="stage-cell-value">{{ stage.expected }}</div>
                </div>
                {% endif %}
              </div>
            </div>
          </div>
          {% endfor %}
        </div>
      </div>

      <!-- Actors & Equipment -->
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
        <div class="section">
          <div class="section-header">
            <div class="section-icon" style="background:#f0fdf4">🎭</div>
            <div class="section-title">Actor Roles</div>
          </div>
          <div class="section-body"><p>{{ case.actors }}</p></div>
        </div>
        <div class="section">
          <div class="section-header">
            <div class="section-icon" style="background:#eff6ff">🩺</div>
            <div class="section-title">Equipment</div>
          </div>
          <div class="section-body"><p>{{ case.equipment }}</p></div>
        </div>
      </div>

    </div><!-- /main-col -->

    <!-- Sidebar -->
    <div class="sidebar">

      <!-- Patient chart -->
      <div class="info-card">
        <div class="info-card-header"><div class="info-card-title">Patient Chart</div></div>
        <div class="info-table">
          <div class="info-row"><span class="info-label">Name</span><span class="info-value">{{ case.patient.name }}</span></div>
          <div class="info-row"><span class="info-label">MRN</span><span class="info-value">{{ case.patient.mrn }}</span></div>
          <div class="info-row"><span class="info-label">Gender</span><span class="info-value">{{ case.patient.gender }}</span></div>
          <div class="info-row"><span class="info-label">Age / DOB</span><span class="info-value">{{ case.patient.age }} / {{ case.patient.dob }}</span></div>
          <div class="info-row"><span class="info-label">Height</span><span class="info-value">{{ case.patient.height }}</span></div>
          <div class="info-row"><span class="info-label">Weight</span><span class="info-value">{{ case.patient.weight }}</span></div>
          <div class="info-row"><span class="info-label">Allergies</span><span class="info-value">{{ case.patient.allergies }}</span></div>
          <div class="info-row"><span class="info-label">CC</span><span class="info-value">{{ case.patient.cc }}</span></div>
          <div class="info-row"><span class="info-label">HPI</span><span class="info-value">{{ case.patient.hpi }}</span></div>
          <div class="info-row"><span class="info-label">PMH</span><span class="info-value">{{ case.patient.pmh }}</span></div>
          <div class="info-row"><span class="info-label">PSH</span><span class="info-value">{{ case.patient.psh }}</span></div>
          <div class="info-row"><span class="info-label">Meds</span><span class="info-value">{{ case.patient.meds }}</span></div>
          <div class="info-row"><span class="info-label">Family</span><span class="info-value">{{ case.patient.family }}</span></div>
        </div>
      </div>

      <!-- Investigations Console -->
      <div class="inv-console">
        <div class="inv-title">📺 Push to Display</div>
        <div id="inv-cards"></div>
        <div style="margin-top:10px;border-top:1px solid rgba(255,255,255,0.07);padding-top:10px;">
          <div style="font-size:0.65rem;color:#475569;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">Custom result</div>
          <textarea id="inv-text" class="inv-textarea" placeholder="Type any result…"></textarea>
          <button class="inv-push-btn" id="inv-push" onclick="pushCustom()">📡 Push Custom</button>
        </div>
        <div class="inv-status" id="inv-status"></div>
      </div>

      <!-- Downloads -->
      <div class="download-bar">
        <div class="download-title">Download Case</div>
        <div class="download-btns">
          <a class="dl-btn" href="/case/{{ case.id }}?format=pdf"><span class="dl-icon">📄</span> Download PDF</a>
          <a class="dl-btn" href="/case/{{ case.id }}?format=docx"><span class="dl-icon">📝</span> Download DOCX</a>
        </div>
      </div>

      <!-- Case nav -->
      <div style="margin-top:12px;">
        <div class="case-nav">
          {% if prev_case %}
          <a class="nav-btn" href="/case/{{ prev_case.id }}">← {{ prev_case.id }}</a>
          {% else %}
          <span class="nav-btn disabled">←</span>
          {% endif %}
          {% if next_case %}
          <a class="nav-btn" href="/case/{{ next_case.id }}">{{ next_case.id }} →</a>
          {% else %}
          <span class="nav-btn disabled">→</span>
          {% endif %}
        </div>
      </div>

    </div><!-- /sidebar -->
  </div><!-- /page-body -->

  <script>
    function toggleStage(el) { el.classList.toggle('open'); }

    var STAGES = {{ case.stages | tojson }};
    var CASE_ID = {{ case.id | tojson }};

    function ts() {
      var n = new Date();
      return n.getHours().toString().padStart(2,'0') + ':' + n.getMinutes().toString().padStart(2,'0');
    }

    function pushHtml(label, resultText, btnEl) {
      var lines = resultText.split('\n').map(function(l) {
        return l.trim() ? '<div style="margin:6px 0;font-size:1.25rem;color:#e2e8f0;font-family:\'Courier New\',monospace;line-height:1.5;">' + l + '</div>' : '<div style="margin:4px 0;"></div>';
      }).join('');
      var t = ts();
      var html = '<div style="padding:36px 52px;">'
        + '<div style="display:flex;align-items:baseline;gap:16px;margin-bottom:28px;border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:16px;">'
        + '<div style="font-size:2.2rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.02em;">' + label + '</div>'
        + '<div style="font-size:0.9rem;color:#334155;font-family:\'Courier New\',monospace;margin-left:auto;">' + t + '</div>'
        + '</div>'
        + '<div style="line-height:1.8;">' + lines + '</div>'
        + '<div style="margin-top:28px;font-size:0.68rem;color:#1e3a5f;letter-spacing:0.14em;text-transform:uppercase;">SimWars 2026 · Case ' + CASE_ID + '</div>'
        + '</div>';
      fetch('/api/score', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({key:'proj_html', value: html})})
        .then(function() {
          if (btnEl) { var orig = btnEl.textContent; btnEl.textContent = '✓ Live'; btnEl.style.background='#16a34a'; setTimeout(function(){ btnEl.textContent = orig; btnEl.style.background=''; }, 3500); }
          document.getElementById('inv-status').textContent = '✓ ' + label + ' pushed at ' + t;
        })
        .catch(function() { document.getElementById('inv-status').textContent = 'Error — check connection.'; });
    }

    // Parse investigations out of a stage's condition and vitals
    function parseInvestigations(stage, stageIdx) {
      var results = [];
      var cond = stage.condition || '';
      var vitals = stage.vitals || '';

      // Labs / Blood gas
      var labMatch = cond.match(/Labs?:?\s*([^\n.]+(?:\.[^\n.]+)?)/i);
      if (labMatch) results.push({label: 'Labs · Stage ' + stageIdx, text: labMatch[1].trim()});

      // pH / ABG in vitals or condition
      var abgMatch = (vitals + ' ' + cond).match(/pH\s*[\d.]+[^,\n]*(,\s*Pa?CO2[^,\n]*)?(,\s*Pa?O2[^,\n]*)?(,\s*HCO3?[^,\n]*)?(,\s*BE[^,\n]*)?(,\s*OI[^,\n]*)?(,\s*Lactate[^,\n]*)?/i);
      if (abgMatch && !labMatch) results.push({label: 'ABG · Stage ' + stageIdx, text: abgMatch[0].trim().replace(/\s+/g,' ')});

      // ECG in vitals
      var ecgMatch = vitals.match(/ECG:\s*([^,\n]+)/i);
      if (ecgMatch) results.push({label: 'ECG · Stage ' + stageIdx, text: ecgMatch[1].trim()});

      // CT / Scan mention in condition
      var ctMatch = cond.match(/(?:CT|MRI|scan)\s*(?:report)?:?\s*([^.]+\.)/i);
      if (ctMatch) results.push({label: 'CT / Scan · Stage ' + stageIdx, text: ctMatch[1].trim()});

      // FAST / Echo in condition
      var fastMatch = cond.match(/(?:FAST|echo|POCUS)[^.]*(?::|—)\s*([^.]+\.)/i);
      if (fastMatch) results.push({label: 'Echo / POCUS · Stage ' + stageIdx, text: fastMatch[1].trim()});

      // IAP
      var iapMatch = (vitals + ' ' + cond).match(/IAP[^,\n]*/i);
      if (iapMatch) results.push({label: 'IAP · Stage ' + stageIdx, text: iapMatch[0].trim()});

      return results;
    }

    function buildCards() {
      var container = document.getElementById('inv-cards');
      var all = [];
      STAGES.forEach(function(s, i) {
        all = all.concat(parseInvestigations(s, i+1));
      });
      if (!all.length) { container.innerHTML = '<div style="font-size:0.75rem;color:#334155;padding:4px 0;">No pre-scripted results detected.</div>'; return; }
      container.innerHTML = all.map(function(inv, idx) {
        return '<button class="inv-card-btn" id="icard-' + idx + '" onclick="pushHtml(' + JSON.stringify(inv.label) + ',' + JSON.stringify(inv.text) + ',this)">'
          + '<span class="inv-card-label">' + inv.label + '</span>'
          + '<span class="inv-card-text">' + inv.text.substring(0,60) + (inv.text.length>60?'…':'') + '</span>'
          + '</button>';
      }).join('');
    }

    function pushCustom() {
      var result = document.getElementById('inv-text').value.trim();
      if (!result) { document.getElementById('inv-status').textContent = 'Enter a result first.'; return; }
      pushHtml('Investigation Result', result, document.getElementById('inv-push'));
    }

    buildCards();
  </script>
</body>
</html>
"""

# ============================================
# ROUTES
# ============================================

@app.route('/')
def root_redirect():
    return redirect('/register')

@app.route('/library')
def index():
    locked = require_role()
    if locked: return locked
    rounds = {}
    for c in CASES:
        rounds.setdefault(c['round'], []).append(c)
    return render_template_string(INDEX_TEMPLATE, cases=CASES, rounds=rounds)

@app.route('/case/<case_id>')
def get_case(case_id):
    case = next((c for c in CASES if c['id'] == case_id), None)
    if not case:
        return "Case not found", 404

    fmt = request.args.get('format', 'html').lower()
    colors = ROUND_COLORS.get(case['round'], ROUND_COLORS['ROUND ONE'])

    # Prev/next navigation
    ids = [c['id'] for c in CASES]
    idx = ids.index(case_id)
    prev_case = CASES[idx - 1] if idx > 0 else None
    next_case = CASES[idx + 1] if idx < len(CASES) - 1 else None

    if fmt == 'html':
        html = render_template_string(CASE_TEMPLATE, case=case, colors=colors, prev_case=prev_case, next_case=next_case)
        return html, 200, {'Content-Type': 'text/html'}

    elif fmt == 'pdf':
        WeasyHTML = _get_weasyprint()
        if WeasyHTML is None:
            return ("PDF export requires WeasyPrint system dependencies (Pango/GLib). "
                    "Install via: brew install pango gobject-introspection && pip install weasyprint", 503)
        html = render_template_string(CASE_TEMPLATE, case=case, colors=colors, prev_case=None, next_case=None)
        pdf = WeasyHTML(string=html).write_pdf()
        return send_file(io.BytesIO(pdf), mimetype='application/pdf', as_attachment=True,
                         download_name=f'{case_id}_{case["title"][:40].replace(" ", "_")}.pdf')

    elif fmt == 'docx':
        doc = Document()
        doc.add_heading(case['title'], 0)
        doc.add_paragraph(case['round'], style='Intense Quote')
        doc.add_heading('Case Summary', level=1)
        doc.add_paragraph(case['summary'])
        doc.add_heading('Background (for participants)', level=1)
        doc.add_paragraph(case['background'])
        doc.add_heading('Expanded Background (if asked)', level=1)
        doc.add_paragraph(case['expanded_history'])
        doc.add_heading('Scenario Stages', level=1)
        tbl = doc.add_table(rows=1, cols=5)
        tbl.style = 'Table Grid'
        hdr = tbl.rows[0].cells
        for i, h in enumerate(['Stage', 'Vitals', 'Condition', 'Expected Interventions', 'Operator Notes']):
            hdr[i].text = h
        for s in case['stages']:
            row = tbl.add_row().cells
            row[0].text = s['name']
            row[1].text = s['vitals']
            row[2].text = s['condition']
            row[3].text = s['expected']
            row[4].text = s['notes']
        doc.add_heading('Patient Chart', level=1)
        p = doc.add_paragraph()
        for k, v in [('Name', case['patient']['name']), ('MRN', case['patient']['mrn']),
                     ('Gender', case['patient']['gender']), ('Age', case['patient']['age']),
                     ('DOB', case['patient']['dob']), ('Height', case['patient']['height']),
                     ('Weight', case['patient']['weight']), ('Allergies', case['patient']['allergies']),
                     ('Chief Complaint', case['patient']['cc']), ('HPI', case['patient']['hpi']),
                     ('PMH', case['patient']['pmh']), ('PSH', case['patient']['psh']),
                     ('Medications', case['patient']['meds']), ('Family/Social', case['patient']['family'])]:
            run = p.add_run(f'{k}: ')
            run.bold = True
            p.add_run(f'{v}\n')
        doc.add_heading('Actor Roles', level=1)
        doc.add_paragraph(case['actors'])
        doc.add_heading('Equipment', level=1)
        doc.add_paragraph(case['equipment'])
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         as_attachment=True, download_name=f'{case_id}_{case["title"][:40].replace(" ", "_")}.docx')

    return "Invalid format. Use ?format=html, pdf, or docx", 400

@app.route('/scoring')
def scoring():
    locked = require_role()
    if locked: return locked
    return send_file(os.path.join(os.path.dirname(__file__), 'scoring.html'))

@app.route('/flow')
def flow():
    return send_file(os.path.join(os.path.dirname(__file__), 'flow-of-program.html'))

@app.route('/register')
def register():
    return send_file(os.path.join(os.path.dirname(__file__), 'simwars-2026-landing-page.html'))

@app.route('/api/scores', methods=['GET'])
def get_scores():
    with get_db() as conn:
        rows = conn.execute('SELECT key, value FROM scores').fetchall()
    return jsonify({row['key']: row['value'] for row in rows})

@app.route('/api/score', methods=['POST'])
def save_score():
    data = request.get_json()
    key = data.get('key')
    value = data.get('value')
    if not key:
        return jsonify({'error': 'missing key'}), 400
    with get_db() as conn:
        conn.execute('INSERT INTO scores (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP',
                     (key, str(value)))
        conn.commit()
    return jsonify({'ok': True})

@app.route('/api/scores/reset', methods=['POST'])
def reset_scores():
    with get_db() as conn:
        conn.execute('DELETE FROM scores')
        conn.commit()
    return jsonify({'ok': True})

@app.route('/api/results')
def get_results():
    with get_db() as conn:
        rows = conn.execute('SELECT key, value FROM scores').fetchall()
    sc = {row['key']: row['value'] for row in rows}
    def flt(val, default=0):
        try: return float(val) if val not in (None, '') else default
        except: return default
    ALL_TEAMS = ['T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12','T13','T14','T15','T16']
    teams = []
    for team in ALL_TEAMS:
        name = (sc.get(f'team_name_{team}') or '').strip() or team
        pals = min(100, flt(sc.get(f'score_pals_{team}')))
        bls  = min(100, flt(sc.get(f'score_bls_{team}')))
        pals_case = sc.get(f'team_pals_case_{team}') or ''
        bls_case  = sc.get(f'team_bls_case_{team}')  or ''
        pals_d3 = flt(sc.get(f'd3_{pals_case}_{team}')) if pals_case else 0
        bls_d3  = flt(sc.get(f'd3_{bls_case}_{team}'))  if bls_case  else 0
        combined = round(pals + bls, 1)
        teams.append({
            'team': team, 'name': name,
            'pals': pals, 'bls': bls, 'combined': combined,
            'pals_d3': pals_d3, 'bls_d3': bls_d3,
        })
    teams.sort(key=lambda t: (-t['combined'], -t['pals'], -(t['pals_d3'] + t['bls_d3'])))
    active = [t for t in teams if t['pals'] > 0 or t['bls'] > 0]
    sf = {t: (sc.get(f'sfName_{t}') or '').strip() or t.upper() for t in ['sf1','sf2','sf3','sf4']}
    fn_names = {t: (sc.get(f'fnName_{t}') or '').strip() or t.upper() for t in ['fin1','fin2']}
    FN_STAGES = {
        'F1': {'stages': [
            [('s1i0',3),('s1i1',4),('s1i2',2),('s1i3',3)],
            [('s2i0',6),('s2i1',5),('s2i2',4)],
            [('s3i0',4),('s3i1',4),('s3i2',2),('s3i3',2)],
            [('s4i0',6)],
        ], 'penalties': [('p0',-8),('p1',-5),('p2',-5),('p3',-4),('p4',-10)],
           'tw': [('tw0',6),('tw1',8),('tw2',8),('tw3',6),('tw4',5),('tw5',7)]},
        'F2': {'stages': [
            [('s1i0',3),('s1i1',3),('s1i2',4),('s1i3',2)],
            [('s2i0',6),('s2i1',5),('s2i2',4)],
            [('s3i0',4),('s3i1',3),('s3i2',2),('s3i3',3)],
            [('s4i0',6)],
        ], 'penalties': [('p0',-8),('p1',-5),('p2',-5),('p3',-4),('p4',-3),('p5',-10)],
           'tw': [('tw0',6),('tw1',8),('tw2',8),('tw3',6),('tw4',5),('tw5',7)]},
    }
    fn_scores = {}
    for t in ['fin1','fin2']:
        fn_scores[t] = {}
        for cid, cd in FN_STAGES.items():
            clin = 0
            for stage in cd['stages']:
                for k, mx in stage:
                    clin += min(mx, max(0, flt(sc.get(f'fn_{cid}_{t}_clin_{k}'))))
            for pk, pts in cd['penalties']:
                if sc.get(f'fn_{cid}_{t}_{pk}') in ('1', 1, True):
                    clin += pts
            clin = max(0, clin)
            tw = sum(min(mx, max(0, flt(sc.get(f'fn_{cid}_{t}_tw_{k}')))) for k, mx in cd['tw'])
            shared = min(15, max(0, flt(sc.get(f'fn_{cid}_{t}_shared'))))
            fn_scores[t][cid] = {'clin': clin, 'tw': tw, 'shared': shared, 'total': clin + tw + shared}
    fn_totals = {t: sum(fn_scores[t][c]['total'] for c in ['F1','F2']) for t in ['fin1','fin2']}
    return jsonify({
        'prelim': active,
        'all_teams': teams,
        'sf': sf,
        'finals': {t: {'name': fn_names[t], 'scores': fn_scores[t], 'total': fn_totals[t]} for t in ['fin1','fin2']},
        'weights': {'policy': 'BLS Domain I x1.25 / Domain II x0.8; PALS unweighted. Fixed — see scoring.html.'},
    })

@app.route('/cases')
def list_cases():
    return jsonify([{'id': c['id'], 'title': c['title'], 'round': c['round']} for c in CASES])

DISPLAY_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SimWars · Investigations Display</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; background: #030712; color: #e2e8f0; font-family: 'Courier New', Courier, monospace; }
#display-wrap { min-height: 100vh; padding: 40px 48px; }
#placeholder {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 80vh; gap: 20px; color: #1e3a5f;
}
#placeholder-icon { font-size: 5rem; }
#placeholder-text { font-size: 1.3rem; letter-spacing: 0.05em; }
#placeholder-sub { font-size: 0.85rem; color: #0f172a; }
</style>
</head>
<body>
<div id="display-wrap">
    <div id="content">
        <div id="placeholder">
            <div id="placeholder-icon">📋</div>
            <div id="placeholder-text">Awaiting investigation result…</div>
            <div id="placeholder-sub">SimWars 2026 — Operator will project results here</div>
        </div>
    </div>
</div>
<script>
var _last = null;
function poll() {
    fetch('/api/scores').then(function(r){ return r.json(); }).then(function(data){
        var html = data['proj_html'];
        if (html && html !== _last) {
            _last = html;
            document.getElementById('content').innerHTML =
                '<div style="font-family:\\'Courier New\\',monospace;color:#e2e8f0;padding:8px 0;">' + html + '</div>';
        }
    }).catch(function(){}).finally(function(){ setTimeout(poll, 1500); });
}
poll();
</script>
</body>
</html>"""

@app.route('/display')
def display():
    return DISPLAY_TEMPLATE

PORTAL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SIMWARS 2026 · PediSTARS India</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" />
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
            background: #eef2f7;
            min-height: 100vh;
            padding: 2rem 1.5rem;
            background-image: radial-gradient(circle at 20% 30%, rgba(249,199,79,0.04) 0%, transparent 60%);
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }

        .portal {
            max-width: 1300px;
            width: 100%;
            background: rgba(255,255,255,0.7);
            backdrop-filter: blur(6px);
            border-radius: 2.8rem;
            box-shadow: 0 40px 80px rgba(11,42,79,0.12), 0 10px 30px rgba(0,0,0,0.03);
            border: 1px solid rgba(255,255,255,0.6);
            overflow: hidden;
        }

        /* ── HERO ── */
        .hero {
            background: linear-gradient(135deg, #0a1a2e 0%, #1b3f64 70%, #2b5780 100%);
            padding: 2.2rem 3rem 1.8rem;
            color: white;
            position: relative;
            overflow: hidden;
        }

        .hero::before {
            content: '';
            position: absolute; top: -60%; right: -10%;
            width: 500px; height: 500px;
            background: radial-gradient(circle, rgba(249,199,79,0.07) 0%, transparent 70%);
            border-radius: 50%; pointer-events: none;
        }

        .hero::after {
            content: '';
            position: absolute; bottom: -50%; left: -5%;
            width: 350px; height: 350px;
            background: radial-gradient(circle, rgba(255,255,255,0.02) 0%, transparent 70%);
            border-radius: 50%; pointer-events: none;
        }

        .hero-top {
            display: flex; flex-wrap: wrap;
            justify-content: space-between; align-items: center;
            gap: 1.5rem; position: relative; z-index: 2;
        }

        .brand { display: flex; align-items: center; gap: 1.2rem; }

        .brand-icon {
            background: #f9c74f; color: #0a1a2e;
            width: 70px; height: 70px; border-radius: 20px;
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 1.8rem; letter-spacing: -0.02em;
            box-shadow: 0 10px 24px rgba(0,0,0,0.25); flex-shrink: 0;
        }

        .brand-text { line-height: 1.2; }
        .brand-text .name { font-size: 2rem; font-weight: 700; letter-spacing: -0.01em; }
        .brand-text .name span { color: #f9c74f; }
        .brand-text .tagline { font-size: 0.85rem; font-weight: 400; opacity: 0.7; letter-spacing: 0.25em; margin-top: 0.1rem; }

        .badge-location {
            background: rgba(255,255,255,0.1); backdrop-filter: blur(4px);
            padding: 0.4rem 1.6rem; border-radius: 60px;
            font-weight: 500; font-size: 0.85rem;
            border: 1px solid rgba(255,255,255,0.15); letter-spacing: 0.05em; white-space: nowrap;
        }

        .badge-location i { margin-right: 8px; color: #f9c74f; }

        .hero-title { margin-top: 2rem; position: relative; z-index: 2; }

        .hero-title h1 {
            font-size: 2.6rem; font-weight: 700;
            line-height: 1.15; letter-spacing: -0.02em;
        }

        .hero-title h1 .gold { color: #f9c74f; }

        .hero-title .sub {
            font-size: 1rem; opacity: 0.8;
            margin-top: 0.3rem; font-weight: 300; letter-spacing: 0.03em;
        }

        .hero-meta {
            display: flex; flex-wrap: wrap; gap: 1.8rem 3rem;
            margin-top: 1.6rem; padding-top: 1.2rem;
            border-top: 1px solid rgba(255,255,255,0.08);
            position: relative; z-index: 2;
        }

        .meta-item { display: flex; align-items: center; gap: 0.7rem; font-size: 0.9rem; }
        .meta-item i { color: #f9c74f; font-size: 1rem; width: 1.4rem; text-align: center; }
        .meta-item strong { font-weight: 600; }
        .meta-item .highlight { color: #f9c74f; }

        /* ── BODY ── */
        .body { padding: 2.5rem 3rem 1.8rem; }

        .grid {
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 2.5rem;
        }

        @media(max-width: 900px) {
            .grid { grid-template-columns: 1fr; gap: 2rem; }
            .hero { padding: 1.8rem; }
            .hero-title h1 { font-size: 1.8rem; }
            .brand-text .name { font-size: 1.5rem; }
            .brand-icon { width: 54px; height: 54px; font-size: 1.4rem; }
            .body { padding: 1.8rem; }
        }

        /* ── SECTION HEADER ── */
        .section-head {
            font-size: 1.1rem; font-weight: 600; color: #0a1a2e;
            margin-bottom: 1.2rem;
            display: flex; align-items: center; gap: 0.6rem;
        }
        .section-head i { color: #f9c74f; }

        .section-sub {
            font-size: 0.65rem; font-weight: 700; letter-spacing: 0.14em;
            text-transform: uppercase; color: #5a7a9a;
            margin: 1.2rem 0 0.6rem;
        }

        /* ── FEATURE GRID ── */
        .feature-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }

        @media(max-width: 600px) { .feature-grid { grid-template-columns: 1fr; } }

        .feature-card {
            background: white; border-radius: 1.2rem;
            padding: 1.2rem 1.2rem 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
            border: 1px solid rgba(0,0,0,0.02);
            transition: 0.25s ease;
            text-decoration: none; color: #0a1a2e;
            display: flex; flex-direction: column;
        }

        .feature-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(11,42,79,0.08);
            border-color: #dce5f0;
        }

        .feature-card .icon { font-size: 1.5rem; color: #f9c74f; margin-bottom: 0.5rem; }
        .feature-card .title { font-weight: 600; font-size: 0.95rem; margin-bottom: 0.2rem; }
        .feature-card .desc { font-size: 0.78rem; color: #5a7a9a; line-height: 1.4; flex: 1; }
        .feature-card .url {
            font-size: 0.62rem; color: #8aaac0; margin-top: 0.6rem;
            font-family: 'SF Mono', monospace;
            border-top: 1px solid #eef4fa; padding-top: 0.5rem;
        }

        .badge {
            display: inline-block;
            background: #f9c74f; color: #0a1a2e;
            font-size: 0.55rem; font-weight: 700;
            padding: 0.15rem 0.6rem; border-radius: 40px;
            text-transform: uppercase; letter-spacing: 0.04em;
            margin-left: 0.4rem;
        }

        .badge-live  { background: #22c55e; color: #fff; }
        .badge-bls   { background: #16a34a; color: #fff; }
        .badge-pals  { background: #1d4ed8; color: #fff; }
        .badge-sf    { background: #0891b2; color: #fff; }
        .badge-fn    { background: #d97706; color: #fff; }
        .badge-spec  { background: #7c3aed; color: #fff; }

        /* ── INFO PANEL (right column) ── */
        .info-panel { display: flex; flex-direction: column; gap: 1.2rem; }

        .info-card {
            background: white; border-radius: 1.5rem;
            padding: 1.4rem 1.8rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
            border-left: 4px solid #f9c74f;
        }

        .info-card .label {
            font-size: 0.7rem; text-transform: uppercase;
            letter-spacing: 0.08em; color: #5a7a9a; font-weight: 600;
        }

        .info-card .value {
            font-size: 0.92rem; color: #0a1a2e;
            margin-top: 0.3rem; line-height: 1.7;
        }

        .info-card .value .coord {
            display: block; font-size: 0.85rem; color: #1a3a5a; margin-top: 0.1rem;
        }
        .info-card .value .coord i { color: #f9c74f; width: 1.2rem; }

        /* quick links inside info-card */
        .quick-links { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.4rem; }

        .quick-link {
            display: flex; align-items: center; gap: 0.8rem;
            background: #f8faff; padding: 0.55rem 1rem;
            border-radius: 0.9rem; text-decoration: none;
            color: #0a1a2e; transition: 0.2s;
            border: 1px solid transparent; font-size: 0.88rem;
        }

        .quick-link:hover { background: white; border-color: #dce5f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
        .quick-link i { color: #f9c74f; width: 1.2rem; font-size: 0.95rem; }
        .quick-link .link-label { font-weight: 500; flex: 1; }
        .quick-link .link-badge { font-size: 0.58rem; }

        /* ── CASES SECTION (full width below grid) ── */
        .cases-section {
            margin-top: 2.5rem;
            padding-top: 2rem;
            border-top: 1px solid #e4ecf5;
        }

        .round-group { margin-bottom: 1.8rem; }

        .round-label {
            display: flex; align-items: center; gap: 8px;
            font-size: 0.65rem; font-weight: 700;
            letter-spacing: 0.16em; text-transform: uppercase;
            color: #5a7a9a; margin-bottom: 0.8rem;
        }

        .round-label .dot {
            width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
        }

        .round-label::after { content: ''; flex: 1; height: 1px; background: #e4ecf5; }

        .dot-bls  { background: #22c55e; }
        .dot-pals { background: #3b82f6; }
        .dot-sf   { background: #06b6d4; }
        .dot-fn   { background: #f59e0b; }

        .case-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }

        .case-grid-2 { grid-template-columns: 1fr 1fr; }

        .case-card {
            background: white; border-radius: 1rem;
            padding: 1rem 1.1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.025);
            border: 1px solid #edf2fa;
            transition: 0.18s;
        }

        .case-card:hover { box-shadow: 0 6px 20px rgba(11,42,79,0.07); transform: translateY(-1px); }

        .round-bls  .case-card { border-top: 3px solid #22c55e; }
        .round-pals .case-card { border-top: 3px solid #3b82f6; }
        .round-sf   .case-card { border-top: 3px solid #06b6d4; }
        .round-fn   .case-card { border-top: 3px solid #f59e0b; }

        .case-id {
            font-size: 0.95rem; font-weight: 800;
            color: #0a1a2e; margin-bottom: 0.6rem; line-height: 1.3;
        }

        .doc-links { display: flex; flex-direction: column; gap: 4px; }

        .doc-link {
            display: inline-flex; align-items: center; gap: 5px;
            font-size: 0.68rem; font-weight: 500;
            color: #5a7a9a; text-decoration: none; padding: 2px 0;
            transition: color 0.15s;
        }

        .doc-link:hover { color: #0a1a2e; }

        /* ── FOOTER ── */
        .footer {
            text-align: center; font-size: 0.8rem; color: #6a8aaa;
            border-top: 1px solid #eef4fa;
            padding: 1.5rem 2rem 1.8rem; letter-spacing: 0.02em;
            background: rgba(255,255,255,0.3);
        }

        .footer i { color: #f9c74f; margin: 0 4px; }
        .footer .sep { opacity: 0.3; margin: 0 0.6rem; }

        @media(max-width: 580px) {
            .case-grid { grid-template-columns: 1fr 1fr; }
            .case-grid-2 { grid-template-columns: 1fr; }
            .hero-top { flex-direction: column; align-items: flex-start; }
        }
    </style>
</head>
<body>

<div class="portal">

    <!-- ══ HERO ══ -->
    <header class="hero">
        <div class="hero-top">
            <div class="brand">
                <div class="brand-icon">PS</div>
                <div class="brand-text">
                    <div class="name">Pedi<span>STARS</span></div>
                    <div class="tagline">INDIA · SIMULATION &amp; RESEARCH</div>
                </div>
            </div>
            <div class="badge-location">
                <i class="fas fa-map-pin"></i> Bengaluru · 22–23 Aug 2026
            </div>
        </div>

        <div class="hero-title">
            <h1>Simulus <span class="gold">11th Annual</span><br>National Conference of PediSTARS</h1>
            <div class="sub"><i class="fas fa-stethoscope" style="margin-right:10px"></i>Healthcare Simulation · SIMWARS 2026</div>
        </div>

        <div class="hero-meta">
            <div class="meta-item">
                <i class="fas fa-calendar-alt"></i>
                <span><strong>23 August 2026</strong> · Main Conference</span>
            </div>
            <div class="meta-item">
                <i class="fas fa-location-dot"></i>
                <span><strong>22 Aug</strong> Prelims @ DHEE Hospitals · <strong>23 Aug</strong> Semis &amp; Finals @ VASA</span>
            </div>
            <div class="meta-item">
                <i class="fas fa-users"></i>
                <span>Max <strong>16 teams</strong> · <span class="highlight">4 members</span> each</span>
            </div>
            <div class="meta-item">
                <i class="fas fa-tag"></i>
                <span>Registration <strong>₹10,000</strong> / <strong>$215</strong> per team</span>
            </div>
        </div>
    </header>

    <!-- ══ BODY ══ -->
    <div class="body">
        <div class="grid">

            <!-- LEFT: Conference tools + scoring sheets -->
            <div>
                <div class="section-head"><i class="fas fa-bolt"></i> Live competition tools</div>
                <div class="feature-grid">

                    <a href="https://merry-intuition-production-1788.up.railway.app/" target="_blank" class="feature-card">
                        <div class="icon"><i class="fas fa-book-open"></i></div>
                        <div class="title">Case Library <span class="badge badge-live">Live</span></div>
                        <div class="desc">All 14 cases · stage-by-stage breakdowns · investigations console · prelim standings.</div>
                        <div class="url">merry-intuition-production…/</div>
                    </a>

                    <a href="https://merry-intuition-production-1788.up.railway.app/scoring" target="_blank" class="feature-card">
                        <div class="icon"><i class="fas fa-bullseye"></i></div>
                        <div class="title">Scoring Engine <span class="badge badge-live">Live</span></div>
                        <div class="desc">Master · Judge · Debriefer · Special Prizes · Semis &amp; Finals. Live sync across devices.</div>
                        <div class="url">…/scoring</div>
                    </a>

                    <a href="https://merry-intuition-production-1788.up.railway.app/display" target="_blank" class="feature-card">
                        <div class="icon"><i class="fas fa-desktop"></i></div>
                        <div class="title">Results Display</div>
                        <div class="desc">Fullscreen investigations display for the room projector. Auto-updates live.</div>
                        <div class="url">…/display</div>
                    </a>

                    <a href="https://claude.ai/code/artifact/631528d3-55b7-45a7-b758-c2e6192fb7b9" target="_blank" class="feature-card">
                        <div class="icon"><i class="fas fa-diagram-project"></i></div>
                        <div class="title">Competition Flow</div>
                        <div class="desc">Full case descriptions · patient profiles · scoring domains · advancement rules.</div>
                        <div class="url">claude.ai/code/artifact/…</div>
                    </a>

                </div>

                <div class="section-sub">Scoring Sheets</div>
                <div class="feature-grid">

                    <a href="https://merry-intuition-production-1788.up.railway.app/scoring#tabBls" target="_blank" class="feature-card">
                        <div class="icon" style="color:#16a34a"><i class="fas fa-list-check"></i></div>
                        <div class="title">BLS Judge Sheet <span class="badge badge-bls">R1</span></div>
                        <div class="desc">Round One · Cases B1–B4 · Clinical + Non-technical rubric per team.</div>
                        <div class="url">…/scoring#tabBls</div>
                    </a>

                    <a href="https://merry-intuition-production-1788.up.railway.app/scoring#tabPals" target="_blank" class="feature-card">
                        <div class="icon" style="color:#1d4ed8"><i class="fas fa-list-check"></i></div>
                        <div class="title">PALS Judge Sheet <span class="badge badge-pals">R2</span></div>
                        <div class="desc">Round Two · Cases P1–P4 · Clinical + Non-technical rubric per team.</div>
                        <div class="url">…/scoring#tabPals</div>
                    </a>

                    <a href="https://merry-intuition-production-1788.up.railway.app/scoring#tabSemiFinals" target="_blank" class="feature-card">
                        <div class="icon" style="color:#0891b2"><i class="fas fa-trophy"></i></div>
                        <div class="title">Semi-Finals Sheet <span class="badge badge-sf">SF</span></div>
                        <div class="desc">SF1 + SF2 · Domain I / II / III · Four judges + Chief · 40/50/10.</div>
                        <div class="url">…/scoring#tabSemiFinals</div>
                    </a>

                    <a href="https://merry-intuition-production-1788.up.railway.app/scoring#tabFinals" target="_blank" class="feature-card">
                        <div class="icon" style="color:#d97706"><i class="fas fa-medal"></i></div>
                        <div class="title">Finals Sheet <span class="badge badge-fn">Final</span></div>
                        <div class="desc">F1 + F2 · Domain A / B / C · 45/40/15 weighting · /200 combined.</div>
                        <div class="url">…/scoring#tabFinals</div>
                    </a>

                    <a href="https://merry-intuition-production-1788.up.railway.app/scoring#tabMaster" target="_blank" class="feature-card">
                        <div class="icon"><i class="fas fa-grid-2"></i></div>
                        <div class="title">Master Sheet</div>
                        <div class="desc">Team setup · draw assignment · Grand Total across all 16 teams.</div>
                        <div class="url">…/scoring#tabMaster</div>
                    </a>

                    <a href="https://merry-intuition-production-1788.up.railway.app/scoring#tabSpecial" target="_blank" class="feature-card">
                        <div class="icon" style="color:#7c3aed"><i class="fas fa-star"></i></div>
                        <div class="title">Special Prizes <span class="badge badge-spec">6</span></div>
                        <div class="desc">Best CPR · CRM · Parental Comms · Interprofessional · Video · Uniform.</div>
                        <div class="url">…/scoring#tabSpecial</div>
                    </a>

                </div>
            </div>

            <!-- RIGHT: Info + quick links -->
            <div class="info-panel">

                <div class="info-card">
                    <div class="label">👥 National Coordinators</div>
                    <div class="value">
                        <strong>Dr Manju Kedarnath</strong>
                        <span class="coord"><i class="fas fa-phone-alt"></i> +91 99866 34300</span>
                        <strong style="display:block;margin-top:0.5rem">Dr Pritesh Nagar</strong>
                        <span class="coord"><i class="fas fa-phone-alt"></i> +91 99596 65000</span>
                        <strong style="display:block;margin-top:0.5rem">Dr Supraja Chandrasekhar</strong>
                        <span class="coord"><i class="fas fa-phone-alt"></i> +91 99458 18818</span>
                    </div>
                    <div style="margin-top:1rem">
                        <div class="label">📍 Local Coordinators</div>
                        <div class="value">
                            <strong>Dr Javed</strong>
                            <span class="coord"><i class="fas fa-phone-alt"></i> +91 81436 09989</span>
                            <strong style="display:block;margin-top:0.5rem">Ms Kavita Chandrakar</strong>
                            <span class="coord"><i class="fas fa-phone-alt"></i> +91 96858 63289</span>
                        </div>
                    </div>
                </div>

                <div class="info-card" style="border-left-color:#2b5780">
                    <div class="label">📌 Venues &amp; Dates</div>
                    <div class="value">
                        <strong>22 August</strong> — Preliminary Rounds<br>
                        DHEE Hospitals, Kanakapura Road, Bengaluru
                        <br><br>
                        <strong>23 August</strong> — Semi-Finals &amp; Finals<br>
                        VASA, Bengaluru
                        <br><br>
                        <span style="font-size:0.82rem;color:#2b5780">
                            <i class="fas fa-info-circle" style="color:#f9c74f"></i>
                            Max 16 teams · 4 members each · at least 2 doctors (PG trainees) · min 1 nurse
                        </span>
                    </div>
                </div>

                <div class="info-card" style="border-left-color:#a0c0d0">
                    <div class="label">🏆 Team Eligibility</div>
                    <div class="value" style="font-size:0.86rem">
                        <span class="coord" style="margin-top:0"><i class="fas fa-angle-right"></i> Physicians &amp; residents: &lt;5 yrs post-MD/DNB</span>
                        <span class="coord"><i class="fas fa-angle-right"></i> Nurses &amp; paramedics: no experience limit</span>
                        <span class="coord"><i class="fas fa-angle-right"></i> Members from different hospitals of same org allowed</span>
                        <span class="coord"><i class="fas fa-angle-right"></i> Max 1 person who competed in the previous SimWars</span>
                    </div>
                </div>

                <div class="info-card" style="border-left-color:#d4a017">
                    <div class="label">🗺️ Competition Reference</div>
                    <div class="quick-links">
                        <a href="https://claude.ai/code/artifact/12f7e01d-f7de-4d8a-b62a-1dd8af0439e1" target="_blank" class="quick-link">
                            <i class="fas fa-diagram-project"></i>
                            <span class="link-label">Flow — Full</span>
                            <span class="badge" style="margin-left:auto">All stages</span>
                        </a>
                        <a href="https://claude.ai/code/artifact/41b20ddd-fa61-4b86-8e57-4f81d7417ff9" target="_blank" class="quick-link">
                            <i class="fas fa-sitemap"></i>
                            <span class="link-label">Flow — Clean</span>
                            <span class="badge" style="margin-left:auto">Structure</span>
                        </a>
                        <a href="https://claude.ai/code/artifact/631528d3-55b7-45a7-b758-c2e6192fb7b9" target="_blank" class="quick-link">
                            <i class="fas fa-file-lines"></i>
                            <span class="link-label">Flow — Detailed</span>
                            <span class="badge" style="margin-left:auto">Full cases</span>
                        </a>
                    </div>
                </div>

            </div>
        </div>

        <!-- CASE PACKETS — full width -->
        <div class="cases-section">
            <div class="section-head"><i class="fas fa-folder-open"></i> Case Packets <span style="font-size:0.75rem;font-weight:400;color:#6a8aaa;margin-left:6px">Local files · open on this Mac only</span></div>

            <!-- BLS -->
            <div class="round-group round-bls">
                <div class="round-label"><div class="dot dot-bls"></div> BLS — Prelims Round 1</div>
                <div class="case-grid">
                    <div class="case-card">
                        <div class="case-id">B1</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B1/B1_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B1/B1_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B1/B1_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B1/B1_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                    <div class="case-card">
                        <div class="case-id">B2</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B2/B2_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B2/B2_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B2/B2_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B2/B2_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                    <div class="case-card">
                        <div class="case-id">B3</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B3/B3_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B3/B3_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B3/B3_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B3/B3_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                    <div class="case-card">
                        <div class="case-id">B4</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B4/B4_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B4/B4_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B4/B4_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/B4/B4_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PALS -->
            <div class="round-group round-pals">
                <div class="round-label"><div class="dot dot-pals"></div> PALS — Prelims Round 2</div>
                <div class="case-grid">
                    <div class="case-card">
                        <div class="case-id">P1</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P1/P1_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P1/P1_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P1/P1_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P1/P1_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                    <div class="case-card">
                        <div class="case-id">P2</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P2/P2_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P2/P2_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P2/P2_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P2/P2_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                    <div class="case-card">
                        <div class="case-id">P3</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P3/P3_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P3/P3_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P3/P3_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P3/P3_Actor_Script.pdf" target="_blank">🎭 Actor Script</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P3/P3_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                    <div class="case-card">
                        <div class="case-id">P4</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P4/P4_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P4/P4_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P4/P4_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/P4/P4_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                </div>
            </div>

            <!-- SEMI-FINALS -->
            <div class="round-group round-sf">
                <div class="round-label"><div class="dot dot-sf"></div> Semi-Finals — Round 1 &amp; Round 2</div>
                <div class="case-grid">
                    <div class="case-card">
                        <div class="case-id">R1a</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R1a/R1a_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R1a/R1a_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R1a/R1a_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R1a/R1a_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                    <div class="case-card">
                        <div class="case-id">R1b</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R1b/R1b_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R1b/R1b_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R1b/R1b_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R1b/R1b_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                    <div class="case-card">
                        <div class="case-id">R2a</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R2a/R2a_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R2a/R2a_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R2a/R2a_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R2a/R2a_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                    <div class="case-card">
                        <div class="case-id">R2b</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R2b/R2b_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R2b/R2b_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R2b/R2b_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/R2b/R2b_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                </div>
            </div>

            <!-- FINALS -->
            <div class="round-group round-fn">
                <div class="round-label"><div class="dot dot-fn"></div> Finals</div>
                <div class="case-grid case-grid-2">
                    <div class="case-card">
                        <div class="case-id">F1 — PICU: Crashing on the Vent</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/F1/F1_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/F1/F1_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/F1/F1_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/F1/F1_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                    <div class="case-card">
                        <div class="case-id">F2 — PEM: Tense Abdomen</div>
                        <div class="doc-links">
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/F2/F2_Scenario.pdf" target="_blank">📄 Scenario</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/F2/F2_Cheat_Sheet.pdf" target="_blank">📋 Cheat Sheet</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/F2/F2_Judge_Scoring.pdf" target="_blank">⚖️ Judge Scoring</a>
                            <a class="doc-link" href="file:///Users/manjukedarnath/Library/CloudStorage/Dropbox/AAA%20Pedistars/Simwars/simwars%202026/Scenarios/files/simwars/dist/SimWars_2026/F2/F2_Slide_Deck.pptx" target="_blank">📊 Slide Deck</a>
                        </div>
                    </div>
                </div>
            </div>

        </div><!-- end cases-section -->
    </div><!-- end body -->

    <!-- ══ FOOTER ══ -->
    <div class="footer">
        <i class="fas fa-heart"></i> PediSTARS · 11th Annual National Conference on Healthcare Simulation · Bengaluru 2026
        <span class="sep">|</span> Supported by DHEE Hospitals &amp; VASA
        <br style="display:block;margin-top:6px">
        <span style="opacity:0.5">SIMWARS 2026 · Scoring Engine v8.0</span>
    </div>

</div>
</body>
</html>
"""

@app.route('/home')
def portal():
    return PORTAL_TEMPLATE
@app.route('/simwars-2026-participant-info.html')
def participant_info():
        return send_file(os.path.join(os.path.dirname(__file__), 'simwars-2026-participant-info.html'))


if __name__ == '__main__':
    import os as _os
    port = int(_os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', debug=False, port=port)

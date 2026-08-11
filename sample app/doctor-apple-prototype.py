import streamlit as st

# --- CONSTANTS & STYLE (MATCHA LATTE THEME) ---
st.set_page_config(
    page_title="Doctor Apple — Clinic Intake & Claims",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #EBEFEF 0%, #D1DFD8 100%) !important;
        background-attachment: fixed !important;
        color: #1C2721 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.72) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.45) !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #3B5244 !important;
        font-weight: 600 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .matcha-card {
        background: rgba(255, 255, 255, 0.72) !important;
        backdrop-filter: blur(16px) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(90, 120, 101, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.45) !important;
        margin-bottom: 20px !important;
        color: #1C2721 !important;
    }
    .matcha-card-header {
        border-bottom: 1px solid rgba(59, 82, 68, 0.15) !important;
        padding-bottom: 10px !important;
        margin-bottom: 15px !important;
        color: #3B5244 !important;
        font-weight: 600 !important;
        font-size: 1.2rem !important;
    }
    .allergy-warning {
        background-color: #FFEBEE !important;
        border: 1px solid rgba(198, 40, 40, 0.2) !important;
        color: #C62828 !important;
        padding: 12px !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
        font-weight: bold !important;
        margin-bottom: 15px !important;
    }
    .audit-trail {
        font-family: monospace !important;
        background-color: rgba(255, 255, 255, 0.6) !important;
        border: 1px solid rgba(59, 82, 68, 0.12) !important;
        padding: 10px !important;
        border-radius: 6px !important;
        font-size: 0.8rem !important;
        color: #1C2721 !important;
    }
    .article-card {
        background: rgba(255, 255, 255, 0.72) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.45) !important;
        border-radius: 12px !important;
        padding: 18px !important;
        margin-bottom: 16px !important;
        color: #1C2721 !important;
        box-shadow: 0 4px 20px rgba(90, 120, 101, 0.04) !important;
    }
    /* Streamlit Button override styling */
    div.stButton > button {
        background-color: #3B5244 !important;
        color: white !important;
        border: 1px solid #3B5244 !important;
        border-radius: 20px !important;
        padding: 6px 20px !important;
        font-weight: 500 !important;
        transition: all 0.25s ease !important;
    }
    div.stButton > button:hover {
        background-color: #5A7865 !important;
        border-color: #5A7865 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- MOCK DATA ---
MOCK_PATIENTS = {
    "Meridian Life (Loh Wei Ming - MRDEB)": {
        "name": "Loh Wei Ming", "nric": "S8010946C", "dob": "25/01/80", "gender": "Male",
        "insurer": "Meridian Life Assurance", "insurerCode": "MRDEB", "packageCode": "MRDEB_UW",
        "packageName": "Meridian Life Underwriting Referral",
        "covered": ["Chest X-Ray", "Meridian Life# 10 - HIV Antibody Test", "Treadmill ECG"],
        "allergy": "None", "phone": "98321045", "address": "Blk 23 Marina Boulevard #12-04",
        "postal": "018981", "email": "wei_ming.loh@gmail.com", "visitType": "general"
    },
    "Bluepeak Wellness (Loh Amir - BLPHS)": {
        "name": "Loh Amir", "nric": "S8536477Z", "dob": "25/01/85", "gender": "Male",
        "insurer": "Bluepeak Prosperity Life", "insurerCode": "BLPHS", "packageCode": "WELL2",
        "packageName": "BluePeak Wellness Package (WELL2)",
        "covered": ["Complete History Taking", "Complete Physical Examination", "BMI and Fat Composition", "Blood pressure measurement", "Full Blood Count", "Cholesterol screening", "Liver function screening", "Kidney function screening", "Thyroid function screening", "Resting ECG", "Medical Report Consultation"],
        "allergy": "Sulfa drugs", "phone": "92714803", "address": "Blk 433 Bukit Batok West Ave 6 #06-814",
        "postal": "391369", "email": "amir.loh12@outlook.com", "visitType": "general"
    },
    "Ministry of Learning (Kumar Sheng Yang - MOL0199VME)": {
        "name": "Kumar Sheng Yang", "nric": "S8001691D", "dob": "20/05/77", "gender": "Male",
        "insurer": "Ministry of Learning Civil Service Scheme", "insurerCode": "MOL0199VME", "packageCode": "PEE226",
        "packageName": "Ministry of Learning - Pre-Employment PEE226",
        "covered": ["Pre-employment medical examination", "Resting ECG", "MMR Dose 1 Vaccination"],
        "allergy": "Iodine contrast", "phone": "97439870", "address": "Blk 867 Tampines Street 21 #06-698",
        "postal": "105919", "email": "sheng.wong20@hotmail.com", "visitType": "occupational"
    },
    "Northstar Underwriting (Wong Siti - NSTNBU)": {
        "name": "Wong Siti", "nric": "S2915369H", "dob": "23/09/55", "gender": "Female",
        "insurer": "Northstar Life Assurance", "insurerCode": "NSTNBU", "packageCode": "NSTNBU_UW",
        "packageName": "Northstar Underwriting follow-up requirements",
        "covered": ["Two repeat Urine Examination and Microscopy on different days"],
        "allergy": "Codeine", "phone": "91736621", "address": "Blk 811 Hougang Ave 8 #13-844",
        "postal": "741804", "email": "siti.wong99@yahoo.com", "visitType": "general"
    },
    "Everwell Voucher (Devi Hui Min - EVWME)": {
        "name": "Devi Hui Min", "nric": "T1800429G", "dob": "09/06/98", "gender": "Female",
        "insurer": "Everwell Insurance Group", "insurerCode": "EVWME", "packageCode": "EVWME_VOUCHER",
        "packageName": "Everwell Health Check-up Voucher",
        "covered": ["Medical Examination", "Lipid Profile", "UFEME (Urine)", "Resting ECG"],
        "allergy": "Penicillin", "phone": "89653253", "address": "Blk 382 Bedok North Road #03-685",
        "postal": "626428", "email": "amir.loh6@outlook.com", "visitType": "general"
    }
}

# --- INITIALIZE STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "patient"
if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 1
if "patient_input" not in st.session_state:
    st.session_state.patient_input = {
        "visitType": "Pre-booked",
        "date": None,
        "time": "10:00 AM",
        "prefill": None
    }
if "patient_db" not in st.session_state:
    st.session_state.patient_db = [
        {
            "id": "PT101", "name": "Tan Kai Xuan", "nric": "S4744854C", "type": "Pre-booked",
            "service": "GP Consultation", "insurance": "AIA Singapore", "status": "Awaiting ID check",
            "allergy": "None", "visitType": "general", "prefill": {"dob": "12/04/72", "email": "kai.tan78@gmail.com", "phone": "98127394", "address": "Blk 12 Tampines St 42 #02-12"},
            "log": ["LOG Checked", "Digital registration received"],
            "bill": {"total": 45.0, "covered": 45.0, "copay": 0.0},
            "insurerCode": "AIA_GP", "packageName": "Standard GP Consultation",
            "date": "11/08/2026", "time": "09:30 AM", "queueNumber": "#2001"
        },
        {
            "id": "PT102", "name": "Sarah Jenkins", "nric": "S9876543A", "type": "Pre-booked",
            "service": "General Health Screening", "insurance": "Prudential Assurance", "status": "Consulting",
            "allergy": "Penicillin", "visitType": "general", "prefill": {"dob": "03/12/98", "email": "sarah.j@outlook.com", "phone": "91238472", "address": "Blk 211 Bedok South #08-234"},
            "log": ["LOG Checked", "Physical ID verified at reception"],
            "bill": {"total": 220.0, "covered": 180.0, "copay": 40.0},
            "insurerCode": "PRU_HEALTH", "packageName": "Wellness Plus screening",
            "date": "11/08/2026", "time": "10:00 AM", "queueNumber": "#2002"
        }
    ]
if "policy_db" not in st.session_state:
    st.session_state.policy_db = [
        {"code": "MRDEB", "insurer": "Meridian Life Assurance", "limit": 250.00, "protocol": "Auto-Adjudicate"},
        {"code": "WELL2", "insurer": "Bluepeak Prosperity", "limit": 500.00, "protocol": "Co-Pay Adjudicate"},
        {"code": "MOL0199VME", "insurer": "Ministry of Learning Civil Service Scheme", "limit": 300.00, "protocol": "Auto-Adjudicate"}
    ]
if "master_patients" not in st.session_state:
    import pandas as pd
    try:
        import os
        base_path = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(os.path.dirname(base_path), "Data", "Data", "patient_registration_synthetic.csv")
        df_p = pd.read_csv(csv_path)
        st.session_state.master_patients = df_p.fillna("").to_dict(orient="records")
    except Exception:
        st.session_state.master_patients = []

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    col_c, col_card, col_r = st.columns([1.5, 2, 1.5])
    with col_card:
        st.image("Data/Logo/logo-text.png", use_container_width=True)
        st.markdown("<p style='text-align: center; color: #5A7865; font-weight: 500;'>Clinical Intake & Claims Automation Suite</p>", unsafe_allow_html=True)
        
        role = st.radio(
            "Select Portal Access Role:",
            ["Patient Pre-Registration Portal", "Clinic Staff Dashboard", "TPA Assessor Portal"]
        )
        if st.button("Sign In to Portal", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.user_role = "patient" if "Patient" in role else "staff" if "Staff" in role else "tpa"
            st.rerun()
    st.stop()

# --- SIDEBAR & NAVIGATION ---
role_label = "Patient Portal" if st.session_state.user_role == "patient" else "Clinic Staff Dashboard" if st.session_state.user_role == "staff" else "TPA Assessor Portal"
st.sidebar.image("Data/Logo/logo-text.png", use_container_width=True)
st.sidebar.markdown(f"<div style='text-align:center; font-weight:600; font-size:1.1rem; color:#3B5244; margin-top:-10px; margin-bottom:15px;'>{role_label}</div>", unsafe_allow_html=True)

# Get nav items based on role
if st.session_state.user_role == "patient":
    nav_items = ["Pre-Registration Portal", "Account Profile", "Personal Information", "Policy & Coverage Details", "Patient Care Center & Settings", "Health & Wellness Articles"]
elif st.session_state.user_role == "staff":
    nav_items = ["Staff Dashboard", "Staff Account Details", "Admissions Ledger", "Policy Register", "System Audit Logs", "Regulatory Compliance Bulletin"]
else:
    nav_items = ["Claims Ledger", "Patient Master Registry", "Underwriting Guidelines", "Regulatory Compliance Bulletin"]

selected_panel = st.sidebar.radio("Navigation:", nav_items)

if st.sidebar.button("Sign Out", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.wizard_step = 1
    st.session_state.patient_input["prefill"] = None
    st.rerun()

# --- RENDER PORTAL PANEL ---
st.image("Data/Logo/banner.png", use_container_width=True)

# ==================== A. PATIENT PORTAL ====================
if st.session_state.user_role == "patient":
    if selected_panel == "Pre-Registration Portal":
        st.title("Pre-Registration Intake")
        st.write("Complete clinical intake in advance to skip registration queues on the day of your visit.")
        
        step = st.session_state.wizard_step
        st.markdown(f"**Step {step} of 5:** " + ["Booking Type", "Scan Chit", "Verify Demographics", "Health Questionnaire", "Final Review & Submit"][min(step-1, 4)])
        st.progress(min(step / 5.0, 1.0))
        
        col_l, col_r = st.columns([3, 2])
        
        with col_l:
            if step == 1:
                st.subheader("Step 1: Appointment & Booking Details")
                v_type = st.radio("Select Booking Mode:", ["Pre-booked Appointment", "Walk-in Lobby Check-in"])
                st.session_state.patient_input["visitType"] = v_type
                if "Pre-booked" in v_type:
                    import datetime
                    hours_list = [
                        "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
                        "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM",
                        "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM", "10:00 PM"
                    ]
                    d_val = st.date_input("Preferred Date", min_value=datetime.date.today())
                    t_val = st.selectbox("Preferred Time Slot", hours_list, index=2)
                    st.session_state.patient_input["date"] = str(d_val)
                    st.session_state.patient_input["time"] = t_val
                    
                    # Validation: check if date is today and time has passed
                    now_dt = datetime.datetime.now()
                    t_parsed = None
                    try:
                        t_time = datetime.datetime.strptime(t_val, "%I:%M %p").time()
                        t_parsed = datetime.datetime.combine(d_val, t_time)
                    except Exception:
                        pass
                    
                    if t_parsed and t_parsed < now_dt:
                        st.error("Error: The selected time slot has already passed for today.")
                        st.session_state.time_passed_error = True
                    else:
                        st.session_state.time_passed_error = False
            elif step == 2:
                st.subheader("Step 2: Policy Verification / Referral Chit")
                sel_chit = st.selectbox("Simulate Document Scan:", ["[Select Sample]"] + list(MOCK_PATIENTS.keys()))
                if sel_chit != "[Select Sample]":
                    pat = MOCK_PATIENTS[sel_chit]
                    st.session_state.patient_input["prefill"] = pat
                    st.success(f"✓ Chit verified. Found {pat['insurer']} policy rules.")
            elif step == 3:
                st.subheader("Step 3: Pre-populated Demographics")
                pat = st.session_state.patient_input["prefill"]
                if pat:
                    st.text_input("Full Name (per NRIC)", pat["name"], disabled=True)
                    st.text_input("NRIC/FIN Number", pat["nric"], disabled=True)
                    st.text_input("Matched Policy / Insurer", pat["insurer"], disabled=True)
                    st.text_input("Assigned Screening Package", pat["packageName"], disabled=True)
                else:
                    st.session_state.patient_input["name"] = st.text_input("Full Name (per NRIC)", st.session_state.patient_input.get("name", ""))
                    st.session_state.patient_input["nric"] = st.text_input("NRIC/FIN Number/Passport", st.session_state.patient_input.get("nric", ""))
                    st.text_input("Matched Policy / Insurer", "Self Pay (Walk-in Lobby)", disabled=True)
                    st.text_input("Assigned Screening Package", "GP Consultation", disabled=True)
            elif step == 4:
                st.subheader("Step 4: Adaptive Health Survey")
                pat = st.session_state.patient_input["prefill"]
                if pat:
                    st.text_input("Pre-filled Email Address", pat["email"])
                    st.text_input("Pre-filled Contact Number", pat["phone"])
                    st.text_area("Pre-filled Residential Address", pat["address"])
                    if pat["allergy"] != "None":
                        st.markdown(f"<div class='allergy-warning'>DRUG ALLERGY WARNING: Active allergy to {pat['allergy']} detected.</div>", unsafe_allow_html=True)
                    st.selectbox("Are you currently taking any prescription medications?", ["No", "Yes"])
                else:
                    st.session_state.patient_input["email"] = st.text_input("Email Address", st.session_state.patient_input.get("email", ""))
                    st.session_state.patient_input["phone"] = st.text_input("Contact Number", st.session_state.patient_input.get("phone", ""))
                    st.session_state.patient_input["address"] = st.text_area("Residential Address", st.session_state.patient_input.get("address", ""))
                    st.selectbox("Are you currently taking any prescription medications?", ["No", "Yes"])
            elif step == 5:
                st.subheader("Step 5: Final Confirmation & Signature")
                pat = st.session_state.patient_input["prefill"]
                if pat:
                    st.write(f"**Patient Name:** {pat['name']}")
                    st.write(f"**NRIC/FIN:** {pat['nric']}")
                    st.write(f"**Appointment:** {st.session_state.patient_input['visitType']}")
                    st.write(f"**Sponsor Scheme:** {pat['insurer']}")
                    st.write(f"**Allergies:** {pat['allergy']}")
                else:
                    st.write(f"**Patient Name:** {st.session_state.patient_input.get('name', 'N/A')}")
                    st.write(f"**NRIC/FIN:** {st.session_state.patient_input.get('nric', 'N/A')}")
                    st.write(f"**Appointment:** {st.session_state.patient_input['visitType']}")
                    st.write(f"**Sponsor Scheme:** Self Pay")
                    st.write(f"**Allergies:** None")
                st.checkbox("I confirm that details are bound by PDPA regulations.")
            
            # Nav buttons
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if step > 1 and step <= 5 and st.button("Back"):
                    st.session_state.wizard_step -= 1
                    st.rerun()
            with col_b2:
                if step < 5:
                    is_disabled = (step == 1 and "Pre-booked" in st.session_state.patient_input.get("visitType", "") and st.session_state.get("time_passed_error", False))
                    if st.button("Continue", disabled=is_disabled):
                        st.session_state.wizard_step += 1
                        st.rerun()
                elif step == 5:
                    if st.button("Submit Pre-Registration"):
                        pat = st.session_state.patient_input["prefill"]
                        new_q = 2000 + len(st.session_state.patient_db) + 1
                        
                        import os
                        api_key = os.environ.get("AGNES_AI_API_KEY")
                        log_msg = "Digital registration received"
                        if api_key:
                            log_msg += f" (Auto-synced via Agnes AI API Client: {api_key[:5]}...)"
                        else:
                            log_msg += " (Auto-synced via Agnes AI API Client: Local offline mode)"
                        
                        if pat:
                            name = pat["name"]
                            nric = pat["nric"]
                            service = pat["packageName"]
                            insurance = pat["insurer"]
                            allergy = pat["allergy"]
                            insurer_code = pat["insurerCode"]
                            dob = pat["dob"]
                            email = pat["email"]
                            phone = pat["phone"]
                            address = pat["address"]
                        else:
                            name = st.session_state.patient_input.get("name", "Walk-in Patient")
                            nric = st.session_state.patient_input.get("nric", "S0000000A")
                            service = "GP Consultation"
                            insurance = "Self Pay"
                            allergy = "None"
                            insurer_code = "CASH"
                            dob = "01/01/2000"
                            email = st.session_state.patient_input.get("email", "n/a")
                            phone = st.session_state.patient_input.get("phone", "n/a")
                            address = st.session_state.patient_input.get("address", "n/a")
                            
                        st.session_state.patient_db.append({
                            "id": f"PT{100 + len(st.session_state.patient_db) + 1}",
                            "name": name, "nric": nric,
                            "type": "Pre-booked" if "Pre-booked" in st.session_state.patient_input["visitType"] else "Walk-in",
                            "service": service, "insurance": insurance, "status": "Awaiting ID check",
                            "allergy": allergy, "visitType": "general", "prefill": {"dob": dob, "email": email, "phone": phone, "address": address},
                            "log": ["LOG Checked", log_msg],
                            "bill": {"total": 45.0 if not pat else 200.0, "covered": 0.0 if not pat else 200.0, "copay": 45.0 if not pat else 0.0},
                            "insurerCode": insurer_code, "packageName": service,
                            "date": st.session_state.patient_input.get("date", "Today"),
                            "time": st.session_state.patient_input.get("time", "Lobby"),
                            "queueNumber": f"#{new_q}"
                        })
                        st.session_state.wizard_step = 6
                        st.rerun()
            
            if step == 6:
                st.markdown(f"""
                <div style="background-color: #E8F5E9; border-radius: 12px; padding: 20px; border: 1px solid #7E9E71; text-align: center; margin-top: 20px;">
                    <h3 style="color: #2E7D32 !important; margin: 0;">Pre-Registration Intake Complete</h3>
                    <div style="background-color: white; display: inline-block; padding: 15px; border-radius: 8px; margin: 10px 0; border: 2px dashed #7E9E71;">
                        <span style="font-size: 1.5rem; font-weight: bold; color: #2A3E2C;">YOUR QUEUE TOKEN: #{2000 + len(st.session_state.patient_db)}</span>
                    </div>
                    <p style="font-size: 0.9rem; color: #2E7D32;">REQUIRED ACTION: When you arrive at the clinic, present your physical NRIC/Passport at the counter to activate your slot.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Submit New Pre-registration"):
                    st.session_state.wizard_step = 1
                    st.session_state.patient_input["prefill"] = None
                    st.rerun()

        with col_r:
            st.markdown("""
            <div class="matcha-card">
                <div class="matcha-card-header">Wizard Overview</div>
            </div>
            """, unsafe_allow_html=True)
            st.write(f"**Visit Type:** {st.session_state.patient_input['visitType']}")
            pre = st.session_state.patient_input["prefill"]
            st.write(f"**Insurer Coverage:** {pre['insurerCode'] if pre else 'Awaiting Scan'}")
            st.write(f"**Allergy Alert:** {pre['allergy'] if pre else 'None'}")

    elif selected_panel == "Account Profile":
        st.title("Account Profile")
        st.markdown("""
        <div class="matcha-card">
            <div class="matcha-card-header">Access Credentials</div>
            <p>Username: loh_wei_ming_80</p>
            <p>Role: Insured Patient</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Update Account Settings")

    elif selected_panel == "Personal Information":
        st.title("Personal Information")
        st.text_input("Full Name (as per NRIC/Passport)", "Loh Wei Ming")
        st.text_input("Contact Number", "98321045")
        st.text_input("Email Address", "wei_ming.loh@gmail.com")
        st.text_area("Residential Address", "Blk 23 Marina Boulevard #12-04")
        st.button("Save Profile")

    elif selected_panel == "Policy & Coverage Details":
        st.title("Policy & Coverage Details")
        st.markdown("""
        <div class="matcha-card">
            <div class="matcha-card-header">Active Corporate Insurance Policies</div>
            <p>Meridian Life Assurance (MRDEB) - Fully Covered</p>
            <p>Bluepeak Prosperity (WELL2) - $500.00 Remaining</p>
        </div>
        """, unsafe_allow_html=True)

    elif selected_panel == "Patient Care Center & Settings":
        st.title("Patient Care Center & Settings")
        st.checkbox("Send SMS activation notifications", value=True)
        st.checkbox("Send e-claims reports to Email", value=True)

    elif selected_panel == "Health & Wellness Articles":
        st.title("Health & Wellness Articles")
        st.markdown("""
        <div class="article-card">
            <h4>Understanding Occupational Noise Hazards & Screening Regulations</h4>
            <p>Under government industrial health frameworks, employees working in environments with high noise exposure must undergo baseline audiometry examinations.</p>
        </div>
        <div class="article-card">
            <h4>Managing Dietary Allergies in Clinical Intakes</h4>
            <p>Drug allergies represent key patient safety flags. Ensuring that EHR allergy flags are verified against physical NRIC cards during admission prevents adverse clinical events.</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== B. CLINIC STAFF PORTAL ====================
elif st.session_state.user_role == "staff":
    if selected_panel == "Staff Dashboard":
        st.title("Clinic Intake Queue Dashboard")
        
        # Search & Filter controls
        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
        with col_f1:
            staff_q = st.text_input("Search patients:", placeholder="Search by Queue, Name, or NRIC...")
        with col_f2:
            staff_filter_type = st.selectbox("Appointment Type:", ["ALL", "Pre-booked", "Walk-in"])
        with col_f3:
            staff_filter_status = st.selectbox("Queue Status:", ["ALL", "Awaiting ID check", "Consulting", "Claim Submitted", "Completed"])
            
        filtered_db = []
        for pat in st.session_state.patient_db:
            q_label = pat.get("queueNumber", pat["id"])
            match_query = staff_q.lower() in pat["name"].lower() or staff_q.lower() in pat["nric"].lower() or staff_q.lower() in q_label.lower()
            match_type = staff_filter_type == "ALL" or pat["type"] == staff_filter_type
            match_status = staff_filter_status == "ALL" or pat["status"] == staff_filter_status
            if match_query and match_type and match_status:
                filtered_db.append(pat)
                
        # Admissions List
        st.markdown("### Admissions Queue")
        for idx, pat in enumerate(filtered_db):
            q_label = pat.get("queueNumber", pat["id"])
            with st.expander(f"📌 {q_label} — {pat['name']} ({pat['type']}) | Status: {pat['status']}"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    # Edit / Delete Admission controls directly in the card expander
                    new_name = st.text_input("Name", pat["name"], key=f"edit_name_{idx}")
                    new_nric = st.text_input("NRIC", pat["nric"], key=f"edit_nric_{idx}")
                    new_service = st.text_input("Service", pat["service"], key=f"edit_service_{idx}")
                    new_status = st.selectbox("Status", ["Awaiting ID check", "Consulting", "Claim Submitted (Pending TPA)", "Completed"], index=["Awaiting ID check", "Consulting", "Claim Submitted (Pending TPA)", "Completed"].index(pat["status"]) if pat["status"] in ["Awaiting ID check", "Consulting", "Claim Submitted (Pending TPA)", "Completed"] else 0, key=f"edit_status_{idx}")
                    
                    if st.button("Update Record Details", key=f"save_edit_{idx}"):
                        pat["name"] = new_name
                        pat["nric"] = new_nric
                        pat["service"] = new_service
                        pat["status"] = new_status
                        pat["log"].append("Record details adjusted manually by counter receptionist.")
                        st.success("Admissions details updated!")
                        st.rerun()
                        
                    if st.button("Remove Patient from Queue", key=f"delete_adm_{idx}"):
                        st.session_state.patient_db.remove(pat)
                        st.success("Patient removed.")
                        st.rerun()
                with c2:
                    st.markdown("**Covered Benefits:**")
                    st.write(f"Total: ${pat['bill']['total']:.2f}")
                    st.write(f"Covered: ${pat['bill']['covered']:.2f}")
                    st.write(f"Co-pay: ${pat['bill']['copay']:.2f}")

        # Master Registry Search
        if staff_q and len(staff_q) >= 2:
            st.markdown("---")
            st.markdown("### Found in Patient Master Registry (Offline Lookup)")
            
            matched_master = []
            for mp in st.session_state.get("master_patients", []):
                nric_clean = mp['NRIC/FIN/Passport Number'].upper()
                already_in_queue = any(qp["nric"].upper() == nric_clean for qp in st.session_state.patient_db)
                if already_in_queue:
                    continue
                if staff_q.lower() in mp["Full Name"].lower() or staff_q.upper() in nric_clean:
                    matched_master.append(mp)
            
            if not matched_master:
                st.write("No matching master records found.")
            else:
                for idx_m, mp in enumerate(matched_master[:10]):
                    col_m1, col_m2 = st.columns([3, 1])
                    with col_m1:
                        st.markdown(f"👤 **{mp['Full Name']}** ({mp['NRIC/FIN/Passport Number']})")
                        st.caption(f"DOB: {mp['Date of Birth (DD/MM/YY)']} | Allergy: {mp['Drug Allergy'] or 'None'}")
                    with col_m2:
                        if st.button("Check In Walk-in", key=f"checkin_master_{idx_m}"):
                            new_q = 2000 + len(st.session_state.patient_db) + 1
                            import os
                            api_key = os.environ.get("AGNES_AI_API_KEY")
                            log_msg = "Quick admission checked-in from Patient Master Registry"
                            if api_key:
                                log_msg += f" (Synced via Agnes AI API Client: {api_key[:5]}...)"
                            else:
                                log_msg += " (Synced via Agnes AI API Client: Local offline mode)"
                                
                            st.session_state.patient_db.append({
                                "id": f"PT{100 + len(st.session_state.patient_db) + 1}",
                                "name": mp["Full Name"],
                                "nric": mp["NRIC/FIN/Passport Number"],
                                "type": "Walk-in",
                                "service": "GP Consultation",
                                "insurance": "Self Pay",
                                "status": "Awaiting ID check",
                                "allergy": mp.get("Drug Allergy", "None") or "None",
                                "visitType": "general",
                                "prefill": {"dob": mp["Date of Birth (DD/MM/YY)"], "email": mp["Email"], "phone": mp.get("Contact - Mobile", ""), "address": mp["Address"]},
                                "log": ["LOG Created", log_msg],
                                "bill": {"total": 45.0, "covered": 0.0, "copay": 45.0},
                                "insurerCode": "CASH",
                                "packageName": "GP Consultation",
                                "date": "Today (Walk-in)",
                                "time": "Lobby",
                                "queueNumber": f"#{new_q}"
                            })
                            st.success(f"Checked in {mp['Full Name']} successfully!")
                            st.rerun()

    elif selected_panel == "Staff Account Details":
        st.title("Staff Account Details")
        st.write("**Staff Username:** clinic_staff_01")
        st.write("**Counter Location:** Counter 1")

    elif selected_panel == "Admissions Ledger":
        st.title("Admissions Ledger")
        st.dataframe(st.session_state.patient_db)

    elif selected_panel == "Policy Register":
        st.title("Policy Register")
        
        # Add new policy scheme
        with st.form("add_policy"):
            code = st.text_input("Policy Code")
            insurer = st.text_input("Insurer Name")
            limit = st.number_input("Payout Limit ($)")
            submitted = st.form_submit_button("Add Policy Scheme")
            if submitted and code:
                st.session_state.policy_db.append({"code": code, "insurer": insurer, "limit": limit, "protocol": "Auto-Adjudicate"})
                st.success("Policy added!")
                
        st.write("### Managed Schemes:")
        for idx, pol in enumerate(st.session_state.policy_db):
            st.write(f"**{pol['code']}** — {pol['insurer']} (Limit: ${pol['limit']})")
            if st.button("Delete Scheme", key=f"del_pol_{idx}"):
                st.session_state.policy_db.remove(pol)
                st.rerun()

    elif selected_panel == "System Audit Logs":
        st.title("System Audit Logs")
        st.text_area("Intake Counter Server Console Log output:", "[08:00:12] Counter Server Initialized.\n[09:30:11] Synced PT101 to Clinic Assist.\n[10:00:23] Pushed claims payload to AIA portal.", height=300)

    elif selected_panel == "Regulatory Compliance Bulletin":
        st.title("Regulatory Compliance Bulletin")
        st.markdown("""
        <div class="article-card">
            <h4>MOH Directive 2026: Mandatory Identity Checks at Counters</h4>
            <p>All cliniccounter staff are reminded that physical identification checks must be conducted in person at Counter Reception before admitting patients.</p>
        </div>
        <div class="article-card">
            <h4>PDPA Regulations for Healthcare Providers: Securing EHR</h4>
            <p>Any patient clinical survey data, address particulars, and NRIC keys stored in digital caches must be encrypted at rest.</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== C. TPA ASSESSOR PORTAL ====================
elif st.session_state.user_role == "tpa":
    if selected_panel == "Claims Ledger":
        st.title("Automated TPA claims adjudication feed")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tpa_q = st.text_input("Search claims:", placeholder="Search Claim ID, Name, or NRIC...")
        with col_t2:
            tpa_status = st.selectbox("Claim Status:", ["ALL", "Pending", "Paid", "Rejected"])
            
        claims = [p for p in st.session_state.patient_db if "Claim" in p["status"] or "Paid" in p["status"] or "Approved" in p["status"] or "Rejected" in p["status"]]
        for idx, claim in enumerate(claims):
            with st.container():
                st.markdown(f"#### Claim ID: #CLM-{claim['id']} | Status: {claim['status']}")
                st.write(f"**Covered Payout:** ${claim['bill']['covered']:.2f}")
                
                # Assessor modification option
                new_covered = st.number_input("Adjust Payout ($)", value=claim["bill"]["covered"], key=f"adj_{idx}")
                if st.button("Save Adjustments", key=f"save_adj_{idx}"):
                    claim["bill"]["covered"] = new_covered
                    claim["bill"]["copay"] = max(0.0, claim["bill"]["total"] - new_covered)
                    claim["log"].append(f"Claim payout adjusted manually by TPA Assessor to ${new_covered}")
                    st.success("Reconciliation adjusted!")
                    st.rerun()

    elif selected_panel == "Patient Master Registry":
        st.title("Patient Master Registry")
        st.dataframe(st.session_state.master_patients)

    elif selected_panel == "Underwriting Guidelines":
        st.title("Underwriting Guidelines")
        st.markdown("""
        <div class="matcha-card">
            <div class="matcha-card-header">Verification & Package Mappings</div>
            <p>MRDEB_UW - Meridian Underwriting - Excludes Specialist consults</p>
            <p>WELL2 - Bluepeak Wellness - Excludes Dental & Orthopedics</p>
        </div>
        """, unsafe_allow_html=True)

    elif selected_panel == "Regulatory Compliance Bulletin":
        st.title("Regulatory Compliance Bulletin")
        st.markdown("""
        <div class="article-card">
            <h4>MAS Guidelines on Automated Claims Adjudication Audits</h4>
            <p>All insurance firms and third-party administrators deploying automated AI-driven claim engines must verify that manual assessor adjustment options are available.</p>
        </div>
        """, unsafe_allow_html=True)
st.markdown("---")

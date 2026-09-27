import streamlit as st
import pandas as pd
import json
from datetime import date
from supabase import create_client, Client

# --- CONFIGURATION ---
st.set_page_config(page_title="Kalakeerthi Arts Academy", layout="wide")

# --- SUPABASE INITIALIZATION ---
url = st.secrets.get("SUPABASE_URL")
key = st.secrets.get("SUPABASE_KEY")

if not url or not key:
    st.error("Please configure SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets.")
    st.stop()

supabase: Client = create_client(url, key)

# --- SESSION STATE ---
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# --- WHATSAPP UTILITY ---
def generate_wa_link(phone, text):
    clean_phone = "".join(filter(str.isdigit, str(phone)))
    if len(clean_phone) == 10: clean_phone = f"91{clean_phone}"
    return f"https://wa.me/{clean_phone}?text={text.replace(' ', '%20')}"

# ==========================================
# MODULE 1: PUBLIC WEBSITE
# ==========================================
def public_website():
    st.title("Welcome to Kalakeerthi Arts")
    st.write("Master Bharatanatyam, Zumba, Western Dance, and Music.")
    
    st.subheader("Our Courses")
    c1, c2, c3, c4 = st.columns(4)
    c1.info("🩰 Bharatanatyam")
    c2.info("💃 Zumba")
    c3.info("🎸 Music & Guitar")
    c4.info("🕺 Western Dance")
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.image("https://images.unsplash.com/photo-1547153760-18fc86324498?w=800", caption="Discover your rhythm")
    with col2:
        st.subheader("Join Our Upcoming Event: Garba Night!")
        with st.form("event_lead_form"):
            name = st.text_input("Full Name")
            phone = st.text_input("Mobile / WhatsApp Number")
            interest = st.selectbox("I am interested in", ["Garba Night", "Bharatanatyam", "Zumba"])
            if st.form_submit_button("Join the Guestlist"):
                if name and phone:
                    clean_phone = "".join(filter(str.isdigit, phone))
                    # Check for existing lead to prevent duplicate
                    existing = supabase.table("leads").select("phone").eq("phone", clean_phone).execute()
                    if not existing.data:
                        supabase.table("leads").insert([{
                            "name": name, "phone": clean_phone, "course": interest, "status": "Hot", "notes": "Web Lead"
                        }]).execute()
                    st.success("Registered! We will WhatsApp you the details.")
                else:
                    st.warning("Please provide name and phone.")

# ==========================================
# MODULE 2: STUDENT PORTAL
# ==========================================
def student_portal():
    if not st.session_state.logged_in_user:
        st.subheader("Student Login")
        phone = st.text_input("Mobile Number")
        otp = st.text_input("OTP (Enter '1234' for demo)", type="password")
        if st.button("Login"):
            if otp == "1234" and phone:
                st.session_state.logged_in_user = phone
                st.rerun()
            else:
                st.error("Invalid OTP")
    else:
        st.subheader("My Dashboard")
        if st.button("Logout"):
            st.session_state.logged_in_user = None
            st.rerun()
            
        user_phone = st.session_state.logged_in_user
        res = supabase.table("leads").select("*").eq("phone", user_phone).execute()
        student = res.data[0] if res.data else None
        
        # Access Check
        if student and student.get("status") == "Suspended":
            st.error("🚨 Your access has been suspended due to pending fees. Please contact admin.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.write("### My Schedule")
            st.info(f"**Course:** {student.get('course') if student else 'Bharatanatyam'}")
            st.info(f"**Batch:** {student.get('batch_time') if student else 'Mon/Wed 6:00 PM'}")
        with col2:
            st.write("### Fee Status")
            st.warning("₹2,000 Overdue")
            st.button("Pay Now (Demo)")

# ==========================================
# MODULE 3: ADMIN CRM
# ==========================================
def admin_crm():
    st.title("Admin Command Center")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Lead Management", "Follow-ups", "Student & Access Control", "Data Importer", "Financials"
    ])
    
    # --- TAB 1: LEAD MANAGEMENT ---
    with tab1:
        st.subheader("Manage Leads & Status")
        res = supabase.table("leads").select("*").order("id", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            edited_df = st.data_editor(
                df[['id', 'name', 'phone', 'course', 'status', 'notes']], 
                column_config={
                    "status": st.column_config.SelectboxColumn("Status", options=["Hot", "Warm", "Cold", "Enrolled", "Suspended"]),
                    "id": st.column_config.NumberColumn(disabled=True)
                },
                use_container_width=True, hide_index=True
            )
            if st.button("Save Changes"):
                for _, row in edited_df.iterrows():
                    supabase.table("leads").update({"status": row['status'], "notes": row['notes']}).eq("id", row['id']).execute()
                st.success("Lead statuses updated!")

    # --- TAB 2: FOLLOW UPS ---
    with tab2:
        st.subheader("Today's Calls")
        active_leads = supabase.table("leads").select("*").in_("status", ["Hot", "Warm"]).execute()
        for lead in active_leads.data:
            c1, c2, c3 = st.columns([2, 3, 2])
            c1.write(f"**{lead.get('name')}** - {lead.get('status')}")
            c2.caption(lead.get('notes'))
            msg = f"Hi {lead.get('name')}, greetings from Kalakeerthi Arts! "
            c3.markdown(f"[💬 Chat on WhatsApp]({generate_wa_link(lead.get('phone'), msg)})")
            st.divider()

    # --- TAB 3: STUDENT MANAGER ---
    with tab3:
        st.subheader("Active Students & Access Control")
        students = supabase.table("leads").select("*").in_("status", ["Enrolled", "Suspended"]).execute()
        if students.data:
            sdf = pd.DataFrame(students.data)
            ed_stu = st.data_editor(
                sdf[['id', 'name', 'phone', 'course', 'status']],
                column_config={"status": st.column_config.SelectboxColumn("Access", options=["Enrolled", "Suspended"])},
                use_container_width=True, hide_index=True
            )
            if st.button("Update Access & Fees"):
                for _, row in ed_stu.iterrows():
                    supabase.table("leads").update({"status": row['status']}).eq("id", row['id']).execute()
                st.success("Student access updated!")

    # --- TAB 4: IMPORTER (WITH DEDUPLICATION) ---
    with tab4:
        st.subheader("Import Legacy Data")
        file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])
        if file and st.button("Import Data"):
            df_up = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
            existing_res = supabase.table("leads").select("phone").execute()
            existing_phones = [str(row['phone']) for row in existing_res.data]
            
            inserted = 0
            for _, row in df_up.iterrows():
                phone = str(row.get("WhatsApp Number", "")).strip()
                if phone and phone not in existing_phones:
                    supabase.table("leads").insert([{
                        "name": str(row.get("Full Name", "Unknown")),
                        "phone": phone,
                        "course": str(row.get("Preferred Class Type", "General")),
                        "status": "Cold"
                    }]).execute()
                    inserted += 1
            st.success(f"Imported {inserted} new records. Skipped duplicates.")

    # --- TAB 5: FINANCIALS ---
    with tab5:
        st.subheader("Dynamic Revenue & Commissions")
        # Simulating dynamic calculation based on enrolled students
        enrolled = supabase.table("leads").select("id").eq("status", "Enrolled").execute()
        student_count = len(enrolled.data)
        fee_per_student = 2000
        gross = student_count * fee_per_student
        instructor_cut = gross * 0.40 # 40% Commission
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Gross Revenue", f"₹{gross:,.2f}")
        c2.metric("Instructor Payouts", f"₹{instructor_cut:,.2f}")
        c3.metric("Net Academy Profit", f"₹{(gross - instructor_cut):,.2f}")

# ==========================================
# ROUTING
# ==========================================
st.sidebar.title("Kalakeerthi Arts")
nav = st.sidebar.radio("Navigate", ["Website", "Student Portal", "Admin CRM"])

if nav == "Website": public_website()
elif nav == "Student Portal": student_portal()
elif nav == "Admin CRM": admin_crm()

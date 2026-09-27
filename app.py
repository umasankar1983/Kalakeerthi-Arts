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

# --- SESSION STATE INITIALIZATION ---
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- WHATSAPP UTILITY FUNCTIONS ---
def generate_wa_link(phone, text):
    """Generates a direct 1-click wa.me chat link with international prefix."""
    clean_phone = "".join(filter(str.isdigit, str(phone)))
    if len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"
    return f"https://wa.me/{clean_phone}?text={text.replace(' ', '%20')}"

def build_whatsapp_payload_1to1(phone, template_name, variables):
    """Meta Cloud API payload structure for individual automated notifications."""
    clean_phone = "".join(filter(str.isdigit, str(phone)))
    if len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"
    return json.dumps({
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en_US"},
            "components": [{"type": "body", "parameters": [{"type": "text", "text": v} for v in variables]}]
        }
    })

def build_whatsapp_broadcast_payload(phones_list, template_name):
    """Generates payloads for mass broadcasting."""
    payloads = []
    for phone in phones_list:
        payloads.append(build_whatsapp_payload_1to1(phone, template_name, []))
    return payloads

# ==========================================
# MODULE 1: PUBLIC WEBSITE & LEAD CAPTURE
# ==========================================
def public_website():
    st.title("Welcome to Kalakeerthi Arts")
    st.write("Master Bharatanatyam, Zumba, Western Dance, and Music.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.image("https://images.unsplash.com/photo-1547153760-18fc86324498?w=800", caption="Discover your rhythm")
    
    with col2:
        st.subheader("Join Our Upcoming Event!")
        st.write("**Garba Night** - October 17, 2026")
        st.write("Celebrate with a night of vibrant music, dance, and community.")
        
        with st.form("event_lead_form"):
            st.write("Register for the Event:")
            name = st.text_input("Full Name")
            phone = st.text_input("Mobile / WhatsApp Number")
            interest = st.selectbox("I am interested in", ["Garba Night", "Bharatanatyam", "Zumba", "Music", "Western Dance"])
            submit = st.form_submit_button("Join the Guestlist")
            
            if submit:
                if name and phone:
                    clean_phone = "".join(filter(str.isdigit, phone))
                    try:
                        # Check existing
                        check = supabase.table("leads").select("id").eq("phone", clean_phone).execute()
                        if check.data:
                            st.info("You are already registered! We will contact you soon.")
                        else:
                            supabase.table("leads").insert([{
                                "name": name,
                                "full_name": name,
                                "phone": clean_phone,
                                "whatsapp_number": clean_phone,
                                "course": interest,
                                "preferred_class_type": interest,
                                "status": "Hot",
                                "notes": "Registered via Public Website Form"
                            }]).execute()
                            st.success("You are on the list! We will WhatsApp you the event passes and details.")
                    except Exception as e:
                        st.error(f"Error submitting entry: {e}")
                else:
                    st.warning("Please provide your name and phone number.")

# ==========================================
# MODULE 2: STUDENT PORTAL (OTP & FEES)
# ==========================================
def student_portal():
    if not st.session_state.logged_in_user:
        st.subheader("Student Login")
        phone = st.text_input("Mobile Number")
        otp = st.text_input("OTP (Enter '1234' for demo)", type="password")
        if st.button("Login"):
            if otp == "1234" and phone:
                st.session_state.logged_in_user = "".join(filter(str.isdigit, phone))
                st.session_state.role = "Student"
                st.rerun()
            else:
                st.error("Invalid OTP or Mobile Number")
    else:
        st.subheader("My Dashboard")
        st.info("📢 Announcement: Garba Night passes are now available!")
        
        user_phone = st.session_state.logged_in_user
        student_data = None
        try:
            leads_res = supabase.table("leads").select("*").eq("phone", user_phone).execute()
            if leads_res.data:
                student_data = leads_res.data[0]
        except Exception:
            pass
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("### My Courses")
            if student_data:
                st.write(f"- **{student_data.get('course') or 'Bharatanatyam'}** | {student_data.get('batch_time') or 'Regular Schedule'}")
            else:
                st.write("- **Bharatanatyam (Intermediate)** | Mon, Wed 6 PM")
                st.write("- **Zumba** | Tue, Thu 7 PM")
        
        with col2:
            st.write("### Fee Status")
            st.error("₹2,000 Overdue (Due: 5 days ago)")
            st.button("Pay Now")
        
        if st.button("Logout"):
            st.session_state.logged_in_user = None
            st.session_state.role = None
            st.rerun()

# ==========================================
# MODULE 3, 4 & 5: ADMIN CRM & OPERATIONS
# ==========================================
def admin_crm():
    st.title("Admin CRM & Academy Operations")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Lead Triage", 
        "Daily Follow-ups", 
        "Student Manager & Importer", 
        "Financials & Commissions",
        "WhatsApp Communicator"
    ])
    
    # --- TAB 1: LEAD TRIAGE ---
    with tab1:
        st.subheader("All Active Inquiries")
        try:
            res = supabase.table("leads").select("*").order("id", desc=True).execute()
            df = pd.DataFrame(res.data)
            if not df.empty:
                st.metric("Total Inquiries", len(df))
                disp_cols = [c for c in ["id", "name", "phone", "student_name", "course", "preferred_time", "status", "created_at"] if c in df.columns]
                st.dataframe(df[disp_cols], use_container_width=True)
            else:
                st.info("No leads found in database.")
        except Exception as e:
            st.error(f"Error loading leads: {e}")
            
    # --- TAB 2: DAILY FOLLOW-UPS ---
    with tab2:
        st.subheader("Direct Follow-up Board")
        try:
            res = supabase.table("leads").select("*").order("id", desc=True).limit(20).execute()
            recent_leads = res.data
            if recent_leads:
                for lead in recent_leads:
                    c1, c2, c3 = st.columns([2, 3, 2])
                    lead_name = lead.get("name") or lead.get("full_name") or "Enquiry"
                    lead_phone = lead.get("phone") or lead.get("whatsapp_number") or ""
                    lead_notes = lead.get("notes") or lead.get("course") or "Inquiry"
                    
                    with c1:
                        st.write(f"**{lead_name}** ({lead_phone})")
                    with c2:
                        st.caption(lead_notes[:120] + "..." if len(str(lead_notes)) > 120 else lead_notes)
                    with c3:
                        msg = f"Hi {lead_name}, greetings from Kalakeerthi Arts! Regarding your inquiry..."
                        st.markdown(f"[💬 Chat on WhatsApp]({generate_wa_link(lead_phone, msg)})")
                    st.divider()
            else:
                st.info("No follow-ups scheduled.")
        except Exception as e:
            st.error(f"Error loading follow-ups: {e}")

    # --- TAB 3: STUDENT MANAGER & EXCEL IMPORTER ---
    with tab3:
        st.subheader("Import Inquiries / Legacy Excel")
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".xlsx"):
                    df_upload = pd.read_excel(uploaded_file)
                else:
                    df_upload = pd.read_csv(uploaded_file)
                    
                st.write("### Data Preview:")
                st.dataframe(df_upload.head(5), use_container_width=True)
                
                if st.button("Import All into Cloud Database", type="primary"):
                    df_upload.columns = df_upload.columns.str.strip()
                    
                    # Deduplicate within the file itself
                    phone_col = "WhatsApp Number" if "WhatsApp Number" in df_upload.columns else None
                    initial_count = len(df_upload)
                    if phone_col:
                        df_upload = df_upload.drop_duplicates(subset=[phone_col], keep="first")
                    dropped_count = initial_count - len(df_upload)

                    # Retrieve existing phones from Supabase to prevent duplicate inserts
                    existing_phones = set()
                    try:
                        existing_res = supabase.table("leads").select("phone").execute()
                        if existing_res.data:
                            existing_phones = {str(r.get("phone", "")).strip() for r in existing_res.data if r.get("phone")}
                    except Exception:
                        pass
                    
                    rows_to_insert = []
                    skipped_duplicates = dropped_count

                    for _, row in df_upload.iterrows():
                        phone_raw = row.get("WhatsApp Number", "")
                        phone_val = str(int(phone_raw)) if pd.notnull(phone_raw) and isinstance(phone_raw, (int, float)) else str(phone_raw).strip()
                        
                        # Discard if phone already exists
                        if phone_val and phone_val in existing_phones:
                            skipped_duplicates += 1
                            continue
                        
                        if phone_val:
                            existing_phones.add(phone_val)

                        full_name = str(row.get("Full Name", "")).strip()
                        student_name = str(row.get("Student Name (if different)", "")).strip()
                        display_name = student_name if student_name and student_name.lower() != "no" else full_name
                        
                        ts = row.get("Timestamp")
                        ts_val = ts.isoformat() if pd.notnull(ts) and hasattr(ts, "isoformat") else None
                        
                        compiled_notes = (
                            f"Joined: {row.get('Who is joining?', 'N/A')} | "
                            f"Exp: {row.get('Experience Level', 'N/A')} | "
                            f"Timing: {row.get('Preferred Time', 'N/A')} | "
                            f"Feedback: {row.get('Feedback (if attended)', 'N/A')} | "
                            f"Query: {row.get('Any questions / requirements (Paragraph)', 'N/A')}"
                        )
                        
                        record = {
                            "timestamp": ts_val,
                            "full_name": full_name,
                            "student_name": student_name,
                            "age": str(row.get("Age", "")),
                            "whatsapp_number": phone_val,
                            "email": str(row.get("Email ID", "")),
                            "email_id": str(row.get("Email ID", "")),
                            "address": str(row.get("Address", "")),
                            "who_is_joining": str(row.get("Who is joining?", "")),
                            "experience_level": str(row.get("Experience Level", "")),
                            "preferred_class_type": str(row.get("Preferred Class Type", "")),
                            "preferred_time": str(row.get("Preferred Time", "")),
                            "preferred_days": str(row.get("Preferred Days  ( mention any specific days if you are looking for)", "")),
                            "have_you_attended_demo": str(row.get("Have you attended demo?", "")),
                            "feedback": str(row.get("Feedback (if attended)", "")),
                            "any_questions": str(row.get("Any questions / requirements (Paragraph)", "")),
                            "name": display_name,
                            "phone": phone_val,
                            "status": "Cold",
                            "course": str(row.get("Preferred Class Type", "Dance")),
                            "batch": "Online / Palavakkam",
                            "batch_time": str(row.get("Preferred Time", "")),
                            "counselor": "Unassigned",
                            "fee_due_date": str(date.today()),
                            "notes": compiled_notes
                        }
                        rows_to_insert.append(record)
                    
                    if rows_to_insert:
                        with st.spinner("Importing records into Supabase..."):
                            supabase.table("leads").insert(rows_to_insert).execute()
                            msg = f"Successfully imported {len(rows_to_insert)} new inquiries!"
                            if skipped_duplicates > 0:
                                msg += f" ({skipped_duplicates} duplicate records were dropped)"
                            st.success(msg)
                            st.rerun()
                    else:
                        st.info("All records in this file already exist in the database. No new entries were added.")
            except Exception as e:
                st.error(f"Error importing file: {e}")

    # --- TAB 4: FINANCIALS & COMMISSIONS ---
    with tab4:
        st.subheader("Financial Overview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Gross Fees Collected", "₹45,000")
        c2.metric("Pending Dues", "₹12,500")
        c3.metric("Instructor Commission (40%)", "₹18,000")
        st.success("Retained Academy Profit: ₹27,000")

    # --- TAB 5: WHATSAPP COMMUNICATOR ---
    with tab5:
        st.subheader("Broadcast / Meta Cloud API Messenger")
        template = st.selectbox("Select WhatsApp Template", ["event_invitation", "fee_reminder", "demo_followup"])
        
        # Pull 5 real phone numbers from leads for payload preview
        lead_numbers = []
        try:
            leads_sample = supabase.table("leads").select("phone").limit(5).execute()
            if leads_sample.data:
                lead_numbers = [r["phone"] for r in leads_sample.data if r.get("phone")]
        except Exception:
            pass
        if not lead_numbers:
            lead_numbers = ["916385302653", "919980418484", "918919003588"]
            
        st.write("Recipient Sample (Auto-selected from leads):")
        st.code(", ".join(lead_numbers))
        
        if st.button("Generate Meta Broadcast Payload"):
            payload = build_whatsapp_broadcast_payload(lead_numbers, template)
            st.json(payload)
            st.info("Payload ready for Meta Graph API dispatch.")

# ==========================================
# NAVIGATION ROUTER
# ==========================================
st.sidebar.title("Kalakeerthi Arts")
nav_choice = st.sidebar.radio("Go to", ["Website", "Student Portal", "Admin CRM"])

if nav_choice == "Website":
    public_website()
elif nav_choice == "Student Portal":
    student_portal()
elif nav_choice == "Admin CRM":
    admin_crm()

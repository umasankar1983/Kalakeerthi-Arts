import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

st.set_page_config(page_title="Kalakeerthi Arts CRM", layout="wide")

# 1. Supabase Initialization
url = st.secrets.get("SUPABASE_URL")
key = st.secrets.get("SUPABASE_KEY")

if not url or not key:
    st.error("Please configure SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets.")
    st.stop()

supabase: Client = create_client(url, key)

# 2. Sidebar Navigation
menu = st.sidebar.radio(
    "Navigation",
    ["Counselor Dashboard", "Upload Contacts / Ads"]
)

# ----------------- MODULE: DASHBOARD -----------------
if menu == "Counselor Dashboard":
    st.title("📋 Follow-up Dashboard")
    
    try:
        response = supabase.table("leads").select("*").order("id", desc=True).execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            st.metric("Total Inquiries", len(df))
            display_cols = [c for c in ["name", "phone", "student_name", "preferred_class_type", "status", "notes"] if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info("No leads available. Start by uploading an enquiry sheet.")
    except Exception as e:
        st.error(f"Error fetching leads: {e}")

# ----------------- MODULE: UPLOAD & IMPORT -----------------
elif menu == "Upload Contacts / Ads":
    st.title("📁 Upload Existing Leads & Contacts")
    
    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".xlsx"):
                df_upload = pd.read_excel(uploaded_file)
            else:
                df_upload = pd.read_csv(uploaded_file)
                
            st.write("### Data Preview")
            st.dataframe(df_upload.head(), use_container_width=True)
            
            if st.button("Import All into Cloud Database", type="primary"):
                # Clean and normalize column names (strip extra spaces and lower-case)
                df_upload.columns = df_upload.columns.str.strip()
                
                rows_to_insert = []
                for _, row in df_upload.iterrows():
                    # Handle full name and student name
                    full_name = str(row.get("Full Name", "")).strip()
                    student_name = str(row.get("Student Name (if different)", "")).strip()
                    display_name = student_name if student_name and student_name.lower() != "no" else full_name
                    
                    # Phone formatting
                    phone_raw = row.get("WhatsApp Number", "")
                    phone_val = str(int(phone_raw)) if pd.notnull(phone_raw) and isinstance(phone_raw, (int, float)) else str(phone_raw).strip()
                    
                    # Timestamp handling
                    ts = row.get("Timestamp")
                    ts_val = ts.isoformat() if pd.notnull(ts) and hasattr(ts, "isoformat") else None
                    
                    # Consolidated counselor notes
                    compiled_notes = (
                        f"Joined: {row.get('Who is joining?', 'N/A')} | "
                        f"Exp: {row.get('Experience Level', 'N/A')} | "
                        f"Timing: {row.get('Preferred Time', 'N/A')} | "
                        f"Days: {row.get('Preferred Days  ( mention any specific days if you are looking for)', 'N/A')} | "
                        f"Demo Attended: {row.get('Have you attended demo?', 'N/A')} | "
                        f"Feedback: {row.get('Feedback (if attended)', 'N/A')} | "
                        f"Query: {row.get('Any questions / requirements (Paragraph)', 'N/A')}"
                    )
                    
                    record = {
                        # Exact mapped columns
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
                        # Dashboard standard fields
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
                
                with st.spinner("Uploading to Supabase..."):
                    supabase.table("leads").insert(rows_to_insert).execute()
                    st.success(f"Successfully imported {len(rows_to_insert)} inquiries!")
                    
        except Exception as e:
            st.error(f"Error reading or uploading file: {e}")

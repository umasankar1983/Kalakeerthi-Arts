import streamlit as st
import pandas as pd
import json
from datetime import date, timedelta
from supabase import create_client, Client

st.set_page_config(page_title="Kalakeerthi Arts CRM", layout="wide")

# --- SUPABASE INITIALIZATION ---
url = st.secrets.get("SUPABASE_URL")
key = st.secrets.get("SUPABASE_KEY")

if not url or not key:
    st.error("Please configure SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets.")
    st.stop()

supabase: Client = create_client(url, key)

# --- SESSION STATE ---
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- WHATSAPP UTILITY FUNCTIONS ---
def generate_wa_link(phone, text):
    clean_phone = "".join(filter(str.isdigit, str(phone)))
    if len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"
    return f"https://wa.me/{clean_phone}?text={text.replace(' ', '%20')}"

def build_whatsapp_payload_1to1(phone, template_name, variables):
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
                    # Supports multiple entries per phone (for multiple events/inquiries)
                    supabase.table("leads").insert([{
                        "name": name,
                        "full_name": name,
                        "phone": clean_phone,
                        "whatsapp_number": clean_phone,
                        "course": interest,
                        "event_name": "Garba Night" if "Garba" in interest else None,
                        "preferred_class_type": interest,
                        "status": "Hot",
                        "notes": "Registered via Public Website"
                    }]).execute()
                    st.success("You are on the list! We will WhatsApp you the event details.")
                else:
                    st.warning("Please enter your name and contact number.")

# ==========================================
# MODULE 2: STUDENT PORTAL (OTP & FEES)
# ==========================================
def student_portal():
    if not st.session_state.logged_in_user:
        st.subheader("Student Login")
        phone = st.text_input("Mobile Number")
        otp = st.text_input("OTP (Demo: 1234)", type="password")
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
        student_records = []
        try:
            res = supabase.table("students").select("*").eq("phone", user_phone).execute()
            student_records = res.data
        except Exception:
            pass
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("### My Active Courses")
            if student_records:
                for s in student_records:
                    st.write(f"- **{s.get('course')}** | Timing: {s.get('batch_timing', 'Regular')}")
            else:
                st.write("- **Bharatanatyam (Intermediate)** | Mon, Wed 6 PM")
        
        with col2:
            st.write("### Fee Status")
            if student_records:
                for s in student_records:
                    fee_amt = s.get('fee_amount', 0)
                    st.metric(f"{s.get('course')} Fee", f"₹{fee_amt}", delta=s.get('fee_status', 'Pending'))
            else:
                st.error("₹2,000 Overdue")
            st.button("Pay Now")
        
        if st.button("Logout"):
            st.session_state.logged_in_user = None
            st.session_state.role = None
            st.rerun()

# ==========================================
# MODULE 3: ADMIN CRM & WORKFLOW ENGINE
# ==========================================
def admin_crm():
    st.title("Admin CRM & Academy Operations")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Lead Triage & Conversion", 
        "Edit Lead Details",
        "Daily Follow-ups", 
        "Student & Event Fee Manager",
        "Student Manager & Importer", 
        "WhatsApp Communicator"
    ])
    
    # ----------------------------------------------------
    # TAB 1: LEAD TRIAGE, FILTER & CONVERSION
    # ----------------------------------------------------
    with tab1:
        st.subheader("Lead Triage & Actions")
        
        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            status_filter = st.selectbox(
                "Filter by Lead Status", 
                ["All", "Hot", "Warm", "Cold", "Converted - Student", "Converted - Attendee"]
            )
        with f_col2:
            search_query = st.text_input("Search by Name or Phone")
            
        try:
            query = supabase.table("leads").select("*").order("id", desc=True)
            if status_filter != "All":
                query = query.eq("status", status_filter)
            res = query.execute()
            leads_data = res.data or []
            
            if search_query:
                leads_data = [
                    l for l in leads_data 
                    if search_query.lower() in str(l.get("name", "")).lower() or search_query in str(l.get("phone", ""))
                ]
            
            st.metric("Total Filtered Leads", len(leads_data))
            
            if leads_data:
                # Build selection dataframe
                df_leads = pd.DataFrame(leads_data)
                
                # Checkbox selection for bulk action
                st.write("#### Select Leads for Bulk Actions")
                selected_ids = []
                
                # Action toolbars
                action_col1, action_col2, action_col3 = st.columns(3)
                with action_col1:
                    new_bulk_status = st.selectbox("Update Status To", ["Hot", "Warm", "Cold", "Not Interested"])
                    if st.button("Apply Status to Selected"):
                        if "selected_lead_ids" in st.session_state and st.session_state.selected_lead_ids:
                            for lid in st.session_state.selected_lead_ids:
                                supabase.table("leads").update({"status": new_bulk_status}).eq("id", lid).execute()
                            st.success(f"Updated {len(st.session_state.selected_lead_ids)} leads to {new_bulk_status}!")
                            st.rerun()
                        else:
                            st.warning("Please select at least one lead below.")
                
                with action_col2:
                    st.markdown("**Convert to Regular Student**")
                    student_course = st.selectbox("Course", ["Bharatanatyam", "Zumba", "Western Dance", "Carnatic Music"], key="conv_c")
                    student_fee = st.number_input("Monthly Fee (₹)", value=2500, step=500, key="conv_f")
                    if st.button("Convert to Student(s)"):
                        if "selected_lead_ids" in st.session_state and st.session_state.selected_lead_ids:
                            for lid in st.session_state.selected_lead_ids:
                                lead_item = next((item for item in leads_data if item["id"] == lid), None)
                                if lead_item:
                                    # Add to students
                                    supabase.table("students").insert([{
                                        "name": lead_item.get("name") or lead_item.get("full_name"),
                                        "phone": lead_item.get("phone"),
                                        "course": student_course,
                                        "batch_timing": lead_item.get("preferred_time") or "Weekday Morning",
                                        "fee_amount": student_fee,
                                        "fee_status": "Pending",
                                        "fee_due_date": str(date.today() + timedelta(days=7))
                                    }]).execute()
                                    # Update lead status
                                    supabase.table("leads").update({"status": "Converted - Student"}).eq("id", lid).execute()
                            st.success("Successfully converted to Enrolled Students!")
                            st.rerun()
                
                with action_col3:
                    st.markdown("**Convert to Event Attendee**")
                    event_title = st.selectbox("Event", ["Garba Night - Oct 17", "Workshop", "Annual Recital"], key="ev_name")
                    pass_type = st.selectbox("Pass Type", ["Standard Entry (₹350)", "VIP Couple (₹700)", "Family Pass (₹1200)"])
                    if st.button("Add to Event Guestlist"):
                        if "selected_lead_ids" in st.session_state and st.session_state.selected_lead_ids:
                            for lid in st.session_state.selected_lead_ids:
                                lead_item = next((item for item in leads_data if item["id"] == lid), None)
                                if lead_item:
                                    supabase.table("event_attendees").insert([{
                                        "name": lead_item.get("name") or lead_item.get("full_name"),
                                        "phone": lead_item.get("phone"),
                                        "event_name": event_title,
                                        "pass_type": pass_type,
                                        "payment_status": "Unpaid",
                                        "amount_paid": 0
                                    }]).execute()
                                    supabase.table("leads").update({"status": "Converted - Attendee"}).eq("id", lid).execute()
                            st.success("Added to Event Guestlist!")
                            st.rerun()
                
                st.divider()
                
                # Interactive Table with Selectors
                display_cols = ["id", "name", "phone", "course", "preferred_time", "status", "created_at"]
                available_cols = [c for c in display_cols if c in df_leads.columns]
                
                # Enable row selections
                selected_lead_ids = []
                for idx, row in df_leads.iterrows():
                    c_chk, c_info = st.columns([1, 15])
                    with c_chk:
                        is_sel = st.checkbox("", key=f"sel_{row['id']}")
                        if is_sel:
                            selected_lead_ids.append(row["id"])
                    with c_info:
                        st.write(
                            f"**#{row.get('id')} | {row.get('name')}** — {row.get('phone')} | "
                            f"**Status:** `{row.get('status')}` | **Course/Event:** {row.get('course')} | "
                            f"**Timing:** {row.get('preferred_time', 'N/A')}"
                        )
                st.session_state.selected_lead_ids = selected_lead_ids
            else:
                st.info("No leads match the selected filter.")
        except Exception as e:
            st.error(f"Error loading leads: {e}")

    # ----------------------------------------------------
    # TAB 2: EDIT LEAD DETAILS
    # ----------------------------------------------------
    with tab2:
        st.subheader("Edit Lead Information")
        try:
            leads_all = supabase.table("leads").select("id, name, phone, course, status, notes").order("id", desc=True).execute().data
            if leads_all:
                lead_options = {f"#{l['id']} - {l.get('name')} ({l.get('phone')})": l for l in leads_all}
                selected_label = st.selectbox("Select Lead to Edit", list(lead_options.keys()))
                current_lead = lead_options[selected_label]
                
                with st.form("edit_lead_form"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        new_name = st.text_input("Name", value=current_lead.get("name") or "")
                        new_phone = st.text_input("Mobile / WhatsApp", value=current_lead.get("phone") or "")
                        new_course = st.text_input("Course / Event", value=current_lead.get("course") or "")
                    with col_e2:
                        status_list = ["Hot", "Warm", "Cold", "Converted - Student", "Converted - Attendee", "Closed"]
                        cur_status = current_lead.get("status", "Cold")
                        stat_idx = status_list.index(cur_status) if cur_status in status_list else 2
                        new_status = st.selectbox("Status", status_list, index=stat_idx)
                        new_notes = st.text_area("Notes / Requirements", value=current_lead.get("notes") or "")
                    
                    if st.form_submit_button("Save Changes"):
                        clean_ph = "".join(filter(str.isdigit, new_phone))
                        supabase.table("leads").update({
                            "name": new_name,
                            "full_name": new_name,
                            "phone": clean_ph,
                            "whatsapp_number": clean_ph,
                            "course": new_course,
                            "status": new_status,
                            "notes": new_notes
                        }).eq("id", current_lead["id"]).execute()
                        st.success("Lead details updated successfully!")
                        st.rerun()
            else:
                st.info("No leads available to edit.")
        except Exception as e:
            st.error(f"Error fetching lead: {e}")

    # ----------------------------------------------------
    # TAB 3: DAILY FOLLOW-UPS
    # ----------------------------------------------------
    with tab3:
        st.subheader("Direct Follow-up Board")
        try:
            res = supabase.table("leads").select("*").in_("status", ["Hot", "Warm"]).order("id", desc=True).limit(20).execute()
            priority_leads = res.data
            if priority_leads:
                for lead in priority_leads:
                    c1, c2, c3 = st.columns([2, 3, 2])
                    lead_name = lead.get("name") or lead.get("full_name") or "Enquiry"
                    lead_phone = lead.get("phone") or lead.get("whatsapp_number") or ""
                    lead_notes = lead.get("notes") or lead.get("course") or "Inquiry"
                    lead_status = lead.get("status")
                    
                    with c1:
                        st.write(f"**{lead_name}** ({lead_phone})")
                        st.caption(f"Status: `{lead_status}`")
                    with c2:
                        st.write(lead_notes[:120] + "..." if len(str(lead_notes)) > 120 else lead_notes)
                    with c3:
                        msg = f"Hi {lead_name}, greetings from Kalakeerthi Arts! Regarding your inquiry for {lead.get('course', 'classes')}..."
                        st.markdown(f"[💬 Chat on WhatsApp]({generate_wa_link(lead_phone, msg)})")
                    st.divider()
            else:
                st.info("No active Hot or Warm leads requiring follow-up.")
        except Exception as e:
            st.error(f"Error loading follow-ups: {e}")

    # ----------------------------------------------------
    # TAB 4: EDITABLE FEES & PAYMENT REMINDERS
    # ----------------------------------------------------
    with tab4:
        st.subheader("Fee Tracking & Payment Reminders")
        fee_view = st.radio("View Trackers by", ["Regular Enrolled Students", "Event Attendees"], horizontal=True)
        
        if fee_view == "Regular Enrolled Students":
            try:
                res_students = supabase.table("students").select("*").order("id", desc=True).execute()
                students_list = res_students.data or []
                
                if students_list:
                    # Class Filter
                    classes = sorted(list(set([s.get("course", "General") for s in students_list])))
                    selected_class = st.selectbox("Filter by Class", ["All Classes"] + classes)
                    
                    filtered_students = students_list
                    if selected_class != "All Classes":
                        filtered_students = [s for s in students_list if s.get("course") == selected_class]
                    
                    st.write(f"### {selected_class} Students ({len(filtered_students)})")
                    
                    for s in filtered_students:
                        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                        with c1:
                            st.write(f"**{s.get('name')}**")
                            st.caption(f"📞 {s.get('phone')} | {s.get('course')}")
                        with c2:
                            st.write(f"Due Date: **{s.get('fee_due_date', 'N/A')}**")
                            st.write(f"Amount: **₹{s.get('fee_amount', 0)}**")
                        with c3:
                            current_stat = s.get("fee_status", "Pending")
                            new_stat = st.selectbox(
                                "Payment Status", 
                                ["Pending", "Paid", "Overdue"], 
                                index=["Pending", "Paid", "Overdue"].index(current_stat) if current_stat in ["Pending", "Paid", "Overdue"] else 0,
                                key=f"stat_s_{s['id']}"
                            )
                            if new_stat != current_stat:
                                supabase.table("students").update({"fee_status": new_stat}).eq("id", s["id"]).execute()
                                st.success("Updated!")
                                st.rerun()
                        with c4:
                            fee_msg = f"Dear {s.get('name')}, your academy fee of ₹{s.get('fee_amount')} for {s.get('course')} is {s.get('fee_status')}. Please complete the payment. Thank you!"
                            st.markdown(f"[📲 Send Reminder]({generate_wa_link(s.get('phone'), fee_msg)})")
                        st.divider()
                else:
                    st.info("No enrolled students found. Convert hot leads from Tab 1 to see them here.")
            except Exception as e:
                st.error(f"Error: {e}")
                
        else:
            # Event Attendees Tracker
            try:
                res_attendees = supabase.table("event_attendees").select("*").order("id", desc=True).execute()
                attendees_list = res_attendees.data or []
                
                if attendees_list:
                    events = sorted(list(set([a.get("event_name", "Garba Night") for a in attendees_list])))
                    selected_event = st.selectbox("Filter by Event", ["All Events"] + events)
                    
                    filtered_attendees = attendees_list
                    if selected_event != "All Events":
                        filtered_attendees = [a for a in attendees_list if a.get("event_name") == selected_event]
                    
                    st.write(f"### {selected_event} Attendees ({len(filtered_attendees)})")
                    
                    for a in filtered_attendees:
                        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                        with c1:
                            st.write(f"**{a.get('name')}**")
                            st.caption(f"📞 {a.get('phone')} | {a.get('pass_type')}")
                        with c2:
                            st.write(f"Event: **{a.get('event_name')}**")
                            st.write(f"Pass: **{a.get('pass_type')}**")
                        with c3:
                            pay_stat = a.get("payment_status", "Unpaid")
                            new_pay = st.selectbox(
                                "Pass Status", 
                                ["Unpaid", "Paid - Confirmed", "Cancelled"], 
                                index=["Unpaid", "Paid - Confirmed", "Cancelled"].index(pay_stat) if pay_stat in ["Unpaid", "Paid - Confirmed", "Cancelled"] else 0,
                                key=f"stat_a_{a['id']}"
                            )
                            if new_pay != pay_stat:
                                supabase.table("event_attendees").update({"payment_status": new_pay}).eq("id", a["id"]).execute()
                                st.success("Updated!")
                                st.rerun()
                        with c4:
                            event_msg = f"Hi {a.get('name')}, your pass for {a.get('event_name')} ({a.get('pass_type')}) is currently {a.get('payment_status')}. Click here to complete registration."
                            st.markdown(f"[📲 Send Pass Link]({generate_wa_link(a.get('phone'), event_msg)})")
                        st.divider()
                else:
                    st.info("No event attendees found. Convert event leads from Tab 1 to see them here.")
            except Exception as e:
                st.error(f"Error: {e}")

    # ----------------------------------------------------
    # TAB 5: STUDENT MANAGER & EXCEL IMPORTER
    # ----------------------------------------------------
    with tab5:
        st.subheader("Import Inquiries / Legacy Excel")
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                df_upload = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
                st.write("### Data Preview:")
                st.dataframe(df_upload.head(5), use_container_width=True)
                
                if st.button("Import All into Cloud Database", type="primary"):
                    df_upload.columns = df_upload.columns.str.strip()
                    
                    rows_to_insert = []
                    for _, row in df_upload.iterrows():
                        phone_raw = row.get("WhatsApp Number", "")
                        phone_val = str(int(phone_raw)) if pd.notnull(phone_raw) and isinstance(phone_raw, (int, float)) else str(phone_raw).strip()
                        
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
                            st.success(f"Successfully imported {len(rows_to_insert)} records into Supabase!")
                            st.rerun()
            except Exception as e:
                st.error(f"Error importing file: {e}")

    # ----------------------------------------------------
    # TAB 6: WHATSAPP COMMUNICATOR
    # ----------------------------------------------------
    with tab6:
        st.subheader("Broadcast / Meta Cloud API Messenger")
        template = st.selectbox("Select WhatsApp Template", ["event_invitation", "fee_reminder", "demo_followup"])
        
        sample_phones = ["916385302653", "919980418484", "918919003588"]
        st.write("Recipient Sample:")
        st.code(", ".join(sample_phones))
        
        if st.button("Generate Meta Broadcast Payload"):
            payload = [build_whatsapp_payload_1to1(p, template, []) for p in sample_phones]
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

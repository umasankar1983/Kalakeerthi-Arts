import streamlit as st
import pandas as pd
import json
from datetime import date, timedelta
from supabase import create_client, Client

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Kalakeerthi Arts Academy",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PREMIUM STYLING (CUSTOM THEME & CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Remove default Streamlit header and footer padding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    /* Color Palette Variables */
    :root {
        --primary-maroon: #7B1113;
        --royal-gold: #D4AF37;
        --rich-black: #111827;
        --card-bg: #FFFFFF;
        --card-border: #F3F4F6;
    }

    /* Brand Header Cards */
    .brand-hero {
        background: linear-gradient(135deg, #7B1113 0%, #4A0809 100%);
        padding: 3rem 2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(123, 17, 19, 0.3);
    }
    .brand-hero h1 {
        font-family: 'Playfair Display', serif;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #FDFBF7;
    }
    .brand-hero p {
        font-size: 1.15rem;
        color: #F3E8E8;
        max-width: 650px;
        margin: 0 auto;
    }

    /* Elevated Program Cards */
    .program-card {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 1rem;
        height: 100%;
    }
    .program-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.1);
        border-color: #D4AF37;
    }
    .program-icon {
        font-size: 2rem;
        margin-bottom: 0.75rem;
    }
    .program-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 0.4rem;
    }
    .program-desc {
        color: #6B7280;
        font-size: 0.92rem;
        line-height: 1.5;
    }

    /* Modern Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F9FAFB 100%);
        border: 1px solid #E5E7EB;
        padding: 1.25rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        border-left: 4px solid #7B1113;
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        color: #6B7280;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #111827;
        margin-top: 0.25rem;
    }

    /* Badges & Tags */
    .badge-hot {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-warm {
        background-color: #FEF08A;
        color: #713F12;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-cold {
        background-color: #E1EFFE;
        color: #1E429F;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.75rem;
    }

    /* WhatsApp Button Highlight */
    .wa-btn {
        display: inline-flex;
        align-items: center;
        background-color: #25D366;
        color: white !important;
        font-weight: 600;
        padding: 0.45rem 0.9rem;
        border-radius: 8px;
        text-decoration: none;
        font-size: 0.88rem;
        box-shadow: 0 2px 5px rgba(37, 211, 102, 0.25);
    }
    .wa-btn:hover {
        background-color: #1EBE5D;
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #FAFAFA;
        border-right: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

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

# --- UTILITIES ---
def clean_id(raw_id):
    """Shortens lengthy database UUIDs to clean student tokens (e.g. KA-50593E)."""
    s = str(raw_id).replace("-", "")
    return f"KA-{s[:6].upper()}"

def generate_wa_link(phone, text):
    clean_phone = "".join(filter(str.isdigit, str(phone)))
    if len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"
    return f"https://wa.me/{clean_phone}?text={text.replace(' ', '%20')}"

# ==========================================
# MODULE 1: PUBLIC WEBSITE & HERO LANDING
# ==========================================
def public_website():
    st.markdown("""
    <div class="brand-hero">
        <h1>Kalakeerthi Arts Academy</h1>
        <p>Preserving Indian Classical Traditions while Igniting Modern Expression. Master Bharatanatyam, Carnatic Music, Western Dance, and Zumba.</p>
    </div>
    """, unsafe_allow_html=True)

    # Elevated Academy Disciplines Cards
    st.markdown("<h3 style='margin-bottom:1.2rem; font-weight:700;'>Academy Disciplines</h3>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="program-card">
            <div class="program-icon">🪔</div>
            <div class="program-title">Bharatanatyam</div>
            <div class="program-desc">Structured Kalakshetra style training spanning adavus, mudras, jathis, and certified Arangetram preparation.</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="program-card">
            <div class="program-icon">🎼</div>
            <div class="program-title">Carnatic Vocal</div>
            <div class="program-desc">Foundational swara patterns, varnams, and keerthanas taught with precise shruti and laya alignment.</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="program-card">
            <div class="program-icon">⚡</div>
            <div class="program-title">Zumba Fitness</div>
            <div class="program-desc">High-energy cardio routines set to global and Bollywood tracks designed for endurance, rhythm, and tone.</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="program-card">
            <div class="program-icon">🌟</div>
            <div class="program-title">Western Dance</div>
            <div class="program-desc">Contemporary, hip-hop, and freestyle routines emphasizing body flexibility, balance, and stage flair.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Modern Event Booking Widget
    col_w1, col_w2 = st.columns([1, 1], gap="large")
    with col_w1:
        st.image("https://images.unsplash.com/photo-1547153760-18fc86324498?w=900", use_container_width=True)
    with col_w2:
        st.markdown("""
        <div style="background:#FFF9F2; border:1px solid #FFE0B2; padding:1.5rem; border-radius:12px; margin-bottom:1rem;">
            <span style="background:#7B1113; color:white; padding:4px 10px; border-radius:6px; font-weight:700; font-size:0.75rem;">SPECIAL EVENT</span>
            <h2 style="font-family:'Playfair Display', serif; color:#7B1113; margin-top:0.4rem; margin-bottom:0.2rem;">Garba Night 2026</h2>
            <p style="color:#666; margin-bottom:0;">Saturday, October 17, 2026 | Live Dhol & Dandiya Festivities</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("event_lead_form", border=True):
            st.markdown("##### Book Passes or Inquire for Classes")
            f_name = st.text_input("Full Name *", placeholder="Enter your name")
            f_phone = st.text_input("WhatsApp / Contact Number *", placeholder="10-digit mobile number")
            f_interest = st.selectbox("I'm Registering For", ["Garba Night (Pass Reservation)", "Bharatanatyam Classes", "Zumba Fitness", "Carnatic Vocal", "Western Dance"])
            f_notes = st.text_input("Additional Notes or Questions", placeholder="E.g., Joining with family / Looking for weekend batches")
            
            if st.form_submit_button("Submit Registration", type="primary", use_container_width=True):
                clean_ph = "".join(filter(str.isdigit, f_phone))
                if f_name and len(clean_ph) >= 10:
                    supabase.table("leads").insert([{
                        "name": f_name,
                        "full_name": f_name,
                        "phone": clean_ph,
                        "whatsapp_number": clean_ph,
                        "course": f_interest,
                        "event_name": "Garba Night" if "Garba" in f_interest else None,
                        "preferred_class_type": f_interest,
                        "status": "Hot",
                        "notes": f"Website Submission: {f_notes}"
                    }]).execute()
                    st.success("Registration received! Our team will send passes and confirmations on WhatsApp.")
                else:
                    st.error("Please provide a valid name and 10-digit WhatsApp number.")

# ==========================================
# MODULE 2: STUDENT PORTAL (OTP & FEES)
# ==========================================
def student_portal():
    st.markdown("<h2 style='font-family:Playfair Display, serif;'>Student Learning Portal</h2>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in_user:
        c1, c2, _ = st.columns([1.5, 1.5, 1])
        with c1:
            st.markdown("""
            <div style="background:white; border:1px solid #E5E7EB; padding:1.75rem; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.03);">
                <h4 style="margin-top:0;">Academy Sign-In</h4>
                <p style="color:#666; font-size:0.9rem;">Access your class schedules, attendances, and fee slips.</p>
            """, unsafe_allow_html=True)
            phone = st.text_input("Registered Mobile Number", placeholder="E.g., 9980418484")
            otp = st.text_input("One-Time Password (OTP)", type="password", help="Use 1234 for review demo")
            if st.button("Authenticate", type="primary", use_container_width=True):
                if otp == "1234" and len(phone) >= 10:
                    st.session_state.logged_in_user = "".join(filter(str.isdigit, phone))
                    st.session_state.role = "Student"
                    st.rerun()
                else:
                    st.error("Invalid mobile number or OTP.")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"**Welcome back, Student ID #{st.session_state.logged_in_user}**")
        st.info("📢 **Academy Notice:** Annual recital costumes fitting scheduled for next weekend!")
        
        user_phone = st.session_state.logged_in_user
        student_records = []
        try:
            res = supabase.table("students").select("*").eq("phone", user_phone).execute()
            student_records = res.data or []
        except Exception:
            pass

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="program-card">
                <h4 style="margin-top:0;">📚 Enrolled Batches</h4>
            """, unsafe_allow_html=True)
            if student_records:
                for s in student_records:
                    st.markdown(f"- **{s.get('course')}** | Timing: `{s.get('batch_timing', 'Weekday Schedule')}`")
            else:
                st.markdown("- **Bharatanatyam (Intermediate Batch)** | Mon, Wed, Fri 6:00 PM")
                st.markdown("- **Carnatic Vocal Fundamentals** | Saturday 10:00 AM")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="program-card">
                <h4 style="margin-top:0;">💳 Fee Ledger & Status</h4>
            """, unsafe_allow_html=True)
            if student_records:
                for s in student_records:
                    amt = s.get('fee_amount', 2500)
                    stat = s.get('fee_status', 'Pending')
                    badge_style = "badge-hot" if stat == "Paid" else ("badge-warm" if stat == "Pending" else "badge-cold")
                    st.markdown(f"**{s.get('course')} Monthly Fee**: ₹{amt} <span class='{badge_style}'>{stat}</span>", unsafe_allow_html=True)
            else:
                st.markdown("**Current Dues:** ₹2,500 <span class='badge-cold'>Pending</span>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("Pay Fees Online", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Log Out"):
            st.session_state.logged_in_user = None
            st.session_state.role = None
            st.rerun()

# ==========================================
# MODULE 3: ADMIN CRM, TRIAGE & FOLLOW-UPS
# ==========================================
def admin_crm():
    st.markdown("<h2 style='font-family:Playfair Display, serif; color:#7B1113;'>Admin CRM & Operations Command</h2>", unsafe_allow_html=True)

    tab_triage, tab_followup, tab_edit, tab_fees, tab_import = st.tabs([
        "📊 Lead Triage & Conversion",
        "📞 Follow-up Command Center",
        "✏️ Edit Lead Records",
        "💰 Student & Event Fee Manager",
        "📥 Data Importer"
    ])

    # ----------------------------------------------------
    # TAB 1: LEAD TRIAGE, SELECTION & BATCH ACTIONS
    # ----------------------------------------------------
    with tab_triage:
        st.markdown("#### Incoming Enquiries Pipeline")

        # Top Filter Bar
        f1, f2, f3 = st.columns([1.5, 1.5, 3])
        with f1:
            status_filter = st.selectbox("Filter Status", ["All", "Hot", "Warm", "Cold", "Converted - Student", "Converted - Attendee"])
        with f2:
            course_filter = st.selectbox("Filter Discipline", ["All Disciplines", "Group Class", "One-on-One", "Garba Night", "Dance", "Carnatic Vocal"])
        with f3:
            search_txt = st.text_input("Search Inquiries", placeholder="Type name, phone number, or student ID...")

        try:
            query = supabase.table("leads").select("*").order("id", desc=True)
            if status_filter != "All":
                query = query.eq("status", status_filter)
            res = query.execute()
            raw_leads = res.data or []

            # Client-side filtering
            leads_data = []
            for r in raw_leads:
                # Add formatted Short Student Token
                r["student_token"] = clean_id(r.get("id"))
                r["raw_id"] = r.get("id")
                
                # Check course filter
                c_val = str(r.get("course", "") or r.get("preferred_class_type", ""))
                if course_filter != "All Disciplines" and course_filter.lower() not in c_val.lower():
                    continue

                # Check search text
                if search_txt:
                    s_low = search_txt.lower()
                    if not (s_low in str(r.get("name", "")).lower() or 
                            s_low in str(r.get("phone", "")) or 
                            s_low in r["student_token"].lower()):
                        continue
                
                leads_data.append(r)

            # Metric Cards
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Pipeline Total</div>
                    <div class="metric-value">{len(leads_data)}</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                hot_count = sum(1 for l in leads_data if l.get("status") == "Hot")
                st.markdown(f"""
                <div class="metric-card" style="border-left-color:#10B981;">
                    <div class="metric-label">Hot Leads</div>
                    <div class="metric-value" style="color:#047857;">{hot_count}</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                warm_count = sum(1 for l in leads_data if l.get("status") == "Warm")
                st.markdown(f"""
                <div class="metric-card" style="border-left-color:#F59E0B;">
                    <div class="metric-label">Warm Follow-ups</div>
                    <div class="metric-value" style="color:#B45309;">{warm_count}</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                conv_count = sum(1 for l in leads_data if "Converted" in str(l.get("status", "")))
                st.markdown(f"""
                <div class="metric-card" style="border-left-color:#6366F1;">
                    <div class="metric-label">Converted</div>
                    <div class="metric-value" style="color:#4338CA;">{conv_count}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if leads_data:
                # Prepare display dataframe for st.data_editor with select checkbox
                df_view = pd.DataFrame(leads_data)
                df_view["Select"] = False
                
                cols_order = ["Select", "student_token", "name", "phone", "course", "preferred_time", "status", "notes"]
                existing_cols = [c for c in cols_order if c in df_view.columns]
                
                edited_df = st.data_editor(
                    df_view[existing_cols],
                    column_config={
                        "Select": st.column_config.CheckboxColumn("Select", help="Check to run bulk conversion", default=False),
                        "student_token": st.column_config.TextColumn("Student ID", help="Compact identifier"),
                        "name": st.column_config.TextColumn("Candidate Name"),
                        "phone": st.column_config.TextColumn("WhatsApp Number"),
                        "course": st.column_config.TextColumn("Course / Event"),
                        "preferred_time": st.column_config.TextColumn("Timing Preference"),
                        "status": st.column_config.SelectboxColumn("Status", options=["Hot", "Warm", "Cold", "Converted - Student", "Converted - Attendee", "Closed"]),
                        "notes": st.column_config.TextColumn("Counselor Notes")
                    },
                    disabled=["student_token", "name", "phone", "course", "preferred_time"],
                    hide_index=True,
                    use_container_width=True,
                    key="lead_editor_grid"
                )

                selected_rows = edited_df[edited_df["Select"] == True]

                # Action Palette
                st.markdown("<h5 style='margin-top:1rem;'>Bulk Conversion & Status Actions</h5>", unsafe_allow_html=True)
                act1, act2, act3 = st.columns([1.5, 2, 2])
                
                with act1:
                    target_status = st.selectbox("Change Status To", ["Hot", "Warm", "Cold", "Closed"])
                    if st.button("Apply Status Change", use_container_width=True):
                        if not selected_rows.empty:
                            for _, r in selected_rows.iterrows():
                                token = r["student_token"]
                                original_lead = next((x for x in leads_data if x["student_token"] == token), None)
                                if original_lead:
                                    supabase.table("leads").update({"status": target_status}).eq("id", original_lead["raw_id"]).execute()
                            st.success(f"Updated {len(selected_rows)} leads to {target_status}!")
                            st.rerun()
                        else:
                            st.warning("Please check at least one row in the table above.")

                with act2:
                    c_batch = st.selectbox("Enroll Course", ["Bharatanatyam (Regular)", "Carnatic Vocal", "Zumba Fitness", "Western Dance"])
                    fee_val = st.number_input("Monthly Fee (₹)", value=2500, step=250)
                    if st.button("Convert to Enrolled Students", type="primary", use_container_width=True):
                        if not selected_rows.empty:
                            for _, r in selected_rows.iterrows():
                                token = r["student_token"]
                                item = next((x for x in leads_data if x["student_token"] == token), None)
                                if item:
                                    supabase.table("students").insert([{
                                        "name": item.get("name") or item.get("full_name"),
                                        "phone": item.get("phone"),
                                        "course": c_batch,
                                        "batch_timing": item.get("preferred_time") or "Regular Timing",
                                        "fee_amount": fee_val,
                                        "fee_status": "Pending",
                                        "fee_due_date": str(date.today() + timedelta(days=7))
                                    }]).execute()
                                    supabase.table("leads").update({"status": "Converted - Student"}).eq("id", item["raw_id"]).execute()
                            st.success(f"Converted {len(selected_rows)} students! See Fee Manager tab.")
                            st.rerun()
                        else:
                            st.warning("Please check at least one row above.")

                with act3:
                    ev_choice = st.selectbox("Event Roster", ["Garba Night - Oct 17", "Navratri Workshop", "Annual Showcase"])
                    pass_tier = st.selectbox("Pass Type", ["Standard Entry (₹350)", "Couple VIP (₹700)", "Family Pass (₹1200)"])
                    if st.button("Add to Event Guestlist", use_container_width=True):
                        if not selected_rows.empty:
                            for _, r in selected_rows.iterrows():
                                token = r["student_token"]
                                item = next((x for x in leads_data if x["student_token"] == token), None)
                                if item:
                                    supabase.table("event_attendees").insert([{
                                        "name": item.get("name") or item.get("full_name"),
                                        "phone": item.get("phone"),
                                        "event_name": ev_choice,
                                        "pass_type": pass_tier,
                                        "payment_status": "Unpaid",
                                        "amount_paid": 0
                                    }]).execute()
                                    supabase.table("leads").update({"status": "Converted - Attendee"}).eq("id", item["raw_id"]).execute()
                            st.success(f"Added {len(selected_rows)} attendees to event roster!")
                            st.rerun()
                        else:
                            st.warning("Please check at least one row above.")
            else:
                st.info("No inquiries matching the specified filters.")
        except Exception as e:
            st.error(f"Error fetching leads: {e}")

    # ----------------------------------------------------
    # TAB 2: MULTI-FILTER DIRECT FOLLOW-UP COMMAND CENTER
    # ----------------------------------------------------
    with tab_followup:
        st.markdown("#### Follow-up Command Center")
        st.caption("Direct messaging hub with pre-configured filters and 1-click WhatsApp automation.")

        # Multi-Variable Filtering Bar
        fl1, fl2, fl3 = st.columns([1.5, 1.5, 2])
        with fl1:
            fu_status = st.multiselect("Lead Status", ["Hot", "Warm", "Cold", "Converted - Student", "Converted - Attendee"], default=["Hot", "Warm"])
        with fl2:
            fu_course = st.selectbox("Filter Course / Event", ["All Offerings", "Group Class", "Garba Night", "One-on-One", "Bharatanatyam", "Zumba"])
        with fl3:
            fu_search = st.text_input("Filter Candidates", placeholder="Search candidate name or phone number...", key="fu_search_box")

        try:
            fu_query = supabase.table("leads").select("*").order("id", desc=True)
            if fu_status:
                fu_query = fu_query.in_("status", fu_status)
            fu_records = fu_query.execute().data or []

            # Filter in Python
            filtered_fu = []
            for r in fu_records:
                c_name = str(r.get("course", "") or r.get("preferred_class_type", ""))
                if fu_course != "All Offerings" and fu_course.lower() not in c_name.lower():
                    continue
                if fu_search:
                    if not (fu_search.lower() in str(r.get("name", "")).lower() or fu_search in str(r.get("phone", ""))):
                        continue
                filtered_fu.append(r)

            st.write(f"Showing **{len(filtered_fu)}** candidates ready for outreach:")
            st.divider()

            if filtered_fu:
                for lead in filtered_fu:
                    token = clean_id(lead.get("id"))
                    lead_name = lead.get("name") or lead.get("full_name") or "Enquiry"
                    lead_phone = lead.get("phone") or lead.get("whatsapp_number") or ""
                    lead_status = lead.get("status", "Warm")
                    lead_course = lead.get("course") or lead.get("preferred_class_type") or "Academy Programs"
                    lead_notes = lead.get("notes") or "Standard Inquiry"
                    
                    badge_class = "badge-hot" if lead_status == "Hot" else ("badge-warm" if lead_status == "Warm" else "badge-cold")
                    
                    c_info, c_details, c_action = st.columns([2.5, 3.5, 2])
                    with c_info:
                        st.markdown(f"**{lead_name}** `({token})`")
                        st.markdown(f"📞 `{lead_phone}` | <span class='{badge_class}'>{lead_status}</span>", unsafe_allow_html=True)
                    with c_details:
                        st.markdown(f"**Target:** {lead_course}")
                        st.caption(lead_notes[:130] + ("..." if len(str(lead_notes)) > 130 else ""))
                    with c_action:
                        message = f"Hello {lead_name}, greetings from Kalakeerthi Arts! Regarding your inquiry for {lead_course}, we'd love to invite you to our upcoming session."
                        wa_url = generate_wa_link(lead_phone, message)
                        st.markdown(f"<a href='{wa_url}' target='_blank' class='wa-btn'>💬 Chat on WhatsApp</a>", unsafe_allow_html=True)
                    st.divider()
            else:
                st.info("No leads match the selected follow-up filters.")
        except Exception as e:
            st.error(f"Error loading follow-up board: {e}")

    # ----------------------------------------------------
    # TAB 3: EDIT LEAD DETAILS
    # ----------------------------------------------------
    with tab_edit:
        st.markdown("#### Modify Lead Profile & Status")
        try:
            all_leads_res = supabase.table("leads").select("id, name, full_name, phone, course, status, notes").order("id", desc=True).limit(50).execute().data or []
            if all_leads_res:
                edit_map = {f"{clean_id(l['id'])} — {l.get('name') or l.get('full_name')} ({l.get('phone')})": l for l in all_leads_res}
                choice = st.selectbox("Select Candidate to Update", list(edit_map.keys()))
                sel_lead = edit_map[choice]

                with st.form("lead_edit_form"):
                    e1, e2 = st.columns(2)
                    with e1:
                        up_name = st.text_input("Name", value=sel_lead.get("name") or sel_lead.get("full_name") or "")
                        up_phone = st.text_input("Mobile / WhatsApp", value=sel_lead.get("phone") or "")
                        up_course = st.text_input("Target Program / Event", value=sel_lead.get("course") or "")
                    with e2:
                        s_options = ["Hot", "Warm", "Cold", "Converted - Student", "Converted - Attendee", "Closed"]
                        cur_stat = sel_lead.get("status", "Cold")
                        idx = s_options.index(cur_stat) if cur_stat in s_options else 2
                        up_status = st.selectbox("Lead Pipeline Status", s_options, index=idx)
                        up_notes = st.text_area("Counselor Notes", value=sel_lead.get("notes") or "")

                    if st.form_submit_button("Save Profile Updates", type="primary"):
                        clean_p = "".join(filter(str.isdigit, up_phone))
                        supabase.table("leads").update({
                            "name": up_name,
                            "full_name": up_name,
                            "phone": clean_p,
                            "whatsapp_number": clean_p,
                            "course": up_course,
                            "status": up_status,
                            "notes": up_notes
                        }).eq("id", sel_lead["id"]).execute()
                        st.success("Lead details successfully updated!")
                        st.rerun()
            else:
                st.info("No leads found to edit.")
        except Exception as e:
            st.error(f"Error fetching lead: {e}")

    # ----------------------------------------------------
    # TAB 4: EDITABLE FEES & PAYMENT REMINDERS
    # ----------------------------------------------------
    with tab_fees:
        st.markdown("#### Student & Event Fee Management")
        fee_mode = st.radio("Tracker View", ["Enrolled Students (Monthly Dues)", "Event Attendees (Pass Dues)"], horizontal=True)

        if fee_mode == "Enrolled Students (Monthly Dues)":
            try:
                st_records = supabase.table("students").select("*").order("id", desc=True).execute().data or []
                if st_records:
                    classes_found = sorted(list(set([s.get("course", "Regular") for s in st_records])))
                    f_cls = st.selectbox("Filter by Class Batch", ["All Batches"] + classes_found)
                    
                    filtered_st = [s for s in st_records if f_cls == "All Batches" or s.get("course") == f_cls]
                    st.write(f"Tracking **{len(filtered_st)}** Enrolled Students:")

                    for s in filtered_st:
                        c1, c2, c3, c4 = st.columns([2.5, 2, 2, 2.5])
                        with c1:
                            st.write(f"**{s.get('name')}**")
                            st.caption(f"📞 {s.get('phone')} | {s.get('course')}")
                        with c2:
                            st.write(f"Due Date: **{s.get('fee_due_date', 'N/A')}**")
                            st.write(f"Fee: **₹{s.get('fee_amount', 0)}**")
                        with c3:
                            current_stat = s.get("fee_status", "Pending")
                            new_stat = st.selectbox(
                                "Payment Status",
                                ["Pending", "Paid", "Overdue"],
                                index=["Pending", "Paid", "Overdue"].index(current_stat) if current_stat in ["Pending", "Paid", "Overdue"] else 0,
                                key=f"pay_st_{s['id']}"
                            )
                            if new_stat != current_stat:
                                supabase.table("students").update({"fee_status": new_stat}).eq("id", s["id"]).execute()
                                st.success("Updated fee status!")
                                st.rerun()
                        with c4:
                            fee_msg = f"Dear {s.get('name')}, your fee of ₹{s.get('fee_amount')} for {s.get('course')} at Kalakeerthi Arts is {s.get('fee_status')}. Please remit to confirm your batch attendance. Thank you!"
                            st.markdown(f"<a href='{generate_wa_link(s.get('phone'), fee_msg)}' target='_blank' class='wa-btn'>📲 WhatsApp Reminder</a>", unsafe_allow_html=True)
                        st.divider()
                else:
                    st.info("No enrolled students found. Use Tab 1 to convert hot leads into students.")
            except Exception as e:
                st.error(f"Error loading students: {e}")
        else:
            try:
                ev_records = supabase.table("event_attendees").select("*").order("id", desc=True).execute().data or []
                if ev_records:
                    events_found = sorted(list(set([a.get("event_name", "Garba Night") for a in ev_records])))
                    f_ev = st.selectbox("Filter by Event", ["All Events"] + events_found)

                    filtered_ev = [a for a in ev_records if f_ev == "All Events" or a.get("event_name") == f_ev]
                    st.write(f"Tracking **{len(filtered_ev)}** Event Attendees:")

                    for a in filtered_ev:
                        c1, c2, c3, c4 = st.columns([2.5, 2, 2, 2.5])
                        with c1:
                            st.write(f"**{a.get('name')}**")
                            st.caption(f"📞 {a.get('phone')} | {a.get('pass_type')}")
                        with c2:
                            st.write(f"Event: **{a.get('event_name')}**")
                            st.write(f"Pass: **{a.get('pass_type')}**")
                        with c3:
                            p_stat = a.get("payment_status", "Unpaid")
                            new_p = st.selectbox(
                                "Pass Status",
                                ["Unpaid", "Paid - Confirmed", "Cancelled"],
                                index=["Unpaid", "Paid - Confirmed", "Cancelled"].index(p_stat) if p_stat in ["Unpaid", "Paid - Confirmed", "Cancelled"] else 0,
                                key=f"ev_st_{a['id']}"
                            )
                            if new_p != p_stat:
                                supabase.table("event_attendees").update({"payment_status": new_p}).eq("id", a["id"]).execute()
                                st.success("Updated pass status!")
                                st.rerun()
                        with c4:
                            pass_msg = f"Hello {a.get('name')}, your reservation for {a.get('event_name')} ({a.get('pass_type')}) is currently {a.get('payment_status')}. Click here to complete entry pass confirmation."
                            st.markdown(f"<a href='{generate_wa_link(a.get('phone'), pass_msg)}' target='_blank' class='wa-btn'>📲 Pass WhatsApp</a>", unsafe_allow_html=True)
                        st.divider()
                else:
                    st.info("No event attendees found. Convert event leads from Tab 1.")
            except Exception as e:
                st.error(f"Error loading event roster: {e}")

    # ----------------------------------------------------
    # TAB 5: DATA IMPORTER
    # ----------------------------------------------------
    with tab_import:
        st.markdown("#### Cloud Batch Data Importer")
        uploaded_file = st.file_uploader("Upload CSV or Excel inquiry spreadsheet", type=["csv", "xlsx"])

        if uploaded_file is not None:
            try:
                df_upload = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
                st.write("##### Sheet Preview:")
                st.dataframe(df_upload.head(4), use_container_width=True)

                if st.button("Import All into Cloud Database", type="primary"):
                    df_upload.columns = df_upload.columns.str.strip()
                    
                    rows = []
                    for _, row in df_upload.iterrows():
                        p_raw = row.get("WhatsApp Number", "")
                        p_val = str(int(p_raw)) if pd.notnull(p_raw) and isinstance(p_raw, (int, float)) else str(p_raw).strip()
                        
                        f_name = str(row.get("Full Name", "")).strip()
                        s_name = str(row.get("Student Name (if different)", "")).strip()
                        disp_name = s_name if s_name and s_name.lower() != "no" else f_name

                        ts = row.get("Timestamp")
                        ts_val = ts.isoformat() if pd.notnull(ts) and hasattr(ts, "isoformat") else None

                        notes_comp = (
                            f"Joined: {row.get('Who is joining?', 'N/A')} | "
                            f"Exp: {row.get('Experience Level', 'N/A')} | "
                            f"Time: {row.get('Preferred Time', 'N/A')} | "
                            f"Feedback: {row.get('Feedback (if attended)', 'N/A')} | "
                            f"Notes: {row.get('Any questions / requirements (Paragraph)', 'N/A')}"
                        )

                        rows.append({
                            "timestamp": ts_val,
                            "full_name": f_name,
                            "student_name": s_name,
                            "age": str(row.get("Age", "")),
                            "whatsapp_number": p_val,
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
                            "name": disp_name,
                            "phone": p_val,
                            "status": "Cold",
                            "course": str(row.get("Preferred Class Type", "Dance")),
                            "batch": "Online / Palavakkam",
                            "batch_time": str(row.get("Preferred Time", "")),
                            "counselor": "Unassigned",
                            "fee_due_date": str(date.today()),
                            "notes": notes_comp
                        })

                    if rows:
                        with st.spinner("Writing records into Supabase..."):
                            supabase.table("leads").insert(rows).execute()
                            st.success(f"Imported {len(rows)} inquiries into your database!")
                            st.rerun()
            except Exception as e:
                st.error(f"Error during import: {e}")

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1.5rem 0;">
        <h2 style="font-family:'Playfair Display', serif; color:#7B1113; margin:0;">🎭 Kalakeerthi</h2>
        <p style="color:#666; font-size:0.85rem; margin:0;">Arts Academy & Cultural Portal</p>
    </div>
    """, unsafe_allow_html=True)
    
    nav = st.radio(
        "Navigation",
        ["🏛️ Public Website", "🎓 Student Portal", "💼 Admin CRM"],
        label_visibility="collapsed"
    )

if nav == "🏛️ Public Website":
    public_website()
elif nav == "🎓 Student Portal":
    student_portal()
elif nav == "💼 Admin CRM":
    admin_crm()

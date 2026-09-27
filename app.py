from datetime import date, datetime
import pandas as pd
import streamlit as st
from supabase import Client, create_client

# Page layout optimized for mobile screens
st.set_page_config(
    page_title="Academy CRM",
    layout="wide",
    page_icon="🎭",
    initial_sidebar_state="collapsed",
)

# Connect to Supabase Cloud DB
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "YOUR_SUPABASE_KEY")


@st.cache_resource
def init_connection():
  return create_client(SUPABASE_URL, SUPABASE_KEY)


try:
  supabase: Client = init_connection()
except Exception:
  st.error("Please configure your Supabase Database credentials in Secrets.")

# Mobile-friendly custom styles
st.markdown(
    """
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    .wa-btn { display: block; text-align: center; background-color: #25D366; color: white; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px; margin-top: 10px; }
    </style>
""",
    unsafe_allow_html=True,
)

COUNSELORS = ["Unassigned", "Counselor 1", "Counselor 2", "Counselor 3", "Admin"]
COURSES = [
    "Bharatanatyam",
    "Zumba",
    "Western Dance",
    "Garba Event",
    "Music",
    "Other",
]
STATUSES = [
    "New Lead",
    "Follow-up Scheduled",
    "Trial Attended",
    "Enrolled (Active)",
    "Payment Pending",
    "Inactive / Lost",
]

menu = st.sidebar.radio(
    "Navigation",
    [
        "📋 Counselor Dashboard",
        "➕ New Inquiry / Student",
        "💰 Fees & Schedules",
        "📲 WhatsApp Communicator",
        "📂 Upload Contacts / Ads",
    ],
)


def get_all_leads():
  response = (
      supabase.table("leads").select("*").order("id", desc=True).execute()
  )
  return pd.DataFrame(response.data) if response.data else pd.DataFrame()


# 1. COUNSELOR DASHBOARD
if menu == "📋 Counselor Dashboard":
  st.title("📋 Follow-up Dashboard")
  df = get_all_leads()

  if not df.empty:
    col1, col2 = st.columns(2)
    with col1:
      c_filter = st.selectbox("My Queue (Counselor)", ["All"] + COUNSELORS)
    with col2:
      s_filter = st.selectbox("Status Filter", ["All"] + STATUSES)

    f_df = df.copy()
    if c_filter != "All":
      f_df = f_df[f_df["counselor"] == c_filter]
    if s_filter != "All":
      f_df = f_df[f_df["status"] == s_filter]

    today_str = str(date.today())
    overdue_count = len(f_df[f_df["followup_date"] <= today_str])

    st.info(f"📌 **{overdue_count} Leads** pending follow-up today or overdue.")
    st.dataframe(f_df, use_container_width=True)

    st.markdown("---")
    st.subheader("Update Call Status")
    with st.form("quick_update"):
      selected_id = st.selectbox(
          "Choose Lead",
          f_df["id"].tolist(),
          format_func=lambda x: (
              f"ID {x} - {f_df[f_df['id'] == x]['name'].values[0]} ("
              f" {f_df[f_df['id'] == x]['phone'].values[0]})"
          ),
      )
      new_status = st.selectbox("Call Result", STATUSES)
      next_f_date = st.date_input("Next Follow-up Date", value=date.today())
      call_note = st.text_input("Remarks")

      if st.form_submit_button("Save Update"):
        supabase.table("leads").update({
            "status": new_status,
            "followup_date": str(next_f_date),
            "notes": (
                f"{f_df[f_df['id'] == selected_id]['notes'].values[0]} |"
                f" {call_note}"
            ),
        }).eq("id", selected_id).execute()
        st.success("Updated successfully!")
        st.rerun()
  else:
    st.info("No leads available. Start by adding one!")

# 2. ADD NEW LEAD
elif menu == "➕ New Inquiry / Student":
  st.title("➕ Add Lead or Student")
  with st.form("new_lead_form", clear_on_submit=True):
    name = st.text_input("Full Name *")
    phone = st.text_input("WhatsApp Number * (e.g. 919876543210)")
    course = st.selectbox("Program / Interest", COURSES)
    counselor = st.selectbox("Assign Counselor", COUNSELORS)
    batch = st.text_input("Batch Timing", value="Pending")
    fee = st.number_input("Monthly Fee (₹)", min_value=0, step=100, value=2000)
    due_date = st.date_input("Fee Due Date", value=date.today())
    notes = st.text_area("Source / Notes (e.g., Meta Ad - Garba Campaign)")

    if st.form_submit_button("Save to CRM"):
      if name and phone:
        supabase.table("leads").insert({
            "name": name,
            "phone": phone.strip(),
            "interest": course,
            "status": "New Lead",
            "counselor": counselor,
            "followup_date": str(date.today()),
            "batch_time": batch,
            "monthly_fee": fee,
            "fee_due_date": str(due_date),
            "last_fee_paid": "Never",
            "notes": notes,
        }).execute()
        st.success(f"Added {name} successfully!")
      else:
        st.error("Name and Phone are required.")

# 3. FEES & SCHEDULES
elif menu == "💰 Fees & Schedules":
  st.title("💰 Fees & Batch Timings")
  df = get_all_leads()

  if not df.empty:
    today_dt = date.today()

    def calc_status(row):
      try:
        due = datetime.strptime(str(row["fee_due_date"]), "%Y-%m-%d").date()
        if due < today_dt and row["status"] == "Enrolled (Active)":
          return "🚨 Overdue"
        elif due == today_dt:
          return "⚠️ Due Today"
        return "✅ OK"
      except:
        return "Not Set"

    df["Fee Status"] = df.apply(calc_status, axis=1)
    st.dataframe(
        df[[
            "id",
            "name",
            "phone",
            "interest",
            "batch_time",
            "monthly_fee",
            "fee_due_date",
            "Fee Status",
        ]],
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("Record Payment")
    with st.form("pay_fee"):
      sid = st.selectbox(
          "Student",
          df["id"].tolist(),
          format_func=lambda x: (
              f"ID {x} - {df[df['id'] == x]['name'].values[0]}"
          ),
      )
      next_due = st.date_input(
          "Next Month Due Date",
          value=date.today().replace(
              month=date.today().month % 12 + 1 if date.today().month < 12 else 1
          ),
      )
      if st.form_submit_button("Mark as Paid"):
        supabase.table("leads").update({
            "last_fee_paid": str(date.today()),
            "fee_due_date": str(next_due),
            "status": "Enrolled (Active)",
        }).eq("id", sid).execute()
        st.success("Fee updated!")
        st.rerun()

# 4. WHATSAPP SENDER
elif menu == "📲 WhatsApp Communicator":
  st.title("📲 1-Click WhatsApp Sender")
  df = get_all_leads()

  if not df.empty:
    sid = st.selectbox(
        "Select Recipient",
        df["id"].tolist(),
        format_func=lambda x: (
            f"{df[df['id'] == x]['name'].values[0]} -"
            f" {df[df['id'] == x]['interest'].values[0]}"
        ),
    )
    p = df[df["id"] == sid].iloc[0]

    template = st.radio(
        "Message Purpose",
        ["Fee Reminder", "Batch Schedule Alert", "Garba / Event Promotion"],
    )

    if template == "Fee Reminder":
      msg = f"Namaste {p['name']}, this is a reminder that your academy fee of ₹{p['monthly_fee']} for {p['interest']} was due on {p['fee_due_date']}. Kindly complete the transfer."
    elif template == "Batch Schedule Alert":
      msg = f"Namaste {p['name']}, please note your upcoming {p['interest']} class schedule: {p['batch_time']}. Please arrive 10 minutes prior."
    else:
      msg = f"Hello {p['name']}, registration for our upcoming Garba & Cultural Festival is open! Reply YES to receive workshop timings and event pass details."

    st.text_area("Preview", msg, height=120)
    clean_p = "".join(filter(str.isdigit, str(p["phone"])))
    encoded = msg.replace(" ", "%20").replace("\n", "%0A")
    wa_link = f"https://wa.me/{clean_p}?text={encoded}"

    st.markdown(
        f'<a href="{wa_link}" target="_blank" class="wa-btn">📲 Open Chat &'
        " Send</a>",
        unsafe_allow_html=True,
    )

# 5. UPLOAD CONTACTS
elif menu == "📂 Upload Contacts / Ads":
  st.title("📂 Upload Existing Leads & Contacts")
  uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
  if uploaded:
    in_df = (
        pd.read_csv(uploaded)
        if uploaded.name.endswith(".csv")
        else pd.read_excel(uploaded)
    )
    st.dataframe(in_df.head())
    if st.button("Import All into Cloud Database"):
      rows = []
      for _, r in in_df.iterrows():
        rows.append({
            "name": str(r.get("name", "Lead")),
            "phone": str(r.get("phone", "")).replace(".0", "").strip(),
            "interest": str(r.get("interest", "Other")),
            "status": "New Lead",
            "counselor": str(r.get("counselor", "Unassigned")),
            "followup_date": str(date.today()),
            "batch_time": str(r.get("batch_time", "Pending")),
            "monthly_fee": int(r.get("monthly_fee", 0)) if pd.notnull(
                r.get("monthly_fee")
            ) else 0,
            "fee_due_date": str(date.today()),
            "notes": str(r.get("notes", "Bulk upload")),
        })
      supabase.table("leads").insert(rows).execute()
      st.success("All contacts imported!")

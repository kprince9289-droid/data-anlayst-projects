import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, time

# ---------------------------------------------------------
# DATABASE DESIGN & DATA LOGIC
# ---------------------------------------------------------
DB_FILE = "medication_scheduler.db"


def init_db():
    """Initializes SQLite tables for medicine schedules and tracking compliance logs."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Medication Inventory Schedule Master
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            frequency TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            instructions TEXT
        )
    ''')

    # 2. Intake Log History Tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intake_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            med_id INTEGER,
            log_date TEXT NOT NULL,
            log_time TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(med_id) REFERENCES medications(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()


def add_medication(name, dosage, frequency, scheduled_time, instructions):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO medications (name, dosage, frequency, scheduled_time, instructions)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, dosage, frequency, scheduled_time, instructions))
    conn.commit()
    conn.close()


def get_active_medications():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM medications", conn)
    conn.close()
    return df


def log_intake(med_id, date_str, time_str, status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Check if entry already exists for this medicine on this specific day to avoid duplicates
    cursor.execute("SELECT id FROM intake_logs WHERE med_id=? AND log_date=?", (med_id, date_str))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("UPDATE intake_logs SET status=?, log_time=? WHERE id=?", (status, time_str, exists[0]))
    else:
        cursor.execute('''
            INSERT INTO intake_logs (med_id, log_date, log_time, status)
            VALUES (?, ?, ?, ?)
        ''', (med_id, date_str, time_str, status))
    conn.commit()
    conn.close()


def get_adherence_report():
    conn = sqlite3.connect(DB_FILE)
    query = '''
        SELECT m.name, m.dosage, m.scheduled_time, l.log_date, l.log_time, l.status
        FROM intake_logs l
        JOIN medications m ON l.med_id = m.id
        ORDER BY l.log_date DESC, l.log_time DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# Initialize core tables instantly
init_db()

# ---------------------------------------------------------
# RESPONSIVE STREAMLIT INTERFACE DESIGN
# ---------------------------------------------------------
st.set_page_config(page_title="Smart Medicine Tracker", page_icon="💊", layout="wide")

st.title("💊 Smart Healthcare Medicine Reminder & Adherence App")
st.markdown(
    "Schedule recurring pharmaceutical dosages, log daily intake compliance metrics, and review patient adherence trends.")
st.markdown("---")

# Navigation bar configuration panels
menu = ["⏰ Today's Pill Organizer", "➕ Schedule New Medication", "📊 Patient Adherence Report"]
choice = st.sidebar.radio("Navigation Control Hub", menu)

# ---------------------------------------------------------
# VIEW A: TODAY'S PILL BOX & LOGGING ENGINE
# ---------------------------------------------------------
if choice == "⏰ Today's Pill Organizer":
    st.header(f"📅 Daily Roster Status: {datetime.now().strftime('%A, %B %d, %Y')}")

    df_meds = get_active_medications()

    if df_meds.empty:
        st.info(
            "💡 No medications scheduled. Go to the 'Schedule New Medication' tab to build your digital prescription chart.")
    else:
        current_date_str = datetime.now().strftime("%Y-%m-%d")

        # Connect to retrieve modern baseline status entries
        conn = sqlite3.connect(DB_FILE)
        df_today_logs = pd.read_sql_query(f"SELECT med_id, status FROM intake_logs WHERE log_date='{current_date_str}'",
                                          conn)
        conn.close()

        # Map existing logged entries to status dictionaries
        status_map = dict(zip(df_today_logs['med_id'], df_today_logs['status'])) if not df_today_logs.empty else {}

        st.markdown("### 📋 Scheduled Dosages Tracker")
        st.caption("Mark each item as Taken or Skipped below to track real-time medication schedules:")

        # Grid layout format loop
        for index, row in df_meds.iterrows():
            med_id = row['id']
            current_status = status_map.get(med_id, "Pending Action")

            # Interactive container card layout design
            with st.container():
                # Apply structural coloring frameworks based on logged condition
                if current_status == "Taken":
                    color_banner = "🍏 **Taken Successfully**"
                elif current_status == "Skipped":
                    color_banner = "🛑 **Skipped / Missed**"
                else:
                    color_banner = "⏳ **Awaiting Log**"

                col1, col2, col3, col4 = st.columns([2, 1, 2, 2])
                with col1:
                    st.markdown(f"#### 🏷️ {row['name']}")
                    st.write(f"**Dosage size:** {row['dosage']}")
                with col2:
                    st.markdown(f"⏱️ **{row['scheduled_time']}**")
                    st.caption(f"Interval: {row['frequency']}")
                with col3:
                    st.markdown(
                        f"ℹ️ *Instructions:*  \n{row['instructions'] if row['instructions'] else 'Take with water'}")
                with col4:
                    st.markdown(f"Status: {color_banner}")

                    btn_take, btn_skip = st.columns(2)
                    with btn_take:
                        if st.button("Mark Taken", key=f"take_{med_id}", use_container_width=True):
                            log_intake(med_id, current_date_str, datetime.now().strftime("%H:%M"), "Taken")
                            st.rerun()
                    with btn_skip:
                        if st.button("Mark Skipped", key=f"skip_{med_id}", use_container_width=True):
                            log_intake(med_id, current_date_str, datetime.now().strftime("%H:%M"), "Skipped")
                            st.rerun()
            st.markdown("<hr style='margin:10px 0px; border-color:#eee;' />", unsafe_allow_html=True)

# ---------------------------------------------------------
# VIEW B: ADD AND ALLOCATE PRESCRIBED MEDICINES
# ---------------------------------------------------------
elif choice == "➕ Schedule New Medication":
    st.header("➕ Build Digital Prescription Log")

    col_form, col_preview = st.columns([1, 1])

    with col_form:
        st.subheader("Medication Details Card")
        med_name = st.text_input("Medicine Commercial Name:", placeholder="e.g., Metformin / Paracetamol")
        med_dosage = st.text_input("Dosage Specification Layout:", placeholder="e.g., 500 mg / 1 Tablet")
        med_freq = st.selectbox("Intake Frequency Cycle:",
                                ["Once Daily", "Twice Daily (AM/PM)", "Thrice Daily", "As Needed (PRN)"])

        # Split layout configuration profiles for time selectors
        med_time = st.time_input("Target Alert Time Selection Schedule:", time(9, 0))
        med_notes = st.text_area("Administration Instructions Notes:",
                                 placeholder="e.g., Take strictly post meals along with lukewarm water.")

        if st.button("Save Prescription to Dashboard Database", type="primary", use_container_width=True):
            if med_name.strip() == "" or med_dosage.strip() == "":
                st.error(
                    "Validation Halt: Please fill in the core name and dosage attributes before committing records.")
            else:
                add_medication(med_name.strip(), med_dosage.strip(), med_freq, med_time.strftime("%H:%M"),
                               med_notes.strip())
                st.success(f"Successfully cataloged {med_name} in active routines!")
                st.balloons()
                st.rerun()

    with col_preview:
        st.subheader("Active Monitored Treatment Plan")
        df_current_manifest = get_active_medications()
        if df_current_manifest.empty:
            st.info("Prescription catalog is currently clean.")
        else:
            st.dataframe(df_current_manifest[["name", "dosage", "frequency", "scheduled_time", "instructions"]],
                         use_container_width=True)

# ---------------------------------------------------------
# VIEW C: COMPLIANCE METRICS & ANALYTICS REPORT
# ---------------------------------------------------------
elif choice == "📊 Patient Adherence Report":
    st.header("📊 Analytical Patient Adherence Log Sheets")

    df_report = get_adherence_report()

    if df_report.empty:
        st.warning(
            "⚠️ No compliance transaction histories found. Start logging your daily pillbox choices to view metrics charts.")
    else:
        # Calculate Adherence Rate Matrixes
        total_logs = len(df_report)
        taken_count = len(df_report[df_report['status'] == "Taken"])
        adherence_percentage = round((taken_count / total_logs) * 100, 2)

        col_metric1, col_metric2 = st.columns(2)
        with col_metric1:
            st.metric(label="Overall Dosage Intake Compliance Metric", value=f"{adherence_percentage}%",
                      delta="Optimal Treatment Track" if adherence_percentage >= 85.0 else "Adherence Drop Warning (Below 85%)",
                      delta_color="normal" if adherence_percentage >= 85.0 else "inverse")
        with col_metric2:
            st.metric(label="Total Logged Interventions", value=f"{total_logs} Events Check")

        st.markdown("---")

        # Build Table Grid Elements
        st.markdown("### 📜 Longitudinal Chronological Treatment History Logs")
        st.dataframe(df_report, use_container_width=True)

        # Download Action Trigger Manifests
        csv = df_report.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Analytical Compliance Audit Sheet", csv, "medical_adherence_report.csv",
                           "text/csv")
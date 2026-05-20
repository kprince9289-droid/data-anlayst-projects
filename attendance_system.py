import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# ---------------------------------------------------------
# DATABASE DESIGN & LOGIC ENGINE
# ---------------------------------------------------------
DB_FILE = "attendance.db"


def init_db():
    """Initializes SQLite tables for student enrollment and attendance logging."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Students Registry Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            roll_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            semester TEXT NOT NULL
        )
    ''')

    # 2. Attendance Ledger Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            date TEXT,
            status TEXT,
            FOREIGN KEY(roll_no) REFERENCES students(roll_no),
            UNIQUE(roll_no, date)
        )
    ''')
    conn.commit()
    conn.close()


def add_student(roll_no, name, course, semester):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (roll_no, name, course, semester) VALUES (?, ?, ?, ?)",
                       (roll_no, name, course, semester))
        conn.commit()
        conn.close()
        return True, "Student registered successfully!"
    except sqlite3.IntegrityError:
        return False, "Error: This Roll Number is already registered!"


def get_all_students():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM students ORDER BY roll_no ASC", conn)
    conn.close()
    return df


def mark_attendance(records_list, selected_date):
    """Saves or updates daily attendance arrays recursively inside SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for roll_no, status in records_list:
        cursor.execute('''
            INSERT INTO attendance (roll_no, date, status)
            VALUES (?, ?, ?)
            ON CONFLICT(roll_no, date) DO UPDATE SET status = excluded.status
        ''', (roll_no, selected_date, status))
    conn.commit()
    conn.close()


def get_attendance_report():
    """Compiles a complete pivot table metric aggregation for presentation grids."""
    conn = sqlite3.connect(DB_FILE)
    query = '''
        SELECT s.roll_no, s.name, s.course, s.semester, a.date, a.status
        FROM students s
        LEFT JOIN attendance a ON s.roll_no = a.roll_no
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# Initialize relational schema right away
init_db()

# ---------------------------------------------------------
# MODERN STREAMLIT INTERFACE
# ---------------------------------------------------------
st.set_page_config(page_title="Student Attendance System", page_icon="🎓", layout="wide")

st.title("🎓 Smart College Student Attendance System")
st.markdown(
    "An institutional dashboard solution to register students, log daily roster attendance, and audit eligibility compliance metrics.")
st.markdown("---")

# Navigation Sidebar Panels
menu = ["🎛️ Dashboard & Analytics", "📝 Mark Daily Attendance", "➕ Student Registration & Roster"]
choice = st.sidebar.radio("Navigation Control Panel", menu)

# ---------------------------------------------------------
# VIEW A: DASHBOARD & METRICS OVERVIEW
# ---------------------------------------------------------
if choice == "🎛️ Dashboard & Analytics":
    st.header("📈 Institutional Compliance Analytics Dashboard")

    df_raw = get_attendance_report()

    if df_raw.empty or df_raw['date'].isna().all():
        st.info(
            "💡 Roster Database is currently clean or missing transaction entries. Head to 'Student Registration' to get started.")
    else:
        # Calculate individual candidate compliance percentages
        summary_records = []
        grouped = df_raw.groupby(['roll_no', 'name', 'course', 'semester'])

        for (roll_no, name, course, semester), group in grouped:
            total_days = group['status'].notna().sum()
            present_days = (group['status'] == "Present").sum()
            percentage = round((present_days / total_days) * 100, 2) if total_days > 0 else 0.0
            summary_records.append({
                "Roll No": roll_no, "Name": name, "Course": course, "Semester": semester,
                "Total Lectures": total_days, "Attended": present_days, "Attendance (%)": percentage
            })

        df_summary = pd.DataFrame(summary_records)

        # UI Top-level KPI Aggregations
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric("Total Enrolled Candidates", f"{len(df_summary)} Students")
        with kpi2:
            avg_attendance = df_summary['Attendance (%)'].mean()
            st.metric("Average Institute Attendance Metric", f"{avg_attendance:.2f}%")
        with kpi3:
            # Highlight default 75% college structural cutoff compliance criteria
            low_attendance_count = len(df_summary[df_summary['Attendance (%)'] < 75.0])
            st.metric("Short Attendance Alerts (<75%)", f"{low_attendance_count} Profiles",
                      delta="-Action Required" if low_attendance_count > 0 else "Clear", delta_color="inverse")

        st.markdown("---")

        # Interactive Plotly Chart Breakdown
        col_chart1, col_chart2 = st.columns([2, 1])
        with col_chart1:
            st.markdown("### 📊 Student Attendance Distribution Index")
            fig_bar = px.bar(df_summary, x="Name", y="Attendance (%)", color="Attendance (%)",
                             color_continuous_scale=px.colors.sequential.Teal, range_y=[0, 100])
            # Add a baseline horizontal layout marker corresponding to university criteria
            fig_bar.add_hline(y=75, line_dash="dash", line_color="red", annotation_text="75% Cut-off")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_chart2:
            st.markdown("### ⚠️ Attendance Risk Categories")
            eligible_count = len(df_summary[df_summary['Attendance (%)'] >= 75.0])
            fig_pie = px.pie(names=["Eligible (≥75%)", "Shortage (<75%)"],
                             values=[eligible_count, low_attendance_count],
                             color_discrete_sequence=["#2ECC71", "#E74C3C"], hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Main Tabular Evaluation Table View
        st.markdown("### 📋 Student Eligibility Registry Matrix")
        st.dataframe(
            df_summary.style.highlight_between(left=0, right=74.99, axis=0, subset=["Attendance (%)"], color="#f8d7da"),
            use_container_width=True)

        # Export administrative raw records spreadsheet structure
        csv = df_summary.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Compliance Sheets to Excel CSV", csv, "attendance_master_report.csv", "text/csv")

# ---------------------------------------------------------
# VIEW B: MARK ATTENDANCE INTERFACE
# ---------------------------------------------------------
elif choice == "📝 Mark Daily Attendance":
    st.header("📝 Daily Attendance Roll-Call Deck")

    df_students = get_all_students()

    if df_students.empty:
        st.warning("⚠️ No student records discovered inside the database ledger. Please register students first.")
    else:
        col_date, col_filter = st.columns(2)
        with col_date:
            target_date = st.date_input("Select Working Attendance Date:", datetime.now())
        with col_filter:
            # Dropdown filters to isolate classes cleanly for large rosters
            courses = ["All"] + list(df_students['course'].unique())
            selected_course = st.selectbox("Filter Course Stream Group:", courses)

        # Apply stream filters
        if selected_course != "All":
            df_filtered = df_students[df_students['course'] == selected_course]
        else:
            df_filtered = df_students

        st.markdown("---")
        st.markdown(
            f"#### Roster Class Sheet: Showing {len(df_filtered)} Candidates for **{target_date.strftime('%Y-%m-%d')}**")

        # Build interactive forms using native checkbox layouts
        attendance_submission_basket = []

        # Table Header
        header_cols = st.columns([1, 2, 2, 2])
        header_cols[0].markdown("**Roll Number**")
        header_cols[1].markdown("**Student Name**")
        header_cols[2].markdown("**Stream Reference**")
        header_cols[3].markdown("**Mark Status**")
        st.markdown("---")

        # Render dynamic form line elements recursively
        for idx, row in df_filtered.iterrows():
            row_cols = st.columns([1, 2, 2, 2])
            row_cols[0].write(row['roll_no'])
            row_cols[1].write(row['name'])
            row_cols[2].write(f"{row['course']} - Sem {row['semester']}")

            # Interactive switch choice selector frame
            status_toggle = row_cols[3].radio(f"Status for {row['roll_no']}", ["Present", "Absent"], horizontal=True,
                                              label_visibility="collapsed")
            attendance_submission_basket.append((row['roll_no'], status_toggle))

        st.markdown("---")
        if st.button("🔥 Save and Commit Daily Attendance Records", type="primary", use_container_width=True):
            mark_attendance(attendance_submission_basket, target_date.strftime("%Y-%m-%d"))
            st.success(
                f"Successfully processed and committed class attendance logs for {target_date.strftime('%Y-%m-%d')}!")
            st.balloons()

# ---------------------------------------------------------
# VIEW C: STUDENT REGISTRATION / ROSTER PROFILES
# ---------------------------------------------------------
elif choice == "➕ Student Registration & Roster":
    st.header("📥 Candidate Profile Enrollment Engine")

    col_reg, col_view = st.columns([1, 2])

    with col_reg:
        st.subheader("Profile Registration Card")
        reg_roll = st.text_input("University Roll Number ID:", placeholder="e.g., BCA-2026-001")
        reg_name = st.text_input("Candidate Full Name:", placeholder="e.g., John Doe")
        reg_course = st.selectbox("Department Course Stream:", ["BCA", "BBA", "B.Tech", "MCA", "MBA"])
        reg_sem = st.selectbox("Current Semester Unit:", ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"])

        if st.button("Register Profile to DB", use_container_width=True, type="secondary"):
            if reg_roll.strip() == "" or reg_name.strip() == "":
                st.error("Validation Omission: Fields cannot sit empty.")
            else:
                success, msg = add_student(reg_roll.strip(), reg_name.strip(), reg_course, reg_sem)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with col_view:
        st.subheader("Active Enrolled Institutional Roster Data")
        df_roster = get_all_students()
        if df_roster.empty:
            st.info("*No active students cataloged inside SQLite context repositories.*")
        else:
            st.dataframe(df_roster, use_container_width=True)
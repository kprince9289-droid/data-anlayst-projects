import os
import re
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PyPDF2 import PdfReader
import docx2txt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------
# HELPER FUNCTIONS FOR TEXT EXTRACTION & PROCESSING
# ---------------------------------------------------------

def extract_text_from_pdf(pdf_file):
    """Extracts text from an uploaded PDF file."""
    text = ""
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text


def extract_text_from_docx(docx_file):
    """Extracts text from an uploaded DOCX file."""
    try:
        return docx2txt.process(docx_file)
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return ""


def clean_text(text):
    """Cleans extracted text by removing URLs, special characters, and extra spaces."""
    text = text.lower()
    text = re.sub(r'http\S+\s*', ' ', text)
    text = re.sub(r'RT|cc', ' ', text)
    text = re.sub(r'#\S+', '', text)
    text = re.sub(r'@\S+', '  ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def load_skills_database():
    """Loads a predefined list of skills from a text file."""
    if os.path.exists("skills.txt"):
        with open("skills.txt", "r") as f:
            skills = [line.strip().lower() for line in f.read().split(",") if line.strip()]
        return skills
    else:
        return ["python", "java", "sql", "html", "css", "machine learning", "excel", "power bi", "communication",
                "leadership"]


def extract_details(text, skills_db):
    """Extracts contact info and matches predefined skills from the text."""
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group(0) if email_match else None

    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    phone = phone_match.group(0) if phone_match else None

    found_skills = []
    for skill in skills_db:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            found_skills.append(skill.lower())

    return email, phone, found_skills


def generate_resume_feedback(resume_text, job_desc_text, candidate_skills, skills_db):
    """Analyzes discrepancies between the resume and JD to provide structural feedback."""
    feedback = []
    solutions = []

    # 1. Check Contact Details & Professional Links
    if "linkedin.com" not in resume_text.lower():
        feedback.append("Missing LinkedIn Profile Link.")
        solutions.append(
            "Add your updated LinkedIn URL to the header section of your resume to verify your professional digital identity.")

    if "github.com" not in resume_text.lower() and ("python" in resume_text.lower() or "java" in resume_text.lower()):
        feedback.append("Missing GitHub Portfolio Link.")
        solutions.append(
            "Since you are applying for technical roles, host your projects online and feature your GitHub profile link prominently.")

    # 2. Extract skills explicit to the Job Description
    jd_skills = []
    for skill in skills_db:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, job_desc_text, re.IGNORECASE):
            jd_skills.append(skill)

    # Find missing critical keywords
    missing_skills = [skill for skill in jd_skills if skill not in candidate_skills]

    if missing_skills:
        feedback.append(
            f"Missing core technical keywords requested by employer: {', '.join([s.upper() for s in missing_skills[:5]])}")
        solutions.append(
            f"Incorporate missing core skills like **{', '.join([s.upper() for s in missing_skills[:3]])}** into your experience details or bullet points organically, if you have worked with them.")

    # 3. Resume Length & Formatting Depth Checks
    word_count = len(resume_text.split())
    if word_count < 200:
        feedback.append("Resume contains insufficient textual context (Too short).")
        solutions.append(
            "Expand on your college projects, core subjects, and specific academic or industrial accomplishments using metric-driven bullet points (e.g., 'Optimized query latency by 15%').")
    elif word_count > 1500:
        feedback.append("Resume text is excessively lengthy (Potential clutter).")
        solutions.append(
            "Condense descriptions into punchy, objective milestones. Limit your document layout rigidly to a clean 1-2 page presentation grid.")

    # Fallback if profile scores cleanly
    if not feedback:
        feedback.append("No critical omissions found!")
        solutions.append(
            "Your resume structure looks clean. Tailor project metrics perfectly aligned to this job description framework to lock in interviews.")

    return feedback, solutions


def calculate_match_percentage(resume_text, job_description):
    """Calculates cosine similarity percentage between resume and job description."""
    documents = [resume_text, job_description]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return round(similarity_matrix[0][0] * 100, 2)


# ---------------------------------------------------------
# STREAMLIT USER INTERFACE DESIGN
# ---------------------------------------------------------

st.set_page_config(page_title="AI Resume Feedback Studio", page_icon="📝", layout="wide")

st.title("📝 AI Resume Optimization Studio")
st.markdown(
    "Upload your resume against a target job description to pinpoint structural missing targets, score compliance, and access instant step-by-step repair guides.")
st.markdown("---")

skills_list = load_skills_database()

# Layout setup splits
col_left, col_right = st.columns([1, 2])

with col_left:
    st.header("🎯 Target Benchmarks")
    job_desc = st.text_area(
        "Paste target Job Description here:",
        placeholder="Enter requirements details to screen against...",
        height=300
    )

with col_right:
    st.header("📂 Select Resume File")
    uploaded_file = st.file_uploader(
        "Browse local system folders (PDF or DOCX):",
        type=["pdf", "docx"]
    )

if uploaded_file and job_desc.strip():
    file_name = uploaded_file.name
    file_extension = os.path.splitext(file_name)[1].lower()

    # Text Extraction Execution
    if file_extension == ".pdf":
        raw_text = extract_text_from_pdf(uploaded_file)
    else:
        raw_text = extract_text_from_docx(uploaded_file)

    if raw_text.strip():
        # Parsing Run
        cleaned_resume = clean_text(raw_text)
        cleaned_jd = clean_text(job_desc)

        email, phone, identified_skills = extract_details(raw_text, skills_list)
        match_score = calculate_match_percentage(cleaned_resume, cleaned_jd)

        # Pull Report Cards Data
        issues, fixes = generate_resume_feedback(raw_text, job_desc, identified_skills, skills_list)

        st.markdown("---")
        st.subheader(f"📊 Assessment Diagnostics Summary for: *{file_name}*")

        # Display Key Score Metric Cards
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric(label="ATS Match Rating Index", value=f"{match_score}%")
        with metric_col2:
            st.metric(label="Contact Records Discovered", value="Valid" if email or phone else "Incomplete")
        with metric_col3:
            st.metric(label="Detected Technical Competencies", value=f"{len(identified_skills)} Verified")

        # Display Detailed Feedback/Solution Dashboard Panels
        st.markdown("### 🛠️ Optimization Blueprint (Actionable Fixes)")

        feed_col, sol_col = st.columns(2)

        with feed_col:
            st.error("❌ Identified Gaps / Criticisms")
            for idx, issue in enumerate(issues, 1):
                st.markdown(f"**{idx}.** {issue}")

        with sol_col:
            st.success("💡 Strategic Recommended Solutions")
            for idx, fix in enumerate(fixes, 1):
                st.markdown(f"**{idx}.** {fix}")

        # Interactive Metadata Explorer Tab Layout Accordion
        with st.expander("🔍 View Raw Parsed Data Markers"):
            meta_col1, meta_col2 = st.columns(2)
            with meta_col1:
                st.write("**Extracted Communication Records:**")
                st.write(f"- **Email Address ID:** {email if email else 'Not Detected'}")
                st.write(f"- **Phone Number Register:** {phone if phone else 'Not Detected'}")
            with meta_col2:
                st.write("**Extracted Skill Set Inventory Match:**")
                st.write(", ".join(
                    identified_skills).upper() if identified_skills else "*None detected from database references.*")

elif uploaded_file and not job_desc.strip():
    st.info(
        "ℹ️ Please paste the reference Job Description details in the left window panel to compute the optimization diagnostics profile mapping.")
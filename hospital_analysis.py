import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title='Hospital Data Analysis', layout='wide')
st.markdown("""
<style>
.stApp{background:linear-gradient(180deg,#f5fbff,#ffffff)}
[data-testid='stMetric']{background:white;padding:12px;border-radius:14px;box-shadow:0 4px 12px rgba(0,0,0,.08)}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def generate_data(n=800):
    np.random.seed(42)
    diseases = ['Fever','Diabetes','Heart Disease','Asthma','Dengue','Flu','Typhoid']
    depts = ['General','Cardiology','Pulmonology','Emergency','ICU']
    status = ['Recovered','Under Treatment','Discharged']
    doctors = ['Dr Sharma','Dr Khan','Dr Singh','Dr Gupta','Dr Verma']
    genders = ['Male','Female']
    start = datetime(2025,1,1)
    rows=[]
    for i in range(1,n+1):
        age = np.random.randint(1,85)
        rows.append([
            f'P{i:04}', f'Patient {i}', age, np.random.choice(genders), np.random.choice(diseases),
            np.random.choice(depts), (start+timedelta(days=np.random.randint(0,500))).date(),
            np.random.randint(1000,50000), np.random.choice(status), np.random.choice(doctors), np.random.randint(1,121)
        ])
    return pd.DataFrame(rows, columns=['Patient ID','Name','Age','Gender','Disease','Department','Admit Date','Cost','Status','Doctor','Bed'])

df = generate_data()

st.title('🏥 Hospital Data Analysis Dashboard')

s1,s2,s3 = st.columns(3)
with s1:
    disease = st.selectbox('Disease', ['All'] + sorted(df['Disease'].unique().tolist()))
with s2:
    dept = st.selectbox('Department', ['All'] + sorted(df['Department'].unique().tolist()))
with s3:
    age = st.slider('Age range', 1, 85, (1,85))

f = df[(df['Age']>=age[0]) & (df['Age']<=age[1])]
if disease != 'All': f = f[f['Disease']==disease]
if dept != 'All': f = f[f['Department']==dept]

c1,c2,c3,c4 = st.columns(4)
c1.metric('Patients', len(f))
c2.metric('Avg Age', int(f['Age'].mean()) if not f.empty else 0)
c3.metric('Avg Cost', f'₹{int(f["Cost"].mean())}' if not f.empty else '₹0')
c4.metric('Top Disease', f['Disease'].mode().iloc[0] if not f.empty else 'N/A')

st.dataframe(f.astype(str), width='stretch')

left,right = st.columns(2)
with left:
    st.subheader('Common Diseases')
    fig, ax = plt.subplots(figsize=(8,4))
    f['Disease'].value_counts().plot(kind='bar', ax=ax)
    st.pyplot(fig)

    st.subheader('Gender Distribution')
    fig, ax = plt.subplots(figsize=(8,4))
    f['Gender'].value_counts().plot(kind='pie', autopct='%1.0f%%', ax=ax)
    st.pyplot(fig)

with right:
    st.subheader('Age-wise Patients')
    fig, ax = plt.subplots(figsize=(8,4))
    pd.cut(f['Age'], bins=[0,18,35,60,100], labels=['0-18','19-35','36-60','60+']).value_counts().sort_index().plot(kind='bar', ax=ax)
    st.pyplot(fig)

    st.subheader('Monthly Admissions')
    monthly = pd.to_datetime(f['Admit Date']).dt.to_period('M').astype(str).value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8,4))
    monthly.plot(ax=ax)
    plt.xticks(rotation=90)
    st.pyplot(fig)

st.subheader('Doctor Performance')
perf = f.groupby('Doctor')['Patient ID'].count().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(8,4)); perf.plot(kind='bar', ax=ax); st.pyplot(fig)

st.subheader('Bed Occupancy')
occupied = f['Bed'].nunique()
st.info(f'Beds occupied: {occupied} / 120')

# PDF export
styles = getSampleStyleSheet()
buf = BytesIO(); doc = SimpleDocTemplate(buf, pagesize=A4)
story = [Paragraph('Hospital Report', styles['Title']), Spacer(1,12), Paragraph(f'Total Patients: {len(f)}', styles['BodyText']), Paragraph(f'Beds Occupied: {occupied}', styles['BodyText'])]
doc.build(story)
st.download_button('⬇ Download PDF Report', buf.getvalue(), 'hospital_report.pdf', 'application/pdf')

st.subheader('AI Insights')
if not f.empty:
    st.success(f"Most common disease: {f['Disease'].mode().iloc[0]} | Highest cost case: ₹{f['Cost'].max()} | Recovery count: {(f['Status']=='Recovered').sum()}")

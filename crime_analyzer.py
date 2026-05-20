import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title='Crime Data Analysis', layout='wide')
st.markdown("""
<style>
.stApp{background:linear-gradient(180deg,#f8fafc,#ffffff)}
[data-testid='stMetric']{background:white;padding:12px;border-radius:14px;box-shadow:0 4px 12px rgba(0,0,0,.08)}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def gen_data(n=700):
    np.random.seed(21)
    areas=['North','South','East','West','Central']
    crimes=['Theft','Assault','Fraud','Burglary','Robbery','Cyber Crime']
    status=['Open','Closed','Investigating']
    rows=[]
    base=datetime(2026,1,1)
    for i in range(n):
        lat = 28.60 + np.random.uniform(-0.08,0.08)
        lon = 77.40 + np.random.uniform(-0.08,0.08)
        rows.append([f'C{i+1:04}', np.random.choice(areas), np.random.choice(crimes), (base+timedelta(days=np.random.randint(0,150))).date(), np.random.randint(0,24), np.random.choice(status), lat, lon, np.random.choice(['Officer A','Officer B','Officer C']), np.random.choice(['Low','Medium','High'])])
    return pd.DataFrame(rows, columns=['Case ID','Area','Crime Type','Date','Hour','Status','Lat','Lon','Officer','Severity'])

df = gen_data()

st.title('🚨 Crime Data Analysis Dashboard')

c1,c2 = st.columns(2)
with c1:
    area = st.selectbox('Area', ['All'] + sorted(df['Area'].unique().tolist()))
with c2:
    crime = st.selectbox('Crime Type', ['All'] + sorted(df['Crime Type'].unique().tolist()))

f = df.copy()
if area != 'All': f = f[f['Area']==area]
if crime != 'All': f = f[f['Crime Type']==crime]

m1,m2,m3,m4 = st.columns(4)
m1.metric('Cases', len(f))
m2.metric('Top Area', f['Area'].mode().iloc[0] if not f.empty else 'N/A')
m3.metric('Top Crime', f['Crime Type'].mode().iloc[0] if not f.empty else 'N/A')
m4.metric('High Severity', (f['Severity']=='High').sum())

st.dataframe(f.astype(str), width='stretch')

st.subheader('Crime Heat Map')
m = folium.Map(location=[28.61,77.42], zoom_start=10)
for _, r in f.iterrows():
    folium.CircleMarker([r['Lat'], r['Lon']], radius=4, fill=True).add_to(m)
st_folium(m, width=700, height=400)

left,right = st.columns(2)
with left:
    st.subheader('Crimes by Area')
    fig, ax = plt.subplots(figsize=(8,4))
    f['Area'].value_counts().plot(kind='bar', ax=ax)
    st.pyplot(fig)

    st.subheader('Crime Types')
    fig, ax = plt.subplots(figsize=(8,4))
    f['Crime Type'].value_counts().plot(kind='bar', ax=ax)
    st.pyplot(fig)

with right:
    st.subheader('Monthly Trend')
    fig, ax = plt.subplots(figsize=(8,4))
    pd.to_datetime(f['Date']).dt.to_period('M').astype(str).value_counts().sort_index().plot(ax=ax)
    st.pyplot(fig)

    st.subheader('Time Trend')
    fig, ax = plt.subplots(figsize=(8,4))
    f['Hour'].value_counts().sort_index().plot(ax=ax)
    st.pyplot(fig)

st.subheader('AI Insight')
if not f.empty:
    st.success(f"High risk area: {f['Area'].mode().iloc[0]} | Most common crime: {f['Crime Type'].mode().iloc[0]} | Peak hour: {f['Hour'].mode().iloc[0]}:00")

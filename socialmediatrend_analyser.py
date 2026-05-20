import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title='Social Media Trend Analyzer', layout='wide')
st.markdown("""
<style>
.stApp{background:#0f172a;color:white}
h1,h2,h3{color:white}
[data-testid='stMetric']{background:#1e293b;padding:12px;border-radius:14px}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def make_data(n=1000):
    np.random.seed(7)
    platforms=['Instagram','Twitter','YouTube']
    tags=['#AI','#Python','#DataScience','#Travel','#Food','#Fitness','#Tech']
    cats=['Education','Entertainment','Lifestyle','News']
    creators=['Creator A','Creator B','Creator C','Creator D']
    rows=[]
    start=datetime(2026,1,1)
    for i in range(n):
        likes=np.random.randint(100,10000)
        comments=np.random.randint(10,2000)
        shares=np.random.randint(5,1500)
        reach=np.random.randint(500,50000)
        rows.append([f'POST{i+1:04}', np.random.choice(platforms), np.random.choice(tags), likes, comments, shares, reach, (start+timedelta(days=np.random.randint(0,120))).date(), np.random.choice(cats), np.random.choice(creators)])
    return pd.DataFrame(rows, columns=['Post ID','Platform','Hashtag','Likes','Comments','Shares','Reach','Date','Category','Creator'])

df = make_data()
df['Engagement'] = ((df['Likes']+df['Comments']+df['Shares'])/df['Reach']*100).round(2)

st.title('📱 Social Media Trend Analyzer')
col1,col2,col3 = st.columns(3)
with col1:
    p = st.selectbox('Platform', ['All']+sorted(df['Platform'].unique().tolist()))
with col2:
    h = st.selectbox('Hashtag', ['All']+sorted(df['Hashtag'].unique().tolist()))
with col3:
    c = st.selectbox('Category', ['All']+sorted(df['Category'].unique().tolist()))

f = df.copy()
if p!='All': f=f[f['Platform']==p]
if h!='All': f=f[f['Hashtag']==h]
if c!='All': f=f[f['Category']==c]

m1,m2,m3,m4 = st.columns(4)
m1.metric('Posts', len(f))
m2.metric('Avg Likes', int(f['Likes'].mean()) if not f.empty else 0)
m3.metric('Avg Engagement', f"{f['Engagement'].mean():.2f}%" if not f.empty else '0%')
m4.metric('Top Creator', f['Creator'].mode().iloc[0] if not f.empty else 'N/A')

st.dataframe(f.astype(str), width='stretch')

left,right = st.columns(2)
with left:
    st.subheader('Top Hashtags')
    fig, ax = plt.subplots(figsize=(8,4))
    f['Hashtag'].value_counts().plot(kind='bar', ax=ax)
    st.pyplot(fig)

    st.subheader('Likes vs Comments')
    fig, ax = plt.subplots(figsize=(8,4))
    ax.scatter(f['Likes'], f['Comments'])
    st.pyplot(fig)

with right:
    st.subheader('Daily Posts')
    fig, ax = plt.subplots(figsize=(8,4))
    pd.to_datetime(f['Date']).value_counts().sort_index().plot(ax=ax)
    st.pyplot(fig)

    st.subheader('Creator Performance')
    fig, ax = plt.subplots(figsize=(8,4))
    f.groupby('Creator')['Engagement'].mean().sort_values().plot(kind='barh', ax=ax)
    st.pyplot(fig)

st.subheader('AI Insight')
if not f.empty:
    st.success(f"Top hashtag: {f['Hashtag'].mode().iloc[0]} | Highest engagement: {f['Engagement'].max()}% | Best platform: {f.groupby('Platform')['Engagement'].mean().idxmax()}")

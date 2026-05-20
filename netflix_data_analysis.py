import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from textblob import TextBlob

st.set_page_config(page_title='Netflix AI Dashboard', layout='wide')

st.markdown('''<style>.stApp {background:#141414;color:white}.stMetric{background:#222;padding:8px;border-radius:8px}</style>''', unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data():
    # Uses free TVMaze API (no API key)
    try:
        rows = []
        for page in range(3):
            data = requests.get(f'https://api.tvmaze.com/shows?page={page}', timeout=10).json()
            for x in data[:80]:
                rows.append([
                    x.get('name',''),
                    'TV Show',
                    int(str(x.get('premiered','2000'))[:4]) if x.get('premiered') else 2000,
                    (x.get('network') or {}).get('country',{}).get('name','Unknown'),
                    x.get('rating',{}).get('average','N/A'),
                    ', '.join(x.get('genres',[])),
                    (x.get('summary') or '').replace('<p>','').replace('</p>','')
                ])
        if rows:
            return pd.DataFrame(rows, columns=['title','type','release_year','country','rating','listed_in','description']).fillna('')
    except Exception:
        pass
    # fallback sample data
    sample = [['Stranger Things','TV Show',2016,'United States','TV-14','Sci-Fi','Supernatural mystery.']]
    return pd.DataFrame(sample, columns=['title','type','release_year','country','rating','listed_in','description']).fillna('')

df = load_data()

st.title('🎬 Netflix AI Dashboard')
st.caption('Netflix-style UI + recommendations + sentiment + PDF')

# Recommendation engine
content = (df['title'] + ' ' + df['listed_in'] + ' ' + df['description']).fillna('')
tfidf = TfidfVectorizer(stop_words='english')
mat = tfidf.fit_transform(content)
cosine_sim = linear_kernel(mat, mat)
indices = pd.Series(df.index, index=df['title']).drop_duplicates()

def recommend(title):
    if title not in indices: return []
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]
    return df.iloc[[i[0] for i in sim_scores]][['title','type','release_year']]

# filters
st.sidebar.header('Filters')
selected_type = st.sidebar.multiselect('Type', df['type'].replace('', pd.NA).dropna().unique(), default=list(df['type'].replace('', pd.NA).dropna().unique()))
ymin, ymax = int(df['release_year'].replace('', 0).astype(int).min()), int(df['release_year'].replace('', 0).astype(int).max())
years = st.sidebar.slider('Release year', ymin, ymax, (ymin, ymax))
query = st.sidebar.text_input('Search title')

f = df[df['type'].isin(selected_type)]
f = f[(pd.to_numeric(f['release_year'], errors='coerce').fillna(0) >= years[0]) & (pd.to_numeric(f['release_year'], errors='coerce').fillna(0) <= years[1])]
if query:
    f = f[f['title'].str.contains(query, case=False, na=False)]

c1,c2,c3,c4 = st.columns(4)
c1.metric('Total', len(f))
c2.metric('Movies', (f['type']=='Movie').sum())
c3.metric('TV Shows', (f['type']=='TV Show').sum())
c4.metric('Top Rating', f['rating'].mode().iloc[0] if not f.empty and f['rating'].replace('', pd.NA).dropna().any() else 'N/A')

st.dataframe(f, use_container_width=True)

def make_chart(series, kind='bar', title=''):
    fig, ax = plt.subplots(figsize=(10,4))
    series.plot(kind=kind, ax=ax)
    ax.set_title(title)
    st.pyplot(fig)

col1,col2 = st.columns(2)
with col1:
    make_chart(f['type'].value_counts(), 'bar', 'Movies vs TV Shows')
    make_chart(pd.to_numeric(f['release_year'], errors='coerce').value_counts().sort_index().tail(20), 'line', 'Recent Year Trend')
with col2:
    make_chart(f[f['country']!='']['country'].value_counts().head(10), 'bar', 'Top Countries')
    make_chart(f[f['rating']!='']['rating'].value_counts().head(10), 'bar', 'Ratings')

st.subheader('AI Insights')
insights = []
if not f.empty:
    desc = ' '.join(f['description'].astype(str).head(50))
    polarity = TextBlob(desc).sentiment.polarity
    mood = 'Positive' if polarity > 0.1 else 'Negative' if polarity < -0.1 else 'Neutral'
    insights += [f'Most content type: {f["type"].mode().iloc[0]}', f'Sentiment of selected content: {mood}', f'Average release year: {int(pd.to_numeric(f["release_year"], errors="coerce").mean())}']
for i in insights:
    st.write('•', i)

st.subheader('🎯 AI Recommendation')
selected_title = st.selectbox('Choose a title', [''] + sorted(df['title'].astype(str).unique().tolist()))
if selected_title:
    rec = recommend(selected_title)
    if len(rec): st.dataframe(rec, use_container_width=True)

# pdf

def pdf_bytes(lines):
    buf = BytesIO(); doc = SimpleDocTemplate(buf, pagesize=A4); styles = getSampleStyleSheet(); story = [Paragraph('Netflix AI Dashboard Report', styles['Title']), Spacer(1, 12)]
    for line in lines: story += [Paragraph(line, styles['BodyText']), Spacer(1, 8)]
    doc.build(story); return buf.getvalue()

pdf = pdf_bytes(insights or ['No data'])
st.download_button('⬇ Download Report PDF', pdf, 'netflix_ai_report.pdf', 'application/pdf')

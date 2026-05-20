import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title='Weather Dashboard', layout='wide')

st.markdown('''
<style>
.stApp{background:linear-gradient(180deg,#eaf4ff,#ffffff)}
.card{padding:12px;border-radius:16px;background:white;box-shadow:0 4px 10px rgba(0,0,0,.08)}
[data-testid='stMetric']{background:white;padding:12px;border-radius:14px;box-shadow:0 4px 10px rgba(0,0,0,.08)}
</style>
''', unsafe_allow_html=True)

st.title('🌦 Smart Weather Dashboard')
API_KEY = 'ab8d6d7b2d075748fae54ea0559513c2'

cities = st.multiselect('Select up to 3 cities', ['Ghaziabad','Delhi','Noida','Mumbai','Bengaluru','Kolkata'], default=['Ghaziabad','Delhi'])

@st.cache_data(ttl=1800)
def fetch_weather(city):
    r = requests.get('https://api.openweathermap.org/data/2.5/forecast', params={'q': city, 'appid': API_KEY, 'units': 'metric'}, timeout=10)
    d = r.json()
    if d.get('cod') != '200':
        return None, None
    coord = d['city']['coord']
    rows=[]
    for x in d['list']:
        rows.append({'city':city,'time':x['dt_txt'],'temp':x['main']['temp'],'humidity':x['main']['humidity'],'rain':x.get('rain',{}).get('3h',0)})
    return pd.DataFrame(rows), {'lat':coord['lat'],'lon':coord['lon']}

all_df=[]; points=[]
for c in cities[:3]:
    df, p = fetch_weather(c)
    if df is not None:
        all_df.append(df); points.append({'city':c,'lat':p['lat'],'lon':p['lon']})

if all_df:
    data = pd.concat(all_df, ignore_index=True)
    c1,c2,c3 = st.columns(3)
    c1.metric('Cities', len(points))
    c2.metric('Avg Temp', round(data['temp'].mean(),1))
    c3.metric('Avg Humidity', round(data['humidity'].mean(),1))

    st.subheader('📅 7-Day Forecast (approx from API)')
    sel_city = cities[0] if cities else None
    if sel_city:
        week = data[data['city']==sel_city].copy()
        week['date'] = pd.to_datetime(week['time']).dt.date
        daily = week.groupby('date')[['temp','humidity','rain']].mean().head(7).reset_index()
        cols = st.columns(min(len(daily),7))
        for i, row in daily.iterrows():
            with cols[i]:
                st.markdown(f"<div class='card'><b>{row['date']}</b><br>🌡 {row['temp']:.1f}°C<br>💧 {row['humidity']:.0f}%<br>🌧 {row['rain']:.1f} mm</div>", unsafe_allow_html=True)

    st.subheader('📍 City Map')
    st.map(pd.DataFrame(points).rename(columns={'lat':'LAT','lon':'LON'}).rename(columns={'LAT':'lat','LON':'lon'}), size=80)

    st.subheader('📊 Comparison')
    pivot = data.groupby('city')[['temp','humidity','rain']].mean().round(1)
    st.dataframe(pivot.astype(str), width='stretch')

    selected = st.selectbox('Focus city', cities[:len(points)])
    one = data[data['city']==selected]

    fig, ax = plt.subplots(figsize=(11,4))
    for city in data['city'].unique():
        city_df = data[data['city']==city].head(12)
        ax.plot(city_df['time'], city_df['temp'], label=city)
    ax.legend(); plt.xticks(rotation=90); plt.tight_layout(); st.pyplot(fig)

    fig, ax = plt.subplots(figsize=(11,4))
    ax.bar(one['time'].head(12), one['rain'].head(12))
    plt.xticks(rotation=90); plt.tight_layout(); st.pyplot(fig)

    st.subheader('⚠ Weather Alerts')
    if not data.empty:
        city_now = data[data['city']==selected]
        if city_now['temp'].max() >= 35:
            st.error('Heat alert: High temperature expected.')
        if city_now['rain'].sum() >= 10:
            st.warning('Rain alert: Significant rainfall forecast.')
        if city_now['humidity'].mean() >= 85:
            st.info('Humidity alert: Very humid conditions.')

    st.subheader('⚠ Weather Alerts')
    if not data.empty:
        city_now = data[data['city']==selected]
        if city_now['temp'].max() >= 35:
            st.error('Heat alert: High temperature expected.')
        if city_now['rain'].sum() >= 10:
            st.warning('Rain alert: Significant rainfall forecast.')
        if city_now['humidity'].mean() >= 85:
            st.info('Humidity alert: Very humid conditions.')

    st.subheader('AI Insight')
    hottest = pivot['temp'].idxmax()
    st.success(f'Hottest city currently: {hottest} | Average temperature {pivot.loc[hottest,"temp"]} °C')
else:
    st.warning('Enter valid API key and select city')

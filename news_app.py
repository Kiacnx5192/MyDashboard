import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista & Trading Intelligence", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background: #020617; color: #ffffff; }
    [data-testid="stVerticalBlockBorderWrapper"] { 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important; 
        background: rgba(15, 23, 42, 0.9) !important;
        padding: 20px;
    }
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 42px !important; font-weight: 800 !important; }
    
    .header-section { 
        background: linear-gradient(to right, #ff0080, #7928ca); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        font-size: 32px; font-weight: 800; text-align: center; margin-bottom: 20px;
    }
    
    /* ปรับแต่งตารางให้ดูแพงและอ่านง่าย */
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------- ส่วน Sidebar ----------------
with st.sidebar:
    st.title("👨‍💼 มายนี่ Assistant")
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.info("จัดระเบียบตารางแบบไม้ล่าสุดอยู่บนสุดเรียบร้อยค่ะ ✨")
    if st.button("🔄 อัปเดตข้อมูลทั้งหมด"):
        st.cache_data.clear()
        st.rerun()

# ---------------- ส่วนหัวข้อหลัก ----------------
st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="font-family: 'Inter', sans-serif; font-size: 60px; font-weight: 900; letter-spacing: -2px; margin: 0; 
            background: linear-gradient(to right, #ff0080, #7928ca, #0070f3);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Market Intelligence
        </h1>
    </div>
""", unsafe_allow_html=True)

# ---------------- ฟังก์ชันดึงราคาและข่าว ----------------
def clean_html(raw_html):
    return re.sub(re.compile('<.*?>'), '', str(raw_html))

@st.cache_data(ttl=600)
def fetch_news(url, limit=4):
    try:
        feed = feedparser.parse(url, agent='Mozilla/5.0')
        results = []
        for entry in feed.entries[:limit]:
            results.append({
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', '#'),
                'date': entry.get('published', 'Recent')[:25],
                'snippet': clean_html(entry.get('summary', ''))[:110] + "..."
            })
        return results
    except: return []

@st.cache_data(ttl=60)
def get_prices():
    try:
        tickers = ["GC=F", "BTC-USD", "^SET.BK", "THB=X"]
        res = []
        for t in tickers:
            h = yf.Ticker(t).history(period="5d")
            c = h['Close'].iloc[-1]
            d = c - h['Open'].iloc[-1]
            res.append((c, d))
        return res
    except: return [(0,0)]*4

# ---------------- ฟังก์ชันดึง Google Sheets (ฉบับแก้ Unnamed และ Sort ไม้ล่าสุด) ----------------
@st.cache_data(ttl=300)
def load_sheet(sheet_name):
    try:
        base_url = "https://docs.google.com/spreadsheets/d/1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w/gviz/tq?tqx=out:csv&sheet="
        full_url = base_url + sheet_name
        df = pd.read_csv(full_url)
        
        # 1. กำจัดคอลัมน์ที่มีชื่อว่า 'Unnamed' ทิ้งไปให้หมด
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # 2. ลบแถวที่เป็นค่าว่างเปล่าออก
        df = df.dropna(how='all')
        
        # 3. สำหรับ Data8: จัดเรียงใหม่ให้แถวที่ 200 (ล่าสุด) มาอยู่บนสุด
        if sheet_name == "Data8":
            df = df.iloc[::-1].reset_index(drop=True) # กลับด้านตาราง
            
        return df.fillna('')
    except:
        return pd.DataFrame()

# ---------------- แสดงผล Metric ราคา ----------------
p = get_prices()
m1, m2, m3, m4 = st.columns(4)
m1.metric("🟡 GOLD", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
m2.metric("🟠 BTC", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
m3.metric("🟢 SET", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
m4.metric("🔵 USDTHB", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")

st.divider()

# ---------------- ส่วน Google Sheets ----------------
st.markdown('<div class="header-section">📊 MY TRADING PERFORMANCE</div>', unsafe_allow_html=True)

col_d1, col_d2 = st.columns([1, 1.8]) # ปรับสัดส่วนให้ Data8 มีพื้นที่โชว์ข้อมูลมากขึ้น

with col_d1:
    with st.container(border=True):
        st.markdown("### 📈 วิเคราะห์การเทรด (Dashboard8)")
        df_dash = load_sheet("Dashboard8")
        if not df_dash.empty:
            st.dataframe(df_dash, use_container_width=True, hide_index=True, height=450)
        else:
            st.warning("กำลังรอข้อมูลจาก Dashboard8...")

with col_d2:
    with st.container(border=True):
        st.markdown("### 📝 บันทึกการเทรดล่าสุด (ไม้ล่าสุดอยู่บน)")
        df_data = load_sheet("Data8")
        if not df_data.empty:
            # โชว์ตารางทั้งหมดเพื่อให้เลื่อนดูได้ (Scrollable)
            st.dataframe(df_data, use_container_width=True, hide_index=True, height=450)
        else:
            st.warning("กำลังรอข้อมูลจาก Data8...")

st.divider()

# ---------------- ส่วนข่าว ----------------
st.markdown('<div class="header-section">🌐 GLOBAL NEWS FEED</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

news_feeds = [
    (c1, "Precious Metals", "https://news.google.com/rss/search?q=gold+spot+market&hl=en-US&gl=US&ceid=US:en", "btn-gold"),
    (c2, "Digital Assets", "https://cointelegraph.com/rss", "btn-crypto"),
    (c3, "SET & TFEX Focus", "https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th", "btn-thai")
]

for col, title, url, btn_class in news_feeds:
    with col:
        with st.container(border=True):
            st.markdown(f"### {title}")
            for n in fetch_news(url):
                st.markdown(f"""<div class="news-card"><span class="news-date">🕒 {n['date']}</span><h4>{n['title']}</h4><p class="news-snippet">{n['snippet']}</p><a href="{n['link']}" target="_blank" class="btn {btn_class}">READ STORY</a></div>""", unsafe_allow_html=True)

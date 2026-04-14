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
    
    /* Container Glassmorphism */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important; 
        background: rgba(15, 23, 42, 0.9) !important;
        padding: 20px;
    }

    /* บังคับตัวอักษรในตารางทุกชนิดให้อยู่ตรงกลาง (Center Alignment) */
    th, td {
        text-align: center !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
    }
    
    /* ปรับแต่งหัวข้อตารางให้สวยพรีเมียม */
    thead tr th {
        background-color: rgba(30, 41, 59, 1) !important;
        color: #38bdf8 !important;
        font-weight: 800 !important;
        text-transform: uppercase;
    }

    /* ปรับสี Metric ราคา */
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 40px !important; font-weight: 800 !important; }
    
    .header-section { 
        background: linear-gradient(to right, #ff0080, #7928ca); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        font-size: 32px; font-weight: 800; text-align: center; margin-bottom: 25px;
    }

    .news-card { 
        background: #1e293b; padding: 22px; border-radius: 18px; margin-bottom: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.1); border-left: 6px solid #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------- ส่วน Sidebar ----------------
with st.sidebar:
    st.title("👨‍💼 มายนี่ Assistant")
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.info("แก้ไขตารางสำหรับ Tablet และจัดตัวอักษรกึ่งกลางเรียบร้อยค่ะ ✨")
    if st.button("🔄 อัปเดตข้อมูลทั้งหมด"):
        st.cache_data.clear()
        st.rerun()

# ---------------- ส่วนหัวข้อรุ้ง ----------------
st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="font-family: 'Inter', sans-serif; font-size: 55px; font-weight: 900; letter-spacing: -2px; margin: 0; 
            background: linear-gradient(to right, #ff0080, #7928ca, #0070f3);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Market Intelligence
        </h1>
    </div>
""", unsafe_allow_html=True)

# ---------------- ฟังก์ชันดึงราคาและข่าว ----------------
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

@st.cache_data(ttl=300)
def load_sheet(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(url)
        if sheet_name == "Dashboard8":
            df = df.iloc[:, :2]
            df.columns = ["📊 รายการ", "✅ ข้อมูลสรุป"]
        else:
            df = df.dropna(axis=1, how='all')
            # เลือกเฉพาะคอลัมน์สำคัญเพื่อไม่ให้ตารางยาวเกินไปใน Tablet
            cols_to_keep = ["ลำดับ", "Setup รูปแบบที่เข้า", "Direction Buy/Sell", "Entry ราคาเข้า", "SL ราคาตัดขาดทุน", "TP ราคาทำกำไร", "Result ผลลัพธ์", "P/L ($) กำไร"]
            df = df[cols_to_keep] if set(cols_to_keep).issubset(df.columns) else df
            df = df.iloc[::-1].reset_index(drop=True)
        return df.fillna('')
    except: return pd.DataFrame()

# ---------------- แสดงผลราคา ----------------
p = get_prices()
col_m = st.columns(4)
col_m[0].metric("🟡 GOLD", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
col_m[1].metric("🟠 BTC", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
col_m[2].metric("🟢 SET", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
col_m[3].metric("🔵 USDTHB", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")

st.divider()

# ---------------- ส่วนพอร์ตการเทรด ----------------
st.markdown('<div class="header-section">📊 MY TRADING PERFORMANCE</div>', unsafe_allow_html=True)

col_d1, col_d2 = st.columns([1, 1.8])

with col_d1:
    with st.container(border=True):
        st.markdown("### 📈 วิเคราะห์การเทรด (Dashboard8)")
        df_dash = load_sheet("Dashboard8")
        if not df_dash.empty:
            # ใช้ st.table แทน st.dataframe เพื่อให้แสดงผลนิ่งๆ ตรงกลาง ไม่ขาดครึ่ง
            st.table(df_dash)

with col_d2:
    with st.container(border=True):
        st.markdown("### 📝 บันทึกการเทรดล่าสุด")
        df_data = load_sheet("Data8")
        if not df_data.empty:
            # ใช้ st.dataframe แต่ล็อค config เพื่อป้องกันการดีดไปขวาเอง
            st.dataframe(
                df_data, 
                use_container_width=True, 
                hide_index=True, 
                height=450,
                column_config={
                    "ลำดับ": st.column_config.NumberColumn("No.", width=40),
                    "Setup รูปแบบที่เข้า": st.column_config.TextColumn("Setup", width=120),
                    "Direction Buy/Sell": st.column_config.TextColumn("Side", width=60),
                    "Entry ราคาเข้า": st.column_config.NumberColumn("Entry", width=80, format="%.4f"),
                    "SL ราคาตัดขาดทุน": st.column_config.NumberColumn("SL", width=80, format="%.4f"),
                    "TP ราคาทำกำไร": st.column_config.NumberColumn("TP", width=80, format="%.4f"),
                    "Result ผลลัพธ์": st.column_config.TextColumn("Result", width=80),
                    "P/L ($) กำไร": st.column_config.TextColumn("P/L", width=80),
                }
            )

st.divider()

# ---------------- ส่วนข่าว ----------------
st.markdown('<div class="header-section">🌐 GLOBAL NEWS FEED</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

def fetch_news(url):
    try:
        feed = feedparser.parse(url, agent='Mozilla/5.0')
        return [{'title': e.title, 'link': e.link, 'snippet': re.sub('<.*?>', '', e.summary)[:110] + "..."} for e in feed.entries[:3]]
    except: return []

news_data = [
    (c1, "Precious Metals", "https://news.google.com/rss/search?q=gold+spot+market&hl=en-US&gl=US&ceid=US:en"),
    (c2, "Digital Assets", "https://cointelegraph.com/rss"),
    (c3, "SET & TFEX Focus", "https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th")
]

for col, title, url in news_data:
    with col:
        st.markdown(f"### {title}")
        for n in fetch_news(url):
            st.markdown(f'<div class="news-card"><h4>{n["title"]}</h4><p class="news-snippet">{n["snippet"]}</p><a href="{n["link"]}" target="_blank" style="color:#38bdf8; font-size:12px; font-weight:bold;">อ่านต่อ ↗️</a></div>', unsafe_allow_html=True)

import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าตาแอป (Sidebar พับไว้เพื่อความคลีนที่สุด)
st.set_page_config(page_title="Carista & Trading Intelligence", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* พื้นหลังเข้มลึกแบบพรีเมียม */
    .stApp { background: #020617; color: #ffffff; }
    
    /* ปรับแต่ง Sidebar */
    section[data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid rgba(255, 255, 255, 0.1); }
    
    /* Container แบบกระจกฟุ้งๆ (Glassmorphism) */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important; 
        background: rgba(15, 23, 42, 0.9) !important;
        padding: 20px;
    }

    /* --- ส่วนความสวยงามของ Metric ราคา --- */
    div[data-testid="stMetricValue"] > div { 
        color: #ffffff !important; 
        font-size: 40px !important; 
        font-weight: 800 !important;
        text-shadow: 0 0 10px rgba(255,255,255,0.2);
    }
    
    [data-testid="stMetricLabel"] * { 
        font-size: 16px !important; 
        font-weight: 800 !important; 
        letter-spacing: 1px;
    }

    /* เอฟเฟกต์ไฟกระพริบ LIVE */
    @keyframes pulse-glow {
        0% { opacity: 1; filter: brightness(1); }
        50% { opacity: 0.7; filter: brightness(1.5); }
        100% { opacity: 1; filter: brightness(1); }
    }
    [data-testid="stMetricLabel"] { animation: pulse-glow 3s infinite ease-in-out; }

    /* --- ส่วนหัวข้อคอลัมน์ข่าว --- */
    .header-gold { background: linear-gradient(to right, #fde047, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 26px; font-weight: 800; text-align: center; margin-bottom: 20px;}
    .header-crypto { background: linear-gradient(to right, #fb923c, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 26px; font-weight: 800; text-align: center; margin-bottom: 20px;}
    .header-thai { background: linear-gradient(to right, #4ade80, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 26px; font-weight: 800; text-align: center; margin-bottom: 20px;}

    /* --- การ์ดข่าวแบบเดิมที่สวยงาม --- */
    .news-card { 
        background: #1e293b; 
        padding: 22px; 
        border-radius: 18px; 
        margin-bottom: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: 0.3s;
    }
    .news-card:hover { transform: translateY(-5px); border-color: rgba(255,255,255,0.3); }
    .news-card h4 { color: #ffffff !important; font-size: 18px !important; font-weight: 700 !important; line-height: 1.4; margin-bottom: 10px; }
    .news-snippet { color: #cbd5e1 !important; font-size: 14.5px !important; line-height: 1.6; }
    .news-date { color: #94a3b8; font-size: 12px; margin-bottom: 10px; display: block; }
    
    .card-gold { border-left: 6px solid #f59e0b; }
    .card-crypto { border-left: 6px solid #ef4444; }
    .card-thai { border-left: 6px solid #10b981; }

    .btn { padding: 8px 18px; border-radius: 30px; color: white !important; font-weight: 700; text-decoration: none; display: inline-block; margin-top: 10px; font-size: 12px; }
    .btn-gold { background: #d97706; }
    .btn-crypto { background: #dc2626; }
    .btn-thai { background: #059669; }

    /* ปรับแต่งตารางให้ดูทันสมัย */
    .stDataFrame { border-radius: 15px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- ส่วน Sidebar ----------------
with st.sidebar:
    st.title("👨‍💼 มายนี่ Assistant")
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.markdown("---")
    st.info("คืนความสวยงามให้ Dashboard 100% แล้วค่ะ! 🚀✨")
    if st.button("🔄 อัปเดตข้อมูลทั้งหมด"):
        st.cache_data.clear()
        st.rerun()

# ---------------- ส่วนหัวข้อรุ้ง (Vibrant Header) ----------------
st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="font-family: 'Inter', sans-serif; font-size: 60px; font-weight: 900; letter-spacing: -2px; margin: 0; 
            background: linear-gradient(to right, #ff0080, #7928ca, #0070f3);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Market Intelligence
        </h1>
        <p style="color: #ffffff; font-size: 16px; letter-spacing: 5px; text-transform: uppercase; font-weight: 700; margin-top: 15px;">
            Global Trading <span style="color: #ff0080;">•</span> Carista Dashboard
        </p>
    </div>
""", unsafe_allow_html=True)

# ---------------- ฟังก์ชันดึงข้อมูล ----------------
def clean_html(raw_html):
    return re.sub(re.compile('<.*?>'), '', str(raw_html))

@st.cache_data(ttl=600)
def fetch_news(url, limit=4):
    try:
        feed = feedparser.parse(url, agent='Mozilla/5.0')
        return [{'title': e.title, 'link': e.link, 'date': e.published[:25], 'snippet': clean_html(e.summary)[:110] + "..."} for e in feed.entries[:limit]]
    except: return []

@st.cache_data(ttl=60)
def get_prices():
    try:
        tickers = ["GC=F", "BTC-USD", "^SET.BK", "THB=X"]
        data = {}
        for t in tickers:
            ticker = yf.Ticker(t)
            hist = ticker.history(period="5d")
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                data[t] = (current, current - hist['Open'].iloc[-1])
            else: data[t] = (0.0, 0.0)
        return data["GC=F"], data["BTC-USD"], data["^SET.BK"], data["THB=X"]
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
            df = df.iloc[::-1].reset_index(drop=True)
        return df.fillna('')
    except: return pd.DataFrame()

# ---------------- การแสดงผลราคา (พร้อมสีประจำตัว) ----------------
p = get_prices()
col_m = st.columns(4)

with col_m[0]:
    st.markdown('<p style="color:#f59e0b; font-weight:900; margin-bottom:-10px;">🔴 LIVE: XAUUSD</p>', unsafe_allow_html=True)
    st.metric("", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
with col_m[1]:
    st.markdown('<p style="color:#fb923c; font-weight:900; margin-bottom:-10px;">🔴 LIVE: BTC/USD</p>', unsafe_allow_html=True)
    st.metric("", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
with col_m[2]:
    st.markdown('<p style="color:#4ade80; font-weight:900; margin-bottom:-10px;">🔴 LIVE: SET Index</p>', unsafe_allow_html=True)
    st.metric("", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
with col_m[3]:
    st.markdown('<p style="color:#38bdf8; font-weight:900; margin-bottom:-10px;">🔴 LIVE: USDTHB</p>', unsafe_allow_html=True)
    st.metric("", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")

st.divider()

# ---------------- ส่วนพอร์ตการเทรด (จัดระเบียบสำหรับ Tablet) ----------------
st.markdown('<div style="background: linear-gradient(to right, #ff0080, #7928ca); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; font-weight: 800; text-align: center; margin-bottom: 20px;">📊 MY TRADING PERFORMANCE</div>', unsafe_allow_html=True)

col_d1, col_d2 = st.columns([1, 1.8])

with col_d1:
    with st.container(border=True):
        st.markdown("### 📈 วิเคราะห์การเทรด")
        df_dash = load_sheet("Dashboard8")
        if not df_dash.empty:
            st.dataframe(df_dash, use_container_width=True, hide_index=True, height=450)

with col_d2:
    with st.container(border=True):
        st.markdown("### 📝 บันทึกการเทรด (ไม้ล่าสุดอยู่บน)")
        df_data = load_sheet("Data8")
        if not df_data.empty:
            st.dataframe(
                df_data, use_container_width=True, hide_index=True, height=450,
                column_config={
                    "ลำดับ": st.column_config.NumberColumn("No.", width="min"),
                    "Setup รูปแบบที่เข้า": st.column_config.TextColumn("Setup", width="medium"),
                    "Direction Buy/Sell": st.column_config.TextColumn("Side", width="small"),
                }
            )

st.divider()

# ---------------- ส่วนข่าว 3 คอลัมน์ (Vibrant Cards) ----------------
st.markdown('<div style="background: linear-gradient(to right, #ff0080, #7928ca); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; font-weight: 800; text-align: center; margin-bottom: 20px;">🌐 GLOBAL NEWS FEED</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
feeds = [
    (c1, "PRECIOUS METALS", "https://news.google.com/rss/search?q=gold+spot+market&hl=en-US&gl=US&ceid=US:en", "header-gold", "card-gold", "btn-gold"),
    (c2, "DIGITAL ASSETS", "https://cointelegraph.com/rss", "header-crypto", "card-crypto", "btn-crypto"),
    (c3, "SET & TFEX INDEX", "https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th", "header-thai", "card-thai", "btn-thai")
]

for col, title, url, head_cls, card_cls, btn_cls in feeds:
    with col:
        st.markdown(f'<div class="{head_cls}">{title}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            for n in fetch_news(url):
                st.markdown(f"""<div class="news-card {card_cls}"><span class="news-date">🕒 {n['date']}</span><h4>{n['title']}</h4><p class="news-snippet">{n['snippet']}</p><a href="{n['link']}" target="_blank" class="btn {btn_cls}">READ STORY</a></div>""", unsafe_allow_html=True)

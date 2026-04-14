import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista & Trading Intelligence", layout="wide", initial_sidebar_state="collapsed")

# --- 🎨 CSS สุดอลังการ (ไล่เฉดสี, กระจกเงา, ตารางเท่ากัน) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* พื้นหลังน้ำเงินไล่เฉดสุดพรีเมียม */
    .stApp { 
        background: linear-gradient(135deg, #020617 0%, #0f172a 40%, #1e1b4b 100%); 
        color: #ffffff; font-family: 'Inter', sans-serif; 
    }
    
    /* หัวข้อหลักรุ้งกินน้ำพร้อมแสงเงา */
    .main-title {
        font-size: 65px; font-weight: 900; text-align: center; margin-bottom: 0px;
        background: linear-gradient(to right, #38bdf8, #818cf8, #e879f9);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0px 10px 30px rgba(56, 189, 248, 0.2);
    }

    /* Container สไตล์กระจก (Glassmorphism) */
    .glass-container {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 25px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
    }

    /* --- 📊 สไตล์ตาราง (ล็อคความสูงเท่ากัน & หัวตารางติดหนึบ) --- */
    .table-wrapper {
        height: 480px; /* ล็อคความสูงให้ 2 ตารางเท่ากันเป๊ะ */
        overflow-y: auto; 
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.05);
        background: rgba(0,0,0,0.2);
    }
    .custom-table { width: 100%; border-collapse: collapse; }
    .custom-table th {
        background: rgba(15, 23, 42, 0.95); color: #38bdf8; padding: 14px; 
        text-align: center !important; font-weight: 800; font-size: 14px; 
        position: sticky; top: 0; z-index: 2; border-bottom: 2px solid rgba(56, 189, 248, 0.3);
    }
    .custom-table td {
        padding: 12px; text-align: center !important; color: #f8fafc; 
        border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px;
    }
    .custom-table tr:hover td { background: rgba(56, 189, 248, 0.15); color: #fff; } /* เอฟเฟกต์ตอนชี้ */

    /* หัวข้อ Section */
    .section-header {
        background: linear-gradient(to right, #38bdf8, #e879f9);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 30px; font-weight: 800; text-align: center; margin: 35px 0 25px 0;
    }

    /* --- 📰 สไตล์ข่าว --- */
    .news-card {
        background: rgba(30, 41, 59, 0.6); padding: 20px; border-radius: 15px; margin-bottom: 15px;
        border-top: 1px solid rgba(255,255,255,0.1); border-left: 4px solid #38bdf8;
        transition: transform 0.2s;
    }
    .news-card:hover { transform: translateY(-3px); border-left: 4px solid #e879f9; }
    .news-card h4 { color: #ffffff !important; margin-bottom: 8px; font-size: 16px; line-height: 1.4;}
    .news-snippet { color: #94a3b8 !important; font-size: 13.5px; line-height: 1.5; }
    
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 42px !important; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 Sidebar ----------------
with st.sidebar:
    st.title("👨‍💼 มายนี่ Assistant")
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.info("อัปเกรดดีไซน์ระดับ Masterpiece ให้แล้วค่ะคุณเกี๊ยะ! ✨")
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

# ---------------- 👑 Main Header ----------------
st.markdown('<h1 class="main-title">Market Intelligence</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#94a3b8; letter-spacing:4px; font-weight:700; margin-top:5px;">CARISTA TRADING DASHBOARD</p>', unsafe_allow_html=True)

# ---------------- 💰 Real-time Prices ----------------
@st.cache_data(ttl=60)
def get_prices():
    try:
        res = []
        for t in ["GC=F", "BTC-USD", "^SET.BK", "THB=X"]:
            h = yf.Ticker(t).history(period="5d")
            c = h['Close'].iloc[-1]
            d = c - h['Open'].iloc[-1]
            res.append((c, d))
        return res
    except: return [(0,0)]*4

p = get_prices()
m1, m2, m3, m4 = st.columns(4)
m1.metric("🟡 GOLD (XAUUSD)", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
m2.metric("🟠 BITCOIN (BTC)", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
m3.metric("🟢 SET INDEX", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
m4.metric("🔵 USD/THB", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")

# ---------------- 📊 Trading Performance ----------------
st.markdown('<div class="section-header">📊 TRADING PERFORMANCE</div>', unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_sheet_data(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(url)
        return df.dropna(axis=1, how='all').fillna('-')
    except: return pd.DataFrame()

col_left, col_right = st.columns([1, 1.8]) # แบ่งสัดส่วนจอ

with col_left:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color:#38bdf8; margin-bottom:15px;'>📈 วิเคราะห์การเทรด</h3>", unsafe_allow_html=True)
    df_dash = load_sheet_data("Dashboard8")
    if not df_dash.empty:
        # ใช้ table-wrapper เพื่อล็อคความสูงให้เลื่อนดูได้
        html = '<div class="table-wrapper"><table class="custom-table"><thead><tr><th>รายการวิเคราะห์</th><th>ข้อมูลสรุป</th></tr></thead><tbody>'
        for i, row in df_dash.iloc[:, :2].iterrows():
            html += f'<tr><td>{row.iloc[0]}</td><td><b style="color:#e879f9;">{row.iloc[1]}</b></td></tr>'
        html += '</tbody></table></div>'
        st.markdown(html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color:#38bdf8; margin-bottom:15px;'>📝 บันทึกการเทรดล่าสุด</h3>", unsafe_allow_html=True)
    df_data = load_sheet_data("Data8")
    if not df_data.empty:
        # ดึงแค่ 8 คอลัมน์แรกเพื่อความสวยงามใน Tablet
        cols = ["ลำดับ", "Setup รูปแบบที่เข้า", "Direction Buy/Sell", "Entry ราคาเข้า", "Result ผลลัพธ์", "P/L ($) กำไร"]
        df_display = df_data[cols] if set(cols).issubset(df_data.columns) else df_data.iloc[:, :8]
        
        html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
        for col in df_display.columns: html += f'<th>{col}</th>'
        html += '</tr></thead><tbody>'
        for _, row in df_display.iterrows():
            html += '<tr>'
            for val in row: 
                # ทำสีให้ตัวเลข Win/Loss (ถ้ามี)
                color = "#4ade80" if str(val).strip() == "Win" else "#f87171" if str(val).strip() == "Loss" else "inherit"
                html += f'<td style="color:{color};">{val}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'
        st.markdown(html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- 🌐 News Feed ----------------
st.markdown('<div class="section-header">🌐 GLOBAL NEWS FEED</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

def get_news(url):
    try:
        f = feedparser.parse(url, agent='Mozilla/5.0')
        return [{'t': e.title, 'l': e.link, 's': re.sub('<.*?>', '', e.summary)[:90]+'...'} for e in f.entries[:3]]
    except: return []

news_list = [
    (c1, "🟡 PRECIOUS METALS", "https://news.google.com/rss/search?q=gold+spot+market&hl=en-US&gl=US&ceid=US:en", "#f59e0b"),
    (c2, "🟠 DIGITAL ASSETS", "https://cointelegraph.com/rss", "#fb923c"),
    (c3, "🟢 SET & TFEX FOCUS", "https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th", "#4ade80")
]

for col, title, url, color in news_list:
    with col:
        st.markdown(f"<h3 style='text-align: center; color:{color}; font-size:22px;'>{title}</h3>", unsafe_allow_html=True)
        for n in get_news(url):
            st.markdown(f"""<div class="news-card"><h4>{n['t']}</h4><p class="news-snippet">{n['s']}</p><a href="{n['l']}" target="_blank" style="color:#38bdf8;text-decoration:none;font-size:12px;font-weight:bold; background:rgba(56,189,248,0.1); padding:4px 10px; border-radius:10px;">อ่านต่อ ↗️</a></div>""", unsafe_allow_html=True)

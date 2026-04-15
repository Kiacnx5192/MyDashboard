import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista & Trading Intelligence", layout="wide", initial_sidebar_state="collapsed")

# --- 🎨 CSS ระดับพรีเมียม ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    
    /* พื้นหลังน้ำเงินไล่เฉด (Midnight Blue Gradient) */
    .stApp { 
        background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #172554 100%); 
        color: #ffffff; font-family: 'Inter', sans-serif; 
    }
    
    /* กล่องกระจก (Glassmorphism) */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(30, 41, 59, 0.5) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important; 
        padding: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.3) !important;
    }

    /* หัวข้อระดับหลัก (Main Title) */
    .main-title {
        font-size: 60px; font-weight: 900; text-align: center; margin-bottom: 0px;
        background: linear-gradient(to right, #ff0080, #7928ca, #0070f3);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 4px 20px rgba(121, 40, 202, 0.3);
    }

    /* --- สีสันหัวข้อ Section --- */
    .section-perf {
        font-size: 28px; font-weight: 900; text-align: center;
        background: linear-gradient(to right, #f59e0b, #e879f9); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: 3px; margin: 40px 0 20px 0; padding-bottom: 10px;
        border-bottom: 2px dashed rgba(232, 121, 249, 0.4);
    }
    
    .section-news {
        font-size: 28px; font-weight: 900; text-align: center;
        background: linear-gradient(to right, #06b6d4, #4ade80); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: 3px; margin: 40px 0 20px 0; padding-bottom: 10px;
        border-bottom: 2px dashed rgba(74, 222, 128, 0.4);
    }

    .sub-header { color: #38bdf8; text-align: center; font-size: 18px; font-weight: 800; margin-bottom: 15px; }

    /* --- 📊 สไตล์ตาราง --- */
    .table-wrapper {
        height: 480px; overflow-y: auto; overflow-x: auto;
        border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);
        background: rgba(0,0,0,0.2);
    }
    .custom-table { width: 100%; border-collapse: collapse; }
    .custom-table th {
        background: #0f172a; color: #38bdf8; padding: 12px; 
        text-align: center !important; font-weight: 800; font-size: 13px; 
        position: sticky; top: 0; z-index: 2; border-bottom: 2px solid #38bdf8;
    }
    .custom-table td {
        padding: 10px; text-align: center !important; color: #e2e8f0; 
        border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px;
    }
    .custom-table tr:hover td { background: rgba(56, 189, 248, 0.1); }

    /* --- 📰 สไตล์ข่าว --- */
    .news-card {
        background: rgba(15, 23, 42, 0.6); padding: 18px; border-radius: 12px; margin-bottom: 15px;
        border-top: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .card-gold { border-left: 5px solid #f59e0b; }
    .card-crypto { border-left: 5px solid #ef4444; }
    .card-thai { border-left: 5px solid #10b981; }

    .news-title { color: #ffffff; font-size: 15px; font-weight: 700; margin: 5px 0 8px 0; line-height: 1.4;}
    .news-date { color: #94a3b8; font-size: 11.5px; font-weight: 600;}
    .news-snip { color: #cbd5e1; font-size: 13px; line-height: 1.5; margin-bottom: 12px;}
    
    .btn { padding: 6px 16px; border-radius: 20px; color: white !important; font-weight: 700; text-decoration: none; font-size: 11px;}
    .btn-gold { background: #d97706; }
    .btn-crypto { background: #dc2626; }
    .btn-thai { background: #059669; }
    
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 40px !important; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 Sidebar ----------------
with st.sidebar:
    st.title("👨‍💼 มายนี่ Assistant")
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.info("อัปเดตแหล่งข่าว CNBC แก้ปัญหาข่าวไม่ขึ้นเรียบร้อยค่ะ! 🚀")
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

# ---------------- 👑 Main Header ----------------
st.markdown('<h1 class="main-title">Market Intelligence</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#94a3b8; letter-spacing:4px; font-weight:700;">CARISTA TRADING DASHBOARD</p>', unsafe_allow_html=True)

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
with m1:
    st.markdown('<p style="color:#f59e0b; font-weight:900; margin-bottom:-10px;">🟡 PRECIOUS METALS (GOLD)</p>', unsafe_allow_html=True)
    st.metric("", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
with m2:
    st.markdown('<p style="color:#fb923c; font-weight:900; margin-bottom:-10px;">🟠 DIGITAL ASSETS (BTC)</p>', unsafe_allow_html=True)
    st.metric("", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
with m3:
    st.markdown('<p style="color:#4ade80; font-weight:900; margin-bottom:-10px;">🟢 SET INDEX (THAI)</p>', unsafe_allow_html=True)
    st.metric("", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
with m4:
    st.markdown('<p style="color:#38bdf8; font-weight:900; margin-bottom:-10px;">🔵 FX (USDTHB)</p>', unsafe_allow_html=True)
    st.metric("", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")

# ---------------- 📊 Trading Performance ----------------
st.markdown('<div class="section-perf">📊 TRADING PERFORMANCE</div>', unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_sheet_data(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(url)
        return df.dropna(axis=1, how='all').fillna('-')
    except: return pd.DataFrame()

col_left, col_right = st.columns([1, 1.8])

with col_left:
    with st.container(border=True): 
        st.markdown('<div class="sub-header">📈 วิเคราะห์การเทรด</div>', unsafe_allow_html=True)
        df_dash = load_sheet_data("Dashboard8")
        if not df_dash.empty:
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr><th>รายการวิเคราะห์</th><th>ข้อมูลสรุป</th></tr></thead><tbody>'
            for i, row in df_dash.iloc[:, :2].iterrows():
                html += f'<tr><td>{row.iloc[0]}</td><td><b style="color:#fde047;">{row.iloc[1]}</b></td></tr>'
            html += '</tbody></table></div>'
            st.markdown(html, unsafe_allow_html=True)

with col_right:
    with st.container(border=True):
        st.markdown('<div class="sub-header">📝 บันทึกการเทรดล่าสุด</div>', unsafe_allow_html=True)
        df_data = load_sheet_data("Data8")
        if not df_data.empty:
            df_display = df_data.iloc[:, :8] 
            
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
            for col in df_display.columns: html += f'<th>{col}</th>'
            html += '</tr></thead><tbody>'
            for _, row in df_display.iterrows():
                html += '<tr>'
                for val in row: 
                    color = "#4ade80" if str(val).strip().lower() == "win" else "#f87171" if str(val).strip().lower() == "loss" else "inherit"
                    html += f'<td style="color:{color};">{val}</td>'
                html += '</tr>'
            html += '</tbody></table></div>'
            st.markdown(html, unsafe_allow_html=True)

# ---------------- 🌐 News Feed ----------------
st.markdown('<div class="section-news">🌐 GLOBAL NEWS FEED</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

def get_news(url):
    try:
        f = feedparser.parse(url, agent='Mozilla/5.0')
        results = []
        for e in f.entries[:3]:
            date_str = e.get('published', e.get('pubDate', 'Recent'))[:25] 
            snip = re.sub('<.*?>', '', e.get('summary', ''))[:100] + '...'
            results.append({'t': e.title, 'l': e.link, 'd': date_str, 's': snip})
        return results
    except: return []

# ⚠️ อัปเดตแหล่งข่าวตรงนี้ค่ะ: เปลี่ยนจาก Google News เป็น CNBC และแหล่งข่าวที่เสถียรกว่า ⚠️
news_list = [
    (c1, "🟡 PRECIOUS METALS", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000115", "card-gold", "btn-gold"), # ใช้ CNBC Commodities ทรงพลังและไม่บล็อก!
    (c2, "🟠 DIGITAL ASSETS",

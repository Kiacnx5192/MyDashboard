import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista & Trading Intelligence", layout="wide", initial_sidebar_state="collapsed")

# --- 🎨 รวมพลังความสวย CSS กลับมาเต็มพิกัด ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    .stApp { background: #020617; color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* หัวข้อหลักรุ้งกินน้ำ */
    .main-title {
        font-size: 60px; font-weight: 900; text-align: center; margin-bottom: 0px;
        background: linear-gradient(to right, #ff0080, #7928ca, #0070f3);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }

    /* Container สไตล์กระจกเงา */
    .glass-container {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 25px;
    }

    /* --- 📊 สไตล์ตารางแบบ Custom --- */
    .custom-table {
        width: 100%; border-collapse: collapse; margin-top: 15px; border-radius: 15px; overflow: hidden;
    }
    .custom-table th {
        background: #1e293b; color: #38bdf8; padding: 12px; text-align: center !important; 
        font-weight: 800; text-transform: uppercase; font-size: 13px; border-bottom: 2px solid rgba(255,255,255,0.1);
    }
    .custom-table td {
        padding: 12px; text-align: center !important; color: #f1f5f9; 
        border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px;
    }
    .custom-table tr:hover { background: rgba(255,255,255,0.05); }
    .scroll-table { max-height: 450px; overflow-y: auto; overflow-x: auto; }

    /* หัวข้อ Section */
    .section-header {
        background: linear-gradient(to right, #ff0080, #7928ca);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 32px; font-weight: 800; text-align: center; margin: 30px 0;
    }

    /* --- 📰 สไตล์ข่าวและปุ่ม (สีกลับมาแล้ว!) --- */
    .header-gold { background: linear-gradient(to right, #fde047, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 24px; font-weight: 800; text-align: center; margin-bottom: 20px;}
    .header-crypto { background: linear-gradient(to right, #fb923c, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 24px; font-weight: 800; text-align: center; margin-bottom: 20px;}
    .header-thai { background: linear-gradient(to right, #4ade80, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 24px; font-weight: 800; text-align: center; margin-bottom: 20px;}

    .news-card { 
        background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 15px; 
        border-top: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .card-gold { border-left: 5px solid #f59e0b; }
    .card-crypto { border-left: 5px solid #ef4444; }
    .card-thai { border-left: 5px solid #10b981; }

    .news-card h4 { color: #ffffff !important; margin-bottom: 8px; font-size: 16px; line-height: 1.4;}
    .news-snippet { color: #94a3b8 !important; font-size: 13.5px; line-height: 1.5; }
    
    .btn { padding: 6px 18px; border-radius: 20px; color: white !important; font-weight: 700; text-decoration: none; display: inline-block; font-size: 12px; margin-top: 10px;}
    .btn-gold { background: #d97706; }
    .btn-crypto { background: #dc2626; }
    .btn-thai { background: #059669; }
    
    /* ตัวเลข Metric ใหญ่จุใจ */
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 42px !important; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 Sidebar ----------------
with st.sidebar:
    st.title("👨‍💼 มายนี่ Assistant")
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.info("สีสันกลับมาแล้ว! เรียงไม้ที่ 1 ไว้บนสุด และจัดตารางกึ่งกลาง 100% ค่ะ ✨")
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

# ---------------- 👑 Main Header ----------------
st.markdown('<h1 class="main-title">Market Intelligence</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#94a3b8; letter-spacing:3px; font-weight:700;">CARISTA TRADING DASHBOARD</p>', unsafe_allow_html=True)

# ---------------- 💰 Real-time Prices (สีหัวข้อกลับมาแล้ว!) ----------------
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
    st.markdown('<p style="color:#f59e0b; font-weight:900; margin-bottom:-10px; font-size:16px;">🟡 GOLD</p>', unsafe_allow_html=True)
    st.metric("", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
with m2:
    st.markdown('<p style="color:#fb923c; font-weight:900; margin-bottom:-10px; font-size:16px;">🟠 BTC</p>', unsafe_allow_html=True)
    st.metric("", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
with m3:
    st.markdown('<p style="color:#4ade80; font-weight:900; margin-bottom:-10px; font-size:16px;">🟢 SET</p>', unsafe_allow_html=True)
    st.metric("", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
with m4:
    st.markdown('<p style="color:#38bdf8; font-weight:900; margin-bottom:-10px; font-size:16px;">🔵 USDTHB</p>', unsafe_allow_html=True)
    st.metric("", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")

st.divider()

# ---------------- 📊 Trading Performance ----------------
st.markdown('<div class="section-header">📊 MY TRADING PERFORMANCE</div>', unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_sheet_data(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(url)
        return df.dropna(axis=1, how='all').fillna('-')
    except: return pd.DataFrame()

col_left, col_right = st.columns([1, 2]) # ขยายฝั่งขวาให้กว้างขึ้นอีกนิด

with col_left:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin-bottom:15px;'>📈 วิเคราะห์การเทรด</h3>", unsafe_allow_html=True)
    df_dash = load_sheet_data("Dashboard8")
    if not df_dash.empty:
        html = '<table class="custom-table"><thead><tr><th>รายการ</th><th>ข้อมูลสรุป</th></tr></thead><tbody>'
        for i, row in df_dash.iloc[:, :2].iterrows():
            html += f'<tr><td>{row.iloc[0]}</td><td><b style="color:#fde047;">{row.iloc[1]}</b></td></tr>'
        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin-bottom:15px;'>📝 บันทึกการเทรด (เรียงตามลำดับ)</h3>", unsafe_allow_html=True)
    df_data = load_sheet_data("Data8")
    if not df_data.empty:
        # ตัดคอลัมน์ให้เหลือแค่ 8 คอลัมน์แรก (จะได้ไม่เบียดกันจนอ่านไม่ออกใน Tablet)
        # และเรียงตามปกติตามที่กรอก (ไม้ 1 อยู่บน) ไม่ต้องสลับหัวท้ายแล้วค่ะ!
        df_display = df_data.iloc[:, :8] 
        
        html = '<div class="scroll-table"><table class="custom-table"><thead><tr>'
        for col in df_display.columns: html += f'<th>{col}</th>'
        html += '</tr></thead><tbody>'
        for _, row in df_display.iterrows():
            html += '<tr>'
            for val in row: html += f'<td>{val}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'
        st.markdown(html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ---------------- 🌐 News Feed (สีสันครบถ้วน) ----------------
st.markdown('<div class="section-header">🌐 GLOBAL NEWS FEED</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

def get_news(url):
    try:
        f = feedparser.parse(url, agent='Mozilla/5.0')
        return [{'t': e.title, 'l': e.link, 's': re.sub('<.*?>', '', e.summary)[:100]+'...'} for e in f.entries[:3]]
    except: return []

news_list = [
    (c1, "PRECIOUS METALS", "https://news.google.com/rss/search?q=gold+spot+market&hl=en-US&gl=US&ceid=US:en", "header-gold", "card-gold", "btn-gold"),
    (c2, "DIGITAL ASSETS", "https://cointelegraph.com/rss", "header-crypto", "card-crypto", "btn-crypto"),
    (c3, "SET & TFEX FOCUS", "https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th", "header-thai", "card-thai", "btn-thai")
]

for col, title, url, head_cls, card_cls, btn_cls in news_list:
    with col:
        st.markdown(f'<div class="{head_cls}">{title}</div>', unsafe_allow_html=True)
        for n in get_news(url):
            st.markdown(f"""<div class="news-card {card_cls}"><h4>{n['t']}</h4><p class="news-snippet">{n['s']}</p><a href="{n['l']}" target="_blank" class="btn {btn_cls}">READ STORY</a></div>""", unsafe_allow_html=True)

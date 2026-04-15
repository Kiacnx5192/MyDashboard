import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista Command Center", layout="wide", initial_sidebar_state="collapsed")

# --- 🔑 เชื่อมต่อ Google Sheets ด้วยตู้เซฟ Secrets ---
def get_gspread_client():
    creds_dict = json.loads(st.secrets["google_creds"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# --- 🎨 CSS ระดับพรีเมียม ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #172554 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(30, 41, 59, 0.5) !important; backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 16px !important; padding: 20px !important;
    }

    .main-title { font-size: 60px; font-weight: 900; text-align: center; background: linear-gradient(to right, #ff0080, #7928ca, #0070f3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .section-perf { font-size: 28px; font-weight: 900; text-align: center; background: linear-gradient(to right, #f59e0b, #e879f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 3px; margin: 40px 0 20px 0; border-bottom: 2px dashed rgba(232, 121, 249, 0.4); }
    .section-news { font-size: 28px; font-weight: 900; text-align: center; background: linear-gradient(to right, #06b6d4, #4ade80); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 3px; margin: 40px 0 20px 0; border-bottom: 2px dashed rgba(74, 222, 128, 0.4); }
    .sub-header { color: #38bdf8; text-align: center; font-size: 18px; font-weight: 800; margin-bottom: 15px; }

    /* สไตล์ตาราง */
    .table-wrapper { height: 480px; overflow-y: auto; overflow-x: auto; border-radius: 10px; background: rgba(0,0,0,0.2); }
    .custom-table { width: 100%; border-collapse: collapse; }
    .custom-table th { background: #0f172a; color: #38bdf8; padding: 12px; text-align: center !important; position: sticky; top: 0; z-index: 2; border-bottom: 2px solid #38bdf8; }
    .custom-table td { padding: 10px; text-align: center !important; color: #e2e8f0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; }
    
    /* สไตล์ข่าว */
    .news-card { background: rgba(15, 23, 42, 0.6); padding: 18px; border-radius: 12px; margin-bottom: 15px; border-top: 1px solid rgba(255,255,255,0.05); }
    .card-gold { border-left: 5px solid #f59e0b; } .card-crypto { border-left: 5px solid #ef4444; } .card-thai { border-left: 5px solid #10b981; }
    .news-title { color: #ffffff; font-size: 15px; font-weight: 700; margin: 5px 0 8px 0; line-height: 1.4;}
    .news-date { color: #94a3b8; font-size: 11.5px; font-weight: 600;}
    .news-snip { color: #cbd5e1; font-size: 13px; line-height: 1.5; margin-bottom: 12px;}
    .btn { padding: 6px 16px; border-radius: 20px; color: white !important; font-weight: 700; text-decoration: none; font-size: 11px;}
    .btn-gold { background: #d97706; } .btn-crypto { background: #dc2626; } .btn-thai { background: #059669; }
    
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 40px !important; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 Sidebar ----------------
with st.sidebar:
    st.title("👨‍💼 มายนี่ Assistant")
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

# ---------------- 👑 Main Header ----------------
st.markdown('<h1 class="main-title">Market Intelligence</h1>', unsafe_allow_html=True)

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

@st.cache_data(ttl=10)
def load_sheet_data(sheet_name):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w") 
        worksheet = sh.worksheet(sheet_name)
        data = worksheet.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0]) 
        return df.replace('', '-').dropna(axis=1, how='all')
    except Exception as e:
        return pd.DataFrame() 

col_left, col_right = st.columns([1, 1.8])

with col_left:
    with st.container(border=True):
        st.markdown('<div class="sub-header">📈 วิเคราะห์การเทรด</div>', unsafe_allow_html=True)
        df_dash = load_sheet_data("Dashboard8")
        if not df_dash.empty and len(df_dash.columns) >= 2:
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr><th>รายการวิเคราะห์</th><th>ข้อมูลสรุป</th></tr></thead><tbody>'
            for _, row in df_dash.iloc[:, :2].iterrows():
                html += f'<tr><td>{row.iloc[0]}</td><td><b style="color:#fde047;">{row.iloc[1]}</b></td></tr>'
            html += '</tbody></table></div>'
            st.markdown(html, unsafe_allow_html=True)

with col_right:
    # --- 📝 ส่วนบันทึกข้อมูล (Write Data) ---
    with st.expander("➕ บันทึกไม้เทรดใหม่ (Write to Sheet)", expanded=False):
        with st.form("trade_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            setup = f1.selectbox("Setup", ["30/30/40", "Breakout", "Retest", "Price Action"])
            direction = f2.selectbox("Direction", ["Buy", "Sell"])
            entry = f3.number_input("Entry Price", format="%.5f")
            
            f4, f5 = st.columns(2)
            result = f4.selectbox("Result", ["Pending", "Win", "Loss", "กันทุน"])
            pl = f5.number_input("P/L ($)", format="%.2f")
            
            submit = st.form_submit_button("🚀 บันทึกไม้เทรดลง Google Sheet")
            
            if submit:
                try:
                    gc = get_gspread_client()
                    sh = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w")
                    wks = sh.worksheet("Data8")
                    total_rows = len(wks.get_all_values())
                    new_row = [total_rows, setup, direction, entry, "-", "-", "-", result, pl]
                    wks.append_row(new_row)
                    st.success("บันทึกข้อมูลสำเร็จ! กด REFRESH DATA ที่ Sidebar เพื่อดูอัปเดตค่ะ ✨")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"บันทึกไม่สำเร็จ: ตรวจสอบการแชร์ไฟล์ให้ carista-bot ด้วยนะคะ")

    # แสดงตารางบันทึก
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

news_list = [
    (c1, "🟡 GOLD NEWS", "https://news.google.com/rss/search?q=gold+price+OR+XAUUSD+-sdbullion&hl=en-US&gl=US&ceid=US:en", "card-gold", "btn-gold"),
    (c2, "🟠 CRYPTO NEWS", "https://cointelegraph.com/rss", "card-crypto", "btn-crypto"),
    (c3, "🟢 THAI MARKET", "https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th", "card-thai", "btn-thai")
]

for col, title, url, card_cls, btn_cls in news_list:
    with col:
        st.markdown(f"<h3 style='text-align: center; color: white; font-size:18px; margin-bottom:15px;'>{title}</h3>", unsafe_allow_html=True)
        for n in get_news(url):
            st.markdown(f"""
            <div class="news-card {card_cls}">
                <span class="news-date">🕒 {n['d']}</span>
                <div class="news-title">{n['t']}</div>
                <div class="news-snip">{n['s']}</div>
                <a href="{n['l']}" target="_blank" class="btn {btn_cls}">READ STORY</a>
            </div>
            """, unsafe_allow_html=True)

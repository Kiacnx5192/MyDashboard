import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time
from datetime import datetime

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista Command Center", layout="wide", initial_sidebar_state="expanded")

# --- 🔑 เชื่อมต่อ Google Sheets ---
def get_gspread_client():
    creds_dict = json.loads(st.secrets["google_creds"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def safe_float(val):
    try: return float(str(val).replace(',', '').replace('-', '0').strip())
    except: return 0.0

# --- 🎨 GLOBAL NEON CSS (ชุดเดียวจบ คลุมทั้งแอป) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* กล่องหลัก */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(15, 23, 42, 0.7) !important; backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important; border-radius: 20px !important; padding: 25px !important;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.15) !important; 
    }

    /* หัวข้อหลัก */
    .main-title { font-size: 55px; font-weight: 900; text-align: center; background: linear-gradient(to right, #00dfd8, #007cf0, #00dfd8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 25px; filter: drop-shadow(0 0 15px rgba(0, 223, 216, 0.3)); }
    .sub-header { color: #f472b6; text-align: center; font-size: 22px; font-weight: 900; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 10px rgba(244, 114, 182, 0.3);}

    /* Tabs Neon Style */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 15px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(15, 23, 42, 0.8); border-radius: 12px 12px 0 0; border: 1px solid rgba(232, 121, 249, 0.3); color: #cbd5e1; padding: 12px 25px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(to bottom, #7928ca, #ff0080) !important; color: #ffffff !important; font-weight: 900 !important; box-shadow: 0 0 15px rgba(255, 0, 128, 0.4) !important; }

    /* ตาราง */
    .table-wrapper { height: 450px; overflow-y: auto; overflow-x: auto; border-radius: 15px; background: rgba(0,0,0,0.4); border: 1px solid rgba(56, 189, 248, 0.2); }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 1000px; } 
    .custom-table th { background: #0f172a; color: #00dfd8; padding: 15px; position: sticky; top: 0; z-index: 10; border-bottom: 3px solid #007cf0; font-size: 13px; text-transform: uppercase;}
    .custom-table td { padding: 12px; text-align: center !important; color: #f8fafc; border-bottom: 1px solid rgba(56, 189, 248, 0.1); font-size: 14px; white-space: nowrap;}
    
    /* สรุปวิเคราะห์ด้านซ้าย */
    .summary-table { width: 100%; border-collapse: collapse; }
    .summary-table td:first-child { text-align: left !important; color: #94a3b8; padding: 10px; font-weight: 600;}
    .summary-table td:last-child { text-align: right !important; font-weight: 900; color: #fde047; padding: 10px; font-size: 16px;}
    .summary-table tr { border-bottom: 1px solid rgba(255,255,255,0.08); }

    /* ข่าว (News Feed) */
    .news-card { background: rgba(15, 23, 42, 0.85); padding: 20px; border-radius: 15px; margin-bottom: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.5); border-left: 5px solid #00dfd8; transition: 0.3s; }
    .news-card:hover { transform: translateY(-5px); box-shadow: 0 0 20px rgba(0, 223, 216, 0.3); }
    .card-gold { border-left-color: #fbbf24; } .card-crypto { border-left-color: #f43f5e; } .card-thai { border-left-color: #10b981; }
    .news-title { color: #ffffff; font-size: 16px; font-weight: 700; margin-bottom: 8px; line-height: 1.4; }
    .btn-news { color: #00dfd8 !important; font-weight: 700; text-decoration: none; font-size: 13px; border: 1px solid #00dfd8; padding: 4px 12px; border-radius: 20px; }

    /* Metrics & Forms */
    div[data-testid="stMetricValue"] > div { color: #00dfd8 !important; font-size: 42px !important; font-weight: 900 !important; }
    .stNumberInput label p, .stTextInput label p, .stSelectbox label p { color: #38bdf8 !important; font-weight: 700; }
    div[data-testid="stFormSubmitButton"] button { background: linear-gradient(45deg, #0070f3, #7928ca, #ff0080) !important; width: 100% !important; font-weight: 900 !important; border-radius: 12px !important; }
    
    /* เตือนสต็อกต่ำ */
    .low-stock { color: #ff0080 !important; font-weight: 900; text-shadow: 0 0 10px rgba(255, 0, 128, 0.5); }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 Sidebar Menu ----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("<h2 style='text-align: center; color: #00dfd8;'>CARISTA SYSTEM</h2>", unsafe_allow_html=True)
    page = st.radio("SELECT PAGE:", ["🌐 MARKET INSIGHT", "📊 TRADING DESK", "📦 STOCK MANAGER"])
    st.divider()
    if st.button("🔄 REFRESH SYSTEM"):
        st.cache_data.clear()
        st.rerun()

# --- 📑 LOADING FUNCTIONS ----------------
@st.cache_data(ttl=60)
def get_prices():
    try:
        res = []
        for t in ["GC=F", "BTC-USD", "^SET.BK", "THB=X"]:
            h = yf.Ticker(t).history(period="5d")
            res.append((h['Close'].iloc[-1], h['Close'].iloc[-1] - h['Open'].iloc[-1]))
        return res
    except: return [(0,0)]*4

@st.cache_data(ttl=10)
def load_sheet_data(sheet_name):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w")
        data = sh.worksheet(sheet_name).get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0]).replace('', '-')
    except: return pd.DataFrame()

# =====================================================================
# 🌐 PAGE 1: MARKET INSIGHT
# =====================================================================
if page == "🌐 MARKET INSIGHT":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/3859/3859033.png" width="80"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">MARKET INSIGHT</h1>', unsafe_allow_html=True)
    
    p = get_prices()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🟡 GOLD", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
    m2.metric("🟠 BTC", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
    m3.metric("🟢 SET", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
    m4.metric("🔵 USD/THB", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")
    
    st.markdown("<h2 style='text-align: center; color: #f59e0b; margin: 30px 0;'>🌐 GLOBAL NEWS FEED</h2>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    urls = [
        ("🟡 GOLD NEWS", "https://news.google.com/rss/search?q=gold+price+XAUUSD&hl=en-US", c1, "card-gold"),
        ("🟠 CRYPTO NEWS", "https://cointelegraph.com/rss", c2, "card-crypto"),
        ("🟢 THAI MARKET", "https://news.google.com/rss/search?q=SET50+TFEX&hl=th", c3, "card-thai")
    ]
    
    for title, url, col, cls in urls:
        with col:
            st.markdown(f"<h3 style='text-align: center; color: #ffffff;'>{title}</h3>", unsafe_allow_html=True)
            f = feedparser.parse(url)
            for e in f.entries[:3]:
                snip = re.sub('<.*?>', '', e.summary)[:100] + "..."
                st.markdown(f"""
                <div class="news-card {cls}">
                    <div class="news-date">🕒 {e.published[:25]}</div>
                    <div class="news-title">{e.title}</div>
                    <p style='font-size:13px; color:#cbd5e1;'>{snip}</p>
                    <a href="{e.link}" target="_blank" class="btn-news">READ STORY</a>
                </div>
                """, unsafe_allow_html=True)

# =====================================================================
# 📊 PAGE 2: TRADING DESK
# =====================================================================
elif page == "📊 TRADING DESK":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2422/2422796.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">TRADING DESK</h1>', unsafe_allow_html=True)
    
    with st.container(border=True):
        tab1, tab2 = st.tabs(["➕ ADD NEW TRADE", "✏️ EDIT & DELETE"])
        with tab1:
            with st.form("add_trade"):
                c1, c2, c3 = st.columns(3)
                setup = c1.selectbox("SETUP", ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"])
                direction = c2.selectbox("Direction", ["Buy", "Sell"])
                res = c3.selectbox("Result", ["Pending", "Win", "Loss", "กันทุน"])
                c4, c5, c6, c7 = st.columns(4)
                en, sl, tp, ex = c4.number_input("Entry", format="%.5f"), c5.number_input("SL", format="%.5f"), c6.number_input("TP", format="%.5f"), c7.number_input("Exit", format="%.5f")
                pl, bp = st.number_input("P/L ($)", format="%.2f"), st.number_input("Best Price", format="%.5f")
                if st.form_submit_button("🚀 SAVE TRADE"):
                    try:
                        gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                        next_r = len(wks.col_values(2)) + 1
                        pl_f = pl if pl != 0.0 else ""; bp_f = bp if bp != 0.0 else ""
                        wks.batch_update([{'range':f'A{next_r}:I{next_r}', 'values':[[next_r-3, setup, direction, en, sl, tp, ex, res, pl_f]]}, {'range':f'K{next_r}:K{next_r}', 'values':[[bp_f]]}], value_input_option="USER_ENTERED")
                        st.success("SAVED!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                    except Exception as e: st.error(e)

    st.divider()
    
    # ⚠️ แสดงผลคู่กัน ซ้าย/ขวา ⚠️
    col_l, col_r = st.columns([1, 2.2])
    
    with col_l:
        st.markdown('<div class="sub-header">📈 ANALYSIS SUMMARY</div>', unsafe_allow_html=True)
        df_dash = load_sheet_data("Dashboard8")
        if not df_dash.empty:
            html = '<div class="table-wrapper"><table class="summary-table"><tbody>'
            for _, row in df_dash.iloc[:, :2].iterrows():
                if str(row.iloc[0]).strip() not in ['-', '']:
                    html += f'<tr><td>{row.iloc[0]}</td><td>{row.iloc[1]}</td></tr>'
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="sub-header">📝 RECENT LOGS</div>', unsafe_allow_html=True)
        df_log = load_sheet_data("Data8")
        if not df_log.empty:
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
            for col in df_log.columns[:10]: html += f'<th>{col}</th>'
            html += '</tr></thead><tbody>'
            for _, row in df_log.iterrows():
                if str(row.iloc[0]).strip() == '-': continue
                c = "#00dfd8" if str(row.iloc[7]).lower()=="win" else "#ff0080" if str(row.iloc[7]).lower()=="loss" else "inherit"
                html += f'<tr>' + "".join(f'<td style="color:{c if i==7 else "inherit"};">{v}</td>' for i, v in enumerate(row[:10])) + '</tr>'
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)

# =====================================================================
# 📦 PAGE 3: STOCK MANAGER
# =====================================================================
elif page == "📦 STOCK MANAGER":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2897/2897864.png" width="80"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">STOCK MANAGER</h1>', unsafe_allow_html=True)

    tab_inv, tab_out, tab_in = st.tabs(["💎 CURRENT STOCK", "📤 OUT (เบิก/ขาย)", "📥 IN (เติมสต็อก)"])

    df_stock = load_sheet_data("Master_Stock (ฐานข้อมูลหลัก)")

    with tab_inv:
        if not df_stock.empty:
            st.markdown('<div class="sub-header">รายการสินค้าคงเหลือปัจจุบัน</div>', unsafe_allow_html=True)
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
            for col in df_stock.columns: html += f'<th>{col}</th>'
            html += '</tr></thead><tbody>'
            for _, row in df_stock.iterrows():
                if str(row.iloc[0]).strip() == '-': continue
                qty = safe_float(row.iloc[7]) # ช่องคงเหลือ (Col H)
                min_q = safe_float(row.iloc[8]) # จุดเตือน (Col I)
                cls = 'class="low-stock"' if qty <= min_q else ""
                html += f'<tr {cls}>' + "".join(f'<td>{v}</td>' for v in row) + '</tr>'
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)

    with tab_out:
        with st.form("out_form"):
            c1, c2, c3 = st.columns(3)
            hn, patient = c1.text_input("HN"), c2.text_input("ชื่อคนไข้")
            items = list(dict.fromkeys(df_stock.iloc[:, 0].tolist())) if not df_stock.empty else []
            cat = c3.selectbox("หมวดหมู่", items)
            c4, c5, c6 = st.columns(3)
            size, color, q = c4.text_input("ไซส์"), c5.text_input("สี"), c6.number_input("จำนวน", min_value=1)
            if st.form_submit_button("📤 CONFIRM OUT"):
                try:
                    gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Log_เบิกออก")
                    wks.append_row([datetime.now().strftime("%Y-%m-%d"), hn, patient, cat, size, color, q], value_input_option="USER_ENTERED")
                    st.success("SAVED!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except Exception as e: st.error(e)

    with tab_in:
        with st.form("in_form"):
            c1, c2, c3 = st.columns(3)
            cat_in = c1.selectbox("หมวดหมู่สินค้า", items)
            size_in, color_in = c2.text_input("ไซส์"), c3.text_input("สี")
            q_in, cost = st.number_input("จำนวนรับเข้า", min_value=1), st.number_input("ต้นทุนรวม")
            if st.form_submit_button("📥 CONFIRM IN"):
                try:
                    gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Log_รับเข้า")
                    wks.append_row([datetime.now().strftime("%Y-%m-%d"), cat_in, size_in, color_in, q_in, cost], value_input_option="USER_ENTERED")
                    st.success("SAVED!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except Exception as e: st.error(e)

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

# 1. SETUP PAGE
st.set_page_config(page_title="Carista Command Center", layout="wide", initial_sidebar_state="expanded")

# --- 🔑 GOOGLE SHEETS CONNECTION ---
def get_gspread_client():
    try:
        creds_dict = json.loads(st.secrets["google_creds"])
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except: return None

def safe_float(val):
    try: return float(str(val).replace(',', '').replace('-', '0').strip())
    except: return 0.0

# --- 🎨 GLOBAL NEON CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(15, 23, 42, 0.7) !important; backdrop-filter: blur(15px) !important; border: 1px solid rgba(56, 189, 248, 0.4) !important; border-radius: 20px !important; padding: 25px !important; box-shadow: 0 0 25px rgba(56, 189, 248, 0.15) !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 15px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(15, 23, 42, 0.8); border-radius: 10px 10px 0 0; border: 1px solid rgba(232, 121, 249, 0.3); color: #cbd5e1; }
    .stTabs [aria-selected="true"] { background: linear-gradient(to bottom, #7928ca, #ff0080) !important; color: #ffffff !important; font-weight: bold; border: 1px solid #ff0080 !important; }
    .main-title { font-size: 50px; font-weight: 900; text-align: center; background: linear-gradient(to right, #00dfd8, #007cf0, #00dfd8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }
    .sub-header { color: #f472b6; text-align: center; font-size: 22px; font-weight: 900; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 10px rgba(244, 114, 182, 0.3);}
    .table-wrapper { height: 450px; overflow-y: auto; overflow-x: auto; border-radius: 15px; background: rgba(0,0,0,0.4); border: 1px solid rgba(56, 189, 248, 0.2); }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 1000px; } 
    .custom-table th { background: #0f172a; color: #00dfd8; padding: 15px; position: sticky; top: 0; z-index: 10; border-bottom: 3px solid #007cf0; font-size: 13px; text-transform: uppercase;}
    .custom-table td { padding: 12px; text-align: center !important; color: #f8fafc; border-bottom: 1px solid rgba(56, 189, 248, 0.1); font-size: 14px; white-space: nowrap;}
    .news-card { background: rgba(15, 23, 42, 0.85); padding: 20px; border-radius: 15px; margin-bottom: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.5); border-left: 5px solid #00dfd8; }
    div[data-testid="stMetricValue"] > div { color: #00dfd8 !important; font-size: 42px !important; font-weight: 900 !important; }
    div[data-testid="stFormSubmitButton"] button { background: linear-gradient(45deg, #0070f3, #7928ca, #ff0080) !important; width: 100% !important; font-weight: 900 !important; border-radius: 12px !important; }
    .low-stock { color: #ff0080 !important; font-weight: 900; text-shadow: 0 0 10px rgba(255, 0, 128, 0.5); }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 SIDEBAR ----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("<h2 style='text-align:center; color:#00dfd8;'>ADMIN PANEL</h2>", unsafe_allow_html=True)
    page = st.radio("MENU:", ["🌐 MARKET INSIGHT", "📊 TRADING DESK", "📦 STOCK MANAGER"])
    st.divider()
    if st.button("🔄 REFRESH"):
        st.cache_data.clear()
        st.rerun()

# --- 📑 LOADING FUNCTIONS ---
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
        if not gc: return pd.DataFrame()
        sh = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w")
        data = sh.worksheet(sheet_name).get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0]).replace('', '-')
    except Exception: return pd.DataFrame()

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
    
    st.markdown("<h2 style='text-align:center; color:#f59e0b;'>🌐 GLOBAL NEWS FEED</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    urls = [("🟡 GOLD", "https://news.google.com/rss/search?q=gold+price&hl=en-US", c1, "#fbbf24"),
            ("🟠 CRYPTO", "https://cointelegraph.com/rss", c2, "#f43f5e"),
            ("🟢 THAI", "https://news.google.com/rss/search?q=SET50&hl=th", c3, "#10b981")]
    for title, url, col, color in urls:
        with col:
            st.markdown(f"<h3 style='text-align:center;'>{title}</h3>", unsafe_allow_html=True)
            f = feedparser.parse(url)
            for e in f.entries[:3]:
                st.markdown(f'<div class="news-card" style="border-left-color:{color};"><strong>{e.title}</strong><br><a href="{e.link}" target="_blank" style="color:#00dfd8; font-size:12px;">READ STORY</a></div>', unsafe_allow_html=True)

# =====================================================================
# 📊 PAGE 2: TRADING DESK
# =====================================================================
elif page == "📊 TRADING DESK":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2422/2422796.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">TRADING DESK</h1>', unsafe_allow_html=True)
    
    df_log = load_sheet_data("Data8")
    
    with st.container(border=True):
        t1, t2 = st.tabs(["➕ ADD NEW TRADE", "✏️ MANAGE LOGS"])
        
        with t1:
            with st.form("add_trade"):
                c1, c2, c3 = st.columns(3)
                setup = c1.selectbox("SETUP", ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"])
                direction = c2.selectbox("Direction", ["Buy", "Sell"])
                res = c3.selectbox("Result", ["Pending", "Win", "Loss", "กันทุน"])
                c4, c5, c6, c7 = st.columns(4)
                en, sl, tp, ex = c4.number_input("Entry", format="%.5f"), c5.number_input("SL", format="%.5f"), c6.number_input("TP", format="%.5f"), c7.number_input("Exit", format="%.5f")
                pl, bp = st.number_input("P/L ($)", format="%.2f"), st.number_input("Best Price", format="%.5f")
                if st.form_submit_button("🚀 SAVE"):
                    try:
                        gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                        next_r = len(wks.col_values(2)) + 1
                        wks.batch_update([{'range':f'A{next_r}:I{next_r}', 'values':[[next_r-3, setup, direction, en, sl, tp, ex, res, pl]]}, {'range':f'K{next_r}:K{next_r}', 'values':[[bp]]}], value_input_option="USER_ENTERED")
                        st.success("SAVED!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                    except: st.error("บันทึกไม่สำเร็จ")

        with t2:
            # ⚠️ กู้คืนระบบ EDIT ⚠️
            st.markdown("<p style='color:#fde047; text-align:center;'>แก้ไขข้อมูลไม้เทรดเก่า</p>", unsafe_allow_html=True)
            if not df_log.empty:
                ids = [str(x) for x in df_log.iloc[:, 0].tolist() if str(x).strip() not in ['', '-']]
                sel_id = st.selectbox("เลือก ID ไม้ที่ต้องการแก้ไข:", ["-- เลือก --"] + ids)
                if sel_id != "-- เลือก --":
                    row_idx = df_log[df_log.iloc[:, 0].astype(str) == sel_id].index[0]
                    with st.form("edit_trade"):
                        ec1, ec2 = st.columns(2)
                        new_res = ec1.selectbox("เปลี่ยนผลลัพธ์", ["Win", "Loss", "กันทุน", "Pending"])
                        new_pl = ec2.number_input("เปลี่ยน P/L ($)", value=safe_float(df_log.iloc[row_idx, 8]))
                        if st.form_submit_button("🔄 UPDATE LOG"):
                            try:
                                gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                                wks.update_cell(row_idx + 4, 8, new_res)
                                wks.update_cell(row_idx + 4, 9, new_pl)
                                st.success("อัปเดตสำเร็จ!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                            except: st.error("Error")
            st.divider()
            conf = st.text_input("พิมพ์ RESET เพื่อลบทั้งหมด:")
            if st.button("🧨 RESET DATA8", type="primary", disabled=(conf != "RESET")):
                try:
                    gc = get_gspread_client(); gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8").batch_clear(["A4:Q1000"])
                    st.success("CLEARED!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except: st.error("Error")

    st.divider()
    col_l, col_r = st.columns([1, 2.2])
    with col_l:
        st.markdown('<p class="sub-header">📈 SUMMARY</p>', unsafe_allow_html=True)
        df_dash = load_sheet_data("Dashboard8")
        if not df_dash.empty:
            html = '<div class="table-wrapper"><table class="summary-table"><tbody>'
            for _, r in df_dash.iloc[:, :2].iterrows():
                if str(r.iloc[0]) != '-': html += f'<tr><td>{r.iloc[0]}</td><td>{r.iloc[1]}</td></tr>'
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)
    with col_r:
        st.markdown('<p class="sub-header">📝 RECENT LOGS</p>', unsafe_allow_html=True)
        if not df_log.empty:
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
            for c in df_log.columns[:10]: html += f'<th>{c}</th>'
            html += '</tr></thead><tbody>'
            for _, r in df_log.iterrows():
                if str(r.iloc[0]) == '-': continue
                cl = "#00dfd8" if str(r.iloc[7]).lower()=="win" else "#ff0080" if str(r.iloc[7]).lower()=="loss" else "inherit"
                html += f'<tr>' + "".join(f'<td style="color:{cl if i==7 else "inherit"};">{v}</td>' for i, v in enumerate(r[:10])) + '</tr>'
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)

# =====================================================================
# 📦 PAGE 3: STOCK MANAGER
# =====================================================================
elif page == "📦 STOCK MANAGER":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/3045/3045488.png" width="80"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">STOCK MANAGER</h1>', unsafe_allow_html=True)
    tab_inv, tab_out, tab_in = st.tabs(["💎 CURRENT STOCK", "📤 OUT (เบิก)", "📥 IN (เติม)"])
    df_stk = load_sheet_data("Master_Stock (ฐานข้อมูลหลัก)")

    with tab_inv:
        if not df_stk.empty:
            st.markdown('<p class="sub-header">รายการสินค้าคงเหลือ</p>', unsafe_allow_html=True)
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
            for c in df_stk.columns: html += f'<th>{c}</th>'
            html += '</tr></thead><tbody>'
            for _, r in df_stk.iterrows():
                if str(r.iloc[0]) == '-': continue
                # ⚠️ ล็อกคอลัมน์ H(7) และ I(8) ⚠️
                q, w = safe_float(r.iloc[7]), safe_float(r.iloc[8])
                cls = 'class="low-stock"' if q <= w else ""
                html += f'<tr {cls}>' + "".join(f'<td>{v}</td>' for v in r) + '</tr>'
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)
        else: st.warning("ยังไม่มีข้อมูลใน Master_Stock")

    with tab_out:
        with st.form("out"):
            c1, c2, c3 = st.columns(3)
            hn, p_name = c1.text_input("HN"), c2.text_input("ชื่อคนไข้")
            cats = list(dict.fromkeys(df_stk.iloc[:, 0].tolist())) if not df_stk.empty else []
            cat = c3.selectbox("หมวดหมู่", cats)
            c4, c5, c6 = st.columns(3)
            sz, cl, q = c4.text_input("ไซส์"), c5.text_input("สี"), c6.number_input("จำนวน", min_value=1)
            if st.form_submit_button("🚀 CONFIRM OUT"):
                try:
                    gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Log_เบิกออก")
                    wks.append_row([datetime.now().strftime("%Y-%m-%d"), hn, p_name, cat, sz, cl, q], value_input_option="USER_ENTERED")
                    st.success("สำเร็จ!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except: st.error("Error")

    with tab_in:
        with st.form("in"):
            c1, c2, c3 = st.columns(3)
            cat_in = c1.selectbox("หมวดหมู่สินค้า", cats)
            sz_in, cl_in = c2.text_input("ไซส์ (IN)"), c3.text_input("สี (IN)")
            q_in, cst = st.number_input("จำนวน", min_value=1), st.number_input("ต้นทุน")
            if st.form_submit_button("🚀 CONFIRM IN"):
                try:
                    gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Log_รับเข้า")
                    wks.append_row([datetime.now().strftime("%Y-%m-%d"), cat_in, sz_in, cl_in, q_in, cst], value_input_option="USER_ENTERED")
                    st.success("สำเร็จ!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except: st.error("Error")

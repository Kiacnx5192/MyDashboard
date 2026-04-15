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
st.set_page_config(page_title="Carista Ultimate Hub", layout="wide", initial_sidebar_state="expanded")

# --- 🔑 GOOGLE SHEETS CONNECTION (Enhanced) ---
def get_gspread_client():
    try:
        creds_dict = json.loads(st.secrets["google_creds"])
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ ระบบเชื่อมต่อล้มเหลว: {e}")
        return None

def safe_float(val):
    try:
        # กำจัดตัวอักษรที่ไม่ใช่ตัวเลขออกให้หมดก่อนแปลง
        clean_val = re.sub(r'[^\d.]', '', str(val))
        return float(clean_val) if clean_val else 0.0
    except: return 0.0

# --- 🎨 GLOBAL NEON CYBER CSS (Full Version) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(15, 23, 42, 0.7) !important; backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important; border-radius: 15px !important; padding: 20px !important;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.15) !important; 
    }

    .main-title { font-size: 48px; font-weight: 900; text-align: center; background: linear-gradient(to right, #00dfd8, #007cf0, #00dfd8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }
    .sub-header { color: #f472b6; text-align: center; font-size: 20px; font-weight: 800; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 10px rgba(244, 114, 182, 0.3);}

    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(15, 23, 42, 0.8); border-radius: 10px 10px 0 0; border: 1px solid rgba(232, 121, 249, 0.3); color: #cbd5e1; height: 50px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(to bottom, #7928ca, #ff0080) !important; color: #ffffff !important; font-weight: bold; border: 1px solid #ff0080 !important; }

    .table-wrapper { height: 450px; overflow-y: auto; overflow-x: auto; border-radius: 15px; background: rgba(0,0,0,0.4); border: 1px solid rgba(56, 189, 248, 0.2); }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 1000px; } 
    .custom-table th { background: #0f172a; color: #00dfd8; padding: 15px; position: sticky; top: 0; z-index: 10; border-bottom: 3px solid #007cf0; font-size: 13px; text-transform: uppercase;}
    .custom-table td { padding: 12px; text-align: center !important; color: #f8fafc; border-bottom: 1px solid rgba(56, 189, 248, 0.1); font-size: 14px; white-space: nowrap;}
    
    .news-card { background: rgba(15, 23, 42, 0.85); padding: 18px; border-radius: 12px; margin-bottom: 12px; box-shadow: 0 10px 20px rgba(0,0,0,0.5); border-left: 5px solid #00dfd8; }
    div[data-testid="stMetricValue"] > div { color: #00dfd8 !important; font-size: 38px !important; font-weight: 900 !important; }
    div[data-testid="stFormSubmitButton"] button { background: linear-gradient(45deg, #0070f3, #7928ca, #ff0080) !important; width: 100% !important; font-weight: 900 !important; height: 50px !important; }
    .low-stock { background-color: rgba(255, 0, 128, 0.15) !important; color: #ff0080 !important; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 SIDEBAR ----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("<h2 style='text-align: center; color: #00dfd8;'>CARISTA SYSTEM</h2>", unsafe_allow_html=True)
    page = st.radio("เลือกหน้าต่าง:", ["🌐 MARKET INSIGHT", "📊 TRADING DESK", "📦 STOCK MANAGER"])
    st.divider()
    if st.button("🔄 FORCE REFRESH"):
        st.cache_data.clear()
        st.rerun()

# --- 📑 UNIVERSAL DATA LOADER (แก้ไขเรื่องชื่อ Sheet) ---
def load_data_flexible(sheet_hint):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w")
        all_sheets = [s.title for s in sh.worksheets()]
        # ค้นหาชื่อที่ใกล้เคียงที่สุดโดยไม่สนตัวอักษรเล็กใหญ่หรือช่องว่าง
        target = next((s for s in all_sheets if sheet_hint.lower().replace(" ", "") in s.lower().replace(" ", "")), None)
        if target:
            data = sh.worksheet(target).get_all_values()
            if data: return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    except: return pd.DataFrame()

# =====================================================================
# 🌐 PAGE 1: MARKET INSIGHT
# =====================================================================
if page == "🌐 MARKET INSIGHT":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/3859/3859033.png" width="80"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">MARKET INSIGHT</h1>', unsafe_allow_html=True)
    
    # ดึงราคา
    try:
        prices = []
        for t in ["GC=F", "BTC-USD", "^SET.BK", "THB=X"]:
            h = yf.Ticker(t).history(period="5d")
            prices.append((h['Close'].iloc[-1], h['Close'].iloc[-1] - h['Open'].iloc[-1]))
    except: prices = [(0,0)]*4

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🟡 GOLD", f"{prices[0][0]:,.2f}", f"{prices[0][1]:+,.2f}")
    m2.metric("🟠 BTC", f"{prices[1][0]:,.2f}", f"{prices[1][1]:+,.2f}")
    m3.metric("🟢 SET", f"{prices[2][0]:,.2f}", f"{prices[2][1]:+,.2f}")
    m4.metric("🔵 USD/THB", f"{prices[3][0]:,.3f}", f"{prices[3][1]:+,.3f}", delta_color="inverse")
    
    st.markdown("<h2 style='text-align: center; color: #f59e0b; margin: 25px 0;'>🌐 GLOBAL NEWS FEED</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    news_config = [
        ("🟡 GOLD NEWS", "https://news.google.com/rss/search?q=gold+price&hl=en-US", c1, "#fbbf24"),
        ("🟠 CRYPTO NEWS", "https://cointelegraph.com/rss", c2, "#f43f5e"),
        ("🟢 THAI MARKET", "https://news.google.com/rss/search?q=SET50&hl=th", c3, "#10b981")
    ]
    for title, url, col, color in news_config:
        with col:
            st.markdown(f"<h3 style='text-align: center;'>{title}</h3>", unsafe_allow_html=True)
            feed = feedparser.parse(url)
            for e in feed.entries[:3]:
                st.markdown(f'<div class="news-card" style="border-left-color:{color};"><strong>{e.title}</strong><br><a href="{e.link}" target="_blank" style="color:#00dfd8; font-size:12px;">READ STORY</a></div>', unsafe_allow_html=True)

# =====================================================================
# 📊 PAGE 2: TRADING DESK
# =====================================================================
elif page == "📊 TRADING DESK":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2422/2422796.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">TRADING DESK</h1>', unsafe_allow_html=True)
    
    df_log = load_data_flexible("Data8")
    
    with st.container(border=True):
        t1, t2 = st.tabs(["➕ ADD NEW TRADE", "✏️ MANAGE LOGS"])
        with t1:
            with st.form("add_trade"):
                c1, c2, c3 = st.columns(3)
                setup = c1.selectbox("SETUP", ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"])
                direction = c2.selectbox("Buy/Sell", ["Buy", "Sell"])
                res = c3.selectbox("Result", ["Pending", "Win", "Loss", "กันทุน"])
                c4, c5, c6, c7 = st.columns(4)
                en = c4.number_input("Entry", format="%.5f")
                sl = c5.number_input("SL", format="%.5f")
                tp = c6.number_input("TP", format="%.5f")
                ex = c7.number_input("Exit", format="%.5f")
                pl = st.number_input("P/L ($)", format="%.2f")
                bp = st.number_input("Best Price", format="%.5f")
                if st.form_submit_button("🚀 SAVE TO DATA8"):
                    try:
                        gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                        next_r = len(wks.col_values(2)) + 1
                        wks.batch_update([{'range':f'A{next_r}:I{next_r}', 'values':[[next_r-3, setup, direction, en, sl, tp, ex, res, pl]]}, {'range':f'K{next_r}:K{next_r}', 'values':[[bp]]}], value_input_option="USER_ENTERED")
                        st.success("✅ บันทึกเรียบร้อย!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                    except: st.error("บันทึกไม่สำเร็จ")
        
        with t2:
            st.markdown("<p style='color:#fde047; text-align:center;'>แก้ไขข้อมูลไม้เทรดเก่า</p>", unsafe_allow_html=True)
            if not df_log.empty:
                ids = [str(x) for x in df_log.iloc[:, 0].tolist() if str(x).strip() not in ['', '-']]
                sel_id = st.selectbox("เลือก ID ไม้ที่ต้องการแก้ไข:", ["-- เลือก --"] + ids)
                if sel_id != "-- เลือก --":
                    row_data = df_log[df_log.iloc[:, 0].astype(str) == sel_id].iloc[0]
                    with st.form("edit_form"):
                        ec1, ec2 = st.columns(2)
                        new_res = ec1.selectbox("เปลี่ยนผลลัพธ์", ["Win", "Loss", "กันทุน", "Pending"])
                        new_pl = ec2.number_input("เปลี่ยน P/L ($)", value=safe_float(row_data.iloc[8]))
                        if st.form_submit_button("🔄 UPDATE LOG"):
                            try:
                                gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                                target_idx = df_log[df_log.iloc[:, 0].astype(str) == sel_id].index[0]
                                wks.update_cell(target_idx + 4, 8, new_res)
                                wks.update_cell(target_idx + 4, 9, new_pl)
                                st.success("✅ อัปเดตสำเร็จ!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                            except: st.error("อัปเดตล้มเหลว")
            st.divider()
            conf = st.text_input("พิมพ์ RESET เพื่อล้าง Data8 (A4:Q1000):")
            if st.button("🧨 RESET ALL TRADES", type="primary", disabled=(conf != "RESET")):
                try:
                    gc = get_gspread_client(); gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8").batch_clear(["A4:Q1000"])
                    st.success("🔥 ล้างข้อมูลเรียบร้อย!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except: st.error("Reset ล้มเหลว")

    st.divider()
    col_l, col_r = st.columns([1, 2.2])
    with col_l:
        st.markdown('<p class="sub-header">📈 SUMMARY</p>', unsafe_allow_html=True)
        df_dash = load_data_flexible("Dashboard8")
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
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2331/2331941.png" width="80"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">STOCK MANAGER</h1>', unsafe_allow_html=True)
    
    # ใช้ระบบค้นหาชื่อ Sheet แบบยืดหยุ่น
    df_stk = load_data_flexible("Master_Stock")
    
    tab1, tab2, tab3 = st.tabs(["💎 CURRENT STOCK", "📤 OUT (เบิก)", "📥 IN (เติม)"])

    with tab1:
        if not df_stk.empty:
            st.markdown('<p class="sub-header">รายการสินค้าคงเหลือปัจจุบัน</p>', unsafe_allow_html=True)
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
            for c in df_stk.columns: html += f'<th>{c}</th>'
            html += '</tr></thead><tbody>'
            for _, r in df_stk.iterrows():
                if str(r.iloc[0]) == '-': continue
                # คอลัมน์ H = Index 7, I = Index 8
                val_h = safe_float(r.iloc[7])
                val_i = safe_float(r.iloc[8])
                row_cls = 'class="low-stock"' if val_h <= val_i else ""
                html += f'<tr {row_cls}>' + "".join(f'<td>{v}</td>' for v in r) + "</tr>"
            st.markdown(html + "</tbody></table></div>", unsafe_allow_html=True)
        else:
            st.error("❌ ไม่พบแผ่นงาน 'Master_Stock' หรือไม่มีข้อมูล! กรุณากดปุ่ม FORCE REFRESH ด้านซ้ายดูอีกรอบนะคะ")

    with tab2:
        with st.form("out_form"):
            c1, c2, c3 = st.columns(3)
            hn, p_name = c1.text_input("HN"), c2.text_input("ชื่อคนไข้")
            cats = list(dict.fromkeys(df_stk.iloc[:, 0].tolist())) if not df_stk.empty else ["-"]
            cat = c3.selectbox("หมวดหมู่", cats)
            c4, c5, c6 = st.columns(3)
            sz, cl, q = c4.text_input("ไซส์"), c5.text_input("สี"), c6.number_input("จำนวนที่เบิก", min_value=1)
            if st.form_submit_button("📤 CONFIRM OUT"):
                try:
                    gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Log_เบิกออก")
                    wks.append_row([datetime.now().strftime("%d/%m/%Y"), hn, p_name, cat, sz, cl, q], value_input_option="USER_ENTERED")
                    st.success("✅ บันทึกการเบิกสำเร็จ!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except: st.error("Error")

    with tab3:
        with st.form("in_form"):
            c1, c2, c3 = st.columns(3)
            cat_in = c1.selectbox("หมวดหมู่สินค้า", cats)
            sz_in, cl_in = c2.text_input("ไซส์"), c3.text_input("สี")
            q_in = st.number_input("จำนวนรับเข้า", min_value=1)
            cost = st.number_input("ต้นทุนรวมล็อตนี้", min_value=0.0)
            if st.form_submit_button("📥 CONFIRM IN"):
                try:
                    gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Log_รับเข้า")
                    wks.append_row([datetime.now().strftime("%d/%m/%Y"), cat_in, sz_in, cl_in, q_in, cost], value_input_option="USER_ENTERED")
                    st.success("✅ เติมสต็อกสำเร็จ!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except: st.error("Error")

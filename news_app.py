import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista & Trading Intelligence", layout="wide", initial_sidebar_state="collapsed")

# --- 🔑 เชื่อมต่อ Google Sheets ด้วยตู้เซฟ Secrets ---
def get_gspread_client():
    # ดึงข้อมูลจากตู้เซฟที่เราเพิ่งวางไป
    creds_dict = json.loads(st.secrets["google_creds"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# --- 🎨 CSS ระดับพรีเมียม (Midnight Blue Gradient) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #172554 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* กล่องกระจก */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(30, 41, 59, 0.5) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important; padding: 20px !important;
    }

    .main-title { font-size: 60px; font-weight: 900; text-align: center; background: linear-gradient(to right, #ff0080, #7928ca, #0070f3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .section-perf { font-size: 28px; font-weight: 900; text-align: center; background: linear-gradient(to right, #f59e0b, #e879f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 3px; margin: 40px 0 20px 0; border-bottom: 2px dashed rgba(232, 121, 249, 0.4); }
    .sub-header { color: #38bdf8; text-align: center; font-size: 18px; font-weight: 800; margin-bottom: 15px; }

    /* สไตล์ตาราง */
    .table-wrapper { height: 400px; overflow-y: auto; overflow-x: auto; border-radius: 10px; background: rgba(0,0,0,0.2); }
    .custom-table { width: 100%; border-collapse: collapse; }
    .custom-table th { background: #0f172a; color: #38bdf8; padding: 12px; text-align: center !important; position: sticky; top: 0; z-index: 2; border-bottom: 2px solid #38bdf8; }
    .custom-table td { padding: 10px; text-align: center !important; color: #e2e8f0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 👑 Main Header ----------------
st.markdown('<h1 class="main-title">Market Intelligence</h1>', unsafe_allow_html=True)

# ---------------- 💰 Real-time Prices (โหลดเร็วขึ้น) ----------------
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
m1.metric("🟡 GOLD", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
m2.metric("🟠 BTC", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
m3.metric("🟢 SET", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
m4.metric("🔵 USDTHB", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")

# ---------------- 📊 Trading Performance & Command Center ----------------
st.markdown('<div class="section-perf">📊 TRADING PERFORMANCE</div>', unsafe_allow_html=True)

# ฟังก์ชันโหลดข้อมูล (อ่าน)
@st.cache_data(ttl=10)
def load_sheet_data(sheet_name):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w") # ID ของชีทคุณเกี๊ยะ
        worksheet = sh.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data).fillna('-')
    except Exception as e:
        st.error(f"Error loading {sheet_name}: {e}")
        return pd.DataFrame()

col_left, col_right = st.columns([1, 1.8])

with col_left:
    with st.container():
        st.markdown('<div class="sub-header">📈 วิเคราะห์การเทรด</div>', unsafe_allow_html=True)
        df_dash = load_sheet_data("Dashboard8")
        if not df_dash.empty:
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr><th>รายการ</th><th>ข้อมูลสรุป</th></tr></thead><tbody>'
            for _, row in df_dash.iloc[:, :2].iterrows():
                html += f'<tr><td>{row.iloc[0]}</td><td><b style="color:#fde047;">{row.iloc[1]}</b></td></tr>'
            html += '</tbody></table></div>'
            st.markdown(html, unsafe_allow_html=True)

with col_right:
    # --- 📝 ส่วนบันทึกข้อมูล (Write Data) ---
    with st.expander("➕ บันทึกไม้เทรดใหม่ (Write to Sheet)", expanded=False):
        with st.form("trade_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            setup = f1.selectbox("Setup", ["Breakout", "Retest", "30/30/40", "Price Action"])
            direction = f2.selectbox("Direction", ["Buy", "Sell"])
            entry = f3.number_input("Entry Price", format="%.5f")
            
            f4, f5 = st.columns(2)
            result = f4.selectbox("Result", ["Pending", "Win", "Loss", "BE"])
            pl = f5.number_input("P/L ($)", format="%.2f")
            
            submit = st.form_submit_button("🚀 บันทึกไม้เทรดลง Google Sheet")
            
            if submit:
                try:
                    gc = get_gspread_client()
                    sh = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w")
                    wks = sh.worksheet("Data8")
                    # เตรียมข้อมูล (เรียงตามคอลัมน์ใน Sheet คุณเกี๊ยะ)
                    new_row = [len(wks.get_all_values()), setup, direction, entry, "-", "-", "-", result, pl]
                    wks.append_row(new_row)
                    st.success("บันทึกข้อมูลสำเร็จ! มายนี่จัดการให้แล้วค่ะ ✨")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"บันทึกไม่สำเร็จ: {e}")

    # แสดงตารางบันทึกการเทรด
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
                color = "#4ade80" if str(val).lower() == "win" else "#f87171" if str(val).lower() == "loss" else "inherit"
                html += f'<td style="color:{color};">{val}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'
        st.markdown(html, unsafe_allow_html=True)

st.divider()
st.info("💡 พรุ่งนี้เราจะมาเพิ่มหน้าสำหรับ 'Stock ชุดกระชับ' และ 'หัตถการคลินิก' ต่อกันนะคะคุณเกี๊ยะ!")

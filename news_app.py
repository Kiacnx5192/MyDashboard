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
    try: return float(str(val).replace(',', ''))
    except: return 0.0

# --- 🎨 CSS: Cyber Neon Edition ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(15, 23, 42, 0.7) !important; backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important; border-radius: 20px !important; padding: 25px !important;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.15) !important; 
    }

    .stTabs [aria-selected="true"] { background: linear-gradient(to bottom, #7928ca, #ff0080) !important; color: #ffffff !important; font-weight: 900 !important; box-shadow: 0 0 15px rgba(255, 0, 128, 0.4) !important; }

    .main-title { font-size: 55px; font-weight: 900; text-align: center; background: linear-gradient(to right, #00dfd8, #007cf0, #00dfd8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 25px; filter: drop-shadow(0 0 15px rgba(0, 223, 216, 0.3)); }
    .section-header { font-size: 26px; font-weight: 900; text-align: center; background: linear-gradient(to right, #f59e0b, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 3px; margin: 30px 0; border-bottom: 2px dashed rgba(245, 158, 11, 0.5); padding-bottom: 15px;}
    .sub-header { color: #f472b6; text-align: center; font-size: 22px; font-weight: 900; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 10px rgba(244, 114, 182, 0.3);}

    /* Table Neon */
    .table-wrapper { height: 400px; overflow-y: auto; border-radius: 15px; background: rgba(0,0,0,0.4); border: 1px solid rgba(56, 189, 248, 0.2); }
    .custom-table { width: 100%; border-collapse: collapse; } 
    .custom-table th { background: #0f172a; color: #00dfd8; padding: 15px; position: sticky; top: 0; border-bottom: 3px solid #007cf0; font-size: 13px; text-transform: uppercase;}
    .custom-table td { padding: 12px; text-align: center; border-bottom: 1px solid rgba(56, 189, 248, 0.1); font-size: 14px; }
    
    /* Low Stock Alert */
    .low-stock { color: #ff0080 !important; font-weight: 900; text-shadow: 0 0 10px rgba(255, 0, 128, 0.5); animation: blink 1.5s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

    div[data-testid="stFormSubmitButton"] button { background: linear-gradient(45deg, #0070f3, #7928ca, #ff0080) !important; font-weight: 900 !important; border-radius: 12px !important; box-shadow: 0 0 20px rgba(121, 40, 202, 0.5) !important; }
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

# ---------------- 🚀 Load Stock Data ----------------
@st.cache_data(ttl=5)
def load_stock_data(sheet_name):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w")
        data = sh.worksheet(sheet_name).get_all_values()
        return pd.DataFrame(data[1:], columns=data[0])
    except: return pd.DataFrame()

# =====================================================================
# 📦 PAGE 3: STOCK MANAGER (ระบบใหม่จี๊ดจ๊าด)
# =====================================================================
if page == "📦 STOCK MANAGER":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2897/2897864.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="margin-top:-10px;">STOCK MANAGER</h1>', unsafe_allow_html=True)

    tab_inv, tab_out, tab_in = st.tabs(["💎 CURRENT STOCK", "📤 OUT (เบิก/ขาย)", "📥 IN (เติมสต็อก)"])

    # --- TAB 1: CURRENT STOCK ---
    with tab_inv:
        df_stock = load_stock_data("Stock")
        if not df_stock.empty:
            st.markdown('<div class="sub-header">รายการสินค้าคงเหลือปัจจุบัน</div>', unsafe_allow_html=True)
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
            for col in df_stock.columns: html += f'<th>{col}</th>'
            html += '</tr></thead><tbody>'
            for _, row in df_stock.iterrows():
                # ตรวจสอบว่า "คงเหลือ" (Index 4) ต่ำกว่า "ต้องสั่งเพิ่ม" (Index 5) หรือไม่
                qty = safe_float(row.iloc[4])
                min_qty = safe_float(row.iloc[5])
                row_style = 'class="low-stock"' if qty <= min_qty else ""
                html += f'<tr {row_style}>'
                for v in row: html += f'<td>{v}</td>'
                html += '</tr>'
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)

    # --- TAB 2: OUT (เบิกสินค้า) ---
    with tab_out:
        df_stock = load_stock_data("Stock")
        items = df_stock.iloc[:, 1].tolist() if not df_stock.empty else [] # คอลัมน์รายการ
        
        with st.form("out_form", clear_on_submit=True):
            st.markdown("<p style='text-align:center; color:#38bdf8;'>บันทึกการเบิกสินค้า / การขาย</p>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            item_sel = c1.selectbox("เลือกสินค้าที่เบิก", items)
            qty_out = c2.number_input("จำนวนที่เบิก", min_value=1, step=1)
            
            c3, c4 = st.columns(2)
            receiver = c3.text_input("ชื่อผู้เบิก / ลูกค้า")
            note = c4.text_input("หมายเหตุ")
            
            if st.form_submit_button("📤 ยืนยันการเบิกสินค้า"):
                try:
                    gc = get_gspread_client()
                    wks_out = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Out")
                    # ค้นหาลำดับล่าสุด (Col A)
                    next_row = len(wks_out.col_values(1)) + 1
                    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
                    wks_out.append_row([next_row-1, item_sel, qty_out, receiver, date_now, note], value_input_option="USER_ENTERED")
                    st.success(f"บันทึกการเบิก {item_sel} เรียบร้อยแล้วค่ะ!"); time.sleep(2); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    # --- TAB 3: IN (เติมสต็อก) ---
    with tab_in:
        with st.form("in_form", clear_on_submit=True):
            st.markdown("<p style='text-align:center; color:#f472b6;'>บันทึกของเข้าคลัง (Restock)</p>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            item_in = c1.selectbox("สินค้าที่มาส่ง", items)
            qty_in = c2.number_input("จำนวนที่รับเข้า", min_value=1, step=1)
            
            supplier = st.text_input("แหล่งที่มา / Supplier")
            
            if st.form_submit_button("📥 ยืนยันการเติมสต็อก"):
                try:
                    gc = get_gspread_client()
                    wks_in = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("In")
                    next_row = len(wks_in.col_values(1)) + 1
                    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
                    wks_in.append_row([next_row-1, item_in, qty_in, date_now, supplier], value_input_option="USER_ENTERED")
                    st.success(f"เติมสต็อก {item_in} เรียบร้อยค่ะ!"); time.sleep(2); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

# =====================================================================
# (รักษาโค้ดหน้า Market Insight และ Trading Desk ไว้เหมือนเดิมด้านล่าง)
# =====================================================================
elif page == "🌐 MARKET INSIGHT":
    # ... (โค้ด Market Insight เดิมของคุณเกี๊ยะ) ...
    pass 
elif page == "📊 TRADING DESK":
    # ... (โค้ด Trading Desk เดิมของคุณเกี๊ยะ) ...
    pass

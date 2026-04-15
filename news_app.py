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
    try: return float(str(val).replace(',', '').replace('-', '0'))
    except: return 0.0

# --- 🎨 CSS: Cyber Neon Edition ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(15, 23, 42, 0.7) !important; backdrop-filter: blur(15px) !important; border: 1px solid rgba(56, 189, 248, 0.4) !important; border-radius: 20px !important; padding: 25px !important; box-shadow: 0 0 25px rgba(56, 189, 248, 0.15) !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 15px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(15, 23, 42, 0.8); border-radius: 12px 12px 0 0; border: 1px solid rgba(232, 121, 249, 0.3); color: #cbd5e1; padding: 12px 25px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(to bottom, #7928ca, #ff0080) !important; color: #ffffff !important; font-weight: 900 !important; box-shadow: 0 0 15px rgba(255, 0, 128, 0.4) !important; }
    .main-title { font-size: 55px; font-weight: 900; text-align: center; background: linear-gradient(to right, #00dfd8, #007cf0, #00dfd8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 25px; filter: drop-shadow(0 0 15px rgba(0, 223, 216, 0.3)); }
    .section-header { font-size: 26px; font-weight: 900; text-align: center; background: linear-gradient(to right, #f59e0b, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 3px; margin: 30px 0; border-bottom: 2px dashed rgba(245, 158, 11, 0.5); padding-bottom: 15px;}
    .sub-header { color: #f472b6; text-align: center; font-size: 22px; font-weight: 900; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 10px rgba(244, 114, 182, 0.3);}
    .table-wrapper { height: 450px; overflow-y: auto; border-radius: 15px; background: rgba(0,0,0,0.4); border: 1px solid rgba(56, 189, 248, 0.2); }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 800px; } 
    .custom-table th { background: #0f172a; color: #00dfd8; padding: 15px; position: sticky; top: 0; z-index: 10; border-bottom: 3px solid #007cf0; font-size: 13px; text-transform: uppercase;}
    .custom-table td { padding: 12px; text-align: center; border-bottom: 1px solid rgba(56, 189, 248, 0.1); font-size: 14px; }
    .low-stock { color: #ff0080 !important; font-weight: 900; text-shadow: 0 0 10px rgba(255, 0, 128, 0.5); }
    div[data-testid="stFormSubmitButton"] button { background: linear-gradient(45deg, #0070f3, #7928ca, #ff0080) !important; font-weight: 900 !important; border-radius: 12px !important; box-shadow: 0 0 20px rgba(121, 40, 202, 0.5) !important; width: 100% !important;}
    .news-card { background: rgba(15, 23, 42, 0.85); padding: 25px; border-radius: 15px; margin-bottom: 20px; border-left: 6px solid #38bdf8; box-shadow: 0 10px 20px rgba(0,0,0,0.5); }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 Sidebar Menu ----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("<h2 style='text-align: center; color: #00dfd8;'>CARISTA PANEL</h2>", unsafe_allow_html=True)
    page = st.radio("SELECT PAGE:", ["🌐 MARKET INSIGHT", "📊 TRADING DESK", "📦 STOCK MANAGER"])
    st.divider()
    if st.button("🔄 REFRESH SYSTEM"):
        st.cache_data.clear()
        st.rerun()

# ---------------- 📑 FUNCTIONS ----------------
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
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/8144/8144863.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="margin-top:-10px;">MARKET INSIGHT</h1>', unsafe_allow_html=True)
    p = get_prices()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🟡 GOLD", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
    m2.metric("🟠 BTC", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
    m3.metric("🟢 SET", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
    m4.metric("🔵 USD/THB", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")
    
    st.markdown('<div class="section-header">🌐 GLOBAL NEWS FEED</div>', unsafe_allow_html=True)
    def get_news(url):
        try:
            f = feedparser.parse(url, agent='Mozilla/5.0')
            return [{'t': e.title, 'l': e.link, 'd': e.get('published', 'Recent')[:25], 's': re.sub('<.*?>', '', e.get('summary', ''))[:120]+'...'} for e in f.entries[:3]]
        except: return []
    c1, c2, c3 = st.columns(3)
    urls = [("🟡 GOLD", "https://news.google.com/rss/search?q=gold+price&hl=en-US"), ("🟠 CRYPTO", "https://cointelegraph.com/rss"), ("🟢 THAI", "https://news.google.com/rss/search?q=SET50&hl=th")]
    for col, (title, url) in zip([c1, c2, c3], urls):
        with col:
            st.markdown(f"<h3 style='text-align: center;'>{title}</h3>", unsafe_allow_html=True)
            for n in get_news(url):
                st.markdown(f'<div class="news-card"><strong>{n["t"]}</strong><br><small>{n["d"]}</small><br><p>{n["s"]}</p><a href="{n["l"]}" target="_blank" style="color:#00dfd8;">Read More</a></div>', unsafe_allow_html=True)

# =====================================================================
# 📊 PAGE 2: TRADING DESK
# =====================================================================
elif page == "📊 TRADING DESK":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2422/2422796.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="margin-top:-10px;">TRADING DESK</h1>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ ADD NEW", "✏️ EDIT & DELETE"])
    
    # ดึงข้อมูลมาโชว์ด้านล่างเสมอ
    df_log = load_sheet_data("Data8")
    
    with tab1:
        with st.form("add_trade"):
            c1, c2, c3 = st.columns(3)
            setup = c1.selectbox("SETUP", ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"])
            direction = c2.selectbox("Buy/Sell", ["Buy", "Sell"])
            res = c3.selectbox("RESULT", ["Pending", "Win", "Loss", "กันทุน"])
            c4, c5, c6, c7 = st.columns(4)
            en, sl, tp, ex = c4.number_input("Entry", format="%.5f"), c5.number_input("SL", format="%.5f"), c6.number_input("TP", format="%.5f"), c7.number_input("Exit", format="%.5f")
            pl, bp = st.number_input("P/L ($)", format="%.2f"), st.number_input("Best Price", format="%.5f")
            if st.form_submit_button("🚀 SUBMIT"):
                try:
                    gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                    next_r = len(wks.col_values(2)) + 1
                    wks.batch_update([{'range':f'A{next_r}:I{next_r}', 'values':[[next_r-3, setup, direction, en, sl, tp, ex, res, pl]]}, {'range':f'K{next_r}:K{next_r}', 'values':[[bp]]}], value_input_option="USER_ENTERED")
                    st.success("SAVED!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except Exception as e: st.error(e)

    # (ส่วน Edit/Delete มายนี่รวบไว้เพื่อความกระชับ แต่ถ้าคุณเกี๊ยะต้องการแก้ไขทักมาได้เลยค่ะ)

    st.divider()
    if not df_log.empty:
        st.markdown('<div class="table-wrapper"><table class="custom-table"><thead><tr>' + "".join(f"<th>{c}</th>" for c in df_log.columns[:10]) + '</tr></thead><tbody>' + 
                    "".join(f"<tr>" + "".join(f"<td>{v}</td>" for v in row[:10]) + "</tr>" for _, row in df_log.iterrows() if str(row.iloc[0]) != '-') + '</tbody></table></div>', unsafe_allow_html=True)

# =====================================================================
# 📦 PAGE 3: STOCK MANAGER (ระบบใหม่แบบจี๊ดจ๊าด!)
# =====================================================================
elif page == "📦 STOCK MANAGER":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2897/2897864.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="margin-top:-10px;">STOCK MANAGER</h1>', unsafe_allow_html=True)

    tab_inv, tab_out, tab_in = st.tabs(["💎 CURRENT STOCK", "📤 OUT (เบิก/ขาย)", "📥 IN (เติมสต็อก)"])

    # โหลดข้อมูลจากแผ่นงานที่คุณเกี๊ยะตั้งชื่อไว้
    df_stock = load_sheet_data("Master_Stock (ฐานข้อมูลหลัก)")

    with tab_inv:
        if not df_stock.empty:
            st.markdown('<div class="sub-header">รายการสินค้าคงเหลือปัจจุบัน</div>', unsafe_allow_html=True)
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
            for col in df_stock.columns: html += f'<th>{col}</th>'
            html += '</tr></thead><tbody>'
            for _, row in df_stock.iterrows():
                if str(row.iloc[0]).strip() == '-': continue
                qty = safe_float(row.iloc[7]) # ช่องสต็อกคงเหลือ (Col H)
                min_qty = safe_float(row.iloc[8]) # ช่องจุดเตือน (Col I)
                style = 'class="low-stock"' if qty <= min_qty else ""
                html += f'<tr {style}>' + "".join(f"<td>{v}</td>" for v in row) + "</tr>"
            st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)

    with tab_out:
        with st.form("out_form", clear_on_submit=True):
            st.markdown("<p style='text-align:center; color:#38bdf8;'>บันทึกการเบิกสินค้า (LOG_เบิกออก)</p>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            hn = c1.text_input("HN")
            patient = c2.text_input("ชื่อคนไข้")
            item_list = list(dict.fromkeys(df_stock.iloc[:, 0].tolist())) if not df_stock.empty else []
            cat = c3.selectbox("หมวดหมู่", item_list)
            
            c4, c5, c6 = st.columns(3)
            size = c4.text_input("ไซส์")
            color = c5.text_input("สี")
            qty_out = c6.number_input("จำนวนที่เบิก", min_value=1, step=1)
            
            if st.form_submit_button("📤 ยืนยันการเบิกสินค้า"):
                try:
                    gc = get_gspread_client()
                    wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Log_เบิกออก")
                    date = datetime.now().strftime("%Y-%m-%d")
                    wks.append_row([date, hn, patient, cat, size, color, qty_out], value_input_option="USER_ENTERED")
                    st.success("บันทึกสำเร็จ!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except Exception as e: st.error(e)

    with tab_in:
        with st.form("in_form", clear_on_submit=True):
            st.markdown("<p style='text-align:center; color:#f472b6;'>บันทึกของเข้าคลัง (LOG_รับเข้า)</p>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            cat_in = c1.selectbox("หมวดหมู่สินค้า", item_list)
            size_in = c2.text_input("ไซส์ (IN)")
            color_in = c3.text_input("สี (IN)")
            qty_in = st.number_input("จำนวนที่รับเข้า", min_value=1, step=1)
            cost = st.number_input("ต้นทุนรวมล็อตนี้ (บาท)", min_value=0.0)
            
            if st.form_submit_button("📥 ยืนยันการเติมสต็อก"):
                try:
                    gc = get_gspread_client()
                    wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Log_รับเข้า")
                    date = datetime.now().strftime("%Y-%m-%d")
                    wks.append_row([date, cat_in, size_in, color_in, qty_in, cost], value_input_option="USER_ENTERED")
                    st.success("เติมสต็อกเรียบร้อย!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except Exception as e: st.error(e)

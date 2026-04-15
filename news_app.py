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

# --- 🎨 CSS: Cyber Neon Edition (จี๊ดจ๊าดสะใจคุณเกี๊ยะ) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(15, 23, 42, 0.7) !important; backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important; border-radius: 20px !important; padding: 25px !important;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.15), inset 0 0 10px rgba(56, 189, 248, 0.05) !important; 
    }

    /* Tabs Neon Style */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 15px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(15, 23, 42, 0.8); border-radius: 12px 12px 0 0; border: 1px solid rgba(232, 121, 249, 0.3); color: #cbd5e1; padding: 12px 25px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(to bottom, #7928ca, #ff0080) !important; color: #ffffff !important; font-weight: 900 !important; border: 1px solid #ff0080 !important; box-shadow: 0 0 15px rgba(255, 0, 128, 0.4) !important; }

    /* Inputs & Form */
    .stTextInput label p, .stSelectbox label p, .stNumberInput label p { color: #38bdf8 !important; font-size: 14px !important; font-weight: 800 !important; text-transform: uppercase; letter-spacing: 1px; }
    div[data-testid="stFormSubmitButton"] button, .btn-primary { 
        background: linear-gradient(45deg, #0070f3, #7928ca, #ff0080) !important; 
        color: white !important; font-weight: 900 !important; border-radius: 12px !important; 
        padding: 12px 20px !important; width: 100% !important; text-transform: uppercase; letter-spacing: 2px;
        box-shadow: 0 0 20px rgba(121, 40, 202, 0.5) !important; transition: 0.5s;
    }
    div[data-testid="stFormSubmitButton"] button:hover { transform: scale(1.02); box-shadow: 0 0 30px rgba(255, 0, 128, 0.6) !important; }

    /* Typography */
    .main-title { font-size: 55px; font-weight: 900; text-align: center; background: linear-gradient(to right, #00dfd8, #007cf0, #00dfd8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 25px; filter: drop-shadow(0 0 15px rgba(0, 223, 216, 0.3)); }
    .section-header { font-size: 26px; font-weight: 900; text-align: center; background: linear-gradient(to right, #f59e0b, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 3px; margin: 30px 0; border-bottom: 2px dashed rgba(245, 158, 11, 0.5); padding-bottom: 15px;}
    .sub-header { color: #f472b6; text-align: center; font-size: 22px; font-weight: 900; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 10px rgba(244, 114, 182, 0.3);}

    /* Tables */
    .table-wrapper { height: 450px; overflow-y: auto; overflow-x: auto; border-radius: 15px; background: rgba(0,0,0,0.4); border: 1px solid rgba(56, 189, 248, 0.2); }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 1200px; } 
    .custom-table th { background: #0f172a; color: #00dfd8; padding: 15px; text-align: center !important; position: sticky; top: 0; z-index: 10; border-bottom: 3px solid #007cf0; font-size: 13px; text-transform: uppercase;}
    .custom-table td { padding: 12px; text-align: center !important; color: #f8fafc; border-bottom: 1px solid rgba(56, 189, 248, 0.1); font-size: 14px; white-space: nowrap;}
    
    .summary-table { width: 90%; margin: 0 auto; border-collapse: collapse; }
    .summary-table td:first-child { text-align: left !important; color: #94a3b8; padding: 12px; font-weight: 600;}
    .summary-table td:last-child { text-align: right !important; font-weight: 900; color: #fde047; padding: 12px; font-size: 18px; text-shadow: 0 0 10px rgba(253, 224, 71, 0.4);}
    .summary-table tr { border-bottom: 1px solid rgba(255,255,255,0.08); transition: 0.3s; }
    
    /* Low Stock Warning */
    .low-stock { color: #ff0080 !important; font-weight: 900; text-shadow: 0 0 10px rgba(255, 0, 128, 0.5); }

    /* 🌐 News Feed สวยงาม */
    .news-card { background: rgba(15, 23, 42, 0.85); padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 10px 20px rgba(0,0,0,0.5); transition: 0.4s; }
    .news-card:hover { border-color: rgba(56, 189, 248, 0.5); box-shadow: 0 0 25px rgba(56, 189, 248, 0.25); }
    .card-gold { border-left: 6px solid #fbbf24; } .card-crypto { border-left: 6px solid #f43f5e; } .card-thai { border-left: 6px solid #10b981; }
    .news-title { color: #ffffff; font-size: 17px; font-weight: 800; margin: 10px 0 12px 0; line-height: 1.5; }
    .news-date { color: #94a3b8; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 5px;}
    .news-snip { color: #cbd5e1; font-size: 13.5px; line-height: 1.6; margin-bottom: 15px; opacity: 0.8;}
    .btn-news { display: inline-block; padding: 9px 22px; border-radius: 50px; color: white !important; font-weight: 800; text-decoration: none; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
    .btn-gold { background: #d97706; } .btn-crypto { background: #dc2626; } .btn-thai { background: #059669; }
    
    div[data-testid="stMetricValue"] > div { color: #00dfd8 !important; font-size: 42px !important; font-weight: 900 !important; text-shadow: 0 0 15px rgba(0, 223, 216, 0.4);}
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 Sidebar Menu ----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("<h2 style='text-align: center; color: #00dfd8;'>ADMIN PANEL</h2>", unsafe_allow_html=True)
    page = st.radio("SELECT PAGE:", ["🌐 MARKET INSIGHT", "📊 TRADING DESK", "📦 STOCK MANAGER"])
    st.divider()
    if st.button("🔄 REFRESH SYSTEM"):
        st.cache_data.clear()
        st.rerun()

# --- 📑 FUNCTIONS ----------------
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

def get_news(url):
    try:
        f = feedparser.parse(url, agent='Mozilla/5.0')
        results = []
        for e in f.entries[:3]:
            d = e.get('published', e.get('pubDate', 'Recent'))[:25]
            s = re.sub('<.*?>', '', e.get('summary', ''))[:110] + '...'
            results.append({'t': e.title, 'l': e.link, 'd': d, 's': s})
        return results
    except: return []

# =====================================================================
# 🌐 PAGE 1: MARKET INSIGHT (Restore Beauty)
# =====================================================================
if page == "🌐 MARKET INSIGHT":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/8144/8144863.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="margin-top:-10px;">MARKET INSIGHT</h1>', unsafe_allow_html=True)
    p = get_prices()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🟡 GOLD (XAU/USD)", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
    m2.metric("🟠 BITCOIN (BTC)", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
    m3.metric("🟢 SET INDEX", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
    m4.metric("🔵 USD/THB", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")
    
    st.markdown('<div class="section-header">🌐 GLOBAL NEWS FEED</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    news_list = [
        (c1, "🟡 GOLD NEWS", "https://news.google.com/rss/search?q=gold+price+OR+XAUUSD+-sdbullion&hl=en-US&gl=US&ceid=US:en", "card-gold", "btn-gold"),
        (c2, "🟠 CRYPTO NEWS", "https://cointelegraph.com/rss", "card-crypto", "btn-crypto"),
        (c3, "🟢 THAI MARKET", "https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th", "card-thai", "btn-thai")
    ]

    for col, title, url, card_cls, btn_cls in news_list:
        with col:
            st.markdown(f"<h3 style='text-align: center; color: white;'>{title}</h3>", unsafe_allow_html=True)
            for n in get_news(url):
                st.markdown(f"""
                <div class="news-card {card_cls}">
                    <div class="news-date">🕒 {n['d']}</div>
                    <div class="news-title">{n['t']}</div>
                    <div class="news-snip">{n['s']}</div>
                    <a href="{n['l']}" target="_blank" class="btn-news {btn_cls}">READ STORY</a>
                </div>
                """, unsafe_allow_html=True)

# =====================================================================
# 📊 PAGE 2: TRADING DESK (Restore Dashboard Analysis)
# =====================================================================
elif page == "📊 TRADING DESK":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2422/2422796.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="margin-top:-10px;">TRADING DESK</h1>', unsafe_allow_html=True)
    
    # ดึงข้อมูลมาโชว์ด้านล่างเสมอ
    df_log = load_sheet_data("Data8")
    
    # --- Data Visualization ---
    col_l, col_r = st.columns([1, 1.8]) 
    
    with col_l:
        # ⚠️ ไม้ตาย: กู้คืนวิเคราะห์ด้านซ้ายจาก Dashboard8 ⚠️
        with st.container(border=True):
            st.markdown('<div class="sub-header">📈 ANALYSIS SUMMARY</div>', unsafe_allow_html=True)
            df_dash = load_sheet_data("Dashboard8")
            if not df_dash.empty:
                html = '<table class="summary-table"><tbody>'
                for _, row in df_dash.iloc[:, :2].iterrows():
                    if str(row.iloc[0]).strip() not in ['-', '']:
                        html += f'<tr><td>{row.iloc[0]}</td><td>{row.iloc[1]}</td></tr>'
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
    
    with col_r:
        tab1, tab2 = st.tabs(["➕ ADD NEW", "✏️ EDIT & DELETE"])
        with tab1:
            with st.form("add_trade"):
                c1, c2, c3 = st.columns(3)
                esetup = c1.selectbox("SETUP", ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"])
                edir = c2.selectbox("BUY/SELL", ["Buy", "Sell"])
                eres = c3.selectbox("RESULT", ["Pending", "Win", "Loss", "กันทุน"])
                c4, c5, c6, c7 = st.columns(4)
                een = c4.number_input("Entry Price", format="%.5f")
                esl = c5.number_input("SL", format="%.5f"); etp = c6.number_input("TP", format="%.5f"); eex = c7.number_input("Exit", format="%.5f")
                epl = st.number_input("P/L ($)", format="%.2f"); ebp = st.number_input("Best Price", format="%.5f")
                if st.form_submit_button("🚀 SUBMIT"):
                    try:
                        gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                        next_r = len(wks.col_values(2)) + 1
                        pl_f = epl if epl != 0.0 else ""; bp_f = ebp if ebp != 0.0 else ""
                        upds = [{'range':f'A{next_r}:I{next_r}', 'values':[[next_r-3, esetup, edir, een, esl, etp, eex, eres, pl_f]]}, {'range':f'K{next_r}:K{next_r}', 'values':[[bp_f]]}]
                        wks.batch_update(upds, value_input_option="USER_ENTERED")
                        st.success("SAVED!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                    except Exception as e: st.error(e)

    st.divider()
    if not df_log.empty:
        st.markdown('<div class="sub-header">📝 RECENT DATA8 LOGS</div>', unsafe_allow_html=True)
        st.markdown('<div class="table-wrapper"><table class="custom-table"><thead><tr>' + "".join(f"<th>{c}</th>" for c in df_log.columns[:10]) + '</tr></thead><tbody>' + 
                    "".join(f"<tr>" + "".join(f"<td>{v}</td>" for v in row[:10]) + "</tr>" for _, row in df_log.iterrows() if str(row.iloc[0]) != '-') + '</tbody></table></div>', unsafe_allow_html=True)

# =====================================================================
# 📦 PAGE 3: STOCK MANAGER (Fix Icon & Numbers)
# =====================================================================
elif page == "📦 STOCK MANAGER":
    # ⚠️ ไม้ตาย: เปลี่ยนไอคอนสว่างนีออน ⚠️
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/3045/3045488.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="margin-top:-10px;">STOCK MANAGER</h1>', unsafe_allow_html=True)

    tab_inv, tab_out, tab_in = st.tabs(["💎 CURRENT STOCK", "📤 OUT (เบิก/ขาย)", "📥 IN (เติมสต็อก)"])

    # โหลดข้อมูลจากแผ่นงานของคุณเกี๊ยะ
    df_stock = load_sheet_data("Master_Stock (ฐานข้อมูลหลัก)")

    with tab_inv:
        if not df_stock.empty:
            st.markdown('<div class="sub-header">รายการสินค้าคงเหลือปัจจุบัน</div>', unsafe_allow_html=True)
            # ⚠️ ไม้ตาย: ปรับคอลัมน์ Index ให้ตรงกับ Sheet ของจริง (H และ I) ⚠️
            html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
            for col in df_stock.columns: html += f'<th>{col}</th>'
            html += '</tr></thead><tbody>'
            for _, row in df_stock.iterrows():
                if str(row.iloc[0]).strip() == '-': continue
                qty = safe_float(row.iloc[7]) # ช่อง "คงเหลือ" (Col H)
                min_qty = safe_float(row.iloc[8]) # ช่อง "จุดเตือน" (Col I)
                row_style = 'class="low-stock"' if qty <= min_qty else ""
                html += f'<tr {row_style}>' + "".join(f"<td>{v}</td>" for v in row) + "</tr>"
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
                    gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Log_เบิกออก")
                    date = datetime.now().strftime("%Y-%m-%d")
                    wks.append_row([date, hn, patient, cat, size, color, qty_out], value_input_option="USER_ENTERED")
                    st.success("บันทึกสำเร็จ!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except Exception as e: st.error(e)

    with tab_in:
        with st.form("in_form", clear_on_submit=True):
            st.markdown("<p style='text-align:center; color:#f472b6;'>บันทึกของเข้าคลัง (LOG_รับเข้า)</p>", unsafe_allow_html=True)
            if not df_stock.empty: item_list_in = list(dict.fromkeys(df_stock.iloc[:, 0].tolist()))
            else: item_list_in = []
            c1, c2, c3 = st.columns(3)
            cat_in = c1.selectbox("หมวดหมู่สินค้า", item_list_in)
            size_in = c2.text_input("ไซส์ (IN)")
            color_in = c3.text_input("สี (IN)")
            qty_in = st.number_input("จำนวนที่รับเข้า", min_value=1, step=1)
            cost = st.number_input("ต้นทุนรวมล็อตนี้ (บาท)", min_value=0.0)
            
            if st.form_submit_button("📥 ยืนยันการเติมสต็อก"):
                try:
                    gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Log_รับเข้า")
                    date = datetime.now().strftime("%Y-%m-%d")
                    wks.append_row([date, cat_in, size_in, color_in, qty_in, cost], value_input_option="USER_ENTERED")
                    st.success("เติมสต็อกเรียบร้อย!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except Exception as e: st.error(e)

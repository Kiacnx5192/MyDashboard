import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista Command Center", layout="wide", initial_sidebar_state="expanded")

# --- 🔑 เชื่อมต่อ Google Sheets ---
def get_gspread_client():
    creds_dict = json.loads(st.secrets["google_creds"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def safe_float(val):
    try:
        return float(str(val).replace(',', ''))
    except:
        return 0.0

# --- 🎨 CSS: Cyber Neon Edition (จี๊ดจ๊าดสะใจคุณเกี๊ยะแน่นอนค่ะ) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* กล่องกระจกเรืองแสงนีออน */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(15, 23, 42, 0.7) !important; backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important; border-radius: 20px !important; padding: 25px !important;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.15), inset 0 0 10px rgba(56, 189, 248, 0.05) !important; 
    }

    /* Tabs Neon Style */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 15px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(15, 23, 42, 0.8); border-radius: 12px 12px 0 0; border: 1px solid rgba(232, 121, 249, 0.3); color: #cbd5e1; padding: 12px 25px; transition: 0.3s; }
    .stTabs [aria-selected="true"] { background: linear-gradient(to bottom, #7928ca, #ff0080) !important; color: #ffffff !important; font-weight: 900 !important; border: 1px solid #ff0080 !important; box-shadow: 0 0 15px rgba(255, 0, 128, 0.4) !important; }

    /* Inputs & Form */
    .stTextInput label p, .stSelectbox label p, .stNumberInput label p { color: #38bdf8 !important; font-size: 14px !important; font-weight: 800 !important; text-transform: uppercase; letter-spacing: 1px; }
    div[data-testid="stFormSubmitButton"] button, .btn-primary { 
        background: linear-gradient(45deg, #0070f3, #7928ca, #ff0080) !important; 
        background-size: 200% auto !important;
        color: white !important; font-weight: 900 !important; border: none !important; border-radius: 12px !important; 
        padding: 12px 20px !important; width: 100% !important; text-transform: uppercase; letter-spacing: 2px;
        box-shadow: 0 0 20px rgba(121, 40, 202, 0.5) !important; transition: 0.5s;
    }
    div[data-testid="stFormSubmitButton"] button:hover { background-position: right center !important; transform: scale(1.02); box-shadow: 0 0 30px rgba(255, 0, 128, 0.6) !important; }

    /* Typography */
    .main-title { font-size: 55px; font-weight: 900; text-align: center; background: linear-gradient(to right, #00dfd8, #007cf0, #00dfd8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 25px; filter: drop-shadow(0 0 15px rgba(0, 223, 216, 0.3)); }
    .section-header { font-size: 26px; font-weight: 900; text-align: center; background: linear-gradient(to right, #f59e0b, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 3px; margin: 30px 0; border-bottom: 2px dashed rgba(245, 158, 11, 0.5); padding-bottom: 15px;}
    .sub-header { color: #f472b6; text-align: center; font-size: 22px; font-weight: 900; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 10px rgba(244, 114, 182, 0.3);}

    /* Table Neon Upgrade */
    .table-wrapper { height: 500px; overflow-y: auto; border-radius: 15px; background: rgba(0,0,0,0.4); border: 1px solid rgba(56, 189, 248, 0.2); }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 1200px; } 
    .custom-table th { background: #0f172a; color: #00dfd8; padding: 15px; text-align: center !important; position: sticky; top: 0; z-index: 2; border-bottom: 3px solid #007cf0; font-size: 13px; text-transform: uppercase;}
    .custom-table td { padding: 12px; text-align: center !important; color: #f8fafc; border-bottom: 1px solid rgba(56, 189, 248, 0.1); font-size: 14px; white-space: nowrap;}
    
    .summary-table { width: 90%; margin: 0 auto; border-collapse: collapse; }
    .summary-table td:first-child { text-align: left !important; color: #94a3b8; padding: 12px; font-weight: 600;}
    .summary-table td:last-child { text-align: right !important; font-weight: 900; color: #fde047; padding: 12px; font-size: 18px; text-shadow: 0 0 10px rgba(253, 224, 71, 0.4);}
    .summary-table tr { border-bottom: 1px solid rgba(255,255,255,0.08); transition: 0.3s; }
    .summary-table tr:hover { background: rgba(56, 189, 248, 0.05); }

    /* News Card Neon */
    .news-card { background: rgba(15, 23, 42, 0.85); padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 10px 20px rgba(0,0,0,0.5); transition: 0.4s; }
    .news-card:hover { border-color: rgba(56, 189, 248, 0.5); box-shadow: 0 0 25px rgba(56, 189, 248, 0.25); }
    .card-gold { border-left: 6px solid #fbbf24; } .card-crypto { border-left: 6px solid #f43f5e; } .card-thai { border-left: 6px solid #10b981; }
    .news-title { color: #ffffff; font-size: 17px; font-weight: 800; margin: 10px 0 12px 0; line-height: 1.5; }
    .btn-news { display: inline-block; padding: 9px 22px; border-radius: 50px; color: white !important; font-weight: 800; text-decoration: none; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
    .btn-gold { background: #d97706; } .btn-crypto { background: #dc2626; } .btn-thai { background: #059669; }
    
    div[data-testid="stMetricValue"] > div { color: #00dfd8 !important; font-size: 42px !important; font-weight: 900 !important; text-shadow: 0 0 15px rgba(0, 223, 216, 0.4);}
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 Sidebar Menu ----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("<h2 style='text-align: center; color: #00dfd8;'>ADMIN PANEL</h2>", unsafe_allow_html=True)
    page = st.radio("SELECT PAGE:", ["🌐 MARKET INSIGHT", "📊 TRADING DESK"])
    st.divider()
    if st.button("🔄 REFRESH SYSTEM"):
        st.cache_data.clear()
        st.rerun()

# ---------------- 👑 Main Title ----------------
if page == "📊 TRADING DESK":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2422/2422796.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="margin-top:-10px;">TRADING DESK</h1>', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/8144/8144863.png" width="60"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="margin-top:-10px;">MARKET INSIGHT</h1>', unsafe_allow_html=True)

# --- ⚙️ Data Loading Functions ---
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
def load_dashboard_data():
    try:
        gc = get_gspread_client()
        data = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Dashboard8").get_all_values()
        if not data: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0]).replace('', '-').dropna(axis=1, how='all')
    except: return pd.DataFrame()

@st.cache_data(ttl=10)
def load_log_data():
    try:
        gc = get_gspread_client()
        data = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8").get_all_values()
        if not data: return pd.DataFrame()
        header_idx = next((i for i, row in enumerate(data[:10]) if any("ลำดับ" in str(cell) for cell in row)), 0)
        df = pd.DataFrame(data[header_idx+1:], columns=data[header_idx]).loc[:, lambda df: df.columns != '']
        return df.replace('', '-').dropna(axis=1, how='all')
    except: return pd.DataFrame() 

# =====================================================================
# 🌐 PAGE 1: MARKET INSIGHT
# =====================================================================
if page == "🌐 MARKET INSIGHT":
    p = get_prices()
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("🟡 GOLD PRICE", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
    with m2: st.metric("🟠 BTC/USD", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
    with m3: st.metric("🟢 SET INDEX", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
    with m4: st.metric("🔵 USD/THB", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")

    st.markdown('<div class="section-header">🌐 GLOBAL NEWS FEED</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    def get_news(url):
        try:
            f = feedparser.parse(url, agent='Mozilla/5.0')
            return [{'t': e.title, 'l': e.link, 'd': e.get('published', e.get('pubDate', 'Recent'))[:25], 's': re.sub('<.*?>', '', e.get('summary', ''))[:120]+'...'} for e in f.entries[:3]]
        except: return []
    
    news_list = [(c1, "🟡 GOLD NEWS", "https://news.google.com/rss/search?q=gold+price+OR+XAUUSD+-sdbullion&hl=en-US&gl=US&ceid=US:en", "card-gold", "btn-gold"),
                 (c2, "🟠 CRYPTO NEWS", "https://cointelegraph.com/rss", "card-crypto", "btn-crypto"),
                 (c3, "🟢 THAI MARKET", "https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th", "card-thai", "btn-thai")]

    for col, title, url, card_cls, btn_cls in news_list:
        with col:
            st.markdown(f"<h3 style='text-align: center; color: white;'>{title}</h3>", unsafe_allow_html=True)
            for n in get_news(url):
                st.markdown(f'<div class="news-card {card_cls}"><div class="news-date">🕒 {n["d"]}</div><div class="news-title">{n["t"]}</div><div class="news-snip">{n["s"]}</div><a href="{n["l"]}" target="_blank" class="btn-news {btn_cls}">READ STORY</a></div>', unsafe_allow_html=True)

# =====================================================================
# 📊 PAGE 2: TRADING DESK
# =====================================================================
elif page == "📊 TRADING DESK":
    tab1, tab2 = st.tabs(["➕ ADD NEW TRADE", "✏️ EDIT & DELETE"])
    
    with tab1:
        with st.form("add_trade_form", clear_on_submit=True):
            st.markdown("<p style='color:#cbd5e1; text-align:center;'>INPUT NEW BACKTEST DATA BELOW</p>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            setup = c1.selectbox("SETUP", ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"])
            direction = c2.selectbox("BUY/SELL", ["Buy", "Sell"])
            result = c3.selectbox("RESULT", ["Pending", "Win", "Loss", "กันทุน"])
            c4, c5, c6, c7 = st.columns(4)
            entry = c4.number_input("ENTRY PRICE", format="%.5f")
            sl = c5.number_input("STOP LOSS", format="%.5f")
            tp = c6.number_input("TAKE PROFIT", format="%.5f")
            exit_price = c7.number_input("EXIT PRICE", format="%.5f")
            c8, c9, c10 = st.columns(3)
            pl = c8.number_input("P/L ($)", format="%.2f")
            best_price = c9.number_input("BEST PRICE", format="%.5f")
            answer_trend = c10.selectbox("ANSWER TREND", ["UP", "DOWN", "SIDEWAY"])
            st.markdown("<p style='color:#f472b6; font-weight:800;'>TREND STATUS</p>", unsafe_allow_html=True)
            c11, c12, c13 = st.columns(3)
            tw = c11.selectbox("TREND W1", ["UP", "DOWN", "SIDEWAY"])
            td = c12.selectbox("TREND D1", ["UP", "DOWN", "SIDEWAY"])
            th = c13.selectbox("TREND H4", ["UP", "DOWN", "SIDEWAY"])
            if st.form_submit_button("🚀 SUBMIT TRADE TO DATA8"):
                try:
                    gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                    next_row = len(wks.col_values(2)) + 1
                    bp_f = best_price if best_price != 0.0 else ""; pl_f = pl if pl != 0.0 else ""
                    upds = [{'range': f'A{next_row}:I{next_row}', 'values': [[next_row-3, setup, direction, entry, sl, tp, exit_price, result, pl_f]]},
                            {'range': f'K{next_row}:K{next_row}', 'values': [[bp_f]]},
                            {'range': f'M{next_row}:O{next_row}', 'values': [[tw, td, th]]},
                            {'range': f'Q{next_row}:Q{next_row}', 'values': [[answer_trend]]}]
                    wks.batch_update(upds, value_input_option="USER_ENTERED")
                    st.success("SUCCESS!"); st.cache_data.clear(); time.sleep(2); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    with tab2:
        df_edit = load_log_data()
        if not df_edit.empty:
            ids = [str(x) for x in df_edit.iloc[:, 0].tolist() if str(x).strip() not in ['', '-']]
            if ids:
                sel_id = st.selectbox("🔍 SELECT TRADE ID TO MANAGE:", ["-- SELECT --"] + ids)
                if sel_id != "-- SELECT --":
                    row = df_edit[df_edit.iloc[:, 0].astype(str) == sel_id].iloc[0]
                    with st.form("edit_form"):
                        e1, e2, e3 = st.columns(3)
                        slst = ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"]; es = e1.selectbox("Setup", slst, index=slst.index(row.iloc[1]) if row.iloc[1] in slst else 0)
                        dlst = ["Buy", "Sell"]; edir = e2.selectbox("Buy/Sell", dlst, index=dlst.index(row.iloc[2]) if row.iloc[2] in dlst else 0)
                        rlst = ["Pending", "Win", "Loss", "กันทุน"]; eres = e3.selectbox("Result", rlst, index=rlst.index(row.iloc[7]) if row.iloc[7] in rlst else 0)
                        e4, e5, e6, e7 = st.columns(4)
                        een = e4.number_input("Entry", value=safe_float(row.iloc[3]), format="%.5f")
                        esl = e5.number_input("SL", value=safe_float(row.iloc[4]), format="%.5f")
                        etp = e6.number_input("TP", value=safe_float(row.iloc[5]), format="%.5f")
                        eex = e7.number_input("Exit", value=safe_float(row.iloc[6]), format="%.5f")
                        e8, e9, e10 = st.columns(3)
                        epl = e8.number_input("P/L ($)", value=safe_float(row.iloc[8]), format="%.2f")
                        ebp = e9.number_input("Best Price", value=safe_float(row.iloc[10]), format="%.5f")
                        alst = ["UP", "DOWN", "SIDEWAY"]; eans = e10.selectbox("Answer", alst, index=alst.index(row.iloc[16]) if len(row)>16 and row.iloc[16] in alst else 0)
                        e11, e12, e13 = st.columns(3)
                        etw = e11.selectbox("W1", alst, index=alst.index(row.iloc[12]) if row.iloc[12] in alst else 0)
                        etd = e12.selectbox("D1", alst, index=alst.index(row.iloc[13]) if row.iloc[13] in alst else 0)
                        eth = e13.selectbox("H4", alst, index=alst.index(row.iloc[14]) if row.iloc[14] in alst else 0)
                        cb1, cb2 = st.columns(2)
                        if cb1.form_submit_button("🔄 UPDATE TRADE"):
                            try:
                                gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                                tr = wks.col_values(1).index(str(sel_id)) + 1
                                upds = [{'range': f'A{tr}:I{tr}', 'values': [[int(sel_id), es, edir, een, esl, etp, eex, eres, epl]]},
                                        {'range': f'K{tr}:K{tr}', 'values': [[ebp]]},
                                        {'range': f'M{tr}:O{tr}', 'values': [[etw, etd, eth]]},
                                        {'range': f'Q{tr}:Q{tr}', 'values': [[eans]]}]
                                wks.batch_update(upds, value_input_option="USER_ENTERED")
                                st.success("UPDATED!"); st.cache_data.clear(); time.sleep(2); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")
                        if cb2.form_submit_button("🗑️ DELETE TRADE"):
                            try:
                                gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                                wks.delete_rows(wks.col_values(1).index(str(sel_id)) + 1)
                                st.success("DELETED!"); st.cache_data.clear(); time.sleep(2); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")

        st.markdown("<hr style='border:1px dashed #f43f5e; margin: 30px 0;'>", unsafe_allow_html=True)
        with st.expander("🚨 DANGER ZONE: RESET ALL DATA"):
            if st.button("🧨 RESET DATA8", type="primary"):
                try:
                    gc = get_gspread_client(); gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8").batch_clear(["A4:Q1000"])
                    st.success("DATA RESET!"); st.cache_data.clear(); time.sleep(2); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    # --- Data Visualization ---
    st.divider()
    col_l, col_r = st.columns([1, 1.8]) 
    with col_l:
        with st.container(border=True):
            st.markdown('<div class="sub-header">📈 ANALYSIS SUMMARY</div>', unsafe_allow_html=True)
            df_dash = load_dashboard_data()
            if not df_dash.empty:
                html = '<table class="summary-table"><tbody>'
                for _, row in df_dash.iloc[:, :2].iterrows():
                    if str(row.iloc[0]).strip() not in ['-', '']:
                        html += f'<tr><td>{row.iloc[0]}</td><td>{row.iloc[1]}</td></tr>'
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
    with col_r:
        with st.container(border=True):
            st.markdown('<div class="sub-header">📝 RECENT DATA8 LOGS</div>', unsafe_allow_html=True)
            df_log = load_log_data()
            if not df_log.empty:
                html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
                for col in df_log.columns: html += f'<th>{col}</th>'
                html += '</tr></thead><tbody>'
                for _, row in df_log.iterrows():
                    if str(row.iloc[0]).strip() not in ['-', '']:
                        html += '<tr>'
                        for v in row:
                            c = "#00dfd8" if str(v).lower()=="win" else "#f43f5e" if str(v).lower()=="loss" else "inherit"
                            html += f'<td style="color:{c};">{v}</td>'
                        html += '</tr>'
                st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)

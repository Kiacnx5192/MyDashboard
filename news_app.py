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

# --- 🎨 CSS: Professional Cyber Theme ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(30, 41, 59, 0.6) !important; backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important; border-radius: 16px !important; padding: 20px !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.05) !important; 
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(15, 23, 42, 0.6); border-radius: 8px 8px 0 0; border: 1px solid rgba(56, 189, 248, 0.3); border-bottom: none; color: #cbd5e1; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, rgba(30,58,138,0.8) 0%, rgba(15,23,42,0.9) 100%) !important; color: #38bdf8 !important; font-weight: bold; border: 1px solid #38bdf8 !important; border-bottom: none !important; }

    /* Forms & Inputs */
    .stTextInput label p, .stSelectbox label p, .stNumberInput label p { color: #cbd5e1 !important; font-size: 13px !important; font-weight: 600 !important; }
    div[data-testid="stFormSubmitButton"] button, .btn-primary { background: linear-gradient(to right, #0ea5e9, #8b5cf6) !important; color: white !important; font-weight: 800 !important; border: none !important; border-radius: 8px !important; padding: 10px 20px !important; width: 100% !important; text-transform: uppercase; letter-spacing: 1px;}

    /* Typography */
    .main-title { font-size: 50px; font-weight: 900; text-align: center; background: linear-gradient(to right, #38bdf8, #e879f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; text-shadow: 0 0 30px rgba(232, 121, 249, 0.2);}
    .section-header { font-size: 24px; font-weight: 900; text-align: center; background: linear-gradient(to right, #f59e0b, #f43f5e); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 2px; margin: 25px 0; border-bottom: 2px dashed rgba(244, 63, 94, 0.4); padding-bottom: 10px;}
    .sub-header { color: #a78bfa; text-align: center; font-size: 20px; font-weight: 800; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;}

    /* Tables */
    .table-wrapper { height: 500px; overflow-y: auto; border-radius: 10px; background: rgba(0,0,0,0.3); }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 1200px; } 
    .custom-table th { background: #0f172a; color: #7dd3fc; padding: 12px; text-align: center !important; position: sticky; top: 0; z-index: 2; border-bottom: 2px solid #38bdf8; font-size: 12px;}
    .custom-table td { padding: 10px; text-align: center !important; color: #f8fafc; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; white-space: nowrap;}
    
    .summary-table { width: 90%; margin: 0 auto; border-collapse: collapse; }
    .summary-table td:first-child { text-align: left !important; color: #cbd5e1; padding: 10px;}
    .summary-table td:last-child { text-align: right !important; font-weight: bold; color: #fde047; padding: 10px;}
    .summary-table tr { border-bottom: 1px solid rgba(255,255,255,0.05); }

    /* 💎 NEW News Feed Design 💎 */
    .news-card { background: rgba(15, 23, 42, 0.7); padding: 20px; border-radius: 12px; margin-bottom: 18px; border-top: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 15px rgba(0,0,0,0.4); transition: transform 0.2s; }
    .news-card:hover { transform: translateY(-5px); background: rgba(30, 41, 59, 0.8); }
    .card-gold { border-left: 5px solid #f59e0b; } .card-crypto { border-left: 5px solid #ef4444; } .card-thai { border-left: 5px solid #10b981; }
    .news-title { color: #ffffff; font-size: 16px; font-weight: 700; margin: 8px 0 10px 0; line-height: 1.4;}
    .news-date { color: #94a3b8; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 5px;}
    .news-snip { color: #cbd5e1; font-size: 13.5px; line-height: 1.6; margin-bottom: 15px; opacity: 0.8;}
    .btn-news { display: inline-block; padding: 7px 18px; border-radius: 30px; color: white !important; font-weight: 700; text-decoration: none; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; transition: 0.3s; }
    .btn-gold { background: #d97706; } .btn-gold:hover { background: #f59e0b; box-shadow: 0 0 15px rgba(245, 158, 11, 0.4); }
    .btn-crypto { background: #dc2626; } .btn-crypto:hover { background: #ef4444; box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }
    .btn-thai { background: #059669; } .btn-thai:hover { background: #10b981; box-shadow: 0 0 15px rgba(16, 185, 129, 0.4); }
    
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 38px !important; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 Sidebar Menu ----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("### 👨‍💼 Carista Menu")
    page = st.radio("เลือกหน้าต่างการทำงาน:", ["🌐 Market Insight", "📊 Trading Desk"])
    st.divider()
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

# ---------------- 👑 Main Title ----------------
if page == "📊 Trading Desk":
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/2422/2422796.png" width="50"></div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="main-title" style="margin-top:-15px;">Trading Desk</h1>', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/8144/8144863.png" width="50"></div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="main-title" style="margin-top:-15px;">Market Insight</h1>', unsafe_allow_html=True)

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
# 🌐 PAGE 1: MARKET INSIGHT (สวยขึ้น อ่านง่ายขึ้น)
# =====================================================================
if page == "🌐 Market Insight":
    p = get_prices()
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("🟡 GOLD (XAU/USD)", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
    with m2: st.metric("🟠 BITCOIN (BTC)", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
    with m3: st.metric("🟢 SET INDEX", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
    with m4: st.metric("🔵 USD/THB", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")

    st.markdown('<div class="section-header">GLOBAL NEWS FEED</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
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

    news_list = [
        (c1, "🟡 GOLD NEWS", "https://news.google.com/rss/search?q=gold+price+OR+XAUUSD+-sdbullion&hl=en-US&gl=US&ceid=US:en", "card-gold", "btn-gold"),
        (c2, "🟠 CRYPTO NEWS", "https://cointelegraph.com/rss", "card-crypto", "btn-crypto"),
        (c3, "🟢 THAI MARKET", "https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th", "card-thai", "btn-thai")
    ]

    for col, title, url, card_cls, btn_cls in news_list:
        with col:
            st.markdown(f"<h3 style='text-align: center; color: white; font-size:18px; margin-bottom:20px;'>{title}</h3>", unsafe_allow_html=True)
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
# 📊 PAGE 2: TRADING DESK
# =====================================================================
elif page == "📊 Trading Desk":
    tab1, tab2 = st.tabs(["➕ เพิ่มไม้เทรดใหม่ (Add New)", "✏️ แก้ไข / ลบ ข้อมูล (Edit & Delete)"])
    
    with tab1:
        with st.form("add_trade_form", clear_on_submit=True):
            st.markdown("<p style='color:#94a3b8; font-size:14px; text-align:center;'>ระบบจะล็อกเป้าหมายให้ข้ามช่องสูตรอัตโนมัติ เพื่อรักษา Auto-Calculate ใน Sheet ค่ะ</p>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            setup = c1.selectbox("รูปแบบที่เข้า (Setup)", ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"])
            direction = c2.selectbox("Buy/Sell", ["Buy", "Sell"])
            result = c3.selectbox("ผลลัพธ์ (Result)", ["Pending", "Win", "Loss", "กันทุน"])

            c4, c5, c6, c7 = st.columns(4)
            entry = c4.number_input("ราคาเข้า (Entry)", format="%.5f")
            sl = c5.number_input("ราคาตัดขาดทุน (SL)", format="%.5f")
            tp = c6.number_input("ราคาทำกำไร (TP)", format="%.5f")
            exit_price = c7.number_input("ราคาออกจริง (Exit)", format="%.5f")

            c8, c9, c10 = st.columns(3)
            pl = c8.number_input("P/L ($) กำไร/ขาดทุน", format="%.2f")
            best_price = c9.number_input("ราคาที่วิ่งไปไกลสุด (Best Price)", format="%.5f")
            answer_trend = c10.selectbox("ทิศทางเฉลย", ["UP", "DOWN", "SIDEWAY"])

            st.markdown("<p style='color:#a78bfa; font-size:14px; margin-top:10px; border-bottom: 1px solid #4c1d95; padding-bottom: 5px;'>สถานะ Trend</p>", unsafe_allow_html=True)
            c11, c12, c13 = st.columns(3)
            trend_w1 = c11.selectbox("Trend W1", ["UP", "DOWN", "SIDEWAY"])
            trend_d1 = c12.selectbox("Trend D1", ["UP", "DOWN", "SIDEWAY"])
            trend_h4 = c13.selectbox("Trend H4", ["UP", "DOWN", "SIDEWAY"])

            if st.form_submit_button("🚀 บันทึกข้อมูลลง Data8"):
                try:
                    gc = get_gspread_client()
                    wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                    col_b = wks.col_values(2) 
                    next_row = len(col_b) + 1 
                    trade_no = next_row - 3   
                    bp_final = best_price if best_price != 0.0 else ""
                    pl_final = pl if pl != 0.0 else ""
                    updates = [
                        {'range': f'A{next_row}:I{next_row}', 'values': [[trade_no, setup, direction, entry, sl, tp, exit_price, result, pl_final]]},
                        {'range': f'K{next_row}:K{next_row}', 'values': [[bp_final]]},
                        {'range': f'M{next_row}:O{next_row}', 'values': [[trend_w1, trend_d1, trend_h4]]},
                        {'range': f'Q{next_row}:Q{next_row}', 'values': [[answer_trend]]}
                    ]
                    wks.batch_update(updates, value_input_option="USER_ENTERED")
                    st.success("บันทึกสำเร็จ!")
                    st.cache_data.clear(); time.sleep(2); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    with tab2:
        df_edit = load_log_data()
        if not df_edit.empty:
            ids = [str(x) for x in df_edit.iloc[:, 0].tolist() if str(x).strip() not in ['', '-']]
            if ids:
                sel_id = st.selectbox("🔍 ค้นหาลำดับไม้เทรดเพื่อแก้ไข:", ["-- เลือก --"] + ids)
                if sel_id != "-- เลือก --":
                    row = df_edit[df_edit.iloc[:, 0].astype(str) == sel_id].iloc[0]
                    with st.form("edit_form"):
                        e1, e2, e3 = st.columns(3)
                        s_list = ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"]
                        e_setup = e1.selectbox("Setup", s_list, index=s_list.index(row.iloc[1]) if row.iloc[1] in s_list else 0)
                        d_list = ["Buy", "Sell"]; e_dir = e2.selectbox("Buy/Sell", d_list, index=d_list.index(row.iloc[2]) if row.iloc[2] in d_list else 0)
                        r_list = ["Pending", "Win", "Loss", "กันทุน"]; e_res = e3.selectbox("Result", r_list, index=r_list.index(row.iloc[7]) if row.iloc[7] in r_list else 0)
                        e4, e5, e6, e7 = st.columns(4)
                        e_en = e4.number_input("ราคาเข้า", value=safe_float(row.iloc[3]), format="%.5f")
                        e_sl = e5.number_input("ราคาตัดขาดทุน", value=safe_float(row.iloc[4]), format="%.5f")
                        e_tp = e6.number_input("ราคาทำกำไร", value=safe_float(row.iloc[5]), format="%.5f")
                        e_ex = e7.number_input("ราคาออกจริง", value=safe_float(row.iloc[6]), format="%.5f")
                        e8, e9, e10 = st.columns(3)
                        e_pl = e8.number_input("P/L ($)", value=safe_float(row.iloc[8]), format="%.2f")
                        e_bp = e9.number_input("Best Price", value=safe_float(row.iloc[10]), format="%.5f")
                        ans_list = ["UP", "DOWN", "SIDEWAY"]; e_ans = e10.selectbox("เฉลย", ans_list, index=ans_list.index(row.iloc[16]) if len(row)>16 and row.iloc[16] in ans_list else 0)
                        e11, e12, e13 = st.columns(3)
                        e_tw = e11.selectbox("Trend W1", ans_list, index=ans_list.index(row.iloc[12]) if row.iloc[12] in ans_list else 0)
                        e_td = e12.selectbox("Trend D1", ans_list, index=ans_list.index(row.iloc[13]) if row.iloc[13] in ans_list else 0)
                        e_th = e13.selectbox("Trend H4", ans_list, index=ans_list.index(row.iloc[14]) if row.iloc[14] in ans_list else 0)
                        cb1, cb2 = st.columns(2)
                        if cb1.form_submit_button("🔄 อัปเดตข้อมูล"):
                            try:
                                gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                                t_row = wks.col_values(1).index(str(sel_id)) + 1
                                upds = [
                                    {'range': f'A{t_row}:I{t_row}', 'values': [[int(sel_id), e_setup, e_dir, e_en, e_sl, e_tp, e_ex, e_res, e_pl]]},
                                    {'range': f'K{t_row}:K{t_row}', 'values': [[e_bp]]},
                                    {'range': f'M{t_row}:O{t_row}', 'values': [[e_tw, e_td, e_th]]},
                                    {'range': f'Q{t_row}:Q{t_row}', 'values': [[e_ans]]}
                                ]
                                wks.batch_update(upds, value_input_option="USER_ENTERED")
                                st.success("อัปเดตเรียบร้อย!"); st.cache_data.clear(); time.sleep(2); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")
                        if cb2.form_submit_button("🗑️ ลบไม้เทรดนี้"):
                            try:
                                gc = get_gspread_client(); wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                                wks.delete_rows(wks.col_values(1).index(str(sel_id)) + 1)
                                st.success("ลบไม้เทรดเรียบร้อย!"); st.cache_data.clear(); time.sleep(2); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")

        st.markdown("<hr style='border:1px dashed #ef4444; margin: 30px 0;'>", unsafe_allow_html=True)
        with st.expander("🚨 โซนอันตราย: ล้างข้อมูลไม้เทรดทั้งหมด (Reset All Data)"):
            conf = st.text_input("พิมพ์ RESET เพื่อยืนยัน:")
            if st.button("🧨 ยืนยันการล้างข้อมูล", type="primary", disabled=(conf != "RESET")):
                try:
                    gc = get_gspread_client(); gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8").batch_clear(["A4:Q1000"])
                    st.success("ล้างข้อมูลเรียบร้อย!"); st.cache_data.clear(); time.sleep(2); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    # --- Data Visualization ---
    st.divider()
    col_l, col_r = st.columns([1, 1.8]) 
    with col_l:
        with st.container(border=True):
            st.markdown('<div class="sub-header">📊 วิเคราะห์การเทรด</div>', unsafe_allow_html=True)
            df_dash = load_dashboard_data()
            if not df_dash.empty:
                html = '<table class="summary-table"><tbody>'
                for _, row in df_dash.iloc[:, :2].iterrows():
                    if str(row.iloc[0]).strip() not in ['-', '']:
                        html += f'<tr><td>{row.iloc[0]}</td><td>{row.iloc[1]}</td></tr>'
                st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
    with col_r:
        with st.container(border=True):
            st.markdown('<div class="sub-header">📝 บันทึก Data8 ล่าสุด</div>', unsafe_allow_html=True)
            df_log = load_log_data()
            if not df_log.empty:
                html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
                for col in df_log.columns: html += f'<th>{col}</th>'
                html += '</tr></thead><tbody>'
                for _, row in df_log.iterrows():
                    if str(row.iloc[0]).strip() not in ['-', '']:
                        html += '<tr>'
                        for v in row:
                            c = "#4ade80" if str(v).lower()=="win" else "#f87171" if str(v).lower()=="loss" else "inherit"
                            html += f'<td style="color:{c};">{v}</td>'
                        html += '</tr>'
                st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)

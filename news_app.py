import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista Command Center", layout="wide", initial_sidebar_state="expanded")

# --- 🔑 เชื่อมต่อ Google Sheets ---
def get_gspread_client():
    creds_dict = json.loads(st.secrets["google_creds"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# --- 🎨 CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #172554 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(30, 41, 59, 0.5) !important; backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 16px !important; padding: 20px !important;
    }

    [data-testid="stExpander"] details summary { background-color: rgba(15, 23, 42, 0.8) !important; color: #38bdf8 !important; border-radius: 8px !important; border: 1px solid rgba(56, 189, 248, 0.3) !important; padding: 15px !important; }
    [data-testid="stExpander"] details summary:hover { background-color: rgba(56, 189, 248, 0.15) !important; }
    [data-testid="stExpander"] details summary p { color: #38bdf8 !important; font-size: 16px !important; font-weight: 800 !important; }
    [data-testid="stExpander"] details summary svg { fill: #38bdf8 !important; }
    
    .stTextInput label p, .stSelectbox label p, .stNumberInput label p { color: #e2e8f0 !important; font-size: 14px !important; font-weight: 600 !important; }

    div[data-testid="stFormSubmitButton"] button { background: linear-gradient(to right, #0ea5e9, #3b82f6) !important; color: white !important; font-weight: 800 !important; border: none !important; border-radius: 8px !important; padding: 10px 20px !important; width: 100% !important; }
    div[data-testid="stFormSubmitButton"] button:hover { background: linear-gradient(to right, #3b82f6, #0ea5e9) !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important; }

    .main-title { font-size: 50px; font-weight: 900; text-align: center; background: linear-gradient(to right, #ff0080, #7928ca, #0070f3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px;}
    .section-header { font-size: 24px; font-weight: 900; text-align: center; background: linear-gradient(to right, #f59e0b, #e879f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 2px; margin: 20px 0; border-bottom: 2px dashed rgba(232, 121, 249, 0.4); padding-bottom: 10px;}
    .sub-header { color: #38bdf8; text-align: center; font-size: 18px; font-weight: 800; margin-bottom: 15px; }

    .table-wrapper { height: 500px; overflow-y: auto; overflow-x: auto; border-radius: 10px; background: rgba(0,0,0,0.2); }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 1200px; /* บังคับความกว้างให้ตารางเลื่อนซ้ายขวาได้ */ } 
    .custom-table th { background: #0f172a; color: #38bdf8; padding: 12px; text-align: center !important; position: sticky; top: 0; z-index: 2; border-bottom: 2px solid #38bdf8; white-space: nowrap;}
    .custom-table td { padding: 10px; text-align: center !important; color: #e2e8f0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; white-space: nowrap;}
    
    .news-card { background: rgba(15, 23, 42, 0.6); padding: 18px; border-radius: 12px; margin-bottom: 15px; border-top: 1px solid rgba(255,255,255,0.05); }
    .card-gold { border-left: 5px solid #f59e0b; } .card-crypto { border-left: 5px solid #ef4444; } .card-thai { border-left: 5px solid #10b981; }
    .news-title { color: #ffffff; font-size: 15px; font-weight: 700; margin: 5px 0 8px 0; line-height: 1.4;}
    .news-date { color: #94a3b8; font-size: 11.5px; font-weight: 600;}
    .news-snip { color: #cbd5e1; font-size: 13px; line-height: 1.5; margin-bottom: 12px;}
    .btn { padding: 6px 16px; border-radius: 20px; color: white !important; font-weight: 700; text-decoration: none; font-size: 11px;}
    .btn-gold { background: #d97706; } .btn-crypto { background: #dc2626; } .btn-thai { background: #059669; }
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 36px !important; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 🤖 Sidebar Menu (แยกระบบเป็นหมวดหมู่) ----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("### 👨‍💼 Carista Menu")
    # สร้างเมนูนำทาง
    page = st.radio("เลือกหน้าต่างการทำงาน:", ["🌐 Market Insight", "📊 Trading Desk"])
    st.divider()
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

st.markdown(f'<h1 class="main-title">{page}</h1>', unsafe_allow_html=True)

# --- ฟังก์ชันโหลดข้อมูล ---
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
# 🌐 PAGE 1: MARKET INSIGHT (หน้าข่าวและราคา)
# =====================================================================
if page == "🌐 Market Insight":
    p = get_prices()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🟡 GOLD", f"{p[0][0]:,.2f}", f"{p[0][1]:+,.2f}")
    m2.metric("🟠 BTC", f"{p[1][0]:,.2f}", f"{p[1][1]:+,.2f}")
    m3.metric("🟢 SET", f"{p[2][0]:,.2f}", f"{p[2][1]:+,.2f}")
    m4.metric("🔵 USDTHB", f"{p[3][0]:,.3f}", f"{p[3][1]:+,.3f}", delta_color="inverse")

    st.markdown('<div class="section-header">GLOBAL NEWS FEED</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    def get_news(url):
        try:
            f = feedparser.parse(url, agent='Mozilla/5.0')
            return [{'t': e.title, 'l': e.link, 'd': e.get('published', 'Recent')[:25], 's': re.sub('<.*?>', '', e.get('summary', ''))[:100]+'...'} for e in f.entries[:3]]
        except: return []

    news_list = [
        (c1, "🟡 GOLD NEWS", "https://news.google.com/rss/search?q=gold+price+OR+XAUUSD+-sdbullion&hl=en-US&gl=US&ceid=US:en", "card-gold", "btn-gold"),
        (c2, "🟠 CRYPTO NEWS", "https://cointelegraph.com/rss", "card-crypto", "btn-crypto"),
        (c3, "🟢 THAI MARKET", "https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th", "card-thai", "btn-thai")
    ]

    for col, title, url, card_cls, btn_cls in news_list:
        with col:
            st.markdown(f"<h3 style='text-align: center; color: white; font-size:18px;'>{title}</h3>", unsafe_allow_html=True)
            for n in get_news(url):
                st.markdown(f'<div class="news-card {card_cls}"><span class="news-date">🕒 {n["d"]}</span><div class="news-title">{n["t"]}</div><div class="news-snip">{n["s"]}</div><a href="{n["l"]}" target="_blank" class="btn {btn_cls}">READ STORY</a></div>', unsafe_allow_html=True)

# =====================================================================
# 📊 PAGE 2: TRADING DESK (หน้าวิเคราะห์และบันทึก Backtest จัดเต็ม)
# =====================================================================
elif page == "📊 Trading Desk":
    
    # --- ส่วนที่ 1: ฟอร์มบันทึกข้อมูลฉบับสมบูรณ์ ---
    with st.expander("➕ ฟอร์มบันทึก Backtest (บันทึกลง Google Sheet)", expanded=True):
        with st.form("full_trade_form", clear_on_submit=True):
            st.markdown("<p style='color:#94a3b8; font-size:14px;'>กรอกข้อมูลให้ครบถ้วน ข้อมูลจะถูกส่งไปเรียงต่อท้ายในชีท Data8 อัตโนมัติ</p>", unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            setup = c1.selectbox("รูปแบบที่เข้า (Setup)", ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"])
            direction = c2.selectbox("Buy/Sell", ["Buy", "Sell"])
            result = c3.selectbox("ผลลัพธ์ (Result)", ["Pending", "Win", "Loss", "กันทุน"])
            trend_align = c4.selectbox("สถานะเทรนด์รวม", ["สอดคล้อง 3 TF (แข็งแกร่ง)", "สวนเทรนด์หลัก", "Sideway"])

            c5, c6, c7, c8 = st.columns(4)
            entry = c5.number_input("ราคาเข้า (Entry)", format="%.5f")
            sl = c6.number_input("ราคาตัดขาดทุน (SL)", format="%.5f")
            tp = c7.number_input("ราคาทำกำไร (TP)", format="%.5f")
            exit_price = c8.number_input("ราคาออกจริง (Exit)", format="%.5f")

            c9, c10, c11, c12 = st.columns(4)
            pl = c9.number_input("กำไร/ขาดทุน (P/L $)", format="%.2f")
            r_mult = c10.number_input("R-Multiple", format="%.2f")
            best_price = c11.number_input("ราคาที่วิ่งไปไกลสุด (Best Price)", format="%.5f")
            max_excursion = c12.number_input("ระยะบวกสูงสุด (Max Excursion)", format="%.0f")

            st.markdown("<p style='color:#38bdf8; font-size:14px; margin-top:10px;'>เทรนด์แต่ละ Timeframe</p>", unsafe_allow_html=True)
            c13, c14, c15, c16 = st.columns(4)
            trend_w1 = c13.selectbox("Trend W1", ["UP", "DOWN", "SIDEWAY"])
            trend_d1 = c14.selectbox("Trend D1", ["UP", "DOWN", "SIDEWAY"])
            trend_h4 = c15.selectbox("Trend H4", ["UP", "DOWN", "SIDEWAY"])
            answer_trend = c16.selectbox("ทิศทางเฉลย", ["UP", "DOWN", "SIDEWAY"])

            submit = st.form_submit_button("🚀 บันทึกข้อมูลลง Data8")
            
            if submit:
                try:
                    gc = get_gspread_client()
                    wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                    total_rows = len([r for r in wks.get_all_values() if any(str(c).strip() for c in r)])
                    # เรียงข้อมูล 17 คอลัมน์ตามรูปเป๊ะๆ
                    new_row = [total_rows, setup, direction, entry, sl, tp, exit_price, result, pl, r_mult, best_price, max_excursion, trend_w1, trend_d1, trend_h4, trend_align, answer_trend]
                    wks.append_row(new_row)
                    st.success("บันทึกสำเร็จ! ดูผลลัพธ์ในตารางด้านล่างได้เลยค่ะ")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"บันทึกไม่สำเร็จ: {e}")

    st.divider()

    # --- ส่วนที่ 2: แสดงผลตาราง ---
    col_left, col_right = st.columns([1, 2]) # ให้ฝั่งบันทึกกว้างกว่าเพราะข้อมูลเยอะ

    with col_left:
        with st.container(border=True):
            st.markdown('<div class="sub-header">📈 วิเคราะห์การเทรด</div>', unsafe_allow_html=True)
            df_dash = load_dashboard_data()
            if not df_dash.empty and len(df_dash.columns) >= 2:
                html = '<div class="table-wrapper"><table class="custom-table"><thead><tr><th>รายการวิเคราะห์</th><th>ข้อมูลสรุป</th></tr></thead><tbody>'
                for _, row in df_dash.iloc[:, :2].iterrows():
                    if str(row.iloc[0]).strip() not in ['-', '']:
                        html += f'<tr><td>{row.iloc[0]}</td><td><b style="color:#fde047;">{row.iloc[1]}</b></td></tr>'
                html += '</tbody></table></div>'
                st.markdown(html, unsafe_allow_html=True)

    with col_right:
        with st.container(border=True):
            st.markdown('<div class="sub-header">📝 บันทึก Data8 ล่าสุด</div>', unsafe_allow_html=True)
            df_data = load_log_data()
            if not df_data.empty:
                # ดึงมาโชว์ทุกคอลัมน์เลยค่ะ ตารางจะเลื่อนซ้ายขวาได้
                html = '<div class="table-wrapper"><table class="custom-table"><thead><tr>'
                for col in df_data.columns: html += f'<th>{col}</th>'
                html += '</tr></thead><tbody>'
                for _, row in df_data.iterrows():
                    if str(row.iloc[0]).strip() not in ['-', '']:
                        html += '<tr>'
                        for val in row:
                            color = "#4ade80" if str(val).strip().lower() == "win" else "#f87171" if str(val).strip().lower() == "loss" else "inherit"
                            html += f'<td style="color:{color};">{val}</td>'
                        html += '</tr>'
                html += '</tbody></table></div>'
                st.markdown(html, unsafe_allow_html=True)

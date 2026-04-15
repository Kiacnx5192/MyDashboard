import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time

st.set_page_config(page_title="Carista Command Center", layout="wide", initial_sidebar_state="expanded")

def get_gspread_client():
    creds_dict = json.loads(st.secrets["google_creds"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# ฟังก์ชันแปลงตัวเลขให้ปลอดภัย (ป้องกัน Error ดึงช่องว่างมาเป็นตัวเลข)
def safe_float(val):
    try:
        return float(str(val).replace(',', ''))
    except:
        return 0.0

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(30, 41, 59, 0.6) !important; backdrop-filter: blur(10px) !important; border: 1px solid rgba(56, 189, 248, 0.2) !important; border-radius: 16px !important; padding: 20px !important; box-shadow: 0 0 20px rgba(56, 189, 248, 0.05) !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(15, 23, 42, 0.6); border-radius: 8px 8px 0 0; border: 1px solid rgba(56, 189, 248, 0.3); border-bottom: none; color: #cbd5e1; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, rgba(30,58,138,0.8) 0%, rgba(15,23,42,0.9) 100%) !important; color: #38bdf8 !important; font-weight: bold; border: 1px solid #38bdf8 !important; border-bottom: none !important; }
    .stTextInput label p, .stSelectbox label p, .stNumberInput label p { color: #cbd5e1 !important; font-size: 13px !important; font-weight: 600 !important; }
    div[data-testid="stFormSubmitButton"] button, .btn-primary { background: linear-gradient(to right, #0ea5e9, #8b5cf6) !important; color: white !important; font-weight: 800 !important; border: none !important; border-radius: 8px !important; padding: 10px 20px !important; width: 100% !important; text-transform: uppercase; letter-spacing: 1px;}
    div[data-testid="stFormSubmitButton"] button:hover, .btn-primary:hover { box-shadow: 0 0 20px rgba(139, 92, 246, 0.6) !important; }
    .btn-danger { background: linear-gradient(to right, #ef4444, #b91c1c) !important; color: white !important; font-weight: 800 !important; border: none !important; border-radius: 8px !important; padding: 10px 20px !important; width: 100% !important; }
    .btn-danger:hover { box-shadow: 0 0 20px rgba(239, 68, 68, 0.6) !important; }
    .main-title { font-size: 50px; font-weight: 900; text-align: center; background: linear-gradient(to right, #38bdf8, #e879f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; text-shadow: 0 0 30px rgba(232, 121, 249, 0.2);}
    .section-header { font-size: 24px; font-weight: 900; text-align: center; background: linear-gradient(to right, #f59e0b, #f43f5e); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 2px; margin: 20px 0; border-bottom: 2px dashed rgba(244, 63, 94, 0.4); padding-bottom: 10px;}
    .sub-header { color: #a78bfa; text-align: center; font-size: 20px; font-weight: 800; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;}
    .table-wrapper { height: 500px; overflow-y: auto; overflow-x: auto; border-radius: 10px; background: rgba(0,0,0,0.3); }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 1200px; } 
    .custom-table th { background: #0f172a; color: #7dd3fc; padding: 12px; text-align: center !important; position: sticky; top: 0; z-index: 2; border-bottom: 2px solid #38bdf8; font-size: 12px;}
    .custom-table td { padding: 10px; text-align: center !important; color: #f8fafc; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; white-space: nowrap;}
    .summary-table { width: 85%; margin: 0 auto; border-collapse: collapse; }
    .summary-table th { background: transparent; color: #7dd3fc; padding: 12px; text-align: center; border-bottom: 1px solid #38bdf8;}
    .summary-table td:first-child { text-align: left !important; padding-left: 20px; color: #cbd5e1;}
    .summary-table td:last-child { text-align: right !important; padding-right: 20px; font-weight: bold;}
    .summary-table tr { border-bottom: 1px solid rgba(255,255,255,0.05); }
    .news-card { background: rgba(15, 23, 42, 0.8); padding: 18px; border-radius: 12px; margin-bottom: 15px; border-top: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 10px rgba(0,0,0,0.3);}
    .card-gold { border-left: 4px solid #f59e0b; } .card-crypto { border-left: 4px solid #ef4444; } .card-thai { border-left: 4px solid #10b981; }
    .news-title { color: #ffffff; font-size: 15px; font-weight: 700; margin: 5px 0 8px 0; line-height: 1.4;}
    .news-date { color: #94a3b8; font-size: 11px; font-weight: 600;}
    .news-snip { color: #cbd5e1; font-size: 13px; line-height: 1.5; margin-bottom: 12px;}
    .btn { padding: 6px 16px; border-radius: 20px; color: white !important; font-weight: 700; text-decoration: none; font-size: 11px;}
    .btn-gold { background: #d97706; } .btn-crypto { background: #dc2626; } .btn-thai { background: #059669; }
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 36px !important; font-weight: 800 !important; text-shadow: 0 2px 10px rgba(255,255,255,0.1);}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("### 👨‍💼 Carista Menu")
    page = st.radio("เลือกหน้าต่างการทำงาน:", ["🌐 Market Insight", "📊 Trading Desk"])
    st.divider()
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

st.markdown(f'<h1 class="main-title">{page}</h1>', unsafe_allow_html=True)

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

elif page == "📊 Trading Desk":
    
    # ⚠️ ระบบแยก Tabs (เพิ่มใหม่ และ แก้ไข/ลบ) ⚠️
    tab1, tab2 = st.tabs(["➕ เพิ่มไม้เทรดใหม่ (Add New)", "✏️ แก้ไข / ลบ ข้อมูล (Edit & Delete)"])
    
    with tab1:
        with st.form("add_trade_form", clear_on_submit=True):
            st.markdown("<p style='color:#94a3b8; font-size:14px; text-align:center;'>บันทึกไม้ใหม่ลงต่อท้าย Sheet ข้อมูลจะกระโดดข้ามช่องสูตรให้อัตโนมัติ</p>", unsafe_allow_html=True)
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

            submit_add = st.form_submit_button("🚀 บันทึกข้อมูลลง Data8")
            
            if submit_add:
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
                    st.success("บันทึกสำเร็จ! รออัปเดตตาราง...")
                    st.cache_data.clear()
                    time.sleep(2) 
                    st.rerun() 
                except Exception as e:
                    st.error(f"บันทึกไม่สำเร็จ: {e}")

    # ⚠️ ระบบ Edit / Delete ของแทร่! ⚠️
    with tab2:
        st.markdown("<p style='color:#f59e0b; font-size:14px; text-align:center;'>เลือกเลขลำดับไม้เทรดที่ต้องการแก้ไข หรือลบทิ้งถาวร</p>", unsafe_allow_html=True)
        df_edit = load_log_data()
        
        if not df_edit.empty:
            # ดึงรายชื่อลำดับไม้เทรดทั้งหมดมาใส่ใน Dropdown
            trade_ids = [str(x) for x in df_edit.iloc[:, 0].tolist() if str(x).strip() not in ['', '-']]
            
            if trade_ids:
                selected_id = st.selectbox("🔍 ค้นหาลำดับไม้เทรด:", ["-- เลือก --"] + trade_ids)
                
                if selected_id != "-- เลือก --":
                    # ดึงข้อมูลของไม้เทรดนั้นๆ มาจาก DataFrame
                    row_data = df_edit[df_edit.iloc[:, 0].astype(str) == selected_id].iloc[0]
                    
                    with st.form("edit_trade_form"):
                        e1, e2, e3 = st.columns(3)
                        # ใช้ try-except ในการหา index ค่าเดิม เพื่อไม่ให้ error เวลาตั้งค่า default
                        setup_options = ["แนวรับสำคัญ", "แนวต้านสำคัญ", "Breakout", "30/30/40"]
                        s_idx = setup_options.index(row_data.iloc[1]) if row_data.iloc[1] in setup_options else 0
                        e_setup = e1.selectbox("รูปแบบที่เข้า", setup_options, index=s_idx)
                        
                        dir_options = ["Buy", "Sell"]
                        d_idx = dir_options.index(row_data.iloc[2]) if row_data.iloc[2] in dir_options else 0
                        e_direction = e2.selectbox("Buy/Sell", dir_options, index=d_idx)
                        
                        res_options = ["Pending", "Win", "Loss", "กันทุน"]
                        r_idx = res_options.index(row_data.iloc[7]) if row_data.iloc[7] in res_options else 0
                        e_result = e3.selectbox("ผลลัพธ์", res_options, index=r_idx)

                        e4, e5, e6, e7 = st.columns(4)
                        e_entry = e4.number_input("ราคาเข้า", value=safe_float(row_data.iloc[3]), format="%.5f")
                        e_sl = e5.number_input("ราคาตัดขาดทุน", value=safe_float(row_data.iloc[4]), format="%.5f")
                        e_tp = e6.number_input("ราคาทำกำไร", value=safe_float(row_data.iloc[5]), format="%.5f")
                        e_exit = e7.number_input("ราคาออกจริง", value=safe_float(row_data.iloc[6]), format="%.5f")

                        e8, e9, e10 = st.columns(3)
                        e_pl = e8.number_input("P/L ($)", value=safe_float(row_data.iloc[8]), format="%.2f")
                        e_best = e9.number_input("ราคาที่วิ่งไปไกลสุด", value=safe_float(row_data.iloc[10]), format="%.5f")
                        
                        ans_options = ["UP", "DOWN", "SIDEWAY"]
                        a_idx = ans_options.index(row_data.iloc[16]) if len(row_data) > 16 and row_data.iloc[16] in ans_options else 0
                        e_ans = e10.selectbox("ทิศทางเฉลย", ans_options, index=a_idx)

                        st.markdown("<p style='color:#a78bfa; font-size:14px; margin-top:10px;'>แก้ไขสถานะ Trend</p>", unsafe_allow_html=True)
                        e11, e12, e13 = st.columns(3)
                        tw_idx = ans_options.index(row_data.iloc[12]) if row_data.iloc[12] in ans_options else 0
                        td_idx = ans_options.index(row_data.iloc[13]) if row_data.iloc[13] in ans_options else 0
                        th_idx = ans_options.index(row_data.iloc[14]) if row_data.iloc[14] in ans_options else 0
                        e_tw = e11.selectbox("Trend W1", ans_options, index=tw_idx)
                        e_td = e12.selectbox("Trend D1", ans_options, index=td_idx)
                        e_th = e13.selectbox("Trend H4", ans_options, index=th_idx)

                        col_btn1, col_btn2 = st.columns(2)
                        submit_update = col_btn1.form_submit_button("🔄 อัปเดตข้อมูล (Update)")
                        submit_delete = col_btn2.form_submit_button("🗑️ ลบไม้เทรดนี้ (Delete)", use_container_width=True)

                        # Logic อัปเดต
                        if submit_update:
                            try:
                                gc = get_gspread_client()
                                wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                                # หาว่าลำดับนี้อยู่บรรทัดไหนใน Sheet จริงๆ
                                col_a = wks.col_values(1)
                                target_row = col_a.index(str(selected_id)) + 1 
                                
                                e_bp_final = e_best if e_best != 0.0 else ""
                                e_pl_final = e_pl if e_pl != 0.0 else ""

                                updates = [
                                    {'range': f'A{target_row}:I{target_row}', 'values': [[int(selected_id), e_setup, e_direction, e_entry, e_sl, e_tp, e_exit, e_result, e_pl_final]]},
                                    {'range': f'K{target_row}:K{target_row}', 'values': [[e_bp_final]]},
                                    {'range': f'M{target_row}:O{target_row}', 'values': [[e_tw, e_td, e_th]]},
                                    {'range': f'Q{target_row}:Q{target_row}', 'values': [[e_ans]]}
                                ]
                                wks.batch_update(updates, value_input_option="USER_ENTERED")
                                st.success("อัปเดตข้อมูลสำเร็จ! รออัปเดตตาราง...")
                                st.cache_data.clear()
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"อัปเดตไม่สำเร็จ: {e}")

                        # Logic ลบ
                        if submit_delete:
                            try:
                                gc = get_gspread_client()
                                wks = gc.open_by_key("1uxDki739Juxrsu1HfYZAsmDVZETRtd-1liaw6LT8P8w").worksheet("Data8")
                                col_a = wks.col_values(1)
                                target_row = col_a.index(str(selected_id)) + 1 
                                
                                wks.delete_rows(target_row) # ลบทิ้งทั้งบรรทัด
                                st.success("ลบข้อมูลสำเร็จ! รออัปเดตตาราง...")
                                st.cache_data.clear()
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"ลบไม่สำเร็จ: {e}")
            else:
                st.info("ยังไม่มีข้อมูลไม้เทรดให้แก้ไขค่ะ")

    st.divider()
    col_left, col_right = st.columns([1, 1.8]) 

    with col_left:
        with st.container(border=True):
            st.markdown('<div class="sub-header">📊 วิเคราะห์การเทรด</div>', unsafe_allow_html=True)
            df_dash = load_dashboard_data()
            if not df_dash.empty and len(df_dash.columns) >= 2:
                html = '<table class="summary-table"><thead><tr><th>รายการวิเคราะห์</th><th>ข้อมูลสรุป</th></tr></thead><tbody>'
                for _, row in df_dash.iloc[:, :2].iterrows():
                    if str(row.iloc[0]).strip() not in ['-', '']:
                        html += f'<tr><td>{row.iloc[0]}</td><td><span style="color:#fde047;">{row.iloc[1]}</span></td></tr>'
                html += '</tbody></table>'
                st.markdown(html, unsafe_allow_html=True)

    with col_right:
        with st.container(border=True):
            st.markdown('<div class="sub-header">📝 บันทึก Data8 ล่าสุด</div>', unsafe_allow_html=True)
            df_data = load_log_data()
            if not df_data.empty:
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

import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista Command Center", layout="wide", initial_sidebar_state="collapsed")

# --- 🔑 เชื่อมต่อ Google Sheets ด้วยตู้เซฟ Secrets ---
def get_gspread_client():
    creds_dict = json.loads(st.secrets["google_creds"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# --- 🎨 CSS ระดับพรีเมียม ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #172554 100%); color: #ffffff; font-family: 'Inter', sans-serif; }
    
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(30, 41, 59, 0.5) !important; backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 16px !important; padding: 20px !important;
    }

    .main-title { font-size: 60px; font-weight: 900; text-align: center; background: linear-gradient(to right, #ff0080, #7928ca, #0070f3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .section-perf { font-size: 28px; font-weight: 900; text-align: center; background: linear-gradient(to right, #f59e0b, #e879f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 3px; margin: 40px 0 20px 0; border-bottom: 2px dashed rgba(232, 121, 249, 0.4); }
    .section-news { font-size: 28px; font-weight: 900; text-align: center; background: linear-gradient(to right, #06b6d4, #4ade80); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 3px; margin: 40px 0 20px 0; border-bottom: 2px dashed rgba(74, 222, 128, 0.4); }
    .sub-header { color: #38bdf8; text-align: center; font-size: 18px; font-weight: 800; margin-bottom: 15px; }

    /* สไตล์ตาราง */
    .table-wrapper { height: 480px; overflow-y: auto; overflow-x: auto; border-radius: 10px; background: rgba(0,0,0,0.2); }
    .custom-table { width: 100%; border-collapse: collapse; }
    .custom-table th { background: #0f172a; color: #38bdf8; padding: 12px; text-align: center !important; position: sticky; top: 0; z-index: 2; border-bottom: 2px solid #38bdf8; }
    .custom-table td { padding: 10px; text-align: center !important; color: #e2e8f0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; }
    
    /* สไตล์ข่าว */
    .news-card { background: rgba(15, 23, 42, 0.6); padding: 18px; border-radius: 12px; margin-bottom: 15px; border-top: 1px solid rgba(255,255,255,0.05); }
    .card-gold { border-left: 5px solid #f59e0b; } .card-crypto { border-left: 5px solid #ef4444; } .card-thai { border-left: 5px solid #10b981; }
    .news-title { color: #ffffff; font-size: 15px; font-weight: 700; margin: 5px 0 8px 0; line-height: 1.4;}
    .

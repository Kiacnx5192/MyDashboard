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
    st.image

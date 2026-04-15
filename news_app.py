import streamlit as st
import feedparser
import re
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Carista & Trading Intelligence", layout="wide", initial_sidebar_state="collapsed")

# --- 🎨 CSS ระดับพรีเมียม (อัปเกรดสีหัวข้อ) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    
    /* พื้นหลังน้ำเงินไล่เฉด (Midnight Blue Gradient) */
    .stApp { 
        background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #172554 100%); 
        color: #ffffff; font-family: 'Inter', sans-serif; 
    }
    
    /* กล่องกระจก (Glassmorphism) */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(30, 41, 59, 0.5) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important; 
        padding: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.3) !important;
    }

    /* หัวข้อระดับหลัก (Main Title) */
    .main-title {
        font-size: 60px; font-weight: 900; text-align: center; margin-bottom: 0px;
        background: linear-gradient(to right, #ff0080, #7928ca, #0070f3);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 4px 20px rgba(121, 40, 202, 0.3);
    }

    /* --- สีสันหัวข้อ Section ใหม่สุดปัง --- */
    .section-perf {
        font-size: 28px; font-weight: 900; text-align: center;
        background: linear-gradient(to right, #f59e0b, #e879f9); /* ทองไปชมพู */
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: 3px; margin: 40px 0 20px 0; padding-bottom: 10px;
        border-bottom: 2px dashed rgba(232, 121, 249, 0.4);
    }
    
    .section-news {
        font-size: 28px; font-weight: 900; text-align: center;
        background: linear-gradient(to right, #06b6d4, #4ade80); /* ฟ้าไปเขียวนีออน */
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: 3px; margin: 40px 0 20px 0; padding-bottom: 10px;
        border-bottom: 2px dashed rgba(74, 222, 128, 0.4);
    }

    /* หัวข้อย่อยในกล่อง */
    .sub-header { color: #38bdf8; text-align: center; font-size: 18px; font-weight: 800; margin-bottom: 15px; }

    /* --- 📊 สไตล์ตาราง (กลางเป๊ะ สูงเท่ากัน) --- */
    .table-wrapper {
        height: 480px; overflow-y: auto; overflow-x: auto;
        border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);
        background: rgba(0,0,0,0.2);
    }
    .custom-table { width: 100%; border-collapse: collapse; }
    .custom-table th {
        background: #0f172a; color: #38bdf8; padding: 12px; 
        text-align: center !important; font-weight: 800; font-size: 13px; 
        position: sticky; top: 0; z-index: 2; border-bottom: 2px solid #38bdf8;
    }
    .custom-table td {
        padding: 10px; text-align: center !important; color: #e2e8f0; 
        border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px;
    }
    .custom-table tr:hover td { background: rgba(56, 189, 248, 0.1); }

    /* --- 📰 สไตล์ข่าว --- */
    .news-card {
        background: rgba(15, 23, 42, 0.6); padding: 18px; border-radius: 12px; margin-bottom: 15px;
        border-top: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .card-gold { border-left: 5px solid #f59e0b; }
    .card-crypto { border-left: 5px solid #ef4444; }
    .card-thai { border-left: 5px solid #10b981; }

    .news-title { color: #ffffff; font-size: 15px; font-weight: 700; margin: 5px 0 8px 0; line-height: 1.4;}
    .news-date { color: #94a3b8; font-size: 11.5px; font-weight: 600;}
    .news-snip { color: #cbd5e1; font-size: 13px; line-height: 1.5; margin-bottom: 12px;}
    
    .btn { padding: 6px 16px; border-radius: 20px; color: white !important; font-weight: 700; text-decoration: none; font-size: 11px;}
    .btn-gold {

import streamlit as st
import feedparser
import re
import yfinance as yf

# 1. ตั้งค่าหน้าตาแอป (Sidebar จะพับไว้ตอนเริ่มเพื่อความคลีนนะคะ)
st.set_page_config(
    page_title="Carista & Trading Intelligence", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* พื้นหลังเข้มลึกขับสี */
    .stApp { background: #020617; color: #ffffff; }
    
    /* Sidebar สไตล์พรีเมียม */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stVerticalBlockBorderWrapper"] { 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important; 
        background: rgba(15, 23, 42, 0.9) !important;
        padding: 20px;
    }
    
    /* ตัวเลข Metric ขาวสว่าง */
    div[data-testid="stMetricValue"] > div { 
        color: #ffffff !important; 
        font-size: 42px !important; 
        font-weight: 800 !important;
    }
    
    /* กล่องข่าว: ตัวหนังสือขาวชัดเจน */
    .news-card { 
        background: #1e293b;
        padding: 22px; 
        border-radius: 18px; 
        margin-bottom: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .news-card h4 { color: #ffffff !important; font-size: 19px !important; font-weight: 700 !important; line-height: 1.4; }
    .news-snippet { color: #f1f5f9 !important; font-size: 15px !important; line-height: 1.6; }
    .news-date { color: #94a3b8; font-size: 12px; font-weight: 600; }
    
    /* หัวข้อคอลัมน์สีสันสดใส */
    .header-gold { background: linear-gradient(to right, #fde047, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 26px; font-weight: 800; text-align: center; margin-bottom: 20px;}
    .header-crypto { background: linear-gradient(to right, #fb923c, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 26px; font-weight: 800; text-align: center; margin-bottom: 20px;}
    .header-thai { background: linear-gradient(to right, #4ade80, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 26px; font-weight: 800; text-align: center; margin-bottom: 20px;}

    .card-gold { border-left: 6px solid #f59e0b; }
    .card-crypto { border-left: 6px solid #ef4444; }
    .card-thai { border-left: 6px solid #10b981; }

    .btn { padding: 8px 20px; border-radius: 30px; color: white !important; font-weight: 700; text-decoration: none; display: inline-block; margin-top: 10px; font-size: 13px; }
    .btn-gold { background: #d97706; }
    .btn-crypto { background: #dc2626; }
    .btn-thai { background: #059669; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- ส่วน Sidebar ----------------
with st.sidebar:
    st.title("👨‍💼 มายนี่ Assistant")
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.markdown("---")
    st.info("ระบบแก้ไข Bug เรียบร้อย! ลุยต่อได้เลยค่ะคุณเกี๊ยะ 🚀")
    if st.button("🔄 อัปเดตราคา & ข่าวเดี๋ยวนี้"):
        st.cache_data.clear()
        st.rerun()

# ---------------- ส่วนหัวข้อ Vibrant Header ----------------
st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="font-family: 'Inter', sans-serif; font-size: 60px; font-weight: 900; letter-spacing: -2px; margin: 0; 
            background: linear-gradient(to right, #ff0080, #7928ca, #0070f3);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Market Intelligence
        </h1>
        <p style="color: #ffffff; font-size: 16px; letter-spacing: 5px; text-transform: uppercase; font-weight: 700; margin-top: 15px;">
            Global Trading <span style="color: #ff0080;">•</span> Carista Dashboard
        </p>
    </div>
""", unsafe_allow_html=True)

# ---------------- ฟังก์ชันดึงข้อมูล ----------------
def clean_html(raw_html):
    return re.sub(re.compile('<.*?>'), '', str(raw_html))

@st.cache_data(ttl=1800)
def fetch_real_news(url, limit=4):
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:limit]:
            title = entry.get('title', 'No Title')
            link = entry.get('link', '#')
            date = entry.get('published', entry.get('pubDate', 'Recent'))
            summary = clean_html(entry.get('summary', ''))
            snippet = summary[:110] + "..." if len(summary) > 110 else summary
            results.append({'title': title, 'link': link, 'date': date[:25], 'snippet': snippet})
        return results
    except Exception:
        return []

@st.cache_data(ttl=60)
def get_live_price():
    try:
        tickers = yf.Tickers("GC=F BTC-USD THB=X ^SET.BK")
        def get_data(t):
            df = tickers.tickers[t].history(period="1d")
            return (df['Close'].iloc[-1], df['Close'].iloc[-1] - df['Open'].iloc[-1]) if not df.empty else (0.0, 0.0)
        return get_data('GC=F'), get_data('BTC-USD'), get_data('^SET.BK'), get_data('THB=X')
    except Exception:
        return ((0.0,0.0),(0.0,0.0),(0.0,0.0),(0.0,0.0))

# ---------------- การแสดงผล Metric ----------------
gold_data, btc_data, set_data, thb_data = get_live_price()

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown('<p style="color:#f59e0b; font-weight:900; margin-bottom:-10px;">🟡 XAUUSD (GOLD)</p>', unsafe_allow_html=True)
    st.metric("", f"{gold_data[0]:,.2f}", f"{gold_data[1]:+,.2f}")
with col_m2:
    st.markdown('<p style="color:#fb923c; font-weight:900; margin-bottom:-10px;">🟠 BTC/USD (CRYPTO)</p>', unsafe_allow_html=True)
    st.metric("", f"{btc_data[0]:,.2f}", f"{btc_data[1]:+,.2f}")
with col_m3:
    st.markdown('<p style="color:#4ade80; font-weight:900; margin-bottom:-10px;">🟢 SET INDEX (THAI)</p>', unsafe_allow_html=True)
    st.metric("", f"{set_data[0]:,.2f}", f"{set_data[1]:+,.2f}")
with col_m4:
    st.markdown('<p style="color:#38bdf8; font-weight:900; margin-bottom:-10px;">🔵 USDTHB (FX)</p>', unsafe_allow_html=True)
    st.metric("", f"{thb_data[0]:,.3f}", f"{thb_data[1]:+,.3f}", delta_color="inverse")

st.divider()

# ---------------- ส่วนข่าว 3 คอลัมน์ ----------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="header-gold">PRECIOUS METALS</div>', unsafe_allow_html=True)
    with st.container(border=True):
        for news in fetch_real_news("https://www.fxstreet.com/rss"):
            st.markdown(f"""<div class="news-card card-gold"><span class="news-date">🕒 {news['date']}</span><h4>{news['title']}</h4><p class="news-snippet">{news['snippet']}</p><a href="{news['link']}" target="_blank" class="btn btn-gold">READ STORY</a></div>""", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="header-crypto">DIGITAL ASSETS</div>', unsafe_allow_html=True)
    with st.container(border=True):
        for news in fetch_real_news("https://cointelegraph.com/rss"):
            st.markdown(f"""<div class="news-card card-crypto"><span class="news-date">🕒 {news['date']}</span><h4>{news['title']}</h4><p class="news-snippet">{news['snippet']}</p><a href="{news['link']}" target="_blank" class="btn btn-crypto">READ STORY</a></div>""", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="header-thai">SET & TFEX INDEX</div>', unsafe_allow_html=True)
    with st.container(border=True):
        for news in fetch_real_news("https://news.google.com/rss/search?q=SET50+OR+TFEX&hl=th&gl=TH&ceid=TH:th"):
            st.markdown(f"""<div class="news-card card-thai"><span class="news-date">🕒 {news['date']}</span><h4>{news['title']}</h4><p class="news-snippet">{news['snippet']}</p><a href="{news['link']}" target="_blank" class="btn btn-thai">READ STORY</a></div>""", unsafe_allow_html=True)
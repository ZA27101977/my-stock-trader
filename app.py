import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות וביטחון ---
PASSWORD = "eitan2026" 
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 כניסה מאובטחת - חמ''ל איתן")
        pwd = st.text_input("הכנס סיסמה:", type="password")
        if st.button("התחבר"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("סיסמה שגויה")
        return False
    return True

if check_password():
    # --- 2. אתחול AI ---
    try:
        genai.configure(api_key=API_KEY.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-AI: {e}")

    def send_telegram(message):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
        except: pass

    # --- 3. רשימות נכסים מורחבות (מעל 20 מניות ו-20 תעודות סל) ---
    POPULAR_STOCKS = [
        "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "META", "GOOGL", "NFLX", "AMD", "INTC",
        "PLTR", "BABA", "COIN", "MARA", "JPM", "BAC", "V", "MA", "DIS", "NKE", 
        "XOM", "CVX", "LLY", "UNH", "COST"
    ]
    
    POPULAR_ETFS = [
        "SPY", "QQQ", "DIA", "IWM", "VOO", "VTI", "SMH", "SOXX", "IBIT", "FBTC",
        "ARKK", "XLF", "XLK", "XLV", "XLE", "XLI", "GLD", "SLV", "TLT", "BITO",
        "EEM", "VEU", "VNQ", "SCHD", "VIG"
    ]

    # --- 4. סורק אוטומטי עם המלצות ---
    def auto_scanner(ticker_list):
        if "last_titles" not in st.session_state: st.session_state.last_titles = {}
        for t in ticker_list:
            try:
                news = yf.Ticker(t).news[:1]
                if news:
                    title = news[0].get('title', "")
                    if st.session_state.last_titles.get(t) != title:
                        time.sleep(1) # מניעת חסימת API
                        prompt = f"""נתח את החדשות למניה {t}: '{title}'. 
                        תן הסבר קצר בעברית ובסוף המלצה ברורה: 'מומלץ לקנות', 'מומלץ למכור' או 'להמתין'. 
                        אם לא קריטי, ענה 'IGNORE'."""
                        resp = model.generate_content(prompt)
                        if "IGNORE" not in resp.text.upper():
                            send_telegram(f"⚡ <b>סיגנל אוטומטי: {t}</b>\n{resp.text}")
                        st.session_state.last_titles[t] = title
            except: continue

    # --- 5. ממשק משתמש ---
    st.set_page_config(page_title="Eitan's Pro Hub", layout="wide")
    st_autorefresh(interval=60000, key="refresh_v20")

    if 'selected' not in st.session_state: st.session_state.selected = "SPY"

    with st.sidebar:
        st.title("🛠️ לוח בקרה")
        search = st.text_input("🔎 חיפוש חופשי (סימול):").upper()
        if st.button("טען נכס"): st.session_state.selected = search

        st.subheader("📈 מניות פופולריות")
        s_choice = st.selectbox("בחר מניה:", [""] + POPULAR_STOCKS)
        if s_choice: st.session_state.selected = s_choice

        st.subheader("🌍 תעודות סל (ETFs)")
        e_choice = st.selectbox("בחר תעודה:", [""] + POPULAR_ETFS)
        if e_choice: st.session_state.selected = e_choice

        st.divider()
        fav_input = st.text_area("⭐ מועדפים לסורק (הפרד בפסיק):", value="NVDA, TSLA, SPY, QQQ, IBIT")
        fav_list = [x.strip().upper() for x in fav_input.split(",")]

    # הפעלת הסורק ברקע
    auto_scanner(fav_list)

    # --- 6. תצוגה מרכזית ---
    curr = st.session_state.selected
    st.title(f"🚀 ניתוח נכס: {curr}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("📊 דאשבורד מועדפים")
        data = []
        for t in fav_list[:10]: # מציג את ה-10 הראשונים בטבלה
            try:
                inf = yf.Ticker(t).fast_info
                p, c = inf['last_price'], ((inf['last_price'] - inf['previous_close']) / inf['previous_close']) * 100
                data.append({"נכס": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%", "מגמה": "🟢" if c > 0 else "🔴"})
            except: continue
        st.table(pd.DataFrame(data))

    with col2:
        hist = yf.Ticker(curr).history(period="1d", interval="5m")
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

    if st.button(f"🤖 נתח את {curr} ושלח המלצה סופית לטלגרם"):
        with st.spinner("AI מנתח נתונים..."):
            try:
                news_text = [n.get('title', "") for n in yf.Ticker(curr).news[:5]]
                prompt = f"Analyze {curr} news: {news_text}. Give a clear 'Buy/Sell/Wait' recommendation in Hebrew."
                resp = model.generate_content(prompt)
                st.info(resp.text)
                send_telegram(f"🤖 <b>ניתוח עומק ({curr}):</b>\n{resp.text}")
            except: st.error("המכסה מלאה, נסה שוב בעוד דקה.")

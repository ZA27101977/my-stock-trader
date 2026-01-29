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

STOCKS = ["AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "META", "GOOGL", "NFLX", "AMD", "INTC", "PLTR", "BABA", "COIN", "MARA", "JPM", "BAC", "V", "MA", "DIS", "NKE", "XOM", "CVX", "LLY", "UNH", "COST"]
ETFS = ["SPY", "QQQ", "DIA", "IWM", "VOO", "VTI", "SMH", "SOXX", "IBIT", "FBTC", "ARKK", "XLF", "XLK", "XLV", "XLE", "XLI", "GLD", "SLV", "TLT", "BITO", "EEM", "VEU", "VNQ", "SCHD", "VIG"]

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 כניסה מאובטחת")
        pwd = st.text_input("הכנס סיסמה:", type="password")
        if st.button("התחבר"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("סיסמה שגויה")
        return False
    return True

if check_password():
    try:
        genai.configure(api_key=API_KEY.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
    except: st.error("שגיאה בחיבור ל-AI")

    def send_telegram(msg):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=5)
        except: pass

    st.set_page_config(page_title="Eitan Terminal Pro", layout="wide")
    st_autorefresh(interval=60000, key="v28_refresh")

    if 'selected' not in st.session_state: st.session_state.selected = "SPY"
    if 'last_scan' not in st.session_state: st.session_state.last_scan = {}

    # --- 2. סידבר (כל הפיצ'רים שחזרו) ---
    with st.sidebar:
        st.title("⚙️ שליטה מלאה")
        search = st.text_input("🔎 חיפוש מניה:").upper()
        if st.button("טען"): st.session_state.selected = search
        
        choice = st.selectbox("📌 בחירה מהירה:", [""] + sorted(STOCKS + ETFS))
        if choice: st.session_state.selected = choice
        
        st.divider()
        st.subheader("📏 תצוגת גרף")
        g_height = st.slider("גובה הגרף (פיקסלים):", 300, 1000, 550)
        
        st.divider()
        st.subheader("🔔 התראת מחיר")
        target_p = st.number_input(f"התראה ל-{st.session_state.selected} ($):", value=0.0)
        
        st.divider()
        st.subheader("⭐ סורק אוטומטי")
        fav_list = [x.strip().upper() for x in st.text_area("מועדפים (פסיקים):", value="NVDA, TSLA, SPY, QQQ").split(",")]

    # --- 3. גרף מתוקן (ללא חללים לבנים) ---
    curr = st.session_state.selected
    st.title(f"🚀 ניתוח: {curr}")

    c_p, c_i = st.columns(2)
    with c_p: p_val = st.selectbox("טווח:", ["1d", "5d", "1mo", "1y", "5y"], index=2)
    with c_i: i_val = st.selectbox("נרות:", ["5m", "15m", "60m", "1d", "1wk"], index=1)

    hist = yf.Ticker(curr).history(period=p_val, interval=i_val)
    if not hist.empty:
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        
        # --- תיקון הגרף הלבן ---
        fig.update_xaxes(rangebreaks=[
            dict(bounds=["sat", "mon"]), # הסרת סופ"ש
            dict(bounds=[16, 9.5], pattern="hour") # הסרת לילות
        ])
        fig.update_layout(template="plotly_dark", height=g_height, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    # --- 4. טבלאות מפורטות (פתיחה ושינוי %) ---
    st.divider()
    t1, t2 = st.tabs(["📊 מניות", "🌍 ETFs"])

    def get_data(tickers):
        rows = []
        for t in tickers:
            try:
                s = yf.Ticker(t)
                open_p = s.history(period="1d")['Open'].iloc[0]
                curr_p = s.fast_info['last_price']
                pct = ((curr_p - open_p) / open_p) * 100
                rows.append({"סימול": t, "מחיר": f"${curr_p:.2f}", "פתיחה": f"${open_p:.2f}", "שינוי יומי": f"{pct:+.2f}%", "מגמה": "🟢" if pct > 0 else "🔴"})
            except: continue
        return pd.DataFrame(rows)

    with t1: st.dataframe(get_data(STOCKS), use_container_width=True)
    with t2: st.dataframe(get_data(ETFS), use_container_width=True)

    # כפתור AI עם הגנה ממכסה
    if st.button("🤖 נתח ושלח לטלגרם"):
        try:
            resp = model.generate_content(f"Analyze {curr}. Hebrew Buy/Sell advice.")
            st.info(resp.text)
            send_telegram(f"🤖 <b>דוח {curr}:</b>\n{resp.text}")
        except: st.error("המכסה מלאה")

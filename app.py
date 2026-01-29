import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות בסיס ואבטחה ---
PASSWORD = "eitan2026" 
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

# רשימות הנכסים המלאות
STOCKS = ["AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "META", "GOOGL", "NFLX", "AMD", "INTC", "PLTR", "BABA", "COIN", "MARA", "JPM", "BAC", "V", "MA", "DIS", "NKE", "XOM", "CVX", "LLY", "UNH", "COST"]
ETFS = ["SPY", "QQQ", "DIA", "IWM", "VOO", "VTI", "SMH", "SOXX", "IBIT", "FBTC", "ARKK", "XLF", "XLK", "XLV", "XLE", "XLI", "GLD", "SLV", "TLT", "BITO", "EEM", "VEU", "VNQ", "SCHD", "VIG"]

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
    # --- 2. אתחול AI ופונקציות ---
    genai.configure(api_key=API_KEY.strip())
    model = genai.GenerativeModel('gemini-1.5-flash')

    def send_telegram(msg):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=5)
        except: pass

    st.set_page_config(page_title="Eitan's Super Terminal", layout="wide")
    st_autorefresh(interval=60000, key="global_v24")

    # ניהול מצבי בחירה
    if 'selected' not in st.session_state: st.session_state.selected = "SPY"
    if 'alert_triggered' not in st.session_state: st.session_state.alert_triggered = {}
    if 'last_scan' not in st.session_state: st.session_state.last_scan = {}

    # --- 3. סידבר (תפריט שליטה) ---
    with st.sidebar:
        st.title("⚙️ הגדרות מערכת")
        if st.button("Logout"): 
            st.session_state.authenticated = False
            st.rerun()
        
        st.divider()
        search = st.text_input("🔎 חיפוש מניה/קריפטו:").upper()
        if st.button("טען נכס"): st.session_state.selected = search
        
        choice = st.selectbox("📌 בחירה מרשימה:", [""] + sorted(STOCKS + ETFS))
        if choice: st.session_state.selected = choice

        st.divider()
        st.subheader("🔔 התראת מחיר לנייד")
        target_p = st.number_input(f"התראה ל-{st.session_state.selected} ב-($):", value=0.0)
        
        st.divider()
        st.subheader("⭐ סורק אוטומטי")
        fav_input = st.text_area("מועדפים לטלגרם (פסיקים):", value="NVDA, TSLA, SPY, QQQ, SMH, IBIT")
        fav_list = [x.strip().upper() for x in fav_input.split(",")]

    # --- 4. לוגיקה ברקע (התראות וסורק) ---
    def background_logic():
        # בדיקת מחיר
        if target_p > 0:
            try:
                curr_p = yf.Ticker(st.session_state.selected).fast_info['last_price']
                alert_key = f"{st.session_state.selected}_{target_p}"
                if curr_p >= target_p and alert_key not in st.session_state.alert_triggered:
                    send_telegram(f"🎯 <b>יעד מחיר הושג!</b>\n{st.session_state.selected} חצה את {target_p}$")
                    st.session_state.alert_triggered[alert_key] = True
            except: pass

        # סורק חדשות והמלצות
        for t in fav_list:
            try:
                stock = yf.Ticker(t)
                news = stock.news[:1]
                if news:
                    title = news[0].get('title', "")
                    if st.session_state.last_scan.get(t) != title:
                        time.sleep(1) # הגנה ממכסה
                        prompt = f"Analyze: '{title}' for {t}. Is it market moving? If yes, explain in Hebrew and end with 'בשורה התחתונה: מומלץ לקנות/למכור'. Else 'IGNORE'."
                        resp = model.generate_content(prompt)
                        if "IGNORE" not in resp.text.upper():
                            send_telegram(f"⚡ <b>סיגנל אוטומטי: {t}</b>\n{resp.text}")
                        st.session_state.last_scan[t] = title
            except: continue

    background_logic()

    # --- 5. תצוגה מרכזית וגרף ---
    curr = st.session_state.selected
    st.title(f"🚀 ניתוח בזמן אמת: {curr}")

    # הגדרות גרף
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: period = st.selectbox("טווח זמן:", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"], index=0)
    with c2: interval = st.selectbox("נרות:", ["1m", "5m", "15m", "30m", "60m", "1d", "1wk"], index=1)

    col_chart, col_ai = st.columns([2, 1])
    with col_chart:
        try:
            hist = yf.Ticker(curr).history(period=period, interval=interval)
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        except: st.warning("אין נתונים לגרף בטווח זה.")

    with col_ai:
        st.subheader("🤖 ניתוח AI עמוק")
        if st.button("הפק דוח והמלצה לטלגרם"):
            with st.spinner("מנתח..."):
                try:
                    s = yf.Ticker(curr)
                    news_titles = [n.get('title', "") for n in s.news[:5]]
                    prompt = f"Analyze {curr} trend and news: {news_titles}. Give a clear Buy/Sell/Wait recommendation in Hebrew."
                    resp = model.generate_content(prompt)
                    st.info(resp.text)
                    send_telegram(f"🤖 <b>דוח מפורט ({curr}):</b>\n{resp.text}")
                except: st.error("המכסה מלאה.")

    # --- 6. טבלאות ריכוז (מניות ו-ETFs) ---
    st.divider()
    t1, t2 = st.tabs(["📊 מניות פופולריות", "🌍 תעודות סל (ETFs)"])
    
    def fetch_data(tickers):
        rows = []
        for t in tickers:
            try:
                inf = yf.Ticker(t).fast_info
                p, c = inf['last_price'], ((inf['last_price'] - inf['previous_close']) / inf['previous_close']) * 100
                rows.append({"סימול": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%", "מגמה": "🟢" if c > 0 else "🔴"})
            except: continue
        return pd.DataFrame(rows)

    with t1: st.dataframe(fetch_data(STOCKS), use_container_width=True, height=400)
    with t2: st.dataframe(fetch_data(ETFS), use_container_width=True, height=400)

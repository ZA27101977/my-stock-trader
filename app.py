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

# רשימות נכסים מלאות
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
    # אתחול AI
    try:
        genai.configure(api_key=API_KEY.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
    except: st.error("שגיאה בחיבור ל-AI")

    def send_telegram(msg):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=5)
        except: pass

    st.set_page_config(page_title="Eitan Terminal Super Pro", layout="wide")
    st_autorefresh(interval=60000, key="global_v27")

    if 'selected' not in st.session_state: st.session_state.selected = "SPY"
    if 'last_scan' not in st.session_state: st.session_state.last_scan = {}
    if 'alert_triggered' not in st.session_state: st.session_state.alert_triggered = {}

    # --- 2. סידבר (שליטה ופיצ'רים) ---
    with st.sidebar:
        st.title("⚙️ הגדרות מערכת")
        search = st.text_input("🔎 חפש מניה:").upper()
        if st.button("טען"): st.session_state.selected = search
        
        choice = st.selectbox("📌 בחירה מהירה:", [""] + sorted(STOCKS + ETFS))
        if choice: st.session_state.selected = choice
        
        st.divider()
        st.subheader("📏 הגדרות תצוגה")
        graph_height = st.slider("גובה הגרף (פיקסלים):", 300, 1000, 550)
        
        st.divider()
        st.subheader("🔔 התראת מחיר")
        target_p = st.number_input(f"התראה ל-{st.session_state.selected} ($):", value=0.0)
        
        st.divider()
        st.subheader("⭐ סורק טלגרם")
        fav_input = st.text_area("מועדפים לסריקה (פסיקים):", value="NVDA, TSLA, SPY, QQQ, SMH")
        fav_list = [x.strip().upper() for x in fav_input.split(",")]

    # --- 3. לוגיקה אוטומטית (התראות וסורק) ---
    def run_auto_logic():
        # התראת מחיר
        if target_p > 0:
            try:
                curr_p = yf.Ticker(st.session_state.selected).fast_info['last_price']
                alert_id = f"{st.session_state.selected}_{target_p}"
                if curr_p >= target_p and alert_id not in st.session_state.alert_triggered:
                    send_telegram(f"🎯 <b>יעד מחיר!</b>\n{st.session_state.selected} חצה את {target_p}$")
                    st.session_state.alert_triggered[alert_id] = True
            except: pass

        # סורק חדשות
        for t in fav_list:
            try:
                stock = yf.Ticker(t)
                news = stock.news[:1]
                if news:
                    title = news[0].get('title', "")
                    if st.session_state.last_scan.get(t) != title:
                        time.sleep(1.5) # הגנה ממכסה
                        prompt = f"Analyze '{title}' for {t}. Hebrew advice: Buy/Sell/Wait."
                        resp = model.generate_content(prompt)
                        if "IGNORE" not in resp.text.upper():
                            send_telegram(f"⚡ <b>סיגנל אוטומטי: {t}</b>\n{resp.text}")
                        st.session_state.last_scan[t] = title
            except: continue

    run_auto_logic()

    # --- 4. הגרף המשופר (רציף וללא חורים) ---
    curr = st.session_state.selected
    st.title(f"🚀 ניתוח גרף בזמן אמת: {curr}")

    c1, c2 = st.columns(2)
    with c1: period = st.selectbox("טווח זמן:", ["1d", "5d", "1mo", "1y", "5y"], index=2)
    with c2: interval = st.selectbox("נרות:", ["5m", "15m", "60m", "1d", "1wk"], index=1)

    hist = yf.Ticker(curr).history(period=period, interval=interval)
    if not hist.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close']
        )])
        
        # הסרת חורים בגרף (סופ"ש ולילות)
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),
                dict(bounds=[16, 9.5], pattern="hour")
            ]
        )
        fig.update_layout(template="plotly_dark", height=graph_height, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("אין נתונים להצגה בטווח זה.")

    # --- 5. טבלאות עם עמודות פתיחה ושינוי ---
    st.divider()
    st.header("📋 נתוני שוק ושינוי יומי")
    t1, t2 = st.tabs(["📊 מניות פופולריות", "🌍 תעודות סל (ETFs)"])

    def get_market_data(tickers):
        rows = []
        for t in tickers:
            try:
                s = yf.Ticker(t)
                inf = s.fast_info
                # שער פתיחה של היום
                open_val = s.history(period="1d")['Open'].iloc[0]
                current_val = inf['last_price']
                pct = ((current_val - open_val) / open_val) * 100
                rows.append({
                    "סימול": t, "מחיר נוכחי": f"${current_val:.2f}",
                    "שער פתיחה": f"${open_val:.2f}", "שינוי יומי": f"{pct:+.2f}%",
                    "מגמה": "🟢" if pct > 0 else "🔴"
                })
            except: continue
        return pd.DataFrame(rows)

    with t1: st.dataframe(get_market_data(STOCKS), use_container_width=True)
    with t2: st.dataframe(get_market_data(ETFS), use_container_width=True)

    # כפתור AI ידני
    if st.button(f"🤖 בצע ניתוח עומק ל-{curr}"):
        try:
            prompt = f"Analyze {curr} trend based on last data. Give Hebrew Buy/Sell advice."
            resp = model.generate_content(prompt)
            st.info(resp.text)
            send_telegram(f"🤖 <b>דוח לבקשתך ({curr}):</b>\n{resp.text}")
        except: st.error("המכסה מלאה, נסה שוב בעוד דקה.")

import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות בסיס ---
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
    # אתחול AI עם הגנה משגיאות מכסה
    try:
        genai.configure(api_key=API_KEY.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
    except: st.error("שגיאה בחיבור ל-AI")

    def send_telegram(msg):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=5)
        except: pass

    st.set_page_config(page_title="Eitan Terminal v3", layout="wide")
    st_autorefresh(interval=60000, key="market_update")

    if 'selected' not in st.session_state: st.session_state.selected = "SPY"

    # --- 2. סידבר ---
    with st.sidebar:
        st.title("⚙️ הגדרות")
        search = st.text_input("🔎 חפש מניה:").upper()
        if st.button("טען"): st.session_state.selected = search
        choice = st.selectbox("📌 בחירה מהירה:", [""] + sorted(STOCKS + ETFS))
        if choice: st.session_state.selected = choice
        st.divider()
        fav_input = st.text_area("⭐ מועדפים לסריקה (פסיקים):", value="NVDA, TSLA, SPY, QQQ, SMH")
        fav_list = [x.strip().upper() for x in fav_input.split(",")]

    # --- 3. גרף משופר (בלי חורים) ---
    curr = st.session_state.selected
    st.title(f"🚀 ניתוח נכס: {curr}")

    c1, c2 = st.columns(2)
    with c1: period = st.selectbox("טווח זמן:", ["1d", "5d", "1mo", "1y", "5y"], index=0)
    with c2: interval = st.selectbox("נרות:", ["1m", "5m", "15m", "60m", "1d", "1wk"], index=1)

    hist = yf.Ticker(curr).history(period=period, interval=interval)
    if not hist.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close']
        )])
        # פתרון לגרף הלא תקין: הסרת זמנים שבהם אין מסחר
        fig.update_xaxes(rangebreaks=[
            dict(bounds=["sat", "mon"]), # הסרת סופי שבוע
            dict(bounds=[16, 9.5], pattern="hour") # הסרת שעות הלילה (לפי שעון ארה"ב)
        ])
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("לא נמצאו נתונים לגרף. נסה לשנות טווח או אינטרוול.")

    # --- 4. טבלאות עם עמודות פתיחה ושינוי (הבקשה שלך) ---
    st.divider()
    t1, t2 = st.tabs(["📊 מניות", "🌍 ETFs"])

    def get_clean_data(tickers):
        rows = []
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                # לוקחים את מחיר הפתיחה של היום
                day_data = stock.history(period="1d")
                if day_data.empty: continue
                
                open_p = day_data['Open'].iloc[0]
                curr_p = stock.fast_info['last_price']
                change_pct = ((curr_p - open_p) / open_p) * 100
                
                rows.append({
                    "סימול": t,
                    "מחיר נוכחי": f"${curr_p:.2f}",
                    "שער פתיחה": f"${open_p:.2f}",
                    "שינוי מהפתיחה": f"{change_pct:+.2f}%",
                    "מצב": "🟢" if change_pct > 0 else "🔴"
                })
            except: continue
        return pd.DataFrame(rows)

    with t1: st.dataframe(get_clean_data(STOCKS), use_container_width=True)
    with t2: st.dataframe(get_clean_data(ETFS), use_container_width=True)

    # כפתור AI עם הגנה משגיאות מכסה
    st.divider()
    if st.button("🤖 נתח ושלח לטלגרם"):
        try:
            # המתנה קטנה למניעת הצפה
            time.sleep(1)
            prompt = f"Analyze {curr}. Give a clear Buy/Sell advice in Hebrew based on current trend."
            resp = model.generate_content(prompt)
            st.info(resp.text)
            send_telegram(f"🤖 <b>דוח {curr}:</b>\n{resp.text}")
        except Exception as e:
            if "ResourceExhausted" in str(e) or "429" in str(e):
                st.error("המכסה של גוגל הסתיימה לדקה זו. המתן 60 שניות ונסה שוב.")
            else: st.error(f"שגיאה: {e}")

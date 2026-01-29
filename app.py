import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
import time
from streamlit_autorefresh import st_autorefresh

# --- הגדרות אבטחה ---
PASSWORD = "eitan2026" 
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

STOCKS = ["AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "META", "GOOGL", "NFLX", "AMD", "INTC", "PLTR", "BABA", "COIN", "MARA"]
ETFS = ["SPY", "QQQ", "DIA", "IWM", "SMH", "IBIT", "FBTC", "GLD", "SLV", "TLT"]

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
    genai.configure(api_key=API_KEY.strip())
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.set_page_config(page_title="Eitan Terminal Pro", layout="wide")
    st_autorefresh(interval=60000, key="v26_refresh")

    if 'selected' not in st.session_state: st.session_state.selected = "SPY"

    with st.sidebar:
        st.title("⚙️ שליטה")
        search = st.text_input("🔎 חפש סימול:").upper()
        if st.button("טען"): st.session_state.selected = search
        choice = st.selectbox("📌 בחירה מהירה:", [""] + sorted(STOCKS + ETFS))
        if choice: st.session_state.selected = choice
        
        st.divider()
        # שליטה בגובה הגרף (הבקשה שלך להגדלה/הקטנה)
        graph_height = st.slider("גובה הגרף (פיקסלים):", 300, 800, 500)

    # --- אזור הגרף (נפרד) ---
    curr = st.session_state.selected
    st.title(f"🚀 ניתוח גרף: {curr}")

    # בורר זמן ואינטרוול
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: period = st.selectbox("טווח זמן:", ["1d", "5d", "1mo", "1y", "5y"], index=2)
    with c2: interval = st.selectbox("נרות:", ["5m", "15m", "60m", "1d", "1wk"], index=3)

    chart_container = st.container()
    with chart_container:
        hist = yf.Ticker(curr).history(period=period, interval=interval)
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                increasing_line_color='#00ff00', decreasing_line_color='#ff0000'
            )])
            
            # --- התיקון הקריטי לגרף לא תקין ---
            # הסרת "חורי מסחר" בסופי שבוע ולילות
            fig.update_xaxes(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]), # הסרת סופ"ש
                    dict(bounds=[16, 9.5], pattern="hour"), # הסרת לילות (שעון ארה"ב)
                ]
            )
            
            fig.update_layout(
                template="plotly_dark", 
                height=graph_height, # גובה דינמי לפי הסליידר בסידבר
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("לא נמצאו נתונים לטווח זה.")

    # --- אזור AI (בין הגרף לטבלה) ---
    st.divider()
    if st.button(f"🤖 נתח את {curr} ושלח לטלגרם"):
        try:
            prompt = f"Analyze {curr} trend. Hebrew Buy/Sell advice."
            resp = model.generate_content(prompt)
            st.info(resp.text)
        except Exception as e:
            if "ResourceExhausted" in str(e):
                st.error("המכסה מלאה. המתן דקה.")

    # --- אזור הטבלאות (נפרד בתחתית) ---
    st.header("📋 נתוני שוק")
    t1, t2 = st.tabs(["📊 מניות", "🌍 ETFs"])

    def get_market_table(tickers):
        rows = []
        for t in tickers:
            try:
                s = yf.Ticker(t)
                inf = s.fast_info
                # חישוב שינוי מהפתיחה (הבקשה הקודמת שלך)
                open_p = s.history(period="1d")['Open'].iloc[0]
                curr_p = inf['last_price']
                change = ((curr_p - open_p) / open_p) * 100
                rows.append({
                    "סימול": t, "מחיר": f"${curr_p:.2f}", 
                    "פתיחה": f"${open_p:.2f}", "שינוי %": f"{change:+.2f}%"
                })
            except: continue
        return pd.DataFrame(rows)

    with t1: st.dataframe(get_market_table(STOCKS), use_container_width=True)
    with t2: st.dataframe(get_market_table(ETFS), use_container_width=True)

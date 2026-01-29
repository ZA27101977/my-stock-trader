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

# פונקציית כניסה
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 כניסה למערכת המסחר - איתן")
        pwd = st.text_input("הכנס סיסמה:", type="password")
        if st.button("התחבר"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("סיסמה שגויה")
        return False
    return True

if check_password():
    # --- 2. אתחול AI וטלגרם ---
    try:
        genai.configure(api_key=API_KEY.strip())
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if 'gemini-1.5-flash' in m), models[0])
        model = genai.GenerativeModel(model_name)
    except Exception as e:
        st.error(f"שגיאה בחיבור: {e}")

    def send_telegram(message):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
        except: pass

    # --- 3. ממשק צד (Sidebar) ---
    st.set_page_config(page_title="Eitan's Terminal", layout="wide")
    st_autorefresh(interval=60000, key="global_refresh")

    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = "SPY"
    if 'alert_triggered' not in st.session_state:
        st.session_state.alert_triggered = {}

    with st.sidebar:
        st.title("⚙️ הגדרות חמ''ל")
        if st.button("יציאה"):
            st.session_state.authenticated = False
            st.rerun()
        
        st.divider()
        # חיפוש ומעבר בין מניות
        search = st.text_input("🔎 חיפוש מניה/קריפטו:").upper()
        if st.button("טען נכס"):
            st.session_state.selected_ticker = search

        # רשימה מהירה
        popular = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "BTC-USD", "ETH-USD"]
        choice = st.selectbox("🎯 בחירה מרשימה:", [""] + popular)
        if choice: st.session_state.selected_ticker = choice

        st.divider()
        # הגדרת התראת מחיר
        st.subheader("🔔 התראת מחיר לנייד")
        target_p = st.number_input(f"שלח התראה ל-{st.session_state.selected_ticker} ב-($):", value=0.0)
        
        st.divider()
        # עריכת מועדפים לסורק
        fav_input = st.text_area("⭐ מועדפים לסורק חדשות (פסיקים):", value="NVDA, TSLA, AAPL, SPY, QQQ")
        fav_list = [x.strip().upper() for x in fav_input.split(",")]

    # --- 4. סורק חדשות והתראות מחיר (Logic) ---
    def background_scanner():
        # בדיקת מחיר יעד
        if target_p > 0:
            try:
                curr_p = yf.Ticker(st.session_state.selected_ticker).fast_info['last_price']
                if curr_p >= target_p and st.session_state.selected_ticker not in st.session_state.alert_triggered:
                    send_telegram(f"🎯 <b>יעד מחיר הושג!</b>\n{st.session_state.selected_ticker} חצה את {target_p}$ (מחיר נוכחי: {curr_p:.2f}$)")
                    st.session_state.alert_triggered[st.session_state.selected_ticker] = True
            except: pass

        # סורק חדשות אוטומטי
        if "last_titles" not in st.session_state: st.session_state.last_titles = {}
        for t in fav_list:
            try:
                news = yf.Ticker(t).news[:1]
                if news:
                    title = news[0].get('title', "")
                    if st.session_state.last_titles.get(t) != title:
                        time.sleep(1) # מניעת ResourceExhausted
                        p = f"Analyze: '{title}' for {t}. If it's market-moving news, explain in 1 Hebrew sentence. Else 'SKIP'."
                        res = model.generate_content(p)
                        if "SKIP" not in res.text.upper():
                            send_telegram(f"📢 <b>חדשות מתפרצות: {t}</b>\n{res.text}")
                        st.session_state.last_titles[t] = title
            except: continue

    background_scanner()

    # --- 5. תצוגה מרכזית ---
    curr = st.session_state.selected_ticker
    st.title(f"📈 מרכז בקרה: {curr}")

    col_dash, col_chart = st.columns([1, 2])

    with col_dash:
        st.subheader("⭐ מעקב מועדפים")
        dash_rows = []
        for t in fav_list:
            try:
                s = yf.Ticker(t).fast_info
                p, c = s['last_price'], ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
                dash_rows.append({"סימול": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%", "סטטוס": "🟢" if c > 0 else "🔴"})
            except: continue
        st.table(pd.DataFrame(dash_rows))

    with col_chart:
        hist = yf.Ticker(curr).history(period="1d", interval="5m")
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

    # --- 6. ניתוח AI ידני ---
    st.divider()
    if st.button(f"🤖 נתח את {curr} ושלח דוח לטלגרם"):
        with st.spinner("ה-AI מנתח סנטימנט..."):
            try:
                news = yf.Ticker(curr).news
                titles = [n.get('title', "") for n in news[:5]]
                prompt = f"Analyze {curr} based on {titles}. Point out risks or opportunities. Hebrew."
                response = model.generate_content(prompt)
                st.info(response.text)
                send_telegram(f"🤖 <b>דוח ניתוח לבקשתך ({curr}):</b>\n{response.text}")
            except: st.error("המכסה מלאה, נסה שוב בעוד דקה.")

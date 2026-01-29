import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות אבטחה ומפתחות ---
PASSWORD = "eytan2026"  # הסיסמה שלך לכניסה
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

# פונקציית בדיקת סיסמה
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔒 כניסה מאובטחת - חדר המסחר")
        pwd = st.text_input("הכנס סיסמה:", type="password")
        if st.button("התחבר"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("סיסמה שגויה!")
        return False
    return True

if check_password():
    # --- 2. אתחול AI ופונקציות עזר ---
    try:
        genai.configure(api_key=API_KEY.strip())
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in available_models if 'gemini-1.5-flash' in m), available_models[0])
        model = genai.GenerativeModel(model_name)
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-AI: {e}")

    def send_telegram(message):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
        except: pass

    # סורק חדשות אוטומטי (Background Scanner)
    def auto_news_scanner(ticker_list):
        if "last_news_check" not in st.session_state:
            st.session_state.last_news_check = {}
        
        for t in ticker_list:
            try:
                stock = yf.Ticker(t)
                news = stock.news[:1] # בודק רק את הידיעה הכי חדשה
                if news:
                    title = news[0].get('title', "")
                    if st.session_state.last_news_check.get(t) != title:
                        # ה-AI בודק אם החדשה "מרעישה"
                        prompt = f"Analyze this headline for {t}: '{title}'. If it can move the stock significantly, explain why in 1 Hebrew sentence. Otherwise reply 'IGNORE'."
                        response = model.generate_content(prompt)
                        if "IGNORE" not in response.text.upper():
                            send_telegram(f"📢 <b>חדשות מתפרצות: {t}</b>\n{response.text}")
                        st.session_state.last_news_check[t] = title
            except: continue

    # --- 3. ממשק משתמש וניהול בחירה ---
    st.set_page_config(page_title="חדר מסחר מאובטח - איתן", layout="wide")
    st_autorefresh(interval=60000, key="market_v12")

    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = "SPY"

    with st.sidebar:
        st.title("🛠️ תפריט")
        if st.button("התנתק (Logout)"):
            st.session_state.authenticated = False
            st.rerun()
            
        st.divider()
        search = st.text_input("🔎 חפש סימול (למשל NVDA):").upper()
        if st.button("עבור למניה"):
            st.session_state.selected_ticker = search
            
        st.divider()
        popular = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL", "MSFT", "BTC-USD"]
        choice = st.selectbox("🎯 בחירה מהירה:", [""] + popular)
        if choice:
            st.session_state.selected_ticker = choice

        st.divider()
        fav_input = st.text_area("⭐ מועדפים לסורק אוטומטי:", value="NVDA, TSLA, AAPL, SPY")
        fav_list = [x.strip().upper() for x in fav_input.split(",")]

    # הפעלת הסורק האוטומטי ברקע
    auto_news_scanner(fav_list)

    # --- 4. תצוגת נתונים ---
    st.title(f"🚀 חדר המסחר: {st.session_state.selected_ticker}")
    
    col_t, col_g = st.columns([1, 2])
    
    with col_t:
        st.subheader("📊 מעקב מהיר")
        dash_data = []
        for t in fav_list[:6]:
            try:
                s = yf.Ticker(t).fast_info
                p, c = s['last_price'], ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
                dash_data.append({"מניה": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%"})
            except: continue
        st.table(pd.DataFrame(dash_data))

    with col_g:
        current = st.session_state.selected_ticker
        hist = yf.Ticker(current).history(period="1d", interval="5m")
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    if st.button(f"🤖 ניתוח AI עמוק ל-{st.session_state.selected_ticker} (שלח לטלגרם)"):
        with st.spinner("מנתח..."):
            news = yf.Ticker(st.session_state.selected_ticker).news
            headlines = [n.get('title', "") for n in news[:5]]
            resp = model.generate_content(f"Analyze {st.session_state.selected_ticker}: {headlines}. Hebrew.")
            st.info(resp.text)
            send_telegram(f"🤖 <b>ניתוח לבקשתך ({st.session_state.selected_ticker}):</b>\n{resp.text}")

import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות אבטחה ומפתחות ---
PASSWORD = "eitan2026" 
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

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
            else:
                st.error("סיסמה שגויה")
        return False
    return True

if check_password():
    # --- 2. אתחול AI עם הגנת מכסה ---
    try:
        genai.configure(api_key=API_KEY.strip())
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in available_models if 'gemini-1.5-flash' in m), available_models[0])
        model = genai.GenerativeModel(model_name)
    except Exception as e:
        st.error(f"שגיאה בחיבור: {e}")

    def send_telegram(message):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
        except: pass

    # סורק חדשות עם השהייה למניעת שגיאת ResourceExhausted
    def auto_news_scanner(ticker_list):
        if "last_news_check" not in st.session_state:
            st.session_state.last_news_check = {}
        
        for t in ticker_list:
            try:
                stock = yf.Ticker(t)
                news = stock.news[:1]
                if news:
                    title = news[0].get('title', "")
                    if st.session_state.last_news_check.get(t) != title:
                        # השהיה קלה כדי לא לעבור את המכסה (פתרון לשגיאה שצירפת)
                        time.sleep(2) 
                        prompt = f"Analyze: '{title}' for {t}. If it's a major move, explain in 1 Hebrew sentence. Else 'IGNORE'."
                        response = model.generate_content(prompt)
                        if "IGNORE" not in response.text.upper():
                            send_telegram(f"📢 <b>חדשות מתפרצות: {t}</b>\n{response.text}")
                        st.session_state.last_news_check[t] = title
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    st.warning("המכסה של גוגל הסתיימה לדקה זו. הסורק ימשיך ברענון הבא.")
                    break
                continue

    # --- 3. ממשק משתמש וניהול בחירה ---
    st.set_page_config(page_title="Trading Hub", layout="wide")
    st_autorefresh(interval=60000, key="market_refresh")

    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = "SPY"

    with st.sidebar:
        st.title("🛠️ ניהול")
        if st.button("התנתק"):
            st.session_state.authenticated = False
            st.rerun()
        
        st.divider()
        # תיקון המעבר בין מניות - שימוש ב-on_change
        search = st.text_input("🔎 חפש מניה:", key="search_bar").upper()
        if st.button("חפש"):
            st.session_state.selected_ticker = search

        popular = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL", "BTC-USD"]
        choice = st.selectbox("🎯 בחירה מהירה:", [""] + popular)
        if choice:
            st.session_state.selected_ticker = choice

        st.divider()
        fav_input = st.text_area("⭐ מועדפים לסורק:", value="NVDA, TSLA, AAPL, SPY")
        fav_list = [x.strip().upper() for x in fav_input.split(",")]

    # הפעלת הסורק
    auto_news_scanner(fav_list)

    # --- 4. תצוגה ---
    current = st.session_state.selected_ticker
    st.title(f"🚀 ניתוח: {current}")
    
    col_t, col_g = st.columns([1, 2])
    
    with col_t:
        st.subheader("📊 מניות במעקב")
        dash_data = []
        for t in fav_list[:6]:
            try:
                s = yf.Ticker(t).fast_info
                p, c = s['last_price'], ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
                dash_data.append({"מניה": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%"})
            except: continue
        st.table(pd.DataFrame(dash_data))

    with col_g:
        hist = yf.Ticker(current).history(period="1d", interval="5m")
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    if st.button(f"🤖 ניתוח AI עמוק ל-{current}"):
        with st.spinner("מנתח..."):
            try:
                news = yf.Ticker(current).news
                headlines = [n.get('title', "") for n in news[:5]]
                resp = model.generate_content(f"Analyze {current}: {headlines}. Hebrew.")
                st.info(resp.text)
                send_telegram(f"🤖 <b>ניתוח {current}:</b>\n{resp.text}")
            except Exception as e:
                st.error("המכסה מלאה, נסה שוב בעוד דקה.")

import streamlit as st
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh

# 1. הגדרת סיסמה (שנה אותה למה שאתה רוצה)
PASSWORD = "1234" 

# 2. בדיקת אבטחה בכניסה
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 כניסה למערכת")
    user_input = st.text_input("הכנס סיסמה:", type="password")
    if st.button("כניסה"):
        if user_input == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("סיסמה שגויה!")
    st.stop() # עוצר את שאר הקוד מלהיטען

# --- מכאן והלאה הקוד הרגיל (רק למורשים) ---

st_autorefresh(interval=30000, key="secure_trader_v1")

def send_telegram(message):
    token = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
    chat_id = "1054735794"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

st.title("📈 מערכת מסחר AI - מאובטחת")
if st.button("יציאה מהמערכת"):
    st.session_state.authenticated = False
    st.rerun()

# הגדרות מניה
with st.sidebar:
    st.header("⚙️ הגדרות")
    ticker = st.text_input("סימול מניה:", value="NVDA").upper().strip()
    target_price = st.number_input("התראת מחיר ($):", value=0.0)

if ticker:
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info['last_price']
        st.metric(f"מחיר {ticker}", f"${price:.2f}")

        if target_price > 0 and price >= target_price:
            send_telegram(f"🚀 <b>התראה מאובטחת:</b> {ticker} הגיעה ל-${price:.2f}")

        data = stock.history(period="1d", interval="1m")
        if not data.empty:
            st.line_chart(data['Close'])
    except:
        st.error("שגיאה במשיכת נתונים")

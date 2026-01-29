import streamlit as st
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# הגדרות דף
st.set_page_config(page_title="Stock AI Trader", layout="wide")
st_autorefresh(interval=30000, key="fixed_v_final")

def send_telegram(message):
    # הטוקן החדש מהתמונה האחרונה שלך
    token = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
    chat_id = "1054735794"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            st.sidebar.success("✅ הודעה נשלחה לטלפון!")
        else:
            st.sidebar.error(f"❌ שגיאה: {response.json().get('description')}")
    except Exception as e:
        st.sidebar.error(f"⚠️ תקלה בחיבור: {e}")

st.title("📈 מערכת מעקב מניות")
st.info("מחובר לבוט: @eytanzafar_bot")

with st.sidebar:
    st.header("⚙️ הגדרות")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    target_price = st.number_input("התראת מחיר ($):", value=0.0)
    
    if st.button("🚀 שלח בדיקה עכשיו"):
        send_telegram("<b>החיבור הצליח!</b>\nהמערכת משתמשת בטוקן החדש.")

if ticker:
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info['last_price']
        st.metric(f"מחיר {ticker}", f"${price:.2f}")

        if target_price > 0 and price >= target_price:
            send_telegram(f"🚀 {ticker} חצתה את ${price:.2f}")

        data = stock.history(period="1d", interval="1m")
        if not data.empty:
            st.line_chart(data['Close'])
    except:
        st.error("לא ניתן למשוך נתונים")

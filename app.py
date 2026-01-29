import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# 1. הגדרות דף וריענון (כל 30 שניות)
st.set_page_config(page_title="AI Trader Israel", layout="wide")
st_autorefresh(interval=30000, key="final_v_fix")

# 2. פונקציית טלגרם עם הטוקן החדש מהצילום שלך
def send_telegram(message):
    # הטוקן המעודכן מהתמונה שלך
    token = "8583393995:AAEhmun0shSH2QSa-U_MvVf7SvIo0tws0Q"
    chat_id = "1054735794" 
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ הודעה נשלחה בהצלחה!")
        else:
            error_msg = response.json().get('description', 'Unknown')
            st.sidebar.error(f"❌ טלגרם מסרב: {error_msg}")
    except Exception as e:
        st.sidebar.error(f"⚠️ תקלה בחיבור: {e}")

# 3. שעון ישראל
israel_now = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
current_time = israel_now.strftime('%H:%M:%S')

st.title("📈 מערכת מעקב מניות חכמה")
st.write(f"🕒 שעון ישראל: **{current_time}**")

# 4. סרגל צד
with st.sidebar:
    st.header("⚙️ הגדרות")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    target_price = st.number_input("שלח התראה כשהמחיר מעל ($):", value=0.0, step=0.01)
    
    if st.button("שלח הודעת בדיקה עכשיו"):
        send_telegram(f"🔔 בדיקה מוצלחת! המערכת מחוברת ב-{current_time}")

# 5. הצגת נתונים (מתוקן ללא שגיאות Syntax)
if ticker:
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info['last_price']
        
        st.metric(f"מחיר נוכחי {ticker}", f"${price:.2f}")

        # שליחת התראה אוטומטית אם המחיר עובר את היעד
        if target_price > 0 and price >= target_price:
            send_telegram(f"🚀 יעד הושג! {ticker} הגיעה ל-${price:.2f}")
            st.toast("התראה נשלחה לטלגרם!")

        # גרף
        data = stock.history(period="1d", interval="1m")
        if not data.empty:
            st.line_chart(data['Close'])
            
    except Exception as e:
        st.error(f"לא ניתן למשוך נתונים עבור {ticker}")

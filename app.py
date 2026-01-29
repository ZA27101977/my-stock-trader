import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# 1. הגדרות דף וריענון אוטומטי (30 שניות)
st.set_page_config(page_title="AI Live Trader Israel", layout="wide")
st_autorefresh(interval=30 * 1000, key="final_live_fix")

# 2. פונקציית טלגרם מעודכנת - שליחה בפורמט POST לביצועים אמינים
def send_telegram(message):
    token = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY"
    chat_id = 1054735794  # ה-ID המדויק שלך כפי שחילצנו
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, data=payload, timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ הודעה נשלחה לטלגרם")
        else:
            st.sidebar.error(f"❌ שגיאת טלגרם: {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"⚠️ שגיאת חיבור: {e}")

# 3. חישוב זמן ישראל (UTC+2 או UTC+3 בהתאם לעונה)
# כרגע מוגדר UTC+2. אם חסרה שעה, שנה ל-hours=3
israel_time = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
current_time_str = israel_time.strftime('%H:%M:%S')

st.title("🚀 מערכת מסחר AI - מחוברת לטלגרם")
st.write(f"🕒 זמן עדכון אחרון (ישראל): **{current_time_str}**")

# 4. סרגל צד (Sidebar)
with st.sidebar:
    st.header("⚙️ הגדרות מניה")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    st.subheader("🔔 הגדר התראה לנייד")
    target_up = st.number_input("שלח הודעה כשהמחיר עולה מעל ($):", value=0.0)
    target_down = st.number_input("שלח הודעה כשהמחיר יורד מתחת ($):", value=0.0)
    st.caption("ההתראה תישלח אוטומטית כשהמחיר יחצה את היעד.")

# 5. משיכת נתונים וניתוח (ללא Cache למחיר חי)
if ticker:
    try:
        stock = yf.Ticker(ticker)

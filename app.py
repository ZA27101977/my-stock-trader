import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# 1. הגדרות דף וריענון (כל 30 שניות)
st.set_page_config(page_title="AI Trader Israel", layout="wide")
st_autorefresh(interval=30000, key="final_v_fix_authorized")

# 2. פונקציית טלגרם עם הטוקן המעודכן ביותר
def send_telegram(message):
    # הטוקן המדויק מהתמונה האחרונה שלך
    token = "8583393995:AAEhmun0shSH2QSa-U_MvVf7SvIo0tws0Q"
    chat_id = "1054735794" 
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ ההודעה הגיעה לטלגרם!")
        else:
            # כאן נראה אם השגיאה השתנתה מ-Unauthorized למשהו אחר
            st.sidebar.error(f"❌ שגיאה מטלגרם: {response.json().get('description')}")
    except Exception as e:
        st.sidebar.error(f"⚠️ תקלה טכנית: {e}")

# 3. תצוגת זמן ושם הבוט
israel_now = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
st.title("📈 מערכת מסחר AI")
st.info("וודא שלחצת START בתוך הבוט @eytanzafar_bot בטלגרם")

# 4. סרגל צד
with st.sidebar:
    st.header("⚙️ הגדרות")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    target_price = st.number_input("התראת מחיר מעל ($):", value=0.0, step=0.01)
    
    if st.button("בדיקת חיבור עכשיו"):
        send_telegram(f"🚀 המערכת מחוברת בהצלחה לבוט החדש שלך!")

# 5. הצגת נתונים וגרפים
if ticker:
    try:
        stock = yf.Ticker(ticker)
        # תיקון משיכת המחיר
        price = stock.fast_info['last_price']
        
        col1, col2 = st.columns(2)
        col1.metric(f"מחיר {ticker}", f"${price:.2f}")
        
        # בדיקת התראה אוטומטית
        if target_price > 0 and price >= target_price:
            send_telegram(f"📢 {ticker} חצתה את מחיר היעד: ${price:.2f}")
            st.toast("התראה נשלחה!")

        # גרף דקות
        data = stock.history(period="1d", interval="1m")
        if not data.empty:
            st.line_chart(data['Close'])
            
    except Exception as e:
        st.error(f"שגיאה בהצגת נתונים. וודא שהסימול {ticker} תקין.")

import streamlit as st
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# הגדרות דף וריענון (כל 30 שניות)
st.set_page_config(page_title="Stock AI Trader", layout="wide")
st_autorefresh(interval=30000, key="final_token_fix")

def send_telegram(message):
    # הטוקן המדויק ששלחת עכשיו - כולל ה-H הגדולה
    token = "8583393995:AAEhmuHn0shSH2QSa-U_MvVf7SvIo0tws0Q"
    chat_id = "1054735794"
    
    # שליחה בפורמט JSON - הכי אמין
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ הודעה נשלחה בהצלחה!")
        else:
            # כאן נראה אם השגיאה עדיין קיימת
            st.sidebar.error(f"❌ שגיאה: {response.json().get('description')}")
    except Exception as e:
        st.sidebar.error(f"⚠️ תקלה בחיבור: {e}")

# זמן ישראל
israel_now = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
st.title("🚀 מערכת מסחר AI - מחוברת לטלגרם")
st.write(f"🕒 זמן ישראל: **{israel_now.strftime('%H:%M:%S')}**")

# סרגל צד
with st.sidebar:
    st.header("⚙️ הגדרות")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    target_price = st.number_input("התראת מחיר ($):", value=0.0, step=0.01)
    
    if st.button("בדיקת חיבור עכשיו"):
        send_telegram(f"🔔 המערכת מחוברת! הטוקן המעודכן עובד.")

# תצוגת מניה
if ticker:
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info['last_price']
        st.metric(f"מחיר {ticker}", f"${price:.2f}")

        # שליחת התראה אוטומטית
        if target_price > 0 and price >= target_price:
            send_telegram(f"🚀 {ticker} הגיעה למחיר היעד: ${price:.2f}")
            st.toast("התראה נשלחה!")

        # גרף פשוט
        data = stock.history(period="1d", interval="1m")
        if not data.empty:
            st.line_chart(data['Close'])
            
    except Exception as e:
        st.error(f"לא ניתן למשוך נתונים עבור {ticker}")

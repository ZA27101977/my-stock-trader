import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# 1. הגדרות דף וריענון אוטומטי (30 שניות)
st.set_page_config(page_title="AI Live Trader Israel", layout="wide")
st_autorefresh(interval=30 * 1000, key="final_telegram_fix_v5")

# 2. פונקציית טלגרם יציבה
def send_telegram(message):
    token = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY"
    chat_id = 1054735794 
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            st.sidebar.success(f"✅ הודעה נשלחה ב-{datetime.datetime.now().strftime('%H:%M:%S')}")
            return True
        else:
            error_desc = response.json().get('description', 'Unknown Error')
            st.sidebar.error(f"❌ שגיאת טלגרם: {error_desc}")
            return False
    except Exception as e:
        st.sidebar.error(f"⚠️ שגיאת חיבור: {e}")
        return False

# 3. שעון ישראל (UTC+2)
israel_now = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
current_time = israel_now.strftime('%H:%M:%S')

st.title("🚀 מערכת מסחר AI - בדיקת טלגרם סופית")
st.write(f"🕒 זמן עדכון אחרון (ישראל): **{current_time}**")

# 4. סרגל צד (Sidebar)
with st.sidebar:
    st.header("⚙️ הגדרות מניה")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    st.subheader("🔔 הגדר התראה לנייד")
    target_up = st.number_input("שלח הודעה כשהמחיר עולה מעל ($):", value=0.0, step=0.01)
    
    st.write("---")
    if st.button("שלח הודעת בדיקה עכשיו"):
        send_telegram("👋 הבדיקה הצליחה! המערכת מחוברת לטלפון שלך.")

# 5. משיכת נתונים וניתוח
if ticker:
    try:
        stock = yf.Ticker(ticker)
        live_info = stock.fast_info
        price = live_info['last_price']
        prev_close = live_info['previous_close']
        change_pct = ((price / prev_close) - 1) * 100

        col_p, col_c = st.columns(2)
        col_p.metric(f"מחיר {ticker}", f"${price:.2f}")
        col_change = col_c.metric("שינוי יומי", f"{change_pct:.2f}%")

        # בדיקת התראה ושליחה
        if target_up > 0 and price >= target_up:
            send_telegram(f"<b>🚀 יעד הושג!</b>\n{ticker} במחיר: ${price:.2f}")
            st.toast("התראה נשלחה!")

        # גרף דקות
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            st.line_chart(hist['Close'], height=250)

    except Exception as e:
        st.error(f"שגיאה במשיכת נתונים עבור {ticker}")

st.caption(f"Status: Live | Last Sync: {current_time}")

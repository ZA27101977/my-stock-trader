import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# 1. הגדרות דף וריענון אוטומטי (30 שניות)
st.set_page_config(page_title="AI Live Trader Israel", layout="wide")
st_autorefresh(interval=30 * 1000, key="final_fix_v3")

# 2. פונקציית טלגרם - שימוש ב-POST עם ID תקין
def send_telegram(message):
    token = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY"
    chat_id = 1054735794 
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, data=payload, timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ התראה נשלחה לטלגרם")
    except:
        pass

# 3. תיקון שעון ישראל (UTC+2)
# בשרתי Streamlit השעה היא UTC, נוסיף 2 שעות לירושלים
israel_now = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
current_time = israel_now.strftime('%H:%M:%S')

st.title("🚀 מערכת מסחר AI בזמן אמת")
st.write(f"🕒 זמן עדכון אחרון (ישראל): **{current_time}**")

# 4. סרגל צד
with st.sidebar:
    st.header("⚙️ הגדרות")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    st.subheader("🔔 הגדר התראה לנייד")
    target_up = st.number_input("שלח הודעה כשהמחיר עולה מעל ($):", value=0.0)
    target_down = st.number_input("שלח הודעה כשהמחיר יורד מתחת ($):", value=0.0)

# 5. משיכת נתונים וניתוח
if ticker:
    try:
        stock = yf.Ticker(ticker)
        
        # מחיר חי ללא Cache (כדי שיתעדכן באמת)
        live_info = stock.fast_info
        price = live_info['last_price']
        prev_close = live_info['previous_close']
        change_pct = ((price / prev_close) - 1) * 100

        # תצוגה
        col1, col2 = st.columns(2)
        col1.metric(f"מחיר נוכחי {ticker}", f"${price:.2f}")
        col2.metric("שינוי יומי", f"{change_pct:.2f}%")

        # בדיקת התראות
        if target_up > 0 and price >= target_up:
            send_telegram(f"<b>🚀 יעד הושג!</b>\n{ticker} במחיר: ${price:.2f}")
            st.toast("התראה נשלחה לטלגרם!")
        
        if target_down > 0 and price <= target_down:
            send_telegram(f"<b>📉 הגנה!</b>\n{ticker} במחיר: ${price:.2f}")
            st.toast("התראה נשלחה לטלגרם!")

        # גרף דקות
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            st.line_chart(hist['Close'], height=250)

        # 6. ניתוח והמלצה
        st.divider()
        st.subheader("🤖 ניתוח חכם")
        
        c1, c2 = st.columns(2)
        with c1:
            news = stock.news
            sent = sum([TextBlob(n.get('title', '')).sentiment.polarity for n in news[:5]]) / 5 if news else 0
            st.write("**סנטימנט:** " + ("חיובי 🔥" if sent > 0.05 else "שלילי 📉" if sent < -0.05 else "נייטרלי 😐"))
            
        with c2:
            fin = stock.financials
            growth = not fin.empty and 'Total Revenue' in fin.index and fin.loc['Total Revenue'].iloc[0] > fin.loc['Total Revenue'].iloc[1]
            st.write("**צמיחה בדוחות:** " + ("כן ✅" if growth else "לא ❌"))

    except Exception as e:
        st.error(f"שגיאה במשיכת נתונים עבור {ticker}. וודא שהסימול נכון.")

st.caption(f"Status: Live | Last Update: {current_time}")

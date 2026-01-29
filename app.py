import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# 1. הגדרות דף וריענון אוטומטי כל 30 שניות
st.set_page_config(page_title="AI Live Trader Israel", layout="wide")
st_autorefresh(interval=30 * 1000, key="live_update")

# 2. פונקציית טלגרם - וודא שה-ID נכון
def send_telegram(message):
    token = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY"
    chat_id = "תכניס_כאן_מספר_בלבד" # למשל "1054735794"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    try:
        response = requests.get(url, timeout=5)
        # זה יעזור לנו לראות אם הטלגרם מחזיר שגיאה
        if response.status_code != 200:
            st.error(f"שגיאת טלגרם: {response.text}")
    except Exception as e:
        st.error(f"שגיאת חיבור: {e}")

# 3. חישוב זמן ישראל (UTC+2)
israel_time = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
current_time_str = israel_time.strftime('%H:%M:%S')

st.title("🚀 מערכת מסחר AI בזמן אמת")
st.write(f"🕒 שעון ישראל: **{current_time_str}** (מתרענן כל 30 שניות)")

# 4. סרגל צד (Sidebar)
with st.sidebar:
    st.header("🔍 הגדרות חיפוש")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    st.header("🔔 התראות לטלפון")
    target_price = st.number_input("שלח הודעה כשהמחיר עולה מעל ($):", value=0.0)
    target_low = st.number_input("שלח הודעה כשהמחיר יורד מתחת ($):", value=0.0)

# 5. משיכת נתונים וניתוח
if ticker:
    try:
        stock = yf.Ticker(ticker)
        
        # מחיר חי (Last Price)
        live_data = stock.fast_info
        price = live_data['last_price']
        prev_close = live_data['previous_close']
        change_pct = ((price / prev_close) - 1) * 100

        # הצגת המחיר בגדול
        col_price, col_change = st.columns(2)
        col_price.metric(f"מחיר נוכחי {ticker}", f"${price:.2f}")
        col_change.metric("שינוי יומי", f"{change_pct:.2f}%", delta_color="normal")

        # לוגיקת התראות לטלגרם
        if target_price > 0 and price >= target_price:
            send_telegram(f"🚀 מטרה הושגה! {ticker} חצתה את ${target_price} ומחירה כעת ${price:.2f}")
            st.toast("הודעה נשלחה לטלגרם!")
        
        if target_low > 0 and price <= target_low:
            send_telegram(f"📉 הגנה! {ticker} ירדה מתחת ל-${target_low} ומחירה כעת ${price:.2f}")
            st.toast("הודעה נשלחה לטלגרם!")

        # גרף דקות אחרונות
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            st.line_chart(hist['Close'], height=250)

        # 6. ניתוח המלצה (שילוב דוחות וחדשות)
        st.divider()
        st.subheader("🤖 ניתוח חכם של הבינה המלאכותית")
        
        c1, c2 = st.columns(2)
        
        # ניתוח סנטימנט חדשות
        with c1:
            st.write("**📰 מה אומרות החדשות?**")
            news = stock.news
            if news:
                sent_score = sum([TextBlob(n.get('title', '')).sentiment.polarity for n in news[:5]]) / 5
                if sent_score > 0.05: st.success("חדשות חיוביות 🔥")
                elif sent_score < -0.05: st.error("חדשות שליליות 📉")
                else: st.info("חדשות נייטרליות 😐")
            else:
                st.write("אין חדשות אחרונות.")

        # ניתוח דוחות (צמיחה)
        with c2:
            st.write("**📊 מה אומרים הדוחות?**")
            fin = stock.financials
            if not fin.empty and 'Total Revenue' in fin.index:
                growth = fin.loc['Total Revenue'].iloc[0] > fin.loc['Total Revenue'].iloc[1]
                if growth: st.success("צמיחה בהכנסות ✅")
                else: st.warning("אין צמיחה בהכנסות ⚠️")
            else:
                st.write("מידע פיננסי לא זמין.")

    except Exception as e:
        st.error(f"שגיאה: {ticker} לא נמצא או שיש בעיה בחיבור.")

st.caption(f"Status: Live | Last Sync: {current_time_str}")

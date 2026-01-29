import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# 1. הגדרות דף וריענון אוטומטי (30 שניות)
st.set_page_config(page_title="AI Live Trader", layout="wide")
st_autorefresh(interval=30 * 1000, key="live_update_final")

# 2. פונקציית טלגרם עם הנתונים המעודכנים שלך
def send_telegram(message):
    token = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY"
    chat_id = "1054735794" # ה-ID שחילצנו מההודעה שלך
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    try:
        requests.get(url, timeout=5)
    except:
        pass

# 3. חישוב זמן ישראל (UTC+2)
israel_time = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
current_time_str = israel_time.strftime('%H:%M:%S')

st.title("🚀 מערכת מסחר AI - מחוברת לטלגרם")
st.write(f"🕒 זמן עדכון אחרון: **{current_time_str}**")

# 4. סרגל צד
with st.sidebar:
    st.header("⚙️ הגדרות")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    st.subheader("🔔 הגדר התראה לנייד")
    target_up = st.number_input("התראת עלייה ($):", value=0.0)
    target_down = st.number_input("התראת ירידה ($):", value=0.0)

# 5. משיכת מחיר חי וניתוח
if ticker:
    try:
        stock = yf.Ticker(ticker)
        # מחיר נוכחי
        live_price = stock.fast_info['last_price']
        prev_close = stock.fast_info['previous_close']
        change = ((live_price / prev_close) - 1) * 100

        # תצוגה
        st.metric(f"מחיר {ticker}", f"${live_price:.2f}", f"{change:.2f}%")

        # בדיקת התראות - זה ישלח הודעה לטלגרם שלך!
        if target_up > 0 and live_price >= target_up:
            send_telegram(f"🔥 המטרה הושגה! {ticker} חצתה את ${target_up}. מחיר נוכחי: ${live_price:.2f}")
            st.toast("הודעה נשלחה לטלגרם!")
        
        if target_down > 0 and live_price <= target_down:
            send_telegram(f"📉 התראת הגנה! {ticker} ירדה מתחת ל-${target_down}. מחיר נוכחי: ${live_price:.2f}")
            st.toast("הודעה נשלחה לטלגרם!")

        # גרף דקות
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            st.line_chart(hist['Close'])

        # ניתוח המלצה
        st.divider()
        news = stock.news
        sent = sum([TextBlob(n.get('title', '')).sentiment.polarity for n in news[:5]]) / 5 if news else 0
        
        fin = stock.financials
        growth = not fin.empty and 'Total Revenue' in fin.index and fin.loc['Total Revenue'].iloc[0] > fin.loc['Total Revenue'].iloc[1]

        if sent > 0.05 and growth:
            st.success("🤖 המלצת AI: קנייה (BUY) 🟢")
        elif sent < -0.05:
            st.error("🤖 המלצת AI: הימנעות (AVOID) 🔴")
        else:
            st.warning("🤖 המלצת AI: המתנה (HOLD) 🟡")

    except Exception as e:
        st.error(f"לא הצלחנו למצוא נתונים עבור {ticker}")

st.caption(f"Status: Live | Israel Time: {current_time_str}")

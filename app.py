import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# ריענון אוטומטי כל 30 שניות
st.set_page_config(page_title="AI Live Trader", layout="wide")
st_autorefresh(interval=30 * 1000, key="price_update")

def send_telegram(message):
    token = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY"
    chat_id = "כאן_שים_את_ה-ID_שלך" # וודא שהכנסת את ה-ID שקיבלת מהבוט
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    try: requests.get(url, timeout=5)
    except: pass

st.title("🚀 מעקב מניות בזמן אמת")

# תפריט צד
ticker = st.sidebar.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
target_price = st.sidebar.number_input("התראת מחיר לטלגרם ($):", value=0.0)

if ticker:
    # משיכת מחיר "חי" ללא Cache
    stock = yf.Ticker(ticker)
    
    try:
        # קבלת המחיר העדכני ביותר מרשת Yahoo
        live_price = stock.fast_info['last_price']
        prev_close = stock.fast_info['previous_close']
        change = ((live_price / prev_close) - 1) * 100

        # תצוגה גדולה של המחיר
        st.metric(f"מחיר נוכחי {ticker}", f"${live_price:.2f}", f"{change:.2f}%")
        st.write(f"⏱️ עדכון אחרון: {datetime.datetime.now().strftime('%H:%M:%S')}")

        # בדיקת התראה
        if target_price > 0 and live_price >= target_price:
            send_telegram(f"🔔 מטרה הושגה! {ticker} במחיר: ${live_price:.2f}")
            st.toast("הודעה נשלחה לטלגרם!")

        # גרף דקות אחרונות (ללא Cache)
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            st.line_chart(hist['Close'])

        # ניתוח המלצה (דוחות וחדשות)
        st.divider()
        st.subheader("🤖 ניתוח חכם (שורה תחתונה)")
        
        news = stock.news
        sent = sum([TextBlob(n.get('title', '')).sentiment.polarity for n in news[:5]]) / 5 if news else 0
        
        fin = stock.financials
        growth = False
        if not fin.empty and 'Total Revenue' in fin.index:
            growth = fin.loc['Total Revenue'].iloc[0] > fin.loc['Total Revenue'].iloc[1]

        if sent > 0.05 and growth:
            st.success("המלצה סופית: BUY 🟢")
        elif sent < -0.05:
            st.error("המלצה סופית: AVOID 🔴")
        else:
            st.warning("המלצה סופית: HOLD 🟡")

    except Exception as e:
        st.error(f"שגיאה במשיכת נתונים: {e}")

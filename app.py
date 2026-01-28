import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import requests
import time

# הגדרות עמוד וריענון אוטומטי כל 30 שניות
st.set_page_config(page_title="Real-Time AI Trader", layout="wide")

# פונקציה לשליחת הודעה לטלגרם
def send_telegram_msg(message):
    token = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY-API Token מ-BotFather
    chat_id = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY-Chat ID שלך
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    try:
        requests.get(url)
    except:
        pass

st.title("🚀 מסחר חכם בזמן אמת (ריענון כל 30 שניות)")

# ריענון אוטומטי בעזרת רכיב Streamlit
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=30 * 1000, key="datarefresh")

# סרגל צד
ticker = st.sidebar.text_input("הכנס סימול (למשל NVDA):", value="NVDA").upper().strip()
alert_up = st.sidebar.number_input("התראת עלייה (מחיר יעד):", value=0.0)
alert_down = st.sidebar.number_input("התראת ירידה (מחיר הגנה):", value=0.0)

def get_live_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        # מחיר בזמן אמת
        data = stock.history(period="1d", interval="1m")
        current_price = data['Close'].iloc[-1]
        prev_close = stock.info.get('previousClose', current_price)
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        # דוחות וחדשות
        news = stock.news
        fin = stock.financials
        
        return current_price, change_pct, news, fin, data
    except:
        return None, None, None, None, None

if ticker:
    price, change, news, fin, hist_data = get_live_data(ticker)
    
    if price:
        # תצוגת מחיר גדולה
        color = "normal" if change == 0 else "inverse" if change < 0 else "normal"
        st.metric(f"מחיר נוכחי {ticker}", f"${price:.2f}", f"{change:.2f}%")

        # בדיקת התראות ושליחה לטלגרם
        if alert_up > 0 and price >= alert_up:
            send_telegram_msg(f"🚀 התראת מכירה! {ticker} הגיעה למחיר יעד: ${price:.2f}")
            st.toast("התראה נשלחה לטלגרם!")
        
        if alert_down > 0 and price <= alert_down:
            send_telegram_msg(f"⚠️ התראת הגנה! {ticker} ירדה למחיר: ${price:.2f}")
            st.toast("התראה נשלחה לטלגרם!")

        # --- לוגיקת המלצה (דוחות + חדשות) ---
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📰 ניתוח חדשות (AI)")
            if news:
                sent_scores = [TextBlob(n.get('title', '')).sentiment.polarity for n in news[:5]]
                avg_sent = sum(sent_scores) / len(sent_scores)
                st.write(f"סנטימנט נוכחי: {'חיובי 🔥' if avg_sent > 0.05 else 'שלילי 📉' if avg_sent < -0.05 else 'נייטרלי 😐'}")
            
        with col2:
            st.subheader("📊 ניתוח דוחות")
            if not fin.empty and 'Total Revenue' in fin.index:
                revs = fin.loc['Total Revenue']
                growth = (revs.iloc[0] / revs.iloc[1]) - 1
                st.write(f"צמיחה שנתית: {growth*100:.1f}% " + ("✅" if growth > 0 else "❌"))

        # גרף דקות אחרונות
        st.line_chart(hist_data['Close'])
        
    else:
        st.error("לא ניתן למשוך נתונים. וודא שהסימול נכון.")

st.caption(f"עודכן לאחרונה: {time.strftime('%H:%M:%S')}")

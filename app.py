import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import requests
from streamlit_autorefresh import st_autorefresh

# ריענון אוטומטי כל 30 שניות
st.set_page_config(page_title="AI Trading Bot", layout="wide")
st_autorefresh(interval=30 * 1000, key="refresh")

# פונקציית טלגרם - כאן תכניס את ה-ID שלך
def send_telegram(message):
    token = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY" # הטוקן מהתמונה שלך
    chat_id = "כאן_שים_את_ה-ID_שלך" # חובה להכניס את ה-ID שקיבלת מ-GetIDBot
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    try: requests.get(url, timeout=5)
    except: pass

st.title("📈 מערכת מסחר בזמן אמת + התראות")

# תפריט צד
ticker = st.sidebar.text_input("הכנס סימול (למשל NVDA):", value="NVDA").upper().strip()
target_price = st.sidebar.number_input("התראת מחיר ($):", value=0.0)

if ticker:
    # משיכת נתונים
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d", interval="1m")
    
    if not data.empty:
        # טיפול בכותרות כפולות אם יש
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        curr_price = float(data['Close'].iloc[-1])
        st.metric(f"מחיר נוכחי {ticker}", f"${curr_price:.2f}")

        # בדיקת התראה
        if target_price > 0 and curr_price >= target_price:
            send_telegram(f"🔔 התראה! {ticker} הגיעה למחיר היעד: ${curr_price:.2f}")
            st.toast("התראה נשלחה לטלגרם!")

        # המלצה מבוססת דוחות וחדשות
        st.divider()
        st.subheader("🤖 ניתוח והמלצה")
        
        # סנטימנט חדשות
        news = stock.news
        sent = sum([TextBlob(n.get('title', '')).sentiment.polarity for n in news[:5]]) / 5 if news else 0
        
        # צמיחה מדוחות
        fin = stock.financials
        growth = "חיובית ✅" if not fin.empty and 'Total Revenue' in fin.index and fin.loc['Total Revenue'].iloc[0] > fin.loc['Total Revenue'].iloc[1] else "לא נמצאה ❌"
        
        # הצגת המלצה
        if sent > 0.05 and "חיובית" in growth:
            st.success("המלצה: BUY 🟢 (חדשות ודוחות טובים)")
        elif sent < -0.05:
            st.error("המלצה: AVOID 🔴 (חדשות שליליות)")
        else:
            st.warning("המלצה: HOLD 🟡 (נתונים מעורבים)")

        # גרף דקות
        st.line_chart(data['Close'])
    else:
        st.error("לא נמצאו נתונים. וודא שהסימול נכון.")

st.caption(f"עודכן לאחרונה: {pd.Timestamp.now().strftime('%H:%M:%S')}")

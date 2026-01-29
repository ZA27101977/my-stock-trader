import streamlit as st
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
import pandas as pd

# 1. הגדרות אבטחה
PASSWORD = "1234" 

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 כניסה למערכת")
    user_input = st.text_input("הכנס סיסמה:", type="password")
    if st.button("כניסה"):
        if user_input == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("סיסמה שגויה!")
    st.stop()

# 2. פונקציית טלגרם (הטוקן וה-ID שלך)
def send_telegram(message):
    token = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
    chat_id = "1054735794"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# 3. הגדרות ריענון (כל 30 שניות)
st_autorefresh(interval=30000, key="watchlist_v1")

st.title("📊 חדר מסחר AI - רשימת מעקב")

# 4. ניהול רשימת המניות (Watchlist)
with st.sidebar:
    st.header("📋 ניהול רשימה")
    # רשימת ברירת מחדל
    tickers_input = st.text_area("הכנס סימולים (מופרדים בפסיק):", value="NVDA, TSLA, AAPL, MSFT")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]
    
    st.divider()
    target_pct = st.number_input("שלח התראה על שינוי יומי מעל (%):", value=2.0)
    
    if st.button("יציאה"):
        st.session_state.authenticated = False
        st.rerun()

# 5. משיכת נתונים והצגה בטבלה
st.subheader("נתוני שוק חיים")
watchlist_data = []

for ticker in ticker_list:
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        price = info['last_price']
        change = ((price - info['previous_close']) / info['previous_close']) * 100
        
        watchlist_data.append({
            "סימול": ticker,
            "מחיר ($)": round(price, 2),
            "שינוי יומי (%)": f"{change:+.2f}%",
            "שווי שוק": f"{info['market_cap']/1e9:.1f}B"
        })
        
        # בדיקת התראה אוטומטית על שינוי חריג
        if abs(change) >= target_pct:
            send_telegram(f"⚡ <b>תנועה חריגה ב-{ticker}:</b>\nהמחיר: ${price:.2f}\nשינוי: {change:+.2f}%")
            
    except:
        continue

if watchlist_data:
    df = pd.DataFrame(watchlist_data)
    st.table(df) # הצגת טבלה נקייה

    # גרף השוואתי למניה הראשונה ברשימה
    st.subheader(f"גרף דקות: {ticker_list[0]}")
    data = yf.Ticker(ticker_list[0]).history(period="1d", interval="1m")
    st.line_chart(data['Close'])

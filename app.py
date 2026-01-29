import streamlit as st
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
import pandas as pd

# אבטחה
PASSWORD = "1234" 
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 כניסה")
    user_input = st.text_input("סיסמה:", type="password")
    if st.button("כניסה"):
        if user_input == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

def send_telegram(message):
    token = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
    chat_id = "1054735794"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

st_autorefresh(interval=60000, key="smart_bot_v2") # ריענון כל דקה (פחות עומס)

st.title("📊 חדר מסחר - שליטה בהתראות")

with st.sidebar:
    st.header("⚙️ הגדרות")
    # הוספת SPY כברירת מחדל עבור ה-S&P 500
    tickers_input = st.text_area("רשימת מניות (הפרד בפסיק):", value="SPY, NVDA, TSLA, AAPL")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]
    
    st.divider()
    # הגדלנו ל-5% כדי לקבל פחות הודעות
    threshold = st.slider("שלח התראה רק בשינוי של מעל (%):", 1.0, 10.0, 5.0)
    
    if st.button("יציאה"):
        st.session_state.authenticated = False
        st.rerun()

# תצוגת נתונים
watchlist_data = []
for ticker in ticker_list:
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info['last_price']
        prev_close = stock.fast_info['previous_close']
        change = ((price - prev_close) / prev_close) * 100
        
        name = "S&P 500 (ETF)" if ticker == "SPY" else ticker
        watchlist_data.append({"מניה": name, "מחיר": f"${price:.2f}", "שינוי יומי": f"{change:+.2f}%"})
        
        # שליחת הודעה רק אם השינוי באמת חריג
        if abs(change) >= threshold:
            # הוספנו מנגנון שמוודא שלא נשלח את אותה הודעה כל דקה
            if f"alert_{ticker}_{round(change)}" not in st.session_state:
                send_telegram(f"⚠️ <b>תנועה חריגה!</b>\n{name} זזה ב-{change:+.2f}% ומחירה ${price:.2f}")
                st.session_state[f"alert_{ticker}_{round(change)}"] = True
    except:
        continue

st.table(pd.DataFrame(watchlist_data))

# גרף של ה-S&P 500
st.subheader("מבט על השוק (S&P 500)")
spy_chart = yf.Ticker("SPY").history(period="1d", interval="5m")
st.line_chart(spy_chart['Close'])

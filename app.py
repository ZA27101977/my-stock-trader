import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות מפתחות ובוטים ---
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

try:
    genai.configure(api_key=API_KEY.strip())
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = next((m for m in available_models if 'gemini-1.5-flash' in m), available_models[0])
    model = genai.GenerativeModel(model_name)
except Exception as e:
    st.error(f"שגיאה בחיבור ל-AI: {e}")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
    except: pass

# --- 2. ממשק המשתמש ---
st.set_page_config(page_title="חדר מסחר עם התראות - איתן", layout="wide")
st.title("🚀 חדר המסחר החכם של איתן")

# רענון אוטומטי (כל 60 שניות) כדי לבדוק התראות
st_autorefresh(interval=60000, key="market_v8")

with st.sidebar:
    st.header("🔍 חיפוש והתראות")
    search_ticker = st.text_input("חפש מניה/תעודה (למשל: NVDA, SPY):", "").upper()
    
    st.divider()
    st.subheader("🔔 הגדר התראת מחיר")
    alert_price = st.number_input("התראת מחיר ($):", value=0.0)
    if st.button("הפעל מעקב התראה"):
        st.success(f"מעקב הופעל ל-{search_ticker or 'SPY'} במחיר {alert_price}")

# --- 3. טבלת מניות חיה עם התראות צבעוניות ---
st.subheader("📊 נתוני שוק בזמן אמת")
dashboard_tickers = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL", "BTC-USD"]
dash_data = []

for t in dashboard_tickers:
    try:
        s = yf.Ticker(t).fast_info
        price = s['last_price']
        change = ((price - s['previous_close']) / s['previous_close']) * 100
        
        # לוגיקת התראות ויזואליות
        status = "⚪ יציב"
        if change > 2.0: status = "🟢 זינוק!"
        elif change < -2.0: status = "🔴 נפילה!"
        
        dash_data.append({
            "מניה": t,
            "מחיר": f"${price:.2f}",
            "שינוי יומי": f"{change:+.2f}%",
            "סטטוס": status
        })
        
        # בדיקת התראת מחיר לטלגרם (אם הוגדרה)
        if search_ticker == t and alert_price > 0:
            if (change > 0 and price >= alert_price) or (change < 0 and price <= alert_price):
                send_telegram(f"🚨 <b>התראת מחיר!</b>\nהמניה {t} הגיעה למחיר {price:.2f}$")
                
    except: continue

if dash_data:
    df = pd.DataFrame(dash_data)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- 4. ניתוח AI וגרף ---
selected_ticker = search_ticker if search_ticker else "SPY"
st.divider()
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"🤖 ניתוח AI: {selected_ticker}")
    if st.button(f"נתח ושלח לטלגרם"):
        with st.spinner("מנתח..."):
            try:
                news = yf.Ticker(selected_ticker).news
                headlines = [n.get('title') or n.get('content', {}).get('title', "אין כותרת") for n in news[:5]]
                prompt = f"Analyze {selected_ticker} news: {headlines}. Hebrew summary."
                response = model.generate_content(prompt)
                
                st.info(response.text)
                send_telegram(f"🤖 <b>ניתוח AI ל-{selected_ticker}:</b>\n{response.text}")
                st.success("הניתוח נשלח לטלגרם שלך!")
            except Exception as e:
                st.error(f"הניתוח נכשל: {e}")

with col2:
    st.subheader(f"📈 גרף תנועה: {selected_ticker}")
    hist = yf.Ticker(selected_ticker).history(period="1d", interval="5m")
    if not hist.empty:
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

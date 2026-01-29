import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות מפתחות (המפתחות החדשים שלך) ---
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

# אתחול AI חכם (מונע 404)
try:
    genai.configure(api_key=API_KEY.strip())
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = next((m for m in available_models if 'gemini-1.5-flash' in m), available_models[0])
    model = genai.GenerativeModel(model_name)
except Exception as e:
    st.error(f"שגיאה בחיבור ל-AI: {e}")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
    except: pass

# --- 2. ממשק המשתמש ---
st.set_page_config(page_title="חדר מסחר זורם - איתן", layout="wide")
st.title("🚀 חדר המסחר החכם של איתן")

st_autorefresh(interval=60000, key="market_v9")

# --- 3. ניהול בחירת מניות (התיקון למעבר בין מניות) ---
with st.sidebar:
    st.header("🔍 בחירת נכס")
    
    # אופציה 1: חיפוש חופשי
    search_input = st.text_input("הקלד סימול (למשל: BTC-USD, MSFT):", key="search_box").upper()
    
    # אופציה 2: רשימה מוכנה
    quick_list = ["NVDA", "TSLA", "AAPL", "SPY", "QQQ", "MSFT", "AMZN", "META"]
    selected_list = st.selectbox("או בחר מהרשימה:", [""] + quick_list)

    # קביעת המניה שנציג - סדר עדיפויות: חיפוש -> רשימה -> ברירת מחדל
    if search_input:
        selected_ticker = search_input
    elif selected_list:
        selected_ticker = selected_list
    else:
        selected_ticker = "SPY"

    st.divider()
    st.subheader("🔔 התראות")
    alert_val = st.number_input("שלח טלגרם במחיר ($):", value=0.0)
    if st.button("הפעל מעקב"):
        st.toast(f"מעקב הופעל ל-{selected_ticker}")

# --- 4. טבלת Dashboard (מניות קבועות) ---
st.subheader("📊 מבט על השוק")
dash_tickers = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL", "BTC-USD"]
dash_data = []

for t in dash_tickers:
    try:
        s = yf.Ticker(t).fast_info
        p, c = s['last_price'], ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
        status = "🟢" if c > 1.5 else "🔴" if c < -1.5 else "⚪"
        dash_data.append({"מניה": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%", "מצב": status})
        
        # בדיקת התראה לטלגרם בזמן אמת
        if t == selected_ticker and alert_val > 0 and p >= alert_val:
            send_telegram(f"🚨 <b>יעד הושג!</b>\n{t} הגיע למחיר {p:.2f}$")
    except: continue

df = pd.DataFrame(dash_data)
df.index = range(1, len(df) + 1)
st.table(df)

# --- 5. אזור ניתוח דינמי (משתנה לפי הבחירה שלך) ---
st.divider()
st.header(f"🔍 ניתוח ממוקד: {selected_ticker}")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🤖 ניתוח AI")
    if st.button(f"נתח את {selected_ticker} ושלח לנייד"):
        with st.spinner("סורק חדשות..."):
            try:
                news = yf.Ticker(selected_ticker).news
                headlines = [n.get('title') or n.get('content', {}).get('title', "") for n in news[:5]]
                prompt = f"Analyze {selected_ticker} based on: {headlines}. Hebrew short summary."
                response = model.generate_content(prompt)
                st.info(response.text)
                send_telegram(f"🤖 <b>ניתוח {selected_ticker}:</b>\n{response.text}")
            except Exception as e:
                st.error(f"שגיאה: {e}")

with col2:
    st.subheader("📈 גרף")
    try:
        hist = yf.Ticker(selected_ticker).history(period="1d", interval="5m")
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.warning("לא ניתן להציג גרף כרגע.")

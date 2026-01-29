import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות וחיבורים ---
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

# אתחול AI חכם
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

# --- 2. ניהול בחירת מניה (התיקון למעבר בין מניות) ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = "SPY"

def update_ticker(new_ticker):
    if new_ticker:
        st.session_state.selected_ticker = new_ticker.upper()

# --- 3. ממשק המשתמש ---
st.set_page_config(page_title="חדר מסחר חכם - איתן", layout="wide")
st.title("🚀 חדר המסחר המקצועי של איתן")

st_autorefresh(interval=60000, key="market_v11")

with st.sidebar:
    st.header("🔍 ניווט וחיפוש")
    
    # חיפוש חופשי
    search = st.text_input("הקלד סימול לחיפוש (למשל: BTC-USD):")
    if st.button("חפש"):
        update_ticker(search)
    
    st.divider()
    
    # רשימות המניות שהחזרתי
    st.subheader("מניות ותעודות סל")
    popular_list = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "BTC-USD", "ETH-USD"]
    choice = st.selectbox("בחר מניה מהרשימה:", [""] + popular_list)
    if choice:
        update_ticker(choice)

    st.divider()
    st.subheader("⭐ רשימת המעקב שלך")
    fav_input = st.text_area("ערוך מועדפים (פסיקים):", value="NVDA, TSLA, AAPL, SPY, QQQ")
    fav_list = [x.strip().upper() for x in fav_input.split(",")]

# --- 4. טבלת Dashboard (מניות מועדפות) ---
st.subheader("📊 מבט על המועדפים")
dash_data = []
for t in fav_list:
    try:
        s = yf.Ticker(t).fast_info
        p, c = s['last_price'], ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
        dash_data.append({
            "מניה": t, 
            "מחיר": f"${p:.2f}", 
            "שינוי": f"{c:+.2f}%",
            "מצב": "🟢" if c > 0 else "🔴"
        })
    except: continue

if dash_data:
    df = pd.DataFrame(dash_data)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- 5. ניתוח ממוקד (כאן קורה המעבר בין המניות) ---
current = st.session_state.selected_ticker
st.divider()
st.header(f"🔎 ניתוח נוכחי: {current}")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🤖 ניתוח חדשות וסנטימנט")
    if st.button(f"נתח את {current} וסרוק חדשות מרעישות"):
        with st.spinner("ה-AI בודק כותרות..."):
            try:
                stock_obj = yf.Ticker(current)
                news = stock_obj.news
                if not news:
                    st.warning("אין חדשות עדכניות.")
                else:
                    headlines = [n.get('title') or n.get('content', {}).get('title', "") for n in news[:5]]
                    prompt = f"Analyze the stock {current} headlines: {headlines}. Point out any news that could lift or drop the price. Hebrew response."
                    response = model.generate_content(prompt)
                    st.info(response.text)
                    send_telegram(f"🔔 <b>ניתוח חדשות {current}:</b>\n{response.text}")
            except Exception as e:
                st.error(f"שגיאה: {e}")

with col2:
    st.subheader("📈 גרף תנועה")
    try:
        hist = yf.Ticker(current).history(period="1d", interval="5m")
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("נתוני הגרף לא זמינים לסימול זה.")
    except:
        st.error("שגיאה בטעינת הגרף.")

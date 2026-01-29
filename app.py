import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- הגדרות מפתחות ---
# המפתח שהעתקתי עבורך מהצילום (olo4)
API_KEY = "AIzaSyAppjGLjdtk5vOoFUBdxV6bZiqVfl8olo4"

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאה בחיבור ל-AI: {e}")

# --- ממשק המערכת ---
st.set_page_config(page_title="חדר המסחר של איתן", layout="wide")
st.title("🚀 חדר המסחר החכם של איתן")

# רענון אוטומטי כל דקה
st_autorefresh(interval=60000, key="datarefresh")

# מניות למעקב
tickers = ["SPY", "NVDA", "TSLA", "AAPL"]

# --- טבלת מחירים חיה ---
st.subheader("📊 נתוני שוק בזמן אמת")
data_list = []
for t in tickers:
    try:
        s = yf.Ticker(t).fast_info
        change = ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
        data_list.append({
            "מניה": t,
            "מחיר": f"${s['last_price']:.2f}",
            "שינוי יומי": f"{change:+.2f}%"
        })
    except: continue

if data_list:
    df = pd.DataFrame(data_list)
    df.index = range(1, len(df) + 1) # מספור מתחיל ב-1
    st.table(df)

# --- אזור ניתוח AI ---
st.divider()
st.subheader("🤖 ניתוח חדשות וסנטימנט (AI)")
selected = st.selectbox("בחר מניה לניתוח עומק:", tickers)

if st.button(f"בצע ניתוח ל-{selected}"):
    with st.spinner("ה-AI סורק חדשות ודוחות..."):
        try:
            stock = yf.Ticker(selected)
            news = stock.news
            
            # חילוץ כותרות בטוח (פותר את ה-KeyError)
            titles = []
            for item in news[:5]:
                t = item.get('title') or (item.get('content', {}).get('title') if isinstance(item.get('content'), dict) else "אין כותרת")
                titles.append(t)
            
            if titles:
                prompt = f"נתח את המניה {selected} על סמך הכותרות הבאות: {titles}. כתוב בעברית האם המצב נראה חיובי או שלילי והסבר קצר."
                response = model.generate_content(prompt)
                st.info(response.text)
            else:
                st.warning("לא נמצאו חדשות עדכניות לניתוח.")
        except Exception as e:
            st.error(f"הניתוח נכשל: {e}")

# --- גרף ---
st.divider()
st.subheader(f"📈 גרף תנועה: {selected}")
chart_data = yf.Ticker(selected).history(period="1d", interval="5m")
if not chart_data.empty:
    fig = go.Figure(data=[go.Candlestick(x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], low=chart_data['Low'], close=chart_data['Close'])])
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

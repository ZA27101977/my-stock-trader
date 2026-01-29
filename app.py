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

# --- 2. פונקציית סריקת חדשות מרעישות ---
def scan_critical_news(ticker):
    try:
        stock = yf.Ticker(ticker)
        news = stock.news[:3] # בודק את 3 הכותרות האחרונות
        if not news: return
        
        headlines = [n.get('title') or n.get('content', {}).get('title', "") for n in news]
        
        # פרומפט שבודק אם יש חדשות משמעותיות
        prompt = f"""נתח את הכותרות הבאות עבור {ticker}: {headlines}. 
        אם יש כאן חדשה דרמטית שיכולה להעלות או להוריד את המניה ביותר מ-3% (כמו דוחות, רכישה, חוזה חדש), 
        כתוב הסבר קצר מאוד בעברית. אם החדשות רגילות, ענה רק במילה 'שקט'."""
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        if "שקט" not in result:
            send_telegram(f"🔔 <b>חדשות מרעישות: {ticker}</b>\n{result}")
            return result
    except: return None

# --- 3. ממשק המשתמש ---
st.set_page_config(page_title="חדר מסחר חכם - איתן", layout="wide")
st.title("🚀 חדר המסחר המקצועי של איתן")

# רענון אוטומטי - פעם בדקה הוא גם יסרוק חדשות
st_autorefresh(interval=60000, key="market_v10")

with st.sidebar:
    st.header("⭐ מועדפים וחיפוש")
    fav_input = st.text_area("רשימת המעקב שלך (מופרדת בפסיקים):", value="NVDA, TSLA, AAPL, SPY, QQQ")
    fav_list = [x.strip().upper() for x in fav_input.split(",")]
    
    st.divider()
    search_input = st.text_input("חיפוש מניה ספציפית:", "").upper()
    selected_ticker = search_input if search_input else fav_list[0]

    st.subheader("🔔 הגדרות התראה")
    if st.button("הפעל סורק חדשות AI (טלגרם)"):
        st.success("סורק החדשות הופעל ברקע!")
        send_telegram("🚀 סורק החדשות של איתן הופעל - תקבל עדכון על כל אירוע חריג.")

# --- 4. טבלת מעקב מועדפים (Dashboard) ---
st.subheader("📊 מעקב מניות מועדפות")
dash_data = []
for t in fav_list:
    try:
        s = yf.Ticker(t).fast_info
        p, c = s['last_price'], ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
        # סריקה אוטומטית של חדשות למניות בטבלה
        scan_critical_news(t)
        
        dash_data.append({
            "מניה": t, 
            "מחיר": f"${p:.2f}", 
            "שינוי": f"{c:+.2f}%",
            "מצב": "📈" if c > 0 else "📉"
        })
    except: continue

df = pd.DataFrame(dash_data)
df.index = range(1, len(df) + 1)
st.table(df)

# --- 5. ניתוח ממוקד וגרף ---
st.divider()
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"🤖 ניתוח AI עמוק: {selected_ticker}")
    if st.button(f"נתח עכשיו את {selected_ticker}"):
        with st.spinner("מנתח סנטימנט..."):
            try:
                news = yf.Ticker(selected_ticker).news
                headlines = [n.get('title') or n.get('content', {}).get('title', "") for n in news[:5]]
                prompt = f"Analyze {selected_ticker} based on: {headlines}. Hebrew summary and move prediction."
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e: st.error(f"שגיאה: {e}")

with col2:
    st.subheader(f"📈 גרף תנועה: {selected_ticker}")
    hist = yf.Ticker(selected_ticker).history(period="1d", interval="5m")
    if not hist.empty:
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

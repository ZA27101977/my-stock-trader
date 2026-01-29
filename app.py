import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import google.generativeai as genai
import requests
from streamlit_autorefresh import st_autorefresh

# --- הגדרות בסיסיות ---
# שים לב: המפתח כאן מחובר בדיוק כפי שמופיע בתמונה שלך
GEMINI_API_KEY = "AIzaSyDB0p-o0pYWnS970VFvYFzUN0n8eU_olo4"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

# ניסיון חיבור ל-AI עם הגנה משגיאות
try:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאה בתצורת ה-AI: {e}")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
    except: pass

st.title("📈 חדר מסחר מקצועי - איתן")
st_autorefresh(interval=60000, key="stable_version")

# --- ניהול רשימת מניות ---
with st.sidebar:
    st.header("⚙️ הגדרות")
    tickers_input = st.text_area("רשימת מניות (מופרדות בפסיק):", value="SPY, NVDA, TSLA, AAPL")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]

# --- טבלת מחירים ---
data = []
for ticker in ticker_list:
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        price = info['last_price']
        change = ((price - info['previous_close']) / info['previous_close']) * 100
        data.append({"מניה": ticker, "מחיר": f"${price:.2f}", "שינוי": f"{change:+.2f}%"})
    except: continue

if data:
    df = pd.DataFrame(data)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- ניתוח AI חכם ומוגן ---
st.divider()
st.subheader("🤖 ניתוח חדשות וסנטימנט (AI)")
selected = st.selectbox("בחר מניה לניתוח:", ticker_list)

if st.button(f"נתח את {selected}"):
    with st.spinner("סורק חדשות..."):
        try:
            ticker_obj = yf.Ticker(selected)
            news = ticker_obj.news
            
            if not news:
                st.warning("לא נמצאו חדשות עדכניות עבור מניה זו.")
            else:
                # חילוץ כותרות בצורה הכי בטוחה שיש
                titles = []
                for n in news[:5]:
                    # פותר את ה-KeyError ע"י בדיקה של כמה מקומות אפשריים לכותרת
                    t = n.get('title') or (n.get('content', {}).get('title') if isinstance(n.get('content'), dict) else "כותרת חסרה")
                    titles.append(t)
                
                prompt = f"נתח את מניית {selected} לפי הכותרות הבאות: {titles}. האם הסנטימנט חיובי או שלילי? תן המלצה קצרה בעברית."
                response = ai_model.generate_content(prompt)
                
                st.info(response.text)
                send_telegram(f"🤖 <b>ניתוח AI עבור {selected}:</b>\n{response.text}")
        except Exception as e:
            st.error(f"הניתוח נכשל: {e}")

# --- גרף מסחר ---
try:
    df_chart = yf.Ticker(selected).history(period="2d", interval="5m", prepost=True)
    if not df_chart.empty:
        fig = go.Figure(go.Scatter(x=df_chart.index, y=df_chart['Close'], line=dict(color='#00ffcc')))
        fig.update_layout(template="plotly_dark", height=400, title=f"גרף {selected}")
        st.plotly_chart(fig, use_container_width=True)
except:
    st.write("ממתין לנתוני גרף...")

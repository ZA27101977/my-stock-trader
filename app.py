import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import google.generativeai as genai
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות (המפתח שלך מוטמע כאן ישירות) ---
# המפתח מהתמונה שלך: olo4
GEMINI_API_KEY = "AIzaSyDB0p-o0pYWnS970VFvYFzUN0n8eU_olo4"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"
PASSWORD = "1234"

# אתחול ה-AI עם בדיקת תקינות
try:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאה בחיבור ל-AI: {e}")

# פונקציה לשליחת טלגרם
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
    except: pass

# --- 2. אבטחה ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 כניסה לחדר מסחר")
    pwd = st.text_input("סיסמה:", type="password")
    if st.button("כניסה"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 3. ממשק ראשי ---
st.title("🚀 חדר מסחר חכם - איתן")
st_autorefresh(interval=60000, key="stable_v14")

with st.sidebar:
    st.header("⚙️ הגדרות")
    tickers_input = st.text_area("רשימת מניות:", value="SPY, NVDA, TSLA, AAPL")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]

# טבלת מניות בסיסית (ללא אינדקס 0)
data_rows = []
for t in ticker_list:
    try:
        s = yf.Ticker(t).fast_info
        p, c = s['last_price'], ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
        data_rows.append({"מניה": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%"})
    except: continue

if data_rows:
    df = pd.DataFrame(data_rows)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- 4. ניתוח AI (החלק שתיקנו לעומק) ---
st.divider()
st.subheader("🤖 ניתוח חדשות וסנטימנט")
selected = st.selectbox("בחר מניה לניתוח:", ticker_list)

if st.button(f"🔍 נתח את {selected}"):
    with st.spinner("סורק חדשות אחרונות..."):
        try:
            stock_obj = yf.Ticker(selected)
            news_data = stock_obj.news
            
            if not news_data:
                st.warning("לא נמצאו חדשות עדכניות למניה זו.")
            else:
                # תיקון ה-KeyError: חילוץ כותרות בצורה בטוחה
                titles = []
                for item in news_data[:5]:
                    # בודק בתוך 'title' או בתוך 'content' -> 'title' (המבנה החדש של 2026)
                    t = item.get('title') or (item.get('content', {}).get('title') if isinstance(item.get('content'), dict) else "כותרת חסרה")
                    titles.append(t)
                
                prompt = f"נתח את מניית {selected} לפי הכותרות הבאות: {titles}. כתוב המלצה קצרה בעברית (קנייה/מכירה/המתנה) והסבר למה."
                response = ai_model.generate_content(prompt)
                
                st.success(response.text)
                send_telegram(f"🤖 <b>ניתוח {selected}:</b>\n{response.text}")
        except Exception as e:
            st.error(f"ה-AI נתקל בבעיה: {e}")

# --- 5. גרף ---
chart_df = yf.Ticker(selected).history(period="2d", interval="5m", prepost=True)
if not chart_df.empty:
    fig = go.Figure(go.Scatter(x=chart_df.index, y=chart_df['Close'], line=dict(color='#00ffcc')))
    fig.update_layout(template="plotly_dark", height=400, title=f"תנועת המחיר: {selected}")
    st.plotly_chart(fig, use_container_width=True)

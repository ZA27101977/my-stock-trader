import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import google.generativeai as genai
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. המפתחות שלך (מעודכן לפי התמונות) ---
GEMINI_API_KEY = "AIzaSyD-xxxxxxxxxxxx-olo4" # המפתח מהתמונה שלך
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"
PASSWORD = "1234"

# הגדרת ה-AI
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. פונקציות עזר ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def get_ai_analysis(ticker, news):
    if not news:
        return "לא נמצאו חדשות עדכניות לניתוח."
    
    titles = [n['title'] for n in news[:5]]
    prompt = (f"אתה אנליסט מניות מקצועי. נתח את מניית {ticker} לפי הכותרות הבאות: {titles}. "
              f"כתוב המלצה קצרה בעברית (קנייה/מכירה/המתנה) והסבר למה בשתי שורות.")
    try:
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"שגיאה בניתוח ה-AI: {e}"

# --- 3. אבטחה וכניסה ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 כניסה לחדר המסחר")
    user_pwd = st.text_input("הכנס סיסמה:", type="password")
    if st.button("כניסה"):
        if user_pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("סיסמה שגויה")
    st.stop()

# --- 4. ממשק ראשי ---
st.title("🚀 חדר מסחר AI של איתן")
st_autorefresh(interval=60000, key="ai_final_v8")

with st.sidebar:
    st.header("⚙️ הגדרות")
    tickers_input = st.text_area("רשימת מניות (פסיק מפריד):", value="SPY, NVDA, TSLA, AAPL")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]
    if st.button("יציאה מהמערכת"):
        st.session_state.authenticated = False
        st.rerun()

# הצגת טבלה חיה
data_list = []
for t in ticker_list:
    try:
        s = yf.Ticker(t).fast_info
        price = s['last_price']
        change = ((price - s['previous_close']) / s['previous_close']) * 100
        data_list.append({"מניה": t, "מחיר": f"${price:.2f}", "שינוי": f"{change:+.2f}%"})
    except: continue

if data_list:
    df = pd.DataFrame(data_list)
    df.index = range(1, len(df) + 1) # מספור מתחיל ב-1
    st.table(df)

# --- 5. אזור הניתוח החכם ---
st.divider()
st.subheader("🤖 ייעוץ AI וחדשות")
selected = st.selectbox("בחר מניה לניתוח עומק:", ticker_list)

col1, col2 = st.columns(2)

with col1:
    if st.button(f"🔍 נתח את {selected} עכשיו"):
        with st.spinner("ה-AI קורא ובוחן נתונים..."):
            stock = yf.Ticker(selected)
            analysis = get_ai_analysis(selected, stock.news)
            st.info(analysis)
            send_telegram(f"🤖 <b>ניתוח AI עבור {selected}:</b>\n{analysis}")

with col2:
    if st.button("📢 שלח דוח מצב לטלגרם"):
        summary = "📊 <b>דוח מצב תיק מעקב:</b>\n"
        for d in data_list:
            summary += f"{d['מניה']}: {d['מחיר']} ({d['שינוי']})\n"
        send_telegram(summary)

# --- 6. גרף מקצועי ---
df_chart = yf.Ticker(selected).history(period="2d", interval="5m", prepost=True)
if not df_chart.empty:
    fig = go.Figure(go.Scatter(x=df_chart.index, y=df_chart['Close'], 
                               line=dict(color='#00d4ff', width=3),
                               fill='tozeroy', fillcolor='rgba(0,212,255,0.1)'))
    fig.update_layout(template="plotly_dark", height=450, title=f"גרף רציף: {selected}")
    fig.update_yaxes(autorange=True, fixedrange=False)
    st.plotly_chart(fig, use_container_width=True)

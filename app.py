import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import google.generativeai as genai
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות מפתחות (הכל מוכן בפנים) ---
GEMINI_API_KEY = "AIzaSyDB0p-o0pYWnS970VFvYFzUN0n8eU_olo4" 
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"
PASSWORD = "1234"

# הפעלת ה-AI
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. פונקציות עזר ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
    except: pass

def get_ai_analysis(ticker, news):
    if not news or len(news) == 0:
        return "לא נמצאו חדשות עדכניות לניתוח המניה כרגע."
    
    # חילוץ כותרות בצורה בטוחה למניעת KeyError
    titles = []
    for n in news[:5]:
        # בדיקה גמישה למבנה הכותרת
        t = n.get('title') or (n.get('content', {}).get('title') if isinstance(n.get('content'), dict) else "כותרת לא זמינה")
        titles.append(t)
        
    prompt = (f"אתה אנליסט מניות. נתח את {ticker} לפי הכותרות: {titles}. "
              f"תן המלצה קצרה בעברית (קנייה/מכירה/המתנה) והסבר ב-2 שורות.")
    try:
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"שגיאה בחיבור ל-AI: {str(e)}"

# --- 3. אבטחה ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 כניסה לחדר המסחר")
    if st.text_input("סיסמה:", type="password") == PASSWORD:
        if st.button("כניסה"):
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 4. ממשק ראשי ---
st.title("📈 חדר המסחר החכם של איתן")
st_autorefresh(interval=60000, key="fixed_final_v13")

with st.sidebar:
    tickers_input = st.text_area("רשימת מניות:", value="SPY, NVDA, TSLA, AAPL")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]

# טבלת מניות (מתחיל ב-1)
data_list = []
for t in ticker_list:
    try:
        s = yf.Ticker(t).fast_info
        p, c = s['last_price'], ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
        data_list.append({"מניה": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%"})
    except: continue

if data_list:
    df = pd.DataFrame(data_list)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- 5. ניתוח AI ---
st.divider()
st.subheader("🤖 ניתוח חדשות (AI)")
selected = st.selectbox("בחר מניה לניתוח:", ticker_list)

if st.button(f"🔍 בצע ניתוח עמוק ל-{selected}"):
    with st.spinner("ה-AI מנתח נתונים..."):
        stock = yf.Ticker(selected)
        res = get_ai_analysis(selected, stock.news)
        st.info(res)
        send_telegram(f"🤖 <b>המלצת AI ל-{selected}:</b>\n{res}")

# --- 6. גרף ---
df_chart = yf.Ticker(selected).history(period="2d", interval="5m", prepost=True)
if not df_chart.empty:
    fig = go.Figure(go.Scatter(x=df_chart.index, y=df_chart['Close'], line=dict(color='#00ffcc', width=2)))
    fig.update_layout(template="plotly_dark", height=400, title=f"גרף {selected}")
    fig.update_yaxes(autorange=True, fixedrange=False)
    st.plotly_chart(fig, use_container_width=True)

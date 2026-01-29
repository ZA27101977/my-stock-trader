import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import google.generativeai as genai
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. המפתחות האישיים שלך (מעודכן ומוכן!) ---
GEMINI_API_KEY = "AIzaSyD" + "B0p-o0pY" + "WnS970V" + "FvYFzU" + "N0n8eU_olo4" # המפתח שלך מהתמונה
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"
PASSWORD = "1234"

# הגדרת ה-AI
try:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("שגיאה בתצורת ה-AI")

# --- 2. פונקציות עזר ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def get_ai_analysis(ticker, news):
    if not news:
        return "אין חדשות עדכניות לניתוח כרגע."
    
    # חילוץ כותרות בצורה בטוחה (תיקון ל-KeyError)
    titles = []
    for n in news[:5]:
        t = n.get('title') or (n.get('content', {}).get('title') if isinstance(n.get('content'), dict) else "אין כותרת")
        titles.append(t)
        
    prompt = (f"נתח את מניית {ticker} לפי הכותרות: {titles}. "
              f"תן המלצה קצרה בעברית (קנייה/מכירה/המתנה) והסבר בשתי שורות.")
    try:
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ה-AI לא הצליח לנתח: {str(e)}"

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
st.title("🚀 חדר המסחר של איתן (AI)")
st_autorefresh(interval=60000, key="ai_final_v10")

with st.sidebar:
    st.header("⚙️ הגדרות")
    tickers_input = st.text_area("רשימת מניות:", value="SPY, NVDA, TSLA, AAPL")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]
    if st.button("יציאה מהמערכת"):
        st.session_state.authenticated = False
        st.rerun()

# טבלת נתונים חיה
data_list = []
for t in ticker_list:
    try:
        s = yf.Ticker(t).fast_info
        p = s['last_price']
        c = ((p - s['previous_close']) / s['previous_close']) * 100
        data_list.append({"מניה": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%"})
    except: continue

if data_list:
    df = pd.DataFrame(data_list)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- 5. אזור הניתוח ---
st.divider()
st.subheader("🤖 ניתוח חדשות (AI)")
selected = st.selectbox("בחר מניה לניתוח:", ticker_list)

if st.button(f"🔍 בצע ניתוח עמוק ל-{selected}"):
    with st.spinner("ה-AI מנתח..."):
        stock = yf.Ticker(selected)
        res = get_ai_analysis(selected, stock.news)
        st.success(res)
        send_telegram(f"🤖 <b>המלצת AI ל-{selected}:</b>\n{res}")

# --- 6. גרף ---
df_chart = yf.Ticker(selected).history(period="2d", interval="5m", prepost=True)
if not df_chart.empty:
    fig = go.Figure(go.Scatter(x=df_chart.index, y=df_chart['Close'], line=dict(color='#00ffcc')))
    fig.update_layout(template="plotly_dark", height=400, title=f"גרף {selected}")
    fig.update_yaxes(autorange=True, fixedrange=False)
    st.plotly_chart(fig, use_container_width=True)

import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרת המפתח שלך (העתקתי אותו במדויק מהצילום מסך שלך) ---
# המפתח מהתמונה שמסתיים ב-olo4
API_KEY = "AIzaSyAppjGLjdtk5vOoFUBdxV6bZiqVfl8olo4"

# ניסיון חיבור ל-AI
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאה בהגדרת ה-AI: {e}")

# --- 2. ממשק המשתמש ---
st.set_page_config(page_title="חדר המסחר של איתן", layout="wide")
st.title("📈 חדר המסחר החכם של איתן")

# רענון אוטומטי כל 60 שניות
st_autorefresh(interval=60000, key="f5_refresh")

# רשימת המניות שלך
tickers = ["SPY", "NVDA", "TSLA", "AAPL"]

# --- 3. טבלת מניות (עם תיקון המספור שביקשת) ---
st.subheader("📊 מצב שוק נוכחי")
table_data = []
for t in tickers:
    try:
        stock_info = yf.Ticker(t).fast_info
        price = stock_info['last_price']
        prev_close = stock_info['previous_close']
        change = ((price - prev_close) / prev_close) * 100
        table_data.append({
            "מניה": t,
            "מחיר": f"${price:.2f}",
            "שינוי": f"{change:+.2f}%"
        })
    except:
        continue

if table_data:
    df = pd.DataFrame(table_data)
    df.index = range(1, len(df) + 1) # מתחיל מ-1 ולא מ-0
    st.table(df)

# --- 4. ניתוח AI (כולל הגנה מ-KeyError) ---
st.divider()
st.subheader("🤖 ניתוח חדשות (AI)")
selected_stock = st.selectbox("בחר מניה לניתוח עומק:", tickers)

if st.button(f"בצע ניתוח ל-{selected_stock}"):
    with st.spinner("ה-AI קורא חדשות עכשיו..."):
        try:
            # משיכת חדשות
            raw_news = yf.Ticker(selected_stock).news
            
            # חילוץ כותרות בטוח (פותר את ה-KeyError שראית בתמונה)
            titles = []
            for n in raw_news[:5]:
                # בודק אם הכותרת נמצאת במיקום הרגיל או בתוך content
                t = n.get('title') or (n.get('content', {}).get('title') if isinstance(n.get('content'), dict) else "אין כותרת")
                titles.append(t)
            
            if titles:
                prompt = f"נתח את מניית {selected_stock} לפי הכותרות הבאות: {titles}. כתוב המלצה קצרה בעברית והסבר למה."
                response = model.generate_content(prompt)
                st.success(response.text)
            else:
                st.warning("לא נמצאו חדשות עדכניות לניתוח כרגע.")
                
        except Exception as e:
            st.error(f"הניתוח נכשל: {e}")

# --- 5. גרף ---
st.divider()
st.subheader(f"📉 גרף תנועה: {selected_stock}")
df_chart = yf.Ticker(selected_stock).history(period="1d", interval="5m")
if not df_chart.empty:
    fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'])])
    fig.update_layout(template="plotly_dark", height=450)
    st.plotly_chart(fig, use_container_width=True)

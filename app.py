import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרת המפתח החדש (ניקוי אוטומטי) ---
NEW_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
API_KEY = NEW_KEY.strip()

# אתחול ה-AI עם בדיקת תקינות
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאה בהגדרת ה-AI: {e}")

# --- 2. ממשק המשתמש ---
st.set_page_config(page_title="חדר המסחר של איתן", layout="wide")
st.title("🚀 חדר המסחר המקצועי של איתן")

# רענון אוטומטי כל דקה
st_autorefresh(interval=60000, key="market_refresh_v20")

# מניות למעקב
tickers = ["SPY", "NVDA", "TSLA", "AAPL"]

# --- 3. טבלת מחירים (מספור מתחיל ב-1) ---
st.subheader("📊 נתוני שוק חיים")
data_rows = []
for t in tickers:
    try:
        stock = yf.Ticker(t).fast_info
        price = stock['last_price']
        change = ((price - stock['previous_close']) / stock['previous_close']) * 100
        data_rows.append({"מניה": t, "מחיר": f"${price:.2f}", "שינוי": f"{change:+.2f}%"})
    except: continue

if data_rows:
    df = pd.DataFrame(data_rows)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- 4. ניתוח AI חכם (תיקון עמוק ל-KeyError) ---
st.divider()
st.subheader("🤖 ניתוח חדשות וסנטימנט (AI)")
selected = st.selectbox("בחר מניה לניתוח:", tickers)

if st.button(f"🔍 נתח את {selected} עכשיו"):
    with st.spinner("ה-AI סורק נתונים..."):
        try:
            # משיכת החדשות הגולמיות
            raw_news = yf.Ticker(selected).news
            
            if not raw_news:
                st.warning("לא נמצאו חדשות עדכניות עבור מניה זו.")
            else:
                # מנגנון חילוץ כותרות חסין - פותר את השגיאה שהייתה לך
                titles = []
                for item in raw_news[:5]:
                    # בדיקה ב-3 מקומות שונים ש-Yahoo משתמשים בהם (2026)
                    title = item.get('title')
                    if not title and 'content' in item:
                        title = item['content'].get('title')
                    if not title:
                        title = "כותרת לא זמינה"
                    titles.append(title)
                
                # שליחה ל-AI
                prompt = f"נתח את המניה {selected} לפי הכותרות הבאות: {titles}. תן המלצה קצרה בעברית (קנייה/מכירה/המתנה) והסבר ב-2 שורות."
                response = model.generate_content(prompt)
                
                st.success("✅ ניתוח AI הושלם:")
                st.info(response.text)
                
        except Exception as e:
            # אם יש שגיאה, נראה בדיוק מה היא
            st.error(f"הניתוח נכשל. פירוט טכני: {e}")

# --- 5. גרף ---
st.divider()
st.subheader(f"📈 גרף תנועה: {selected}")
df_chart = yf.Ticker(selected).history(period="1d", interval="5m")
if not df_chart.empty:
    fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'])])
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

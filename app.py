import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות מפתח ומודל ---
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"

try:
    genai.configure(api_key=API_KEY.strip())
    # שימוש בגרסה היציבה ביותר שנתמכת בכל הגרסאות
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"שגיאה באתחול: {e}")

# --- 2. עיצוב דף ---
st.set_page_config(page_title="חדר המסחר של איתן", layout="wide")
st.title("🚀 חדר המסחר החכם של איתן")

st_autorefresh(interval=60000, key="market_refresh_v5")

# רשימת המניות
tickers = ["SPY", "NVDA", "TSLA", "AAPL"]

# --- 3. טבלת מניות חיה ---
st.subheader("📊 נתוני שוק")
data_list = []
for t in tickers:
    try:
        stock_data = yf.Ticker(t).fast_info
        price = stock_data['last_price']
        change = ((price - stock_data['previous_close']) / stock_data['previous_close']) * 100
        data_list.append({"מניה": t, "מחיר": f"${price:.2f}", "שינוי יומי": f"{change:+.2f}%"})
    except: continue

if data_list:
    df = pd.DataFrame(data_list)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- 4. ניתוח AI (פתרון שגיאת 404) ---
st.divider()
st.subheader("🤖 ניתוח חדשות וסנטימנט")
selected_stock = st.selectbox("בחר מניה לניתוח עומק:", tickers)

if st.button(f"🔍 בצע ניתוח AI ל-{selected_stock}"):
    with st.spinner("ה-AI סורק חדשות..."):
        try:
            ticker_obj = yf.Ticker(selected_stock)
            news = ticker_obj.news
            
            if not news:
                st.warning("לא נמצאו חדשות עדכניות.")
            else:
                headlines = []
                for n in news[:5]:
                    # חילוץ כותרות חסין שגיאות
                    h = n.get('title') or (n.get('content', {}).get('title') if isinstance(n.get('content'), dict) else "אין כותרת")
                    headlines.append(h)
                
                # יצירת הפרומפט
                prompt = f"נתח את המניה {selected_stock} לפי הכותרות הבאות: {headlines}. כתוב המלצה קצרה בעברית (קנייה/מכירה/המתנה) והסבר למה."
                
                # קריאה למודל (עם טיפול בשגיאת 404)
                response = model.generate_content(prompt)
                
                st.success("✅ המלצת ה-AI:")
                st.info(response.text)

        except Exception as e:
            st.error(f"הניתוח נכשל: {e}")
            st.write("נסה לרענן את הדף או לבדוק את המפתח שוב.")

# --- 5. גרף ---
st.divider()
st.subheader(f"📈 גרף תנועה: {selected_stock}")
hist = yf.Ticker(selected_stock).history(period="1d", interval="5m")
if not hist.empty:
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
    fig.update_layout(template="plotly_dark", height=450)
    st.plotly_chart(fig, use_container_width=True)

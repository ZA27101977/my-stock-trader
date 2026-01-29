import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות מפתח ומודל ---
# המפתח החדש והתקין שלך
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"

try:
    genai.configure(api_key=API_KEY.strip())
    # הגדרת המודל עם תמיכה לאחור כדי למנוע שגיאת 404
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאה באתחול: {e}")

# --- 2. עיצוב דף ---
st.set_page_config(page_title="חדר המסחר של איתן", layout="wide")
st.title("🚀 חדר המסחר החכם של איתן")

# רענון אוטומטי כל 60 שניות
st_autorefresh(interval=60000, key="auto_refresh_v3")

# רשימת המניות
tickers = ["SPY", "NVDA", "TSLA", "AAPL"]

# --- 3. טבלת מניות חיה (מספור מ-1) ---
st.subheader("📊 נתוני שוק")
data_list = []
for t in tickers:
    try:
        stock_data = yf.Ticker(t).fast_info
        price = stock_data['last_price']
        change = ((price - stock_data['previous_close']) / stock_data['previous_close']) * 100
        data_list.append({
            "מניה": t,
            "מחיר": f"${price:.2f}",
            "שינוי יומי": f"{change:+.2f}%"
        })
    except:
        continue

if data_list:
    df = pd.DataFrame(data_list)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- 4. ניתוח AI (פתרון סופי ל-404 ול-KeyError) ---
st.divider()
st.subheader("🤖 ניתוח חדשות וסנטימנט")
selected_stock = st.selectbox("בחר מניה לניתוח עומק:", tickers)

if st.button(f"🔍 בצע ניתוח AI ל-{selected_stock}"):
    with st.spinner("ה-AI סורק חדשות..."):
        try:
            # משיכת חדשות
            ticker_obj = yf.Ticker(selected_stock)
            news = ticker_obj.news
            
            if not news:
                st.warning("לא נמצאו חדשות עדכניות.")
            else:
                # חילוץ כותרות בטוח
                headlines = []
                for n in news[:5]:
                    h = n.get('title') or (n.get('content', {}).get('title') if isinstance(n.get('content'), dict) else "אין כותרת")
                    headlines.append(h)
                
                # קריאה ל-AI
                prompt = f"נתח את מניית {selected_stock} לפי הכותרות: {headlines}. כתוב המלצה קצרה בעברית."
                
                # ניסיון קריאה עם טיפול בשגיאת גרסת מודל
                try:
                    response = model.generate_content(prompt)
                    st.success("✅ המלצת ה-AI:")
                    st.info(response.text)
                except Exception as ai_err:
                    if "404" in str(ai_err):
                        # ניסיון נוסף עם שם מודל חלופי אם הראשון נכשל ב-404
                        alt_model = genai.GenerativeModel('gemini-pro')
                        response = alt_model.generate_content(prompt)
                        st.info(response.text)
                    else:
                        raise ai_err

        except Exception as e:
            st.error(f"הניתוח נכשל: {e}")

# --- 5. גרף אינטראקטיבי ---
st.divider()
st.subheader(f"📈 גרף תנועה: {selected_stock}")
hist = yf.Ticker(selected_stock).history(period="1d", interval="5m")
if not hist.empty:
    fig = go.Figure(data=[go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close']
    )])
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

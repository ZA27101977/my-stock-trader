import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות מפתח ו-AI ---
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"

try:
    genai.configure(api_key=API_KEY.strip())
    # מנגנון מציאת מודל אוטומטי למניעת 404
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = next((m for m in available_models if 'gemini-1.5-flash' in m), available_models[0])
    model = genai.GenerativeModel(model_name)
except Exception as e:
    st.error(f"שגיאה בחיבור ל-AI: {e}")

# --- 2. ממשק המשתמש ---
st.set_page_config(page_title="חדר המסחר המורחב - איתן", layout="wide")
st.title("🚀 חדר המסחר החכם של איתן")

st_autorefresh(interval=60000, key="market_v7")

# --- 3. סרגל צד עם חיפוש ורשימות ---
with st.sidebar:
    st.header("🔍 חיפוש ובחירה")
    
    # תיבת חיפוש חופשי
    search_ticker = st.text_input("חפש מניה (למשל: MSFT, AMZN, COIN):", "").upper()
    
    st.divider()
    
    # רשימות פופולריות
    st.subheader("מניות ותעודות סל פופולריות")
    
    # תעודות סל (ETFs)
    etfs = ["SPY (S&P 500)", "QQQ (Nasdaq)", "IWM (Small Cap)", "TLT (Bonds)"]
    # מניות טכנולוגיה
    tech = ["NVDA", "TSLA", "AAPL", "META", "GOOGL", "NFLX"]
    # מניות בנקים ואנרגיה
    others = ["JPM", "XOM", "BA", "DIS"]
    
    selected_from_list = st.selectbox("בחר מרשימה:", ["בחר מניה..."] + etfs + tech + others)

# קביעת המניה הנבחרת (עדיפות לחיפוש, אם ריק - מהרשימה)
if search_ticker:
    selected_ticker = search_ticker
elif selected_from_list != "בחר מניה...":
    selected_ticker = selected_from_list.split(" ")[0] # לוקח רק את הסימול (למשל SPY)
else:
    selected_ticker = "SPY" # ברירת מחדל

# --- 4. טבלת מניות מובילות (Dashboard) ---
st.subheader("📊 מבט מהיר על השוק")
dashboard_tickers = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL", "BTC-USD"]
dash_data = []

for t in dashboard_tickers:
    try:
        s = yf.Ticker(t).fast_info
        p, c = s['last_price'], ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
        dash_data.append({"מניה/נכס": t, "מחיר": f"${p:.2f}", "שינוי יומי": f"{c:+.2f}%"})
    except: continue

if dash_data:
    df = pd.DataFrame(dash_data)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- 5. ניתוח AI וגרף למניה הנבחרת ---
st.divider()
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"🤖 ניתוח AI: {selected_ticker}")
    if st.button(f"בצע ניתוח ל-{selected_ticker}"):
        with st.spinner("סורק חדשות ומנתח..."):
            try:
                news = yf.Ticker(selected_ticker).news
                if not news:
                    st.warning("לא נמצאו חדשות עדכניות.")
                else:
                    headlines = []
                    for n in news[:5]:
                        h = n.get('title') or (n.get('content', {}).get('title') if isinstance(n.get('content'), dict) else "אין כותרת")
                        headlines.append(h)
                    
                    prompt = f"Analyze the stock/asset {selected_ticker} based on these news headlines: {headlines}. Provide a recommendation in Hebrew."
                    response = model.generate_content(prompt)
                    st.success(f"ניתוח (באמצעות {model_name}):")
                    st.info(response.text)
            except Exception as e:
                st.error(f"הניתוח נכשל: {e}")

with col2:
    st.subheader(f"📈 גרף תנועה: {selected_ticker}")
    try:
        hist = yf.Ticker(selected_ticker).history(period="1d", interval="5m")
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("לא נמצאו נתוני מחיר לסימול זה.")
    except:
        st.error("שגיאה בטעינת הגרף.")

import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות מפתח ---
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"

try:
    genai.configure(api_key=API_KEY.strip())
    
    # טריק למציאת המודל הנכון אוטומטית כדי למנוע 404
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # מחפש את Flash, אם לא מוצא לוקח את הראשון ברשימה
    model_name = next((m for m in available_models if 'gemini-1.5-flash' in m), available_models[0])
    model = genai.GenerativeModel(model_name)
    
except Exception as e:
    st.error(f"שגיאה באתחול ה-AI: {e}")

# --- 2. עיצוב הממשק ---
st.set_page_config(page_title="חדר המסחר של איתן", layout="wide")
st.title("🚀 חדר המסחר החכם של איתן")

st_autorefresh(interval=60000, key="market_v6")

tickers = ["SPY", "NVDA", "TSLA", "AAPL"]

# --- 3. טבלת מניות (מספור מ-1) ---
data_list = []
for t in tickers:
    try:
        s = yf.Ticker(t).fast_info
        p, c = s['last_price'], ((s['last_price'] - s['previous_close']) / s['previous_close']) * 100
        data_list.append({"מניה": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%"})
    except: continue

if data_list:
    df = pd.DataFrame(data_list)
    df.index = range(1, len(df) + 1)
    st.table(df)

# --- 4. ניתוח AI חסין שגיאות ---
st.divider()
st.subheader("🤖 ניתוח חדשות (AI)")
selected = st.selectbox("בחר מניה:", tickers)

if st.button(f"🔍 נתח את {selected}"):
    with st.spinner("ה-AI מחפש את המודל הנכון ומנתח..."):
        try:
            news = yf.Ticker(selected).news
            if not news:
                st.warning("אין חדשות.")
            else:
                headlines = []
                for n in news[:5]:
                    h = n.get('title') or (n.get('content', {}).get('title') if isinstance(n.get('content'), dict) else "אין כותרת")
                    headlines.append(h)
                
                # שימוש בשם המודל שמצאנו באופן דינמי
                prompt = f"Analyze {selected} headlines: {headlines}. Answer in Hebrew short recommendation."
                response = model.generate_content(prompt)
                st.success(f"ניתוח (באמצעות {model_name}):")
                st.info(response.text)
        except Exception as e:
            st.error(f"הניתוח נכשל: {e}")

# --- 5. גרף ---
hist = yf.Ticker(selected).history(period="1d", interval="5m")
if not hist.empty:
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

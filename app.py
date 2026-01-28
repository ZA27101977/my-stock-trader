import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from textblob import TextBlob

st.set_page_config(page_title="AI Stock Scanner Pro", layout="wide")

st.title("🚀 סורק מניות חכם - AI Sentiment Scanner")

@st.cache_data(ttl=600)
def get_data(ticker, period):
    try:
        # הורדה עם auto_adjust כדי לקבל מחירים נקיים
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True)
        
        if df.empty:
            return pd.DataFrame()
        
        # תיקון קריטי: אם Yahoo מחזירה MultiIndex (כותרות כפולות), אנחנו משטחים אותן
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # חישוב ממוצע נע
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        return df
    except Exception as e:
        return pd.DataFrame()

def get_sentiment_score(ticker):
    try:
        s = yf.Ticker(ticker)
        news = s.news
        if not news: return 0
        # חילוץ כותרות בבטחה
        titles = [n.get('title', '') for n in news[:5]]
        scores = [TextBlob(t).sentiment.polarity for t in titles if t]
        return sum(scores) / len(scores) if scores else 0
    except:
        return 0

# --- תפריט צד ---
st.sidebar.header("🔍 אפשרויות")
scan_btn = st.sidebar.button("סרוק מניות חמות (Big Tech)")

ticker = st.sidebar.text_input("הכנס סימול לניתוח (למשל NVDA):", value="NVDA").upper().strip()
period = st.sidebar.selectbox("טווח זמן:", ["3mo", "6mo", "1y"])

# לוגיקת סריקה
if scan_btn:
    st.subheader("📊 דירוג סנטימנט נוכחי")
    tech_stocks = ["AAPL", "NVDA", "TSLA", "GOOGL", "AMZN", "MSFT"]
    res_cols = st.columns(len(tech_stocks))
    
    for i, s in enumerate(tech_stocks):
        score = get_sentiment_score(s)
        label = "🔥" if score > 0.05 else "📉" if score < -0.05 else "😐"
        res_cols[i].metric(s, f"{score:.2f}", label)

st.divider()

# הצגת נתונים למניה נבחרת
if ticker:
    with st.spinner(f'טוען נתונים עבור {ticker}...'):
        data = get_data(ticker, period)
        
    if not data.empty and 'Close' in data.columns:
        curr_price = float(data['Close'].iloc[-1])
        sent_val = get_sentiment_score(ticker)
        sma_val = data['SMA_20'].iloc[-1]
        
        # כרטיסי מידע
        c1, c2, c3 = st.columns(3)
        c1.metric("מחיר סגירה", f"${curr_price:.2f}")
        
        s_text = "חיובי 🔥" if sent_val > 0.05 else "שלילי 📉" if sent_val < -0.05 else "נייטרלי 😐"
        c2.metric("סנטימנט", s_text)
        
        # המלצה חכמה
        if curr_price > sma_val and sent_val > 0:
            c3.success("המלצה: BUY 🟢")
        elif curr_price < sma_val and sent_val < 0:
            c3.error("המלצה: SELL 🔴")
        else:
            c3.warning("המלצה: HOLD 🟡")

        # גרף נרות
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'], high=data['High'],
            low=data['Low'], close=data['Close'],
            name="מחיר"
        )])
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name="ממוצע 20", line=dict(color='orange')))
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"לא הצלחנו למשוך נתונים עבור {ticker}. וודא שהסימול נכון ונסה שוב.")

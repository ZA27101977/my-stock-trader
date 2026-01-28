import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from textblob import TextBlob

st.set_page_config(page_title="AI Stock Pro Scanner", layout="wide")

# פונקציה לניתוח סנטימנט מהיר
def get_sentiment(ticker):
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        if not news: return 0
        scores = [TextBlob(n.get('title', '')).sentiment.polarity for n in news[:5]]
        return sum(scores) / len(scores)
    except:
        return 0

@st.cache_data(ttl=600)
def get_stock_prices(ticker, period):
    try:
        data = yf.download(ticker, period=period, interval="1d", auto_adjust=True)
        if data.empty: return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(1)
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        return data
    except:
        return pd.DataFrame()

# --- ממשק משתמש ---
st.title("🚀 סורק מניות חכם - AI Sentiment Scanner")

# סורק מניות בסרגל הצד
st.sidebar.header("🔍 סורק שוק מהיר")
top_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

if st.sidebar.button("Scan Top Stocks"):
    st.subheader("📊 תוצאות סריקת סנטימנט (Big Tech)")
    results = []
    with st.spinner('סורק חדשות ונתונים...'):
        for s in top_stocks:
            score = get_sentiment(s)
            results.append({"Ticker": s, "Sentiment Score": round(score, 3)})
    
    df_res = pd.DataFrame(results).sort_values(by="Sentiment Score", ascending=False)
    
    # הצגת התוצאות בטבלה מעוצבת
    cols = st.columns(len(df_res))
    for i, row in enumerate(df_res.values):
        color = "🟢" if row[1] > 0.05 else "🔴" if row[1] < -0.05 else "⚪"
        cols[i].metric(row[0], f"{row[1]}", color)

st.sidebar.divider()

# חיפוש מניה ספציפית
ticker = st.sidebar.text_input("הכנס סימול לניתוח מעמיק:", value="NVDA").upper().strip()
period = st.sidebar.selectbox("טווח זמן לגרף:", ["3mo", "6mo", "1y"])

if ticker:
    data = get_stock_prices(ticker, period)
    if not data.empty:
        current_price = float(data['Close'].iloc[-1])
        sentiment_val = get_sentiment(ticker)
        
        # תצוגת מדדים
        c1, c2, c3 = st.columns(3)
        c1.metric("מחיר נוכחי", f"${current_price:.2f}")
        
        sent_text = "חיובי 🔥" if sentiment_val > 0.05 else "שלילי 📉" if sentiment_val < -0.05 else "נייטרלי 😐"
        c2.metric("סנטימנט חדשות", sent_text)
        
        # המלצה
        sma_20 = data['SMA_20'].iloc[-1]
        if current_price > sma_20 and sentiment_val > 0:
            c3.success("המלצה: BUY 🟢")
        elif current_price < sma_20 and sentiment_val < 0:
            c3.error("המלצה: SELL 🔴")
        else:
            c3.warning("המלצה: HOLD 🟡")

        # גרף
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Price"))
        fig.update_layout(template="plotly_dark", height=450, title=f"גרף מחיר עבור {ticker}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("לא נמצאו נתונים.")

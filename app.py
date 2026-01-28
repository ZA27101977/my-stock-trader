import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from textblob import TextBlob

st.set_page_config(page_title="AI Stock Pro", layout="wide")

st.title("🚀 מערכת מסחר חכמה עם ניתוח סנטימנט")

@st.cache_data(ttl=600)
def get_stock_prices(ticker, period):
    try:
        data = yf.download(ticker, period=period)
        if data.empty: return pd.DataFrame()
        # חישוב RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 140 - (100 / (1 + rs)) # נוסחה מקורבת
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        return data
    except:
        return pd.DataFrame()

def analyze_sentiment(news_list):
    if not news_list: return 0
    sentiments = []
    for n in news_list:
        analysis = TextBlob(n['title'])
        sentiments.append(analysis.sentiment.polarity)
    return sum(sentiments) / len(sentiments)

# ממשק צד
ticker = st.sidebar.text_input("הכנס סימול (AAPL, NVDA, TSLA):", value="NVDA").upper()
period = st.sidebar.selectbox("טווח זמן:", ["3mo", "6mo", "1y", "5y"])

if ticker:
    data = get_stock_prices(ticker, period)
    stock_obj = yf.Ticker(ticker)
    
    if not data.empty:
        current_price = float(data['Close'].iloc[-1])
        rsi_val = float(data['RSI'].iloc[-1])
        news = stock_obj.news
        sentiment_score = analyze_sentiment(news)

        # שורת מדדים עליונה
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("מחיר", f"${current_price:.2f}")
        
        rsi_status = "נורמלי"
        if rsi_val > 70: rsi_status = "קניית יתר ⚠️"
        elif rsi_val < 30: rsi_status = "מכירת יתר ✅"
        c2.metric("מדד RSI", f"{rsi_val:.1f}", rsi_status)

        sent_label = "נייטרלי 😐"
        if sentiment_score > 0.1: sent_label = "חיובי 🔥"
        elif sentiment_score < -0.1: sent_label = "שלילי 📉"
        c3.metric("סנטימנט חדשות", sent_label)

        # לוגיקת המלצה משולבת
        if current_price > data['SMA_20'].iloc[-1] and sentiment_score > 0:
            c4.success("המלצה: BUY 🟢")
        elif current_price < data['SMA_20'].iloc[-1] and sentiment_score < 0:
            c4.error("המלצה: SELL 🔴")
        else:
            c4.warning("המלצה: HOLD 🟡")

        # גרף משולב
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="מחיר"))
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name="ממוצע 20", line=dict(color='orange', width=1)))
        st.plotly_chart(fig, use_container_width=True)

        # הצגת חדשות עם ניתוח אישי
        st.subheader("📰 חדשות אחרונות וניתוח AI")
        for item in news[:5]:
            score = TextBlob(item['title']).sentiment.polarity
            icon = "✅" if score > 0 else "❌" if score < 0 else "⚪"
            st.write(f"{icon} [{item['title']}]({item['link']})")
    else:
        st.error("לא ניתן למשוך נתונים. בדוק את הסימול.")

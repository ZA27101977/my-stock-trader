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
        data = yf.download(ticker, period=period, interval="1d", auto_adjust=True)
        if data.empty: return pd.DataFrame()
        
        # חישוב RSI ו-SMA
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        return data
    except:
        return pd.DataFrame()

# ממשק צד
ticker = st.sidebar.text_input("הכנס סימול (למשל: NVDA, AAPL):", value="NVDA").upper().strip()
period = st.sidebar.selectbox("טווח זמן:", ["3mo", "6mo", "1y", "5y"])

if ticker:
    data = get_stock_prices(ticker, period)
    stock_obj = yf.Ticker(ticker)
    
    if not data.empty:
        current_price = float(data['Close'].iloc[-1])
        rsi_val = float(data['RSI'].iloc[-1]) if not pd.isna(data['RSI'].iloc[-1]) else 50
        
        # טיפול בחדשות בצורה בטוחה (תיקון השגיאה מהצילום)
        try:
            news = stock_obj.news
            processed_news = []
            for n in news:
                title = n.get('title') or n.get('summary') # מחפש כותרת או סיכום
                link = n.get('link') or "#"
                if title:
                    processed_news.append({'title': title, 'link': link})
        except:
            processed_news = []

        # שורת מדדים
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("מחיר", f"${current_price:.2f}")
        c2.metric("מדד RSI", f"{rsi_val:.1f}")

        # ניתוח סנטימנט בטוח
        sentiment_score = 0
        if processed_news:
            scores = [TextBlob(n['title']).sentiment.polarity for n in processed_news]
            sentiment_score = sum(scores) / len(scores)
        
        sent_label = "חיובי 🔥" if sentiment_score > 0.05 else "שלילי 📉" if sentiment_score < -0.05 else "נייטרלי 😐"
        c3.metric("סנטימנט", sent_label)

        # המלצה סופית
        sma_20 = data['SMA_20'].iloc[-1]
        if current_price > sma_20 and sentiment_score > 0:
            c4.success("המלצה: BUY 🟢")
        elif current_price < sma_20 and sentiment_score < 0:
            c4.error("המלצה: SELL 🔴")
        else:
            c4.warning("המלצה: HOLD 🟡")

        # גרף
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Price"))
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name="SMA 20", line=dict(color='orange')))
        fig.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)

        # הצגת חדשות
        if processed_news:
            st.subheader("📰 חדשות וניתוח AI")
            for item in processed_news[:5]:
                st.write(f"🔗 [{item['title']}]({item['link']})")
    else:
        st.error(f"לא נמצאו נתונים עבור {ticker}.")

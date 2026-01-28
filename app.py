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
        # שינוי שיטת ההורדה לשיטה יציבה יותר
        data = yf.download(ticker, period=period, interval="1d", group_by='ticker', auto_adjust=True)
        
        if data.empty:
            return pd.DataFrame()
            
        # תיקון למקרה שהנתונים חוזרים עם Multi-index
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(1)

        # חישוב RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        return data
    except Exception as e:
        return pd.DataFrame()

# ממשק צד
ticker = st.sidebar.text_input("הכנס סימול (למשל: NVDA, AAPL, TSLA):", value="NVDA").upper().strip()
period = st.sidebar.selectbox("טווח זמן:", ["3mo", "6mo", "1y", "5y"])

if ticker:
    with st.spinner('מושך נתונים מהבורסה...'):
        data = get_stock_prices(ticker, period)
        stock_obj = yf.Ticker(ticker)
    
    if not data.empty:
        current_price = float(data['Close'].iloc[-1])
        rsi_val = float(data['RSI'].iloc[-1]) if not pd.isna(data['RSI'].iloc[-1]) else 50
        
        # משיכת חדשות בזהירות
        try:
            news = stock_obj.news
        except:
            news = []

        # שורת מדדים עליונה
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("מחיר", f"${current_price:.2f}")
        
        rsi_status = "נורמלי"
        if rsi_val > 70: rsi_status = "קניית יתר ⚠️"
        elif rsi_val < 30: rsi_status = "מכירת יתר ✅"
        c2.metric("מדד RSI", f"{rsi_val:.1f}", rsi_status)

        # ניתוח סנטימנט
        sentiment_score = 0
        if news:
            titles = [n['title'] for n in news]
            sentiment_score = sum([TextBlob(t).sentiment.polarity for t in titles]) / len(titles)
        
        sent_label = "נייטרלי 😐"
        if sentiment_score > 0.05: sent_label = "חיובי 🔥"
        elif sentiment_score < -0.05: sent_label = "שלילי 📉"
        c3.metric("סנטימנט חדשות", sent_label)

        # המלצה
        sma_20 = data['SMA_20'].iloc[-1]
        if current_price > sma_20 and sentiment_score > 0:
            c4.success("המלצה: BUY 🟢")
        elif current_price < sma_20 and sentiment_score < 0:
            c4.error("המלצה: SELL 🔴")
        else:
            c4.warning("המלצה: HOLD 🟡")

        # גרף
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="מחיר"))
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name="ממוצע 20", line=dict(color='orange', width=1.5)))
        fig.update_layout(height=500, template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # חדשות
        if news:
            st.subheader("📰 חדשות אחרונות וניתוח AI")
            for item in news[:5]:
                score = TextBlob(item['title']).sentiment.polarity
                icon = "✅" if score > 0 else "❌" if score < 0 else "⚪"
                st.write(f"{icon} [{item['title']}]({item['link']})")
    else:
        st.error(f"לא נמצאו נתונים עבור {ticker}. וודא שהסימול נכון (למשל NVDA) ונסה שוב.")

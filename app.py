import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="AI Stock Trader", layout="wide")

st.title("📈 מערכת מסחר חכמה - מניות ארה''ב")

# בחירת מניה על ידי המשתמש
ticker = st.sidebar.text_input("הכנס סימול מניה (למשל AAPL, TSLA):", value="AAPL").upper()
period = st.sidebar.selectbox("טווח זמן לגרף:", ["1mo", "3mo", "6mo", "1y", "2y", "5y"])

if ticker:
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    
    if not data.empty:
        # חישוב אינדיקטורים להמלצה
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        current_price = data['Close'].iloc[-1]
        sma_20_val = data['SMA_20'].iloc[-1]
        
        # לוגיקת המלצה
        if current_price > sma_20_val:
            recommendation = "BUY 🟢"
            advice = "המחיר מעל הממוצע הנע (מגמה חיובית)"
        else:
            recommendation = "SELL 🔴"
            advice = "המחיר מתחת לממוצע הנע (מגמה שלילית)"

        # תצוגת המלצה
        col1, col2, col3 = st.columns(3)
        col1.metric("מחיר נוכחי", f"${current_price:.2f}")
        col2.metric("המלצה", recommendation)
        col3.write(f"**הסבר:** {advice}")

        # גרף נרות יפניים
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                        open=data['Open'], high=data['High'],
                        low=data['Low'], close=data['Close'], name="Price")])
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name="SMA 20", line=dict(color='orange')))
        st.plotly_chart(fig, use_container_width=True)

        # דוחות וחדשות
        st.subheader("📊 נתונים פונדמנטליים וחדשות")
        tabs = st.tabs(["דוחות כספיים", "חדשות אחרונות"])
        
        with tabs[0]:
            st.write(stock.calendar)
            st.write("**נתוני מפתח:**")
            st.json(stock.info.get('ebitdaMargins', 'אין נתונים'))
            
        with tabs[1]:
            news = stock.news[:5]
            for item in news:
                st.write(f"🔗 [{item['title']}]({item['link']})")
    else:
        st.error("לא נמצאו נתונים עבור הסימול שהוכנס.")

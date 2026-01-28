import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="AI Stock Trader", layout="wide")

st.title("📈 מערכת מסחר חכמה - מניות ארה''ב")

# פונקציה עם Cache כדי למנוע חסימות מ-Yahoo
@st.cache_data(ttl=3600)  # שומר את המידע לשעה שלמה
def get_stock_data(ticker, period):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data, stock
    except:
        return pd.DataFrame(), None

# בחירת מניה
ticker = st.sidebar.text_input("הכנס סימול מניה (למשל AAPL, TSLA):", value="AAPL").upper()
period = st.sidebar.selectbox("טווח זמן לגרף:", ["1mo", "3mo", "6mo", "1y", "5y"])

if ticker:
    data, stock = get_stock_data(ticker, period)
    
    if not data.empty:
        # חישוב אינדיקטורים
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        current_price = data['Close'].iloc[-1]
        sma_20_val = data['SMA_20'].iloc[-1]
        
        # לוגיקת המלצה
        col1, col2, col3 = st.columns(3)
        col1.metric("מחיר נוכחי", f"${current_price:.2f}")
        
        if current_price > sma_20_val:
            col2.success("המלצה: BUY 🟢")
            col3.info("הסבר: מגמה חיובית (מעל ממוצע 20)")
        else:
            col2.error("המלצה: SELL 🔴")
            col3.info("הסבר: מגמה שלילית (מתחת לממוצע 20)")

        # גרף
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                        open=data['Open'], high=data['High'],
                        low=data['Low'], close=data['Close'], name="Price")])
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name="SMA 20", line=dict(color='orange')))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Yahoo Finance חסמו את הגישה זמנית. נסה שוב בעוד כמה דקות או החלף סימול מניה.")

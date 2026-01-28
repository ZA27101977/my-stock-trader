import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="AI Stock Trader", layout="wide")

st.title("📈 מערכת מסחר חכמה - מניות ארה''ב")

# פונקציה למשיכת נתוני מחיר בלבד (מחזירה רק DataFrame שקל לשמור ב-Cache)
@st.cache_data(ttl=600)
def get_stock_prices(ticker, period):
    try:
        data = yf.download(ticker, period=period)
        return data
    except:
        return pd.DataFrame()

# פונקציה למשיכת חדשות ודוחות (ללא Cache כדי למנוע את השגיאה מהצילום)
def get_stock_info(ticker):
    stock = yf.Ticker(ticker)
    return stock.news, stock.calendar, stock.info

# בחירת מניה
ticker = st.sidebar.text_input("הכנס סימול מניה (למשל AAPL, TSLA):", value="AAPL").upper()
period = st.sidebar.selectbox("טווח זמן לגרף:", ["1mo", "3mo", "6mo", "1y", "5y"])

if ticker:
    data = get_stock_prices(ticker, period)
    
    if not data.empty:
        # חישוב אינדיקטורים
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        current_price = float(data['Close'].iloc[-1])
        sma_20_val = float(data['SMA_20'].iloc[-1])
        
        # תצוגת המלצה
        col1, col2, col3 = st.columns(3)
        col1.metric("מחיר נוכחי", f"${current_price:.2f}")
        
        if current_price > sma_20_val:
            col2.success("המלצה: BUY 🟢")
            col3.info("הסבר: המחיר במגמת עלייה מעל ממוצע 20")
        else:
            col2.error("המלצה: SELL 🔴")
            col3.info("הסבר: המחיר במגמת ירידה מתחת לממוצע 20")

        # גרף
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                        open=data['Open'], high=data['High'],
                        low=data['Low'], close=data['Close'], name="Price")])
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name="SMA 20", line=dict(color='orange')))
        st.plotly_chart(fig, use_container_width=True)
        
        # חדשות ודוחות (בתוך Try כדי שלא יפיל את האפליקציה אם Yahoo חוסמים)
        try:
            st.subheader("📊 נתונים פונדמנטליים וחדשות")
            news, calendar, info = get_stock_info(ticker)
            
            t1, t2 = st.tabs(["חדשות אחרונות", "מידע פיננסי"])
            with t1:
                for item in news[:5]:
                    st.write(f"🔗 [{item['title']}]({item['link']})")
            with t2:
                st.write(f"**שווי שוק:** {info.get('marketCap', 'N/A')}")
                st.write(f"**מכפיל רווח (P/E):** {info.get('trailingPE', 'N/A')}")
        except:
            st.info("לא ניתן היה למשוך חדשות כרגע, אך הגרף וההמלצה מעודכנים.")

    else:
        st.warning("לא נמצאו נתונים. וודא שהסימול נכון או נסה שוב מאוחר יותר.")

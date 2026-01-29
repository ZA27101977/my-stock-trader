import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. אבטחה (נשאר זהה)
PASSWORD = "1234" 
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 כניסה למערכת")
    user_input = st.text_input("הכנס סיסמה:", type="password")
    if st.button("כניסה"):
        if user_input == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# 2. הגדרות רשימת מניות (חייב להופיע לפני הגרף!)
with st.sidebar:
    st.header("⚙️ הגדרות")
    tickers_input = st.text_area("רשימת מניות (פסיק מפריד):", value="SPY, NVDA, TSLA, AAPL")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]
    if st.button("יציאה"):
        st.session_state.authenticated = False
        st.rerun()

st.title("📈 חדר מסחר מקצועי")
st_autorefresh(interval=60000, key="fixed_v4")

# 3. טבלה חיה
watchlist_data = []
for ticker in ticker_list:
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info['last_price']
        prev_close = stock.fast_info['previous_close']
        change = ((price - prev_close) / prev_close) * 100
        watchlist_data.append({"מניה": ticker, "מחיר": f"${price:.2f}", "שינוי": f"{change:+.2f}%"})
    except: continue

if watchlist_data:
    st.table(pd.DataFrame(watchlist_data))

# 4. תיקון הגרף (ציר Y דינמי ונתוני 5 ימים)
st.subheader("📊 ניתוח גרפי מתקדם")
selected_stock = st.selectbox("בחר מניה לתצוגה:", ticker_list)

if selected_stock:
    df_chart = yf.Ticker(selected_stock).history(period="5d", interval="15m")
    if not df_chart.empty:
        fig = go.Figure()
        is_up = df_chart['Close'].iloc[-1] >= df_chart['Open'].iloc[0]
        
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart['Close'],
            line=dict(color='green' if is_up else 'red', width=3),
            fill='tozeroy',
            fillcolor='rgba(0,250,0,0.1)' if is_up else 'rgba(250,0,0,0.1)'
        ))

        fig.update_layout(
            title=f"גרף {selected_stock} - 5 ימים אחרונים",
            yaxis_title="מחיר ($)",
            template="plotly_white",
            height=450
        )
        
        # השורה שמתקנת את ה"קו הישר" - גורמת לציר Y להתמקד במחיר
        fig.update_yaxes(autorange=True, fixedrange=False)
        
        st.plotly_chart(fig, use_container_width=True)

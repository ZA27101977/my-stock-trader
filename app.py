import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. אבטחה וכניסה
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

# 2. הגדרות רשימה (בסרגל הצד)
with st.sidebar:
    st.header("⚙️ הגדרות")
    tickers_input = st.text_area("רשימת מניות (פסיק מפריד):", value="SPY, NVDA, TSLA, AAPL")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]
    if st.button("יציאה מהמערכת"):
        st.session_state.authenticated = False
        st.rerun()

st.title("📈 חדר מסחר - נתונים רציפים")
st_autorefresh(interval=60000, key="final_table_v6")

# 3. בניית הטבלה עם תיקון האינדקס ועמודות נוספות
watchlist_data = []
for ticker in ticker_list:
    try:
        stock = yf.Ticker(ticker)
        fast = stock.fast_info
        price = fast['last_price']
        change = ((price - fast['previous_close']) / fast['previous_close']) * 100
        
        watchlist_data.append({
            "מניה": ticker,
            "מחיר": f"${price:.2f}",
            "שינוי": f"{change:+.2f}%",
            "גבוה יומי": f"${fast['day_high']:.2f}",
            "נמוך יומי": f"${fast['day_low']:.2f}"
        })
    except: continue

if watchlist_data:
    df = pd.DataFrame(watchlist_data)
    # תיקון המספור: במקום 0,1,2 יהיה 1,2,3
    df.index = range(1, len(df) + 1) 
    
    st.table(df)

# 4. גרף מקצועי (כולל Pre/Post Market)
st.subheader("📊 ניתוח גרפי רציף")
selected_stock = st.selectbox("בחר מניה מהרשימה לתצוגה:", ticker_list)

if selected_stock:
    # משיכת נתונים כולל מסחר מחוץ לשעות
    df_chart = yf.Ticker(selected_stock).history(period="2d", interval="5m", prepost=True)
    
    if not df_chart.empty:
        fig = go.Figure()
        # צבע לפי מגמה מהפתיחה
        is_up = df_chart['Close'].iloc[-1] >= df_chart['Open'].iloc[0]
        
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart['Close'],
            line=dict(color='#00FF00' if is_up else '#FF3131', width=3),
            fill='tozeroy',
            fillcolor='rgba(0,250,0,0.1)' if is_up else 'rgba(250,0,0,0.1)'
        ))

        fig.update_layout(
            template="plotly_dark",
            height=500,
            yaxis_title="מחיר ($)",
            xaxis_title="זמן",
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        # מיקוד אוטומטי במחיר המניה (מונע קו ישר)
        fig.update_yaxes(autorange=True, fixedrange=False)
        
        st.plotly_chart(fig, use_container_width=True)

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

# 2. הגדרות רשימת מניות
with st.sidebar:
    st.header("⚙️ הגדרות")
    tickers_input = st.text_area("רשימת מניות (פסיק מפריד):", value="SPY, NVDA, TSLA, AAPL")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]
    if st.button("יציאה"):
        st.session_state.authenticated = False
        st.rerun()

st.title("📈 חדר מסחר - מסחר רציף (24h)")
st_autorefresh(interval=60000, key="full_day_v5")

# 3. טבלה חיה
watchlist_data = []
for ticker in ticker_list:
    try:
        stock = yf.Ticker(ticker)
        # משיכת מחיר כולל מסחר מאוחר
        price = stock.fast_info['last_price']
        prev_close = stock.fast_info['previous_close']
        change = ((price - prev_close) / prev_close) * 100
        watchlist_data.append({"מניה": ticker, "מחיר": f"${price:.2f}", "שינוי": f"{change:+.2f}%"})
    except: continue

if watchlist_data:
    st.table(pd.DataFrame(watchlist_data))

# 4. גרף כולל Pre-Market ו-After-Hours
st.subheader("📊 ניתוח גרפי (כולל מסחר מחוץ לשעות)")
selected_stock = st.selectbox("בחר מניה לתצוגה:", ticker_list)

if selected_stock:
    # השינוי המרכזי: prepost=True מאפשר לראות את המסחר המאוחר והמוקדם
    df_chart = yf.Ticker(selected_stock).history(period="2d", interval="5m", prepost=True)
    
    if not df_chart.empty:
        fig = go.Figure()
        
        # צבע הקו
        is_up = df_chart['Close'].iloc[-1] >= df_chart['Open'].iloc[0]
        
        fig.add_trace(go.Scatter(
            x=df_chart.index, 
            y=df_chart['Close'],
            line=dict(color='#00FF00' if is_up else '#FF3131', width=2),
            fill='tozeroy',
            fillcolor='rgba(0,250,0,0.05)' if is_up else 'rgba(250,0,0,0.05)',
            name="מחיר בזמן אמת"
        ))

        fig.update_layout(
            title=f"גרף רציף: {selected_stock}",
            xaxis_title="זמן (שעון מקומי)",
            yaxis_title="מחיר ($)",
            template="plotly_dark", # העברתי למצב כהה - נראה יותר טוב למסחר בלילה
            height=500,
            hovermode="x unified"
        )
        
        # מוודא שציר Y לא קופץ לאפס וממוקד במחיר
        fig.update_yaxes(autorange=True, fixedrange=False, gridcolor='gray')
        fig.update_xaxes(showgrid=True, gridcolor='gray')
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("ממתין לנתוני מסחר...")

import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 1. אבטחה
PASSWORD = "1234" 
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 כניסה למערכת")
    user_input = st.text_input("סיסמה:", type="password")
    if st.button("כניסה"):
        if user_input == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# 2. פונקציית טלגרם
def send_telegram(message):
    token = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
    chat_id = "1054735794"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

# ריענון כל דקה
st_autorefresh(interval=60000, key="fancy_charts_v3")

st.title("📈 חדר מסחר מקצועי")

# 3. סרגל צד
with st.sidebar:
    st.header("⚙️ הגדרות")
    tickers_input = st.text_area("רשימת מניות (פסיק מפריד):", value="SPY, NVDA, TSLA, AAPL")
    ticker_list = [t.strip().upper() for t in tickers_input.split(",")]
    threshold = st.slider("התראת שינוי חריג (%):", 1.0, 10.0, 5.0)
    st.divider()
    if st.button("יציאה"):
        st.session_state.authenticated = False
        st.rerun()

# 4. טבלת נתונים חיה
watchlist_data = []
for ticker in ticker_list:
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info['last_price']
        prev_close = stock.fast_info['previous_close']
        change = ((price - prev_close) / prev_close) * 100
        watchlist_data.append({"מניה": ticker, "מחיר": f"${price:.2f}", "שינוי": f"{change:+.2f}%", "raw_change": change})
        
        # סינון הודעות חכם
        if abs(change) >= threshold:
            alert_key = f"sent_{ticker}_{pd.Timestamp.now().hour}"
            if alert_key not in st.session_state:
                send_telegram(f"⚠️ <b>תנועה חריגה ב-{ticker}!</b>\nמחיר: ${price:.2f}\nשינוי: {change:+.2f}%")
                st.session_state[alert_key] = True
    except:
        continue

if watchlist_data:
    df = pd.DataFrame(watchlist_data)
    # עיצוב הטבלה עם צבעים לשינוי
    def color_change(val):
        color = 'red' if '-' in val else 'green'
        return f'color: {color}'
    st.table(df[["מניה", "מחיר", "שינוי"]].style.applymap(color_change, subset=['שינוי']))

# 5. גרף Plotly מעוצב (עבור המניה הראשונה ברשימה או בחירה)
st.subheader("📊 ניתוח גרפי מתקדם")
selected_stock = st.selectbox("בחר מניה לתצוגת גרף:", ticker_list)

if selected_stock:
    df_chart = yf.Ticker(selected_stock).history(period="1d", interval="5m")
    if not df_chart.empty:
        # יצירת הגרף המעוצב
        fig = go.Figure()
        
        # קביעת צבע הקו (ירוק אם המחיר הנוכחי גבוה ממחיר הפתיחה)
        line_color = 'green' if df_chart['Close'][-1] >= df_chart['Open'][0] else 'red'
        
        fig.add_trace(go.Scatter(
            x=df_chart.index, 
            y=df_chart['Close'],
            mode='lines',
            name='מחיר סגירה',
            line=dict(color=line_color, width=3),
            fill='tozeroy', # הוספת צל מתחת לקו
            fillcolor='rgba(0, 255, 0, 0.1)' if line_color == 'green' else 'rgba(255, 0, 0, 0.1)'
        ))

        fig.update_layout(
            title=f"תנועת המחיר של {selected_stock} היום",
            xaxis_title="זמן",
            yaxis_title="מחיר ($)",
            plot_bgcolor="white",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            height=400
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        
        st.plotly_chart(fig, use_container_width=True)

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from textblob import TextBlob

st.set_page_config(page_title="AI Stock Scanner & Financials", layout="wide")

st.title("🚀 סורק מניות ומערכת ניתוח דוחות")

@st.cache_data(ttl=3600) # דוחות משתנים פחות, נשמור לשעה
def get_financials(ticker):
    try:
        stock = yf.Ticker(ticker)
        # משיכת דוח רווח והפסד שנתי
        df_finance = stock.financials
        # משיכת תאריכי דוחות קרובים
        calendar = stock.calendar
        return df_finance, calendar
    except:
        return pd.DataFrame(), None

@st.cache_data(ttl=600)
def get_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True)
        if df.empty: return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        return df
    except:
        return pd.DataFrame()

def get_sentiment_score(ticker):
    try:
        s = yf.Ticker(ticker)
        news = s.news
        if not news: return 0
        titles = [n.get('title', '') for n in news[:5]]
        scores = [TextBlob(t).sentiment.polarity for t in titles if t]
        return sum(scores) / len(scores) if scores else 0
    except:
        return 0

# --- תפריט צד ---
st.sidebar.header("🔍 הגדרות")
ticker = st.sidebar.text_input("הכנס סימול (למשל TSLA, NVDA):", value="NVDA").upper().strip()
period = st.sidebar.selectbox("טווח זמן לגרף:", ["6mo", "1y", "2y"])

if ticker:
    data = get_data(ticker, period)
    
    if not data.empty:
        curr_price = float(data['Close'].iloc[-1])
        sent_val = get_sentiment_score(ticker)
        sma_val = data['SMA_20'].iloc[-1]
        
        # מדדים עליונים
        c1, c2, c3 = st.columns(3)
        c1.metric("מחיר סגירה", f"${curr_price:.2f}")
        s_text = "חיובי 🔥" if sent_val > 0.05 else "שלילי 📉" if sent_val < -0.05 else "נייטרלי 😐"
        c2.metric("סנטימנט", s_text)
        
        if curr_price > sma_val and sent_val > 0:
            c3.success("המלצה: BUY 🟢")
        elif curr_price < sma_val and sent_val < 0:
            c3.error("המלצה: SELL 🔴")
        else:
            c3.warning("המלצה: HOLD 🟡")

        # גרף
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Price")])
        fig.update_layout(template="plotly_dark", height=400, margin=dict(t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

        # --- מגזר דוחות כספיים ---
        st.divider()
        st.subheader(f"📊 דוחות כספיים וביצועים - {ticker}")
        
        tab1, tab2 = st.tabs(["📑 דוח רווח והפסד (Financials)", "📅 לוח שנה של דוחות (Earnings)"])
        
        fin_df, cal_info = get_financials(ticker)
        
        with tab1:
            if not fin_df.empty:
                # מציג את 4 השנים האחרונות בצורה קריאה
                st.dataframe(fin_df.style.format("{:,.0f}"), use_container_width=True)
            else:
                st.info("לא נמצאו נתונים פיננסיים זמינים כרגע.")
                
        with tab2:
            if cal_info is not None:
                # הצגת תאריכי דוחות קרובים ותחזיות (אם יש)
                st.write("**תאריכי דוחות קרובים ותחזית EPS:**")
                st.json(cal_info)
            else:
                st.info("לא נמצא מידע על דוחות קרובים.")
    else:
        st.error(f"לא הצלחנו למשוך נתונים עבור {ticker}.")

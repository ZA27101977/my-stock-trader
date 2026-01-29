import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go

# --- שלב 1: ניקוי והגדרת המפתח ---
# המפתח שלך מהתמונה המסתיים ב-olo4
RAW_KEY = "AIzaSyDB0p-o0pYWnS970VFvYFzUN0n8eU_olo4"
API_KEY = RAW_KEY.strip() # מסיר רווחים שעלולים לגרום ל-API_KEY_INVALID

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאה באתחול ה-AI: {e}")

# --- שלב 2: פונקציית ניתוח עם הגנה מ-KeyError ---
def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        if not news:
            return "לא נמצאו חדשות לניתוח."
        
        # פתרון ל-KeyError: חילוץ כותרות בצורה גמישה
        titles = []
        for item in news[:5]:
            # בודק אם הכותרת נמצאת במיקום הישן או החדש של Yahoo
            title = item.get('title') or (item.get('content', {}).get('title') if isinstance(item.get('content'), dict) else "אין כותרת")
            titles.append(title)
        
        prompt = f"נתח את המניה {ticker} לפי הכותרות: {titles}. תן המלצה קצרה בעברית."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"שגיאה בתהליך הניתוח: {str(e)}"

# --- שלב 3: ממשק המשתמש ---
st.title("📊 חדר מסחר מקצועי (תיקון סופי)")

# טבלת מניות עם תיקון מספור (מתחיל מ-1)
ticker_list = ["SPY", "NVDA", "TSLA", "AAPL"]
data = []
for t in ticker_list:
    s = yf.Ticker(t).fast_info
    data.append({"מניה": t, "מחיר": f"${s['last_price']:.2f}", "שינוי": f"{((s['last_price']-s['previous_close'])/s['previous_close'])*100:+.2f}%"})

df = pd.DataFrame(data)
df.index = range(1, len(df) + 1) # תיקון המספור שביקשת
st.table(df)

# אזור הניתוח
selected = st.selectbox("בחר מניה לניתוח AI:", ticker_list)
if st.button(f"בצע ניתוח עומק ל-{selected}"):
    with st.spinner("ה-AI מנתח..."):
        res = analyze_stock(selected)
        st.info(res)

# גרף תקין
df_chart = yf.Ticker(selected).history(period="1d", interval="5m")
if not df_chart.empty:
    fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'])])
    fig.update_layout(title=f"גרף תוך-יומי: {selected}", template="plotly_dark")
    st.plotly_chart(fig)

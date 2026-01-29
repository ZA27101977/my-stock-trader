import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# 1. הגדרות דף וריענון אוטומטי (30 שניות)
st.set_page_config(page_title="AI Live Trader Israel", layout="wide")
st_autorefresh(interval=30 * 1000, key="final_production_v1")

# 2. פונקציית טלגרם יציבה
def send_telegram(message):
    token = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY"
    chat_id = 1054735794 
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            st.sidebar.success(f"✅ נשלח ב-{datetime.datetime.now().strftime('%H:%M:%S')}")
        else:
            error_msg = response.json().get('description', 'Unknown')
            st.sidebar.error(f"❌ שגיאת טלגרם: {error_msg}")
    except Exception as e:
        st.sidebar.error(f"⚠️ תקלה: {e}")

# 3. ניהול זמן ישראל (UTC+2)
israel_now = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
current_time = israel_now.strftime('%H:%M:%S')

st.title("🚀 מסחר חכם בזמן אמת (ריענון כל 30 שניות)")
st.write(f"🕒 שעה בישראל: **{current_time}**")

# 4. סרגל צד (Sidebar)
with st.sidebar:
    st.header("⚙️ הגדרות מניה")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    st.subheader("🔔 הגדר התראה לנייד")
    target_up = st.number_input("שלח הודעה כשהמחיר עולה מעל ($):", value=0.0, step=0.01)
    target_down = st.number_input("שלח הודעה כשהמחיר יורד מתחת ($):", value=0.0, step=0.01)
    
    if st.button("שלח הודעת בדיקה עכשיו"):
        send_telegram("👋 בדיקה מהאפליקציה! המערכת מחוברת.")

# 5. משיכת נתונים וניתוח
if ticker:
    try:
        stock = yf.Ticker(ticker)
        
        # משיכת מחיר "חי" מרשת Yahoo
        live_info = stock.fast_info
        price = live_info['last_price']
        prev_close = live_info['previous_close']
        change_pct = ((price / prev_close) - 1) * 100

        # הצגת המחיר
        c_p, c_c = st.columns(2)
        c_p.metric(f"מחיר {ticker}", f"${price:.2f}")
        c_c.metric("שינוי יומי", f"{change_pct:.2f}%")

        # בדיקת תנאי התראה ושליחה
        if target_up > 0 and price >= target_up:
            send_telegram(f"<b>🚀 יעד הושג!</b>\n{ticker} חצתה את ${target_up}\nמחיר נוכחי: ${price:.2f}")
            st.toast("התראה נשלחה!")
        
        if target_down > 0 and price <= target_down:
            send_telegram(f"<b>📉 יעד ירידה!</b>\n{ticker} ירדה מתחת ל-${target_down}\nמחיר נוכחי: ${price:.2f}")
            st.toast("התראה נשלחה!")

        # גרף דקות
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            st.line_chart(hist['Close'], height=250)

        # 6. ניתוח AI
        st.divider()
        st.subheader("🤖 ניתוח חכם")
        col1, col2 = st.columns(2)
        
        with col1:
            news = stock.news
            sent = sum([TextBlob(n.get('title', '')).sentiment.polarity for n in news[:5]]) / 5 if news else 0
            st.write("**סנטימנט חדשות:** " + ("חיובי 🔥" if sent > 0.05 else "שלילי 📉" if sent < -0.05 else "נייטרלי 😐"))
            
        with col2:
            fin = stock.financials
            growth = not fin.empty and 'Total Revenue' in fin.index and len(fin.loc['Total Revenue']) > 1 and fin.loc['Total Revenue'].iloc[0] > fin.loc['Total Revenue'].iloc[1]
            st.write("**צמיחה בהכנסות:** " + ("כן ✅" if growth else "לא ❌"))

    except Exception as e:
        st.error(f"לא ניתן למשוך נתונים עבור {ticker}. וודא שהסימול נכון.")

st.caption(f"Last Sync: {current_time} | Market Status: Open (Mon-Fri)")

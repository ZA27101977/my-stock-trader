import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# 1. הגדרות דף וריענון אוטומטי (30 שניות)
st.set_page_config(page_title="AI Live Trader Israel", layout="wide")
st_autorefresh(interval=30 * 1000, key="final_telegram_fix")

# 2. פונקציית טלגרם משופרת - שליחת JSON
def send_telegram(message):
    token = "8553256276:AAG2AWkV_cssOAnlWe8MUChR-MQ8VgFJ1ZY"
    chat_id = 1054735794  # המזהה שלך כפי שחילצנו
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        # שימוש ב-json=payload מבטיח תאימות מלאה לטלגרם
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            st.sidebar.success(f"✅ הודעה נשלחה ב-{datetime.datetime.now().strftime('%H:%M:%S')}")
        else:
            # אם יש שגיאה, נציג אותה בסידבר כדי להבין מה קרה
            error_desc = response.json().get('description', 'Unknown Error')
            st.sidebar.error(f"❌ שגיאת טלגרם: {error_desc}")
    except Exception as e:
        st.sidebar.error(f"⚠️ תקלת תקשורת: {e}")

# 3. שעון ישראל (UTC+2)
israel_now = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
current_time = israel_now.strftime('%H:%M:%S')

st.title("🚀 מערכת מסחר AI בזמן אמת")
st.write(f"🕒 זמן עדכון אחרון (ישראל): **{current_time}**")

# 4. סרגל צד (Sidebar)
with st.sidebar:
    st.header("⚙️ הגדרות מניה")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    st.subheader("🔔 הגדר התראה לנייד")
    target_up = st.number_input("שלח הודעה כשהמחיר עולה מעל ($):", value=0.0, step=0.01)
    target_down = st.number_input("שלח הודעה כשהמחיר יורד מתחת ($):", value=0.0, step=0.01)
    
    if st.button("שלח הודעת בדיקה עכשיו"):
        send_telegram("👋 בדיקה מהאפליקציה! אם אתה רואה את זה, הכל עובד.")

# 5. משיכת נתונים וניתוח (ללא Cache למחיר חי)
if ticker:
    try:
        stock = yf.Ticker(ticker)
        
        # משיכת מחיר "חי"
        live_info = stock.fast_info
        price = live_info['last_price']
        prev_close = live_info['previous_close']
        change_pct = ((price / prev_close) - 1) * 100

        # תצוגה
        col_price, col_change = st.columns(2)
        col_price.metric(f"מחיר {ticker}", f"${price:.2f}")
        col_change.metric("שינוי יומי", f"{change_pct:.2f}%")

        # בדיקת התראות ושליחה
        if target_up > 0 and price >= target_up:
            send_telegram(f"<b>🚀 יעד עלייה הושג!</b>\nהמניה: {ticker}\nמחיר: ${price:.2f}")
            st.toast("נשלחה התראת עלייה!")
        
        if target_down > 0 and price <= target_down:
            send_telegram(f"<b>📉 הגנת הפסד הופעלה!</b>\nהמניה: {ticker}\nמחיר: ${price:.2f}")
            st.toast("נשלחה התראת ירידה!")

        # גרף דקות
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            st.line_chart(hist['Close'], height=250)

        # 6. ניתוח AI (סנטימנט ודוחות)
        st.divider()
        st.subheader("🤖 ניתוח חכם")
        c1, c2 = st.columns(2)
        
        with c1:
            news = stock.news
            sent = sum([TextBlob(n.get('title', '')).sentiment.polarity for n in news[:5]]) / 5 if news else 0
            st.write("**סנטימנט:** " + ("חיובי 🔥" if sent > 0.05 else "שלילי 📉" if sent < -0.05 else "נייטרלי 😐"))
            
        with c2:
            fin = stock.financials
            growth = not fin.empty and 'Total Revenue' in fin.index and fin.loc['Total Revenue'].iloc[0] > fin.loc['Total Revenue'].iloc[1]
            st.write("**צמיחה בדוחות:** " + ("כן ✅" if growth else "לא ❌"))

    except Exception as e:
        st.error(f"שגיאה במשיכת נתונים עבור {ticker}. וודא שהסימול נכון.")

st.caption(f"Status: Connected | Update Frequency: 30s")

import streamlit as st
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
import datetime

# הגדרות דף
st.set_page_config(page_title="Stock AI Trader", layout="wide")
st_autorefresh(interval=30000, key="success_v1")

def send_telegram(message):
    # הטוקן המדויק מהתמונה שלך
    token = "8583393995:AAEhmuHn0shSH2QSa-U_MvVf7SvIo0tws0Q"
    # ה-ID המדויק מה-JSON שלך
    chat_id = "1054735794"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        # שליחה ישירה
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            st.sidebar.success("✅ הודעה נשלחה לטלפון!")
        else:
            st.sidebar.error(f"❌ שגיאה: {response.json().get('description')}")
    except Exception as e:
        st.sidebar.error(f"⚠️ תקלה בחיבור: {e}")

# זמן ישראל
israel_now = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
st.title("📈 מערכת מעקב מניות חכמה")
st.write(f"🕒 עדכון אחרון: **{israel_now.strftime('%H:%M:%S')}**")

# סרגל צד
with st.sidebar:
    st.header("⚙️ הגדרות")
    ticker = st.text_input("סימול מניה (למשל NVDA):", value="NVDA").upper().strip()
    st.divider()
    target_up = st.number_input("התראת מחיר מעל ($):", value=0.0, step=0.01)
    
    if st.button("🚀 שלח בדיקה עכשיו"):
        send_telegram(f"<b>בדיקת חיבור!</b>\nהמערכת מחוברת בהצלחה לבוט שלך.")

# הצגת נתונים
if ticker:
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info['last_price']
        
        st.metric(f"מחיר {ticker}", f"${price:.2f}")

        # התראה אוטומטית
        if target_up > 0 and price >= target_up:
            send_telegram(f"🚀 <b>יעד הושג!</b>\nהמניה {ticker} הגיעה ל-${price:.2f}")
            st.toast("התראה נשלחה!")

        # גרף
        data = stock.history(period="1d", interval="1m")
        if not data.empty:
            st.line_chart(data['Close'])
            
    except Exception as e:
        st.error(f"לא ניתן למשוך נתונים. וודא שהסימול {ticker} תקין.")

st.caption("מחובר לבוט: @eytanzafar_bot")

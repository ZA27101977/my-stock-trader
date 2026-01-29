import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות בסיס ---
PASSWORD = "eitan2026" 
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

# רשימות הנכסים המלאות
STOCKS = ["AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "META", "GOOGL", "NFLX", "AMD", "INTC", "PLTR", "BABA", "COIN", "MARA", "JPM", "BAC", "V", "MA", "DIS", "NKE", "XOM", "CVX", "LLY", "UNH", "COST"]
ETFS = ["SPY", "QQQ", "DIA", "IWM", "VOO", "VTI", "SMH", "SOXX", "IBIT", "FBTC", "ARKK", "XLF", "XLK", "XLV", "XLE", "XLI", "GLD", "SLV", "TLT", "BITO", "EEM", "VEU", "VNQ", "SCHD", "VIG"]

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 כניסה מאובטחת - איתן")
        pwd = st.text_input("הכנס סיסמה:", type="password")
        if st.button("התחבר"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("סיסמה שגויה")
        return False
    return True

if check_password():
    genai.configure(api_key=API_KEY.strip())
    model = genai.GenerativeModel('gemini-1.5-flash')

    def send_telegram(msg):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=5)
        except: pass

    st.set_page_config(page_title="Eitan's Terminal", layout="wide")
    st_autorefresh(interval=60000, key="v22_refresh")

    if 'selected' not in st.session_state: st.session_state.selected = "SPY"

    # --- 2. סידבר (תפריט צד) ---
    with st.sidebar:
        st.title("🛠️ תפריט שליטה")
        search = st.text_input("🔎 חפש סימול חופשי:").upper()
        if st.button("טען"): st.session_state.selected = search
        
        st.divider()
        st.subheader("📌 בחירה מהירה")
        all_options = STOCKS + ETFS
        choice = st.selectbox("בחר מהרשימה המלאה:", [""] + sorted(all_options))
        if choice: st.session_state.selected = choice

        st.divider()
        st.subheader("⭐ סורק טלגרם")
        fav_input = st.text_area("מניות למעקב אוטומטי (פסיק):", value="NVDA, TSLA, SPY, QQQ, SMH")
        fav_list = [x.strip().upper() for x in fav_input.split(",")]

    # --- 3. תצוגה מרכזית ---
    curr = st.session_state.selected
    st.title(f"🚀 ניתוח נכס: {curr}")

    col_chart, col_ai = st.columns([2, 1])
    
    with col_chart:
        hist = yf.Ticker(curr).history(period="1d", interval="5m")
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        
    with col_ai:
        st.subheader("🤖 פעולת AI")
        if st.button("בצע ניתוח טכני + המלצה"):
            with st.spinner("מנתח גרף וחדשות..."):
                try:
                    stock = yf.Ticker(curr)
                    h = stock.history(period="1d", interval="15m").tail(5).to_string()
                    news = stock.news[0].get('title', "") if stock.news else "אין"
                    prompt = f"Analyze {curr}. Price data: {h}. News: {news}. Give Buy/Sell recommendation in Hebrew."
                    resp = model.generate_content(prompt)
                    st.info(resp.text)
                    send_telegram(f"🚀 <b>סיגנל ל-{curr}:</b>\n{resp.text}")
                except: st.error("נסה שוב בעוד דקה.")

    # --- 4. טבלאות ריכוז (כאן אתה תראה את כולם!) ---
    st.divider()
    st.header("📋 ריכוז נתוני שוק")
    
    tab1, tab2 = st.tabs(["📊 כל המניות (25)", "🌍 כל תעודות הסל (25)"])
    
    def get_table_data(list_of_tickers):
        rows = []
        for t in list_of_tickers:
            try:
                inf = yf.Ticker(t).fast_info
                p, c = inf['last_price'], ((inf['last_price'] - inf['previous_close']) / inf['previous_close']) * 100
                rows.append({"סימול": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%", "מגמה": "🟢" if c > 0 else "🔴"})
            except: continue
        return pd.DataFrame(rows)

    with tab1:
        st.dataframe(get_table_data(STOCKS), use_container_width=True, height=400)

    with tab2:
        st.dataframe(get_table_data(ETFS), use_container_width=True, height=400)mport streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות בסיס ואבטחה ---
PASSWORD = "eitan2026" 
API_KEY = "AIzaSyBHDnYafyU_ewuZj583NwENVrMNQyFbIvY"
TELEGRAM_TOKEN = "8583393995:AAGdpAx-wh2l6pB2Pq4FL5lOhQev1GFacAk"
CHAT_ID = "1054735794"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 כניסה למערכת הניתוח - איתן")
        pwd = st.text_input("הכנס סיסמה:", type="password")
        if st.button("התחבר"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("סיסמה שגויה")
        return False
    return True

if check_password():
    # --- 2. אתחול AI ופונקציות ---
    genai.configure(api_key=API_KEY.strip())
    model = genai.GenerativeModel('gemini-1.5-flash')

    def send_telegram(message):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
        except: pass

    # --- 3. סורק חכם: מנתח גרף + חדשות (כמו בסרטון) ---
    def smart_scanner(ticker_list):
        if "last_scan" not in st.session_state: st.session_state.last_scan = {}
        
        for t in ticker_list:
            try:
                stock = yf.Ticker(t)
                hist = stock.history(period="1d", interval="15m").tail(5) # 5 הנרות האחרונים
                if hist.empty: continue
                
                # תמצית נתוני גרף ל-AI
                current_price = hist['Close'].iloc[-1]
                high_price = hist['High'].max()
                low_price = hist['Low'].min()
                
                # בדיקה אם יש חדשה חדשה
                news = stock.news[:1]
                title = news[0].get('title', "") if news else "אין חדשות מיוחדות"
                
                if st.session_state.last_scan.get(t) != title:
                    time.sleep(1)
                    # פרומפט שמשלב טכני + פונדמנטלי
                    prompt = f"""נתח את המניה {t} לפי הנתונים:
                    מחיר נוכחי: {current_price:.2f}
                    טווח יומי אחרון: {low_price:.2f} עד {high_price:.2f}
                    כותרת חדשות: {title}
                    
                    האם לפי כיוון המחיר והחדשות יש כאן הזדמנות? 
                    ענה בעברית קצרה: הסבר מה רואים בגרף ובחדשות, ובסוף המלצה ברורה: 
                    'מומלץ לקנות' (אם יש פריצה/חדשות טובות), 'מומלץ למכור' (נפילה/חדשות רעות) או 'להמתין'.
                    אם אין תנועה מעניינת, ענה 'IGNORE'."""
                    
                    resp = model.generate_content(prompt)
                    if "IGNORE" not in resp.text.upper():
                        send_telegram(f"📉 <b>ניתוח טכני וסיגנל: {t}</b>\n{resp.text}")
                    st.session_state.last_scan[t] = title
            except: continue

    # --- 4. הגדרות ממשק ---
    st.set_page_config(page_title="Eitan's Technical Terminal", layout="wide")
    st_autorefresh(interval=60000, key="v21_refresh")

    # רשימות מורחבות (20+ מניות ו-20+ ETFs)
    STOCKS = ["AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "META", "GOOGL", "NFLX", "AMD", "INTC", "PLTR", "BABA", "COIN", "MARA", "JPM", "BAC", "V", "MA", "DIS", "NKE", "XOM", "CVX", "LLY", "UNH", "COST"]
    ETFS = ["SPY", "QQQ", "DIA", "IWM", "VOO", "VTI", "SMH", "SOXX", "IBIT", "FBTC", "ARKK", "XLF", "XLK", "XLV", "XLE", "XLI", "GLD", "SLV", "TLT", "BITO", "EEM", "VEU", "VNQ", "SCHD", "VIG"]

    if 'selected' not in st.session_state: st.session_state.selected = "SPY"

    with st.sidebar:
        st.title("📊 ניתוח טכני")
        search = st.text_input("חפש סימול:").upper()
        if st.button("נתח נכס"): st.session_state.selected = search
        
        st.subheader("מניות")
        s_choice = st.selectbox("בחר מניה:", [""] + STOCKS)
        if s_choice: st.session_state.selected = s_choice
        
        st.subheader("תעודות סל")
        e_choice = st.selectbox("בחר ETF:", [""] + ETFS)
        if e_choice: st.session_state.selected = e_choice
        
        st.divider()
        fav_input = st.text_area("⭐ רשימת סריקה לטלגרם:", value="NVDA, TSLA, SPY, QQQ, SMH")
        fav_list = [x.strip().upper() for x in fav_input.split(",")]

    # הפעלת הסורק
    smart_scanner(fav_list)

    # --- 5. תצוגה מרכזית ---
    curr = st.session_state.selected
    st.title(f"🔍 חדר מסחר - ניתוח {curr}")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("📊 דאשבורד")
        data = []
        for t in fav_list[:10]:
            try:
                inf = yf.Ticker(t).fast_info
                p, c = inf['last_price'], ((inf['last_price'] - inf['previous_close']) / inf['previous_close']) * 100
                data.append({"נכס": t, "מחיר": f"${p:.2f}", "שינוי": f"{c:+.2f}%"})
            except: continue
        st.table(pd.DataFrame(data))

    with col2:
        # הצגת הגרף
        hist = yf.Ticker(curr).history(period="1d", interval="5m")
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

    # כפתור ניתוח לפי הסרטון
    if st.button(f"🚀 בצע ניתוח גרף וחדשות מלא ל-{curr}"):
        with st.spinner("ה-AI קורא את הגרף..."):
            try:
                stock = yf.Ticker(curr)
                h = stock.history(period="5d", interval="60m")
                prompt = f"Analyze the trend for {curr} based on last 5 days data: {h.tail().to_string()}. Consider recent news. Be decisive: Buy or Sell. Hebrew."
                resp = model.generate_content(prompt)
                st.info(resp.text)
                send_telegram(f"🚀 <b>ניתוח טכני מלא ({curr}):</b>\n{resp.text}")
            except: st.error("נסה שוב בעוד דקה.")

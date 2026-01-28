import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob

st.set_page_config(page_title="Stock Buy Advisor", layout="wide")

st.title("🤖 יועץ בינה מלאכותית לקניית מניות")
st.write("המערכת מנתחת דוחות כספיים וחדשות בזמן אמת כדי לתת המלצה.")

def get_recommendation(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        # 1. ניתוח חדשות (סנטימנט)
        news = stock.news
        sent_score = 0
        if news:
            scores = [TextBlob(n.get('title', '')).sentiment.polarity for n in news[:5]]
            sent_score = sum(scores) / len(scores)
        
        # 2. ניתוח דוחות (צמיחה)
        fin = stock.financials
        growth_status = "Unknown"
        if not fin.empty and 'Total Revenue' in fin.index:
            revs = fin.loc['Total Revenue']
            if len(revs) > 1:
                growth = (revs.iloc[0] / revs.iloc[1]) - 1
                growth_status = "Positive" if growth > 0 else "Negative"

        # 3. ניתוח טכני (מגמה)
        hist = stock.history(period="50d")
        current_price = hist['Close'].iloc[-1]
        avg_price = hist['Close'].mean()
        trend = "Up" if current_price > avg_price else "Down"

        return {
            "price": current_price,
            "sent_score": sent_score,
            "growth": growth_status,
            "trend": trend
        }
    except:
        return None

# --- ממשק המלצה ---
ticker = st.text_input("הכנס סימול מניה (למשל: NVDA, MSFT, GOOGL):", value="NVDA").upper().strip()

if ticker:
    with st.spinner('מנתח נתונים וחדשות...'):
        rec = get_recommendation(ticker)
    
    if rec:
        st.subheader(f"📋 סיכום המלצה עבור {ticker}")
        
        # יצירת לוגיקה פשוטה להמלצה
        score = 0
        if rec['sent_score'] > 0.05: score += 1
        if rec['growth'] == "Positive": score += 1
        if rec['trend'] == "Up": score += 1

        # הצגת התוצאה הסופית בצורה בולטת
        if score == 3:
            st.success(f"🔥 המלצה חזקה: קנייה (BUY) - כל המדדים (חדשות, דוחות, מחיר) חיוביים!")
        elif score == 2:
            st.warning(f"⚖️ המלצה: החזק (HOLD) - רוב המדדים חיוביים, אך יש סיכון מסוים.")
        else:
            st.error(f"⚠️ המלצה: הימנע (AVOID) - המדדים מראים חולשה בחדשות או בדוחות.")

        # פירוט הסיבות
        st.write("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            icon = "✅" if rec['sent_score'] > 0.05 else "❌"
            st.write(f"{icon} **חדשות:** " + ("חיוביות" if rec['sent_score'] > 0.05 else "שליליות/נייטרליות"))
        
        with col2:
            icon = "✅" if rec['growth'] == "Positive" else "❌"
            st.write(f"{icon} **דוחות כספיים:** " + ("צמיחה בהכנסות" if rec['growth'] == "Positive" else "אין צמיחה"))

        with col3:
            icon = "✅" if rec['trend'] == "Up" else "❌"
            st.write(f"{icon} **מגמת מחיר:** " + ("במגמת עלייה" if rec['trend'] == "Up" else "במגמת ירידה"))
    else:
        st.error("לא ניתן לנתח את המניה. וודא שהסימול נכון.")

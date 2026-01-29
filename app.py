import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# (חלק האבטחה והטלגרם נשאר אותו דבר...)

st.subheader("📊 ניתוח גרפי מתקדם")

# תיבת בחירה מתוך הרשימה שלך
selected_stock = st.selectbox("בחר מניה מהרשימה כדי לראות את הגרף שלה:", ticker_list)

if selected_stock:
    # משיכת נתונים ל-5 הימים האחרונים כדי לוודא שהגרף לא יהיה ריק
    stock_data = yf.Ticker(selected_stock)
    df_chart = stock_data.history(period="5d", interval="15m")
    
    if not df_chart.empty:
        fig = go.Figure()
        
        # קביעת צבע לפי מחיר סגירה אחרון מול פתיחה
        is_up = df_chart['Close'].iloc[-1] >= df_chart['Open'].iloc[0]
        line_color = 'green' if is_up else 'red'
        
        fig.add_trace(go.Scatter(
            x=df_chart.index, 
            y=df_chart['Close'],
            line=dict(color=line_color, width=2),
            fill='tozeroy',
            fillcolor='rgba(0,255,0,0.1)' if is_up else 'rgba(255,0,0,0.1)',
            name=selected_stock
        ))

        fig.update_layout(
            title=f"גרף 5 ימים: {selected_stock}",
            template="plotly_white",
            height=450,
            hovermode="x unified"
        )
        
        # תיקון לציר ה-Y כדי שלא יתחיל מ-0 (ככה הגרף לא ייראה כמו קו ישר)
        fig.update_yaxes(autorange=True, fixedrange=False)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"לא נמצאו נתונים עבור {selected_stock}. נסה שוב בעוד כמה דקות.")

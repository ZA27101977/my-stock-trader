import streamlit as st
import google.generativeai as genai

# בדיקת המפתח הספציפי מהתמונה שלך
# העתקתי אותו תו תו מהצילום (המסתיים ב-olo4)
TEST_KEY = "AIzaSyDB0p-o0pYWnS970VFvYFzUN0n8eU_olo4"

st.title("🧪 בדיקת תקינות מפתח AI")

try:
    genai.configure(api_key=TEST_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if st.button("לחץ כאן לבדיקת חיבור"):
        with st.spinner("שולח שאילתת בדיקה לגוגל..."):
            response = model.generate_content("תגיד שלום בבקשה")
            st.success("✅ המפתח עובד! ה-AI ענה:")
            st.write(response.text)
            st.balloons()
except Exception as e:
    st.error(f"❌ המפתח עדיין לא תקין. השגיאה:")
    st.code(str(e))

st.info("אם מופיעה שגיאת 400, המפתח לא הועתק נכון או שהוא עדיין בסטטוס 'Pending' במערכת של גוגל.")

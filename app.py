import streamlit as st
import requests
import time
import gspread
import yaml
from yaml.loader import SafeLoader
from oauth2client.service_account import ServiceAccountCredentials
import streamlit_authenticator as stauth

# --------- UI & Page Setup ----------
st.set_page_config(page_title="LinX SMART To-Do", layout="centered")
st.title("🧠 LinX SMART To-Do")
st.caption("Minimal Input • Smart AI • Maximum Focus")

# --------- Custom CSS ----------
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        .stButton > button {
            width: 100%;
        }
        .stRadio > div {
            flex-direction: row;
            gap: 1rem;
            justify-content: center;
        }
        @media only screen and (max-width: 768px) {
            .stTextInput, .stFileUploader {
                width: 100% !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --------- Load Auth Config ----------
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# ✅ FIXED LOGIN METHOD
name, auth_status, username = authenticator.login(
    form_name='Login', location='main'
)

# --------- Login State Handling ---------
if auth_status == False:
    st.error("❌ Invalid username or password.")
elif auth_status == None:
    st.warning("🔐 Please enter your login credentials.")
elif auth_status:

    authenticator.logout('Logout', 'sidebar')
    st.sidebar.success(f"✅ Logged in as: {name}")

    # --------- Connect to Google Sheet ----------
    @st.cache_resource
    def connect_gsheet():
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("linx_tasks").sheet1
        return sheet

    sheet = connect_gsheet()

    # --------- Task Categorizer (AI Sorting) ----------
    def categorize(task):
        t = task.lower()
        if "urgent" in t or "today" in t or "deadline" in t:
            return "🟥 Urgent & Important"
        elif "plan" in t or "study" in t or "project" in t:
            return "🟨 Not Urgent but Important"
        elif "call" in t or "email" in t or "text" in t:
            return "🟦 Urgent but Not Important"
        else:
            return "⬜ Not Urgent & Not Important"

    # --------- Input Options ----------
    input_type = st.radio("Choose Input Type:", ["Typing", "Handwriting Image"])

    # --------- Typing Input ----------
    if input_type == "Typing":
        task = st.text_input("✍️ Type your task here:")
        if st.button("Submit Task"):
            if task:
                category = categorize(task)
                sheet.append_row([username, task, category])
                st.success(f"✅ Added: {task}")
                st.info(f"📌 Category: {category}")
            else:
                st.warning("Please type something before submitting.")

    # --------- OCR Image Upload ----------
    elif input_type == "Handwriting Image":
        uploaded_img = st.file_uploader("📸 Upload an image of handwritten tasks", type=["png", "jpg", "jpeg"])
        if uploaded_img and st.button("🧠 Extract & Sort Tasks"):
            with st.spinner("Running OCR..."):
                result = requests.post(
                    "https://api.ocr.space/parse/image",
                    files={"filename": uploaded_img},
                    data={"apikey": "helloworld", "language": "eng"}
                )
                if result.status_code == 200:
                    text = result.json()['ParsedResults'][0]['ParsedText']
                    st.success("✅ Extracted Tasks:")
                    st.code(text)
                    tasks = text.strip().split('\n')
                    for t in tasks:
                        if t.strip():
                            category = categorize(t)
                            sheet.append_row([username, t.strip(), category])
                            st.write(f"• **{t.strip()}** → {category}")
                else:
                    st.error("❌ OCR failed. Check your image or try again later.")

    # --------- Pomodoro Timer ----------
    st.markdown("### ⏱️ Pomodoro Focus Timer")
    if st.button("▶️ Start 25-Minute Focus"):
        st.success("Pomodoro started. Stay focused!")
        with st.empty():
            for remaining in range(25 * 60, 0, -1):
                mins, secs = divmod(remaining, 60)
                st.metric("Time Left", f"{mins:02d}:{secs:02d}")
                time.sleep(1)
        st.balloons()
        st.success("🎉 Great job! You’ve completed a Pomodoro session.")

    # --------- Task History ----------
    if st.checkbox("📂 View My Task History"):
        rows = sheet.get_all_records()
        user_tasks = [row for row in rows if row['username'] == username]
        if user_tasks:
            st.dataframe(user_tasks)
        else:
            st.info("No tasks found for your account.")

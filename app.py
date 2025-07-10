import streamlit as st
import requests
import time
import gspread
import yaml
from yaml.loader import SafeLoader
from oauth2client.service_account import ServiceAccountCredentials
import streamlit_authenticator as stauthimport streamlit as st
import streamlit_authenticator as stauth
import yaml
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from datetime import datetime, timedelta

# ------------------------------
# Load credentials from config.yaml
with open('config.yaml') as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('Username/password is incorrect')
if authentication_status == None:
    st.warning('Please enter your username and password')

if authentication_status:
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.write(f'Welcome, {name}!')

    # ------------------------------
    # Connect to Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open('linx_tasks').worksheet(username)

    st.title("LinX SMART To-Do")

    # ------------------------------
    # Task Input
    task_text = st.text_input("Enter your task:")
    uploaded_file = st.file_uploader("Or upload handwriting image (OCR):")

    if st.button("Add Task"):
        task = ""
        if task_text:
            task = task_text
        elif uploaded_file is not None:
            # Call OCR.space API
            ocr_url = "https://api.ocr.space/parse/image"
            result = requests.post(
                ocr_url,
                files={"file": uploaded_file},
                data={"apikey": "helloworld"}
            )
            result_text = result.json()['ParsedResults'][0]['ParsedText']
            task = result_text.strip()

        if task:
            # Simple Eisenhower: user chooses
            urgency = st.selectbox("Is it urgent?", ["Yes", "No"])
            importance = st.selectbox("Is it important?", ["Yes", "No"])
            category = ""
            if urgency == "Yes" and importance == "Yes":
                category = "Do Now"
            elif urgency == "No" and importance == "Yes":
                category = "Schedule"
            elif urgency == "Yes" and importance == "No":
                category = "Delegate"
            else:
                category = "Eliminate"

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([now, task, urgency, importance, category])
            st.success(f"Task added: {task} ({category})")

    # ------------------------------
    # Show Task History
    st.subheader("Your Tasks")
    data = sheet.get_all_values()
    st.table(data)

    # ------------------------------
    # Pomodoro Timer
    st.subheader("Pomodoro Timer (25 min)")
    if st.button("Start Pomodoro"):
        pomodoro_end = datetime.now() + timedelta(minutes=25)
        st.session_state['pomodoro_end'] = pomodoro_end

    if 'pomodoro_end' in st.session_state:
        remaining = st.session_state['pomodoro_end'] - datetime.now()
        if remaining.total_seconds() > 0:
            mins, secs = divmod(remaining.seconds, 60)
            st.info(f"Time left: {mins}m {secs}s")
        else:
            st.success("Pomodoro session complete!")



# --------- UI Setup ----------
st.set_page_config(page_title="LinX SMART To-Do", layout="centered")
st.title("🧠 LinX SMART To-Do")
st.caption("Minimal Input • Smart AI • Maximum Focus")

# --------- Custom CSS ----------
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 2rem; }
        .stButton > button { width: 100%; }
        .stRadio > div { flex-direction: row; gap: 1rem; justify-content: center; }
        @media only screen and (max-width: 768px) {
            .stTextInput, .stFileUploader { width: 100% !important; }
        }
    </style>
""", unsafe_allow_html=True)

# --------- Load Login Credentials ----------
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# ✅ Login: Compatible with streamlit-authenticator==0.2.2
name, auth_status, username = authenticator.login('Login', 'main')

if auth_status == False:
    st.error("❌ Invalid username or password.")
elif auth_status == None:
    st.warning("🔐 Please enter your login credentials.")
elif auth_status:

    authenticator.logout('Logout', 'sidebar')
    st.sidebar.success(f"✅ Logged in as: {name}")

    # --------- Google Sheet Connection ----------
    @st.cache_resource
    def connect_gsheet():
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("linx_tasks").sheet1
        return sheet

    sheet = connect_gsheet()

    # --------- Categorize Tasks with Eisenhower Logic ----------
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

    # --------- Task Input ----------
    input_type = st.radio("Choose Input Type:", ["Typing", "Handwriting Image"])

    if input_type == "Typing":
        task = st.text_input("✍️ Type your task:")
        if st.button("Submit Task"):
            if task:
                category = categorize(task)
                sheet.append_row([username, task, category])
                st.success(f"✅ Added: {task}")
                st.info(f"📌 Category: {category}")
            else:
                st.warning("Please type something.")

    elif input_type == "Handwriting Image":
        uploaded_img = st.file_uploader("📸 Upload a handwritten task image", type=["png", "jpg", "jpeg"])
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
                    st.error("❌ OCR failed. Try again later.")

    # --------- Pomodoro Timer ----------
    st.markdown("### ⏱️ Pomodoro Focus Timer")
    if st.button("▶️ Start 25-Minute Pomodoro"):
        st.success("Pomodoro started. Stay focused!")
        with st.empty():
            for remaining in range(25 * 60, 0, -1):
                mins, secs = divmod(remaining, 60)
                st.metric("Time Left", f"{mins:02d}:{secs:02d}")
                time.sleep(1)
        st.balloons()
        st.success("🎉 Session Complete! Great work!")

    # --------- Task History ----------
    if st.checkbox("📂 View My Task History"):
        rows = sheet.get_all_records()
        user_tasks = [row for row in rows if row['username'] == username]
        if user_tasks:
            st.dataframe(user_tasks)
        else:
            st.info("No tasks found for your account.")

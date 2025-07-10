import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml import SafeLoader
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from datetime import datetime, timedelta
import hashlib

# ---------------------------------
# Load config
CONFIG_FILE = 'config.yaml'

def load_config():
    with open(CONFIG_FILE) as file:
        return yaml.load(file, Loader=SafeLoader)

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

config = load_config()

# ---------------------------------
# Authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# ---------------------------------
# Register Page
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Login", "Register"])

if page == "Register":
    st.title("Register New User")

    new_username = st.text_input("Username")
    new_email = st.text_input("Email")
    new_password = st.text_input("Password", type="password")

    if st.button("Register"):
        if new_username in config['credentials']['usernames']:
            st.error("Username already exists!")
        else:
            # Hash the password
            hashed_pw = stauth.Hasher([new_password]).generate()[0]

            # Add to config
            config['credentials']['usernames'][new_username] = {
                'email': new_email,
                'name': new_username,
                'password': hashed_pw
            }

            save_config(config)
            st.success("Registration successful! Go to Login tab.")

elif page == "Login":
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status == False:
        st.error('Username/password is incorrect')
    if authentication_status == None:
        st.warning('Please enter your username and password')

    if authentication_status:
        authenticator.logout('Logout', 'sidebar')
        st.sidebar.write(f'Welcome, {name}!")

        # ------------------------------
        # Connect to Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        client = gspread.authorize(creds)

        # Make sure the user has a worksheet:
        try:
            sheet = client.open('linx_tasks').worksheet(username)
        except:
            # If not found, create it
            sheet = client.open('linx_tasks').add_worksheet(title=username, rows="1000", cols="5")
            sheet.append_row(["Timestamp", "Task", "Urgent", "Important", "Category"])

        st.title("LinX SMART To-Do")

        # ------------------------------
        # Task Input
        task_text = st.text_input("Enter your task:")
        uploaded_file = st.file_uploader("Or upload handwriting image (OCR):")

        urgency = st.selectbox("Is it urgent?", ["Yes", "No"])
        importance = st.selectbox("Is it important?", ["Yes", "No"])

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

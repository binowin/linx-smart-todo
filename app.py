import streamlit as st

st.set_page_config(page_title="LinX SMART To-Do", layout="centered")

st.title("🧠 LinX SMART To-Do")
st.subheader("Minimal Input • Smart AI • Maximum Focus")

input_type = st.radio("Select Input Type:", ["Typing", "Voice (Coming Soon)", "Handwriting Image"])

if input_type == "Typing":
    task = st.text_input("Type your task here:")
elif input_type == "Handwriting Image":
    uploaded_img = st.file_uploader("Upload handwritten to-do list image", type=["png", "jpg", "jpeg"])

st.button("Sort with AI (Eisenhower Matrix)")

st.markdown("---")
st.write("🔁 Coming soon: Google Calendar sync, Pomodoro Timer, Voice-to-Text, and AI Prioritizer")

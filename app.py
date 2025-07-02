import streamlit as st
import requests

# Set app title and layout
st.set_page_config(page_title="LinX SMART To-Do", layout="centered")
st.title("🧠 LinX SMART To-Do")
st.caption("Minimal Input • Smart AI • Maximum Focus")

# Select input method
input_type = st.radio("Select Input Method:", ["Typing", "Handwriting Image"])

# --- Typing input ---
if input_type == "Typing":
    task = st.text_input("Type your task:")
    if st.button("Submit Task"):
        if task:
            st.success(f"Task Added: {task}")
            
            # Simple AI sorting
            st.markdown("### 🧠 Eisenhower Prioritization")
            def categorize(t):
                t = t.lower()
                if "urgent" in t or "today" in t or "deadline" in t:
                    return "🟥 Urgent & Important"
                elif "plan" in t or "study" in t:
                    return "🟨 Not Urgent but Important"
                elif "call" in t or "email" in t:
                    return "🟦 Urgent but Not Important"
                else:
                    return "⬜ Not Urgent & Not Important"
            st.write(f"• **{task.strip()}** → {categorize(task)}")
        else:
            st.warning("Please type a task before submitting.")

# --- Handwriting OCR Input ---
elif input_type == "Handwriting Image":
    uploaded_img = st.file_uploader("Upload handwritten to-do list image (PNG or JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_img:
        if st.button("Extract Text with AI"):
            with st.spinner("Processing with OCR..."):
                response = requests.post(
                    "https://api.ocr.space/parse/image",
                    files={"filename": uploaded_img},
                    data={"apikey": "K81248791588957", "language": "eng"}
                )

                if response.status_code == 200:
                    result = response.json()
                    extracted_text = result['ParsedResults'][0]['ParsedText']
                    st.success("📝 Extracted Tasks:")
                    st.code(extracted_text)

                    # Sort extracted tasks using simple AI logic
                    st.markdown("### 🧠 Eisenhower Prioritization")
                    tasks = extracted_text.strip().split('\n')

                    def categorize(t):
                        t = t.lower()
                        if "urgent" in t or "today" in t or "deadline" in t:
                            return "🟥 Urgent & Important"
                        elif "plan" in t or "study" in t:
                            return "🟨 Not Urgent but Important"
                        elif "call" in t or "email" in t:
                            return "🟦 Urgent but Not Important"
                        else:
                            return "⬜ Not Urgent & Not Important"

                    for t in tasks:
                        if t.strip():
                            st.write(f"• **{t.strip()}** → {categorize(t)}")
                else:
                    st.error("❌ OCR API request failed. Try again.")

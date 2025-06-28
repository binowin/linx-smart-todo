import streamlit as st
from PIL import Image
import pytesseract

st.set_page_config(page_title="LinX SMART To-Do", layout="centered")
st.title("🧠 LinX SMART To-Do")
st.subheader("Minimal Input • Smart AI • Maximum Focus")

input_type = st.radio("Select Input Type:", ["Typing", "Handwriting Image"])

if input_type == "Typing":
    task = st.text_input("Type your task here:")
    if st.button("Submit Task"):
        st.success(f"Task Added: {task}")

elif input_type == "Handwriting Image":
    uploaded_img = st.file_uploader("Upload a handwritten to-do list (PNG or JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_img is not None:
        image = Image.open(uploaded_img)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        if st.button("Extract Text with OCR"):
            with st.spinner("Reading handwriting..."):
                extracted_text = pytesseract.image_to_string(image)
                st.success("📝 Extracted Tasks:")
                st.write(extracted_text)

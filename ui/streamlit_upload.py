import streamlit as st
import requests

API_URL = "http://localhost:8000/upload-pdf"

st.title("📄 PDF Ingestion System")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file is not None:
    if st.button("Submit for Ingestion"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}

        with st.spinner("Uploading and processing..."):
            response = requests.post(API_URL, files=files)

        if response.status_code == 200:
            st.success("Upload & ingestion completed!")
            st.json(response.json())
        else:
            st.error("Something went wrong")
            st.text(response.text)
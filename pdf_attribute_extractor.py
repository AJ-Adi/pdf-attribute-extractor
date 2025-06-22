
import streamlit as st
import fitz  # PyMuPDF
import re

st.set_page_config(page_title="PDF Datasheet Attribute Extractor", layout="centered")

st.title("📄 Datasheet Attribute Extractor")
st.markdown("Upload a product datasheet PDF and input the attributes you want to extract.")

# Upload PDF
pdf_file = st.file_uploader("Upload Datasheet PDF", type=["pdf"])

# Attribute input
attributes_input = st.text_area("Enter Attribute Names (one per line):", height=200)
attributes = [attr.strip() for attr in attributes_input.split("\n") if attr.strip()]

def extract_text_from_pdf(pdf):
    doc = fitz.open(stream=pdf.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_attribute(text, attr):
    pattern = re.compile(fr"{re.escape(attr)}\s*[:\-–]?\s*(.+)", re.IGNORECASE)
    matches = pattern.findall(text)
    if matches:
        return matches[0].strip()
    return "Not found"

if pdf_file and attributes:
    with st.spinner("Reading and analyzing the PDF..."):
        pdf_text = extract_text_from_pdf(pdf_file)

    st.success("Extraction complete!")
    st.markdown("### 🧠 Extracted Attribute Values:")
    for attr in attributes:
        value = extract_attribute(pdf_text, attr)
        st.write(f"**{attr}:** {value}")

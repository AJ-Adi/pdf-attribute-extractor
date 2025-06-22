
import streamlit as st
import fitz  # PyMuPDF
import re
from fuzzywuzzy import fuzz

st.set_page_config(page_title="📄 Smart PDF Attribute Extractor", layout="centered")

st.title("🧠 Extracted Attribute Values")
st.markdown("Upload a datasheet PDF and enter attribute names to extract the best-matched values.")

# Upload PDF
pdf_file = st.file_uploader("📄 Upload Datasheet PDF", type=["pdf"])

# Attribute input
attributes_input = st.text_area("✍️ Enter Attribute Names (one per line):", height=200)
attributes = [attr.strip() for attr in attributes_input.split("\n") if attr.strip()]

# Extract full text from PDF
def extract_text_from_pdf(pdf):
    doc = fitz.open(stream=pdf.read(), filetype="pdf")
    lines = []
    for page in doc:
        text = page.get_text()
        lines += text.split("\n")
    return [line.strip() for line in lines if line.strip()]

# Find best-matching value near the attribute name
def find_attribute_value(lines, attr_name):
    best_match = ""
    best_score = 0
    for i, line in enumerate(lines):
        score = fuzz.partial_ratio(attr_name.lower(), line.lower())
        if score > best_score:
            best_score = score
            best_match = i

    if best_score >= 75:
        value_line = lines[best_match]
        # Try to extract value after ':' or '-' or next line
        if ':' in value_line:
            return value_line.split(':', 1)[-1].strip()
        elif '-' in value_line:
            return value_line.split('-', 1)[-1].strip()
        elif best_match + 1 < len(lines):
            return lines[best_match + 1].strip()
        else:
            return "(Matched, but value not found)"
    return "Not found"

# Main logic
if pdf_file and attributes:
    with st.spinner("📖 Analyzing PDF..."):
        lines = extract_text_from_pdf(pdf_file)

    st.success("✅ Extraction complete!")
    st.markdown("### 🧾 Attribute Results:")
    for attr in attributes:
        value = find_attribute_value(lines, attr)
        st.write(f"**{attr}:** {value}")

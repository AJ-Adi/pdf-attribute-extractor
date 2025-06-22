
import streamlit as st
import fitz  # PyMuPDF
import pdfplumber
import pandas as pd
from fuzzywuzzy import fuzz
import openai

st.set_page_config(page_title="🔍 Smart Datasheet Attribute Extractor", layout="centered")
st.title("🧠 Smart Datasheet Attribute Extractor")

st.markdown("""
Upload a product datasheet (PDF), enter attribute names, and get the most relevant values.
Now includes:
- ✅ Table-aware parsing
- 🤖 Optional GPT fallback (OpenAI API key)
- 📤 Export to Excel
""")

# Upload PDF
pdf_file = st.file_uploader("📄 Upload Datasheet PDF", type=["pdf"])

# Attribute input
attributes_input = st.text_area("✍️ Enter Attribute Names (one per line):", height=200)
attributes = [attr.strip() for attr in attributes_input.split("\n") if attr.strip()]

# Optional GPT key
openai_key = st.text_input("🔑 (Optional) Enter OpenAI API Key for GPT fallback", type="password")
use_gpt = bool(openai_key)

# Extract text lines using PyMuPDF
def extract_text_lines_mupdf(pdf):
    doc = fitz.open(stream=pdf.read(), filetype="pdf")
    lines = []
    for page in doc:
        lines += page.get_text().split("\n")
    return [line.strip() for line in lines if line.strip()]

# Extract table text using pdfplumber
def extract_text_from_tables(pdf):
    pdf.seek(0)
    tables = []
    with pdfplumber.open(pdf) as doc:
        for page in doc.pages:
            table = page.extract_table()
            if table:
                tables.extend(table)
    return tables

# GPT fallback
def ask_gpt(attr, context):
    if not openai_key:
        return "GPT key not provided"
    openai.api_key = openai_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a helpful assistant that extracts attribute values from product datasheets."},
                {"role": "user", "content": f"Given this datasheet content, what is the value of '{attr}'?

{context}"}
            ],
            max_tokens=100,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"GPT Error: {str(e)}"

# Match attribute in lines or tables
def find_best_match(attr_name, lines, tables):
    best_score = 0
    best_value = "Not found"

    for line in lines:
        score = fuzz.partial_ratio(attr_name.lower(), line.lower())
        if score > best_score:
            best_score = score
            if ':' in line:
                best_value = line.split(':', 1)[-1].strip()
            else:
                best_value = line.strip()

    for row in tables:
        for i, cell in enumerate(row):
            if cell and fuzz.partial_ratio(attr_name.lower(), cell.lower()) >= 85:
                if i + 1 < len(row) and row[i+1]:
                    return row[i+1].strip()
                else:
                    return "(Matched, value unclear)"

    if best_score >= 70:
        return best_value
    return "Not found"

# Run extraction
if pdf_file and attributes:
    with st.spinner("📖 Analyzing PDF..."):
        lines = extract_text_lines_mupdf(pdf_file)
        tables = extract_text_from_tables(pdf_file)

    st.success("✅ Extraction complete!")

    results = []
    st.markdown("### 📋 Extracted Results:")
    for attr in attributes:
        value = find_best_match(attr, lines, tables)
        if value == "Not found" and use_gpt:
            context = "\n".join(lines[:100])  # send first 100 lines to GPT for context
            value = ask_gpt(attr, context)
        results.append({"Attribute": attr, "Extracted Value": value})
        st.write(f"**{attr}:** {value}")

    # Export option
    if results:
        df = pd.DataFrame(results)
        st.download_button("📤 Download as Excel", data=df.to_excel(index=False), file_name="attribute_results.xlsx")

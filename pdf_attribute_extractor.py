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
openai_key = st.text_input("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", type="password")
use_gpt = bool(openai_key)

# --- Text Cleaning & Normalization ---
def clean_text(text):
    import re
    text = text.lower()
    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9:\.\-_%/ ]", "", text)  # keep common units/symbols
    return text.strip()

# --- Improved Table Extraction ---
def extract_text_from_tables(pdf):
    pdf.seek(0)
    tables = []
    with pdfplumber.open(pdf) as doc:
        for page in doc.pages:
            page_tables = page.extract_tables()
            for table in page_tables:
                if table:
                    tables.append(table)
    return tables

# --- Enhanced Line Extraction ---
def extract_text_lines_mupdf(pdf):
    doc = fitz.open(stream=pdf.read(), filetype="pdf")
    lines = []
    for page in doc:
        lines += page.get_text().split("\n")
    return [line.strip() for line in lines if line.strip()]

# --- Improved Attribute Matching ---
def find_best_match(attr_name, lines, tables):
    import re
    attr_clean = clean_text(attr_name)
    best_score = 0
    best_value = "Not found"

    # Special handling for EN 388 attributes
    if attr_clean.startswith("en 388"):
        pattern = re.compile(r"en[\\s-]?388[\\s:]*([\\d]+)?", re.IGNORECASE)
        for line in lines:
            if pattern.search(line):
                # Try to extract numbers after EN 388
                numbers = re.findall(r"\\d+", line)
                if numbers:
                    return ' '.join(numbers)
        # Try in tables as well
        for table in tables:
            for row in table:
                for cell in row:
                    if cell and pattern.search(cell):
                        numbers = re.findall(r"\\d+", cell)
                        if numbers:
                            return ' '.join(numbers)
        return "Not found"
    # ...rest of your matching logic...

# --- Improved GPT Fallback Context ---
def get_gpt_context(attr, lines):
    # Find the best matching line and return 20 lines before/after as context
    attr_clean = clean_text(attr)
    best_score = 0
    best_idx = 0
    for idx, line in enumerate(lines):
        score = fuzz.partial_ratio(attr_clean, clean_text(line))
        if score > best_score:
            best_score = score
            best_idx = idx
    start = max(0, best_idx - 20)
    end = min(len(lines), best_idx + 20)
    return "\n".join(lines[start:end])

# --- GPT fallback (unchanged except context) ---
def ask_gpt(attr, context):
    if not openai_key:
        return "GPT key not provided"
    openai.api_key = openai_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a helpful assistant that extracts attribute values from product datasheets."},
                {"role": "user", "content": f"Given this datasheet content, what is the value of '{attr}'?\n\n{context}"}
            ],
            max_tokens=100,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"GPT Error: {str(e)}"

# --- Main Extraction Logic ---
if pdf_file and attributes:
    with st.spinner("📖 Analyzing PDF..."):
        lines = extract_text_lines_mupdf(pdf_file)
        tables = extract_text_from_tables(pdf_file)

    st.success("✅ Extraction complete!")

    # --- Debug Output: Show first 50 lines and first 3 tables ---
    with st.expander("🛠️ Show Raw Extracted Lines & Tables (Debug)"):
        st.markdown("#### First 50 Extracted Lines:")
        for i, line in enumerate(lines[:50]):
            st.write(f"{i+1}: {line}")
        st.markdown("#### First 3 Extracted Tables:")
        for t_idx, table in enumerate(tables[:3]):
            st.write(f"Table {t_idx+1}:")
            st.table(table)

    results = []
    st.markdown("### 📋 Extracted Results:")
    for attr in attributes:
        value = find_best_match(attr, lines, tables)
        if value == "Not found" and use_gpt:
            context = get_gpt_context(attr, lines)
            value = ask_gpt(attr, context)
        results.append({"Attribute": attr, "Extracted Value": value})
        st.write(f"**{attr}:** {value}")

    # Export option
    if results:
        df = pd.DataFrame(results)
        st.download_button("📤 Download as Excel", data=df.to_excel(index=False), file_name="attribute_results.xlsx")

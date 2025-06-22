import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import openai

st.set_page_config(page_title="🧠 GPT Datasheet Extractor", layout="centered")
st.title("📄 GPT-Powered Datasheet Attribute Extractor")

st.markdown("""
Upload a product datasheet PDF and enter the attributes you want to extract.  
This version uses **OpenAI GPT-4** to intelligently read the full document and extract values.
""")

pdf_file = st.file_uploader("📄 Upload Datasheet PDF", type=["pdf"])
attributes_input = st.text_area("✍️ Enter Attribute Names (one per line):", height=200)
attributes = [attr.strip() for attr in attributes_input.split("\n") if attr.strip()]
openai_key = st.text_input("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", type="password")

# Synonym mapping
synonyms = {
    "colour": ["color", "shade"],
    "coating": ["coating material"],
    "material": ["liner material", "composition"],
    "size": ["dimension", "length"],
    "series": ["model", "product line"],
    "standards/approvals": ["certifications", "compliance"],
    "product type": ["glove type", "application"],
    "resistance features": ["resistance", "protective features"]
}

def extract_text_full(pdf):
    doc = fitz.open(stream=pdf.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

def ask_gpt_batch(attrs, context, api_key):
    openai.api_key = api_key
    synonyms_text = "\n".join(
        [f"{attr}: {', '.join(synonyms.get(attr.lower(), []))}" for attr in attrs]
    )
    prompt = f"""
Given the following datasheet content, extract the most accurate values for each of these attributes.

Attributes:
{', '.join(attrs)}

Synonyms and alternate labels to help you:
{synonyms_text}

Content:
{context}

Return the results in the format:
Attribute: Value
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at reading and extracting structured data from technical documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

# Run processing
if pdf_file and attributes and openai_key:
    with st.spinner("🔍 Reading and analyzing PDF with GPT..."):
        pdf_text = extract_text_full(pdf_file)
        gpt_output = ask_gpt_batch(attributes, pdf_text, openai_key)

    st.success("✅ GPT Extraction Complete!")
    st.markdown("### 📋 Extracted Results:")

    results = []
    for line in gpt_output.split("\n"):
        if ':' in line:
            attr, val = line.split(':', 1)
            st.write(f"**{attr.strip()}:** {val.strip()}")
            results.append({"Attribute": attr.strip(), "Extracted Value": val.strip()})

    if results:
        df = pd.DataFrame(results)
        st.download_button("📤 Download as Excel", data=df.to_excel(index=False), file_name="gpt_extracted_attributes.xlsx")

elif not openai_key and pdf_file:
    st.warning("⚠️ Please enter your OpenAI API key to enable GPT extraction.")

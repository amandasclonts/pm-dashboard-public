import streamlit as st
import base64
import pdfplumber
import re
import fitz  # PyMuPDF
import pandas as pd

from openai import OpenAI
openai_api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=openai_api_key)

st.set_page_config(page_title="AI Dashboard", layout="wide")

# --- Password Gate ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "Wbg3033!":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.error("❌ Incorrect password")
        st.stop()

check_password()

# --- Branding ---
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
        return f"data:image/jpeg;base64,{encoded}"

encoded_logo = get_base64_image("logo.jpg")
st.markdown(
    f"""
    <div style='text-align: center;'>
        <img src="{encoded_logo}" style='width: 375px; margin-bottom: 10px;' />
        <h1 style='color: white; font-size: 36px;'>🧠 AI Tools Dashboard</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Tabs ---
tabs = st.tabs(["Forecast AI", "Compliance Checker", "Summarizer", "Contract Parsing", "More Coming Soon"])

with tabs[1]:  # Compliance Checker Tab
    st.subheader("📋 Civil Plan Compliance Checker")

with tabs[3]:  # Contract Parsing Tab
    st.subheader("📂 Contract Parsing – Section Lookup (AI Mode)")

    uploaded_contract = st.file_uploader("Upload a contract PDF", type=["pdf"])

    if uploaded_contract:
        # Extract text chunks with page numbers
        text_chunks = []
        with fitz.open(stream=uploaded_contract.read(), filetype="pdf") as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if text.strip():
                    text_chunks.append({"text": text.strip(), "page": page_num})

        # Combine all text for batching
        all_text = ""
        for c in text_chunks:
            all_text += f"[Page {c['page']}] {c['text']}\n\n"

        # Split into batches of ~6000 characters to avoid token errors
        batch_size = 6000
        batches = [all_text[i:i+batch_size] for i in range(0, len(all_text), batch_size)]

        topics = [
            "Contract Value", "Payment Terms", "Liquidated Damages", "Delays",
            "Retention", "Schedule", "Scope of Work", "Safety Requirements",
            "CCIP", "OCIP", "Bond", "Textura", "Procore"
        ]

        final_results = {topic: [] for topic in topics}

        # Process each batch and collect results
        for idx, batch in enumerate(batches, start=1):
            with st.spinner(f"Analyzing batch {idx}/{len(batches)}..."):
                prompt = f"""
You are a contract analysis assistant. Extract details for each of these topics:

{', '.join(topics)}

Rules:
- Include page numbers if available (from [Page X] in the text).
- If nothing is found for a topic in this batch, just say "Not Found" for that topic.
- Return results ONLY in this JSON format (no extra text):

{{
  "Contract Value": ["...details... (Page X)"],
  "Payment Terms": ["...details... (Page X)"],
  ...
}}
Text to analyze:
\"\"\"
{batch}
\"\"\"
                """
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You extract structured data from contracts for project managers."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    max_tokens=800
                )

                import json
                try:
                    batch_data = json.loads(response.choices[0].message.content)
                    for topic in topics:
                        if topic in batch_data and batch_data[topic] != "Not Found":
                            final_results[topic].extend(batch_data[topic])
                except:
                    st.error(f"⚠️ Failed to parse batch {idx} response")

        # Show final combined summary
        st.markdown("### 🤖 AI Combined Contract Summary")
        for topic in topics:
            if final_results[topic]:
                st.markdown(f"**{topic}:**")
                for item in final_results[topic]:
                    st.markdown(f"- {item}")
            else:
                st.markdown(f"**{topic}:** Not Found")



with tabs[4]:
    st.info("🚧 Stay tuned for more tools here!")

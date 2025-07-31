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

    topic_keywords = {
        "Contract Value": ["contract price", "contract value", "contract sum", "compensation", "subcontract price", "subcontract amount", "total compensation", "base bid", "contract amount", "agrees to pay subcontractor", "shall pay to subcontractor"],
        "Payment Terms": ["payment terms", "invoice", "progress payments", "final payment", "paid by owner", "schedule of values", "payment application"],
        "Liquidated Damages": ["liquidated damages", "penalty", "late delivery", "delay damages"],
        "Delays": ["delay", "extension of time", "force majeure", "project delay", "weather delay", "time is of the essence"],
        "Retention": ["retainage", "retained", "withheld", "10%", "retention", "retainage percentage"],
        "Schedule": ["completion date", "timeline", "project schedule", "construction timeline", "milestone"],
        "Scope of Work": ["scope of work", "subcontract work", "services include", "work to be performed"],
        "Safety Requirements": ["safety", "osha", "ppe", "site safety", "safety program", "injury prevention"],
        "CCIP": ["ccip"],
        "OCIP": ["ocip"],
        "Bond": ["bond", "surety bond", "performance bond", "payment bond"],
        "Textura": ["textura"],
        "Procore": ["procore"]
    }

    if uploaded_contract:
        # ✅ Extract text chunks with page numbers
        text_chunks = []
        with fitz.open(stream=uploaded_contract.read(), filetype="pdf") as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                parts = re.split(r'\n(?=\d+\.\d+(?:\.\d+)*|ARTICLE \d+|Section \d+)', text)
                for part in parts:
                    if len(part.strip()) > 50:
                        text_chunks.append({"text": part.strip(), "page": page_num})

        # 🔹 Dropdown for single-topic analysis
        topic = st.selectbox("Choose a single topic to analyze:", list(topic_keywords.keys()))

        def keyword_found(text, keywords):
            return any(re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE) for kw in keywords)

        keywords = topic_keywords[topic]
        matches = [c for c in text_chunks if keyword_found(c["text"], keywords)]

        # ✅ Show up to 3 matches for the selected topic
        if matches:
            st.markdown(f"### 🔍 Found {len(matches)} section(s) related to **{topic}**:")
            for idx, section in enumerate(matches[:3]):  # ← Limit to 3 for display
                with st.expander(f"Match {idx + 1} (Page {section['page']})"):
                    st.markdown(f"<div style='white-space: pre-wrap;'>{section['text']}</div>", unsafe_allow_html=True)
        else:
            st.warning(f"No relevant sections found for **{topic}**.")

        # 🔹 FULL AI ANALYSIS (uses ALL contract text)
        if st.button("🔍 Full Contract Analysis with AI"):
            with st.spinner("Contacting OpenAI..."):
                combined_text = "\n\n".join(
                    f"[Page {c['page']}] {c['text']}" for c in text_chunks
                )[:15000]  # Includes ALL chunks, limit text length to avoid token errors

                prompt = f"""
You are a contract analysis assistant. Review the following contract text and extract details for EACH of these topics:

1. Contract Value
2. Payment Terms
3. Liquidated Damages
4. Delays
5. Retention
6. Schedule
7. Scope of Work
8. Safety Requirements
9. CCIP
10. OCIP
11. Bond
12. Textura
13. Procore

✅ For each topic:
- Write **"Not Found"** if no relevant text exists.
- If found, give a **short bullet-point summary** and **page number(s)**.

Here is the contract text:
\"\"\"
{combined_text}
\"\"\"

Return ONLY in this format:

**Contract Value** (Page #):
- Details...

**Payment Terms** (Page #):
- Details...

... and so on for all topics.
"""

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You summarize and extract details from contracts for project managers."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=2000  # More tokens for bigger output
                )

                summary = response.choices[0].message.content
                st.markdown("### 🤖 AI Full Summary")
                st.write(summary)



with tabs[4]:
    st.info("🚧 Stay tuned for more tools here!")

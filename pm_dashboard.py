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

with tabs[3]:
    st.subheader("📂 Contract Parsing – AI Optimized Lookup")

    uploaded_contract = st.file_uploader("Upload a contract PDF", type=["pdf"])

    topic_keywords = {
        "Contract Value": ["contract price", "contract value", "contract sum", "compensation", "subcontract price", "subcontract amount", "total compensation", "base bid", "contract amount", "agrees to pay subcontractor", "shall pay to subcontractor"],
        "Payment Terms": ["payment terms", "invoice", "progress payments", "final payment", "paid by owner", "schedule of values", "payment application"],
        "Liquidated Damages": ["liquidated damages", "penalty", "late delivery", "delay damages"],
        "Delays": ["delay", "extension of time", "force majeure", "project delay", "time is of the essence"],
        "Retention": ["retainage", "retained", "withheld", "10%", "retention", "retainage percentage"],
        "Schedule": ["completion date", "timeline", "project schedule", "construction timeline", "milestone"],
        "Scope of Work": ["scope of work", "subcontract work", "services include", "work to be performed"],
        "Safety Requirements": ["safety", "osha", "ppe", "site safety", "safety program", "injury prevention"],
        "CCIP": ["ccip", "contractor controlled insurance program"],
        "OCIP": ["ocip", "owner controlled insurance program"],
        "Bond": ["bond", "surety bond", "performance bond", "payment bond"],
        "Textura": ["textura"],
        "Procore": ["procore"]
    }

    if uploaded_contract:
        import re
        import fitz

        # Extract PDF text by page
        doc = fitz.open(stream=uploaded_contract.read(), filetype="pdf")
        page_texts = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            page_texts.append({"page": i, "text": text})

        # Detect relevant pages based on keywords
        relevant_pages = []
        for page in page_texts:
            lowered = page["text"].lower()
            if any(kw in lowered for kws in topic_keywords.values() for kw in kws):
                relevant_pages.append(page)

        if not relevant_pages:
            st.warning("No relevant pages found for analysis.")
        else:
            # Button to run AI analysis
            if st.button("🔍 AI Full Contract Summary"):
                combined_text = "\n\n".join([f"[Page {p['page']}] {p['text']}" for p in relevant_pages])
                combined_text = combined_text[:12000]  # Hard limit to reduce tokens

                prompt = f"""
You are a contract analysis assistant. Using ONLY the text below, summarize details for these topics:

Contract Value, Payment Terms, Liquidated Damages, Delays, Retention, Schedule, Scope of Work,
Safety Requirements, CCIP, OCIP, Bond, Textura, Procore.

For each topic:
- If found, give up to 3 short bullet points with page numbers.
- If not found, just write "Not Found" (do NOT list multiple 'Not Found' messages).

Contract text:
\"\"\"
{combined_text}
\"\"\"

Return in this format:

**Contract Value (Page #)**  
- Bullet 1  
- Bullet 2  

**Payment Terms (Page #)**  
- Bullet 1  

...and so on.
                """

                with st.spinner("Analyzing contract..."):
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",  # cheaper model but still good
                        messages=[
                            {"role": "system", "content": "You are an AI that summarizes contracts for project managers."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=900,
                        temperature=0.3
                    )

                st.markdown("### 🤖 AI Contract Summary")
                st.write(response.choices[0].message.content)


with tabs[4]:
    st.info("🚧 Stay tuned for more tools here!")

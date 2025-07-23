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
        "Liquidated Damages": ["liquidated damages", "penalty", "late delivery", "delay damages"],
        "Payment Terms": ["payment terms", "invoice", "progress payments", "final payment", "paid by owner", "schedule of values", "payment application"],
        "Delays": ["delay", "extension of time", "force majeure", "project delay", "weather delay", "time is of the essence"],
        "Retention": ["retainage", "retained", "withheld", "10%", "retention", "retainage percentage"],
        "Schedule": ["completion date", "timeline", "project schedule", "construction timeline", "milestone"],
        "Scope of Work": ["scope of work", "subcontract work", "services include", "work to be performed"],
        "Contract Value": ["contract price", "contract value", "contract sum", "compensation", "subcontract price", "subcontract amount", "total compensation", "base bid", "contract amount", "zero dollars", "agrees to pay subcontractor", "shall pay to subcontractor", "contract total"],
        "Safety Requirements": ["safety", "osha", "ppe", "site safety", "safety program", "injury prevention"]
    }

    topic = st.selectbox("Choose a contract topic to analyze:", list(topic_keywords.keys()))

if uploaded_contract:
    with fitz.open(stream=uploaded_contract.read(), filetype="pdf") as doc:
        full_text = "\n".join([page.get_text() for page in doc])

    # Split into chunks
    chunks = re.split(r'\n(?=\d+\.\d+(?:\.\d+)*|ARTICLE \d+|Section \d+)', full_text)
    chunks = [c.strip() for c in chunks if len(c.strip()) > 50]

    keywords = topic_keywords[topic]

    # Optional: tighten noisy matches for specific topics
    safety_exclusions = ["decorative", "design-build provisions", "scope of amenities", "contract sum", "unit prices"]

    matches = []
    for chunk in chunks:
        lowered = chunk.lower()
        match_score = sum(kw in lowered for kw in keywords)

        if topic == "Safety Requirements":
            if match_score >= 2 and not any(ex_kw in lowered for ex_kw in safety_exclusions):
                matches.append(chunk.strip())
        else:
            if match_score > 0:
                matches.append(chunk.strip())

    if matches:
        st.markdown(f"### 🔍 Found {len(matches)} section(s) related to **{topic}**:")
        for idx, section in enumerate(matches):
            with st.expander(f"Match {idx + 1}"):
                st.markdown(f"<div style='overflow-x: auto; white-space: pre-wrap;'>{section}</div>", unsafe_allow_html=True)

        if st.button("Summarize All Matches with AI"):
            with st.spinner("Contacting OpenAI..."):
                combined_text = "\n\n".join(matches[:3])[:8000] #roughly 2,000 tokens
                prompt = f"""
You are a contract analysis assistant. Carefully review the contract text and extract relevant information for the following topics. Each topic includes example keywords to help guide your extraction. Return your results in the following format:

**Topic**  
- What the contract says (summarized in bullet points)
- If nothing relevant is found, write "Not Found"

Topics and example keywords:

1. **Contract Value** – contract value, contract price, subcontract price, agreement amount, total compensation  
2. **Payment Terms** – invoice, payment schedule, net 30, progress payments, pay application  
3. **Liquidated Damages** – penalty, late delivery, delay fee, damages, liquidated damages  
4. **Delays** – delay, extension of time, weather delay, force majeure, project delay  
5. **Retention** – retainage, withheld, 10%, retention, retainage percentage  
6. **Schedule** – project schedule, timeline, completion date, milestone  
7. **Scope of Work** – scope of work, services include, subcontract work, description of work  
8. **Safety Requirements** – OSHA, PPE, site safety, safety plan, injury prevention  

Only include information supported directly by the contract text.

Contract Section:
\"\"\"
{combined_text}
\"\"\"
"""
                    response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You summarize and extract details from contracts for project managers."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=500
                )

                summary = response.choices[0].message.content
                st.markdown("### 🤖 AI Summary")
                st.write(summary)
    else:
        st.warning(f"No relevant sections found for **{topic}**.")

with tabs[4]:
    st.info("🚧 Stay tuned for more tools here!")

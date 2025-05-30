import streamlit as st
import base64
import pdfplumber
import openai
import nltk
import re
from nltk.tokenize import sent_tokenize

# Download nltk tokenizer (only first time)
nltk.download('punkt', quiet=True)

# Set OpenRouter (OpenAI-compatible) API
openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = st.secrets["openai"]["api_key"] if "openai" in st.secrets else "sk-your-key-here"

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
        "Contract Value": ["contract price", "contract value", "contract sum", "subcontract amount", "total compensation", "base bid"],
        "Safety Requirements": ["safety", "osha", "ppe", "site safety", "safety program", "injury prevention"]
    }

    topic = st.selectbox("Choose a contract topic to analyze:", list(topic_keywords.keys()))

    if uploaded_contract:
        with pdfplumber.open(uploaded_contract) as pdf:
            full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        # Tokenize sentences
        sentences = sent_tokenize(full_text)

        # Group into smart chunks (based on headers or breaks)
        chunks = []
        current_chunk = ""
        for sent in sentences:
            if re.match(r'^(ARTICLE\s+\d+|Section\s+\d+|\d+\.\d+)', sent.strip(), re.IGNORECASE):
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sent
            else:
                current_chunk += " " + sent
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Match scoring
        keywords = topic_keywords[topic]
        exclusion_keywords = ["insurance", "deductible", "bond", "ocip", "liability"]
        money_regex = re.compile(r"\$\d[\d,]*(?:\.\d{2})?")

        matches = []
        for chunk in chunks:
            lowered = chunk.lower()
            match_score = sum(kw in lowered for kw in keywords)
            has_exclusion = any(ex_kw in lowered for ex_kw in exclusion_keywords)
            if match_score > 0 and not has_exclusion:
                matches.append(chunk.strip())

        # Show matches
        if matches:
            st.markdown(f"### 🔍 Found {len(matches)} section(s) related to **{topic}**:")
            for idx, section in enumerate(matches):
                with st.expander(f"Match {idx + 1}"):
                    st.markdown(f"<div style='overflow-x: auto; white-space: pre-wrap;'>{section}</div>", unsafe_allow_html=True)

            if st.button("Summarize All Matches with AI"):
                with st.spinner("Contacting OpenRouter..."):
                    combined_text = "\n\n".join(matches[:3])
                    prompt = f"""
You are a contract analysis assistant. Summarize the following section(s) from a contract related to:
**{topic}**

Section Text:
{combined_text}
"""
                    response = openai.ChatCompletion.create(
                        model="openchat/openchat-3.5-0106",
                        messages=[
                            {"role": "system", "content": "You summarize and extract details from contracts."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.4
                    )
                    summary = response.choices[0].message.content
                    st.markdown("### 🤖 AI Summary")
                    st.write(summary)
        else:
            st.warning(f"No relevant sections found for **{topic}**.")

with tabs[4]:
    st.info("🚧 Stay tuned for more tools here!")

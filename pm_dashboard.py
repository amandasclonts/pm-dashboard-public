import streamlit as st
import base64
import openai
import re
import fitz  # PyMuPDF

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

# --- Text Cleanup Function ---
def clean_contract_text(text):
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\n{2,}', '\n\n', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

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
        "Contract Value": [
            "contract price", "contract value", "contract sum", "subcontract amount",
            "total compensation", "base bid", "contract amount", "zero dollars",
            "agrees to pay subcontractor", "shall pay to subcontractor", "contract total"
        ],
        "Safety Requirements": ["safety", "osha", "ppe", "site safety", "safety program", "injury prevention"]
    }

    topic = st.selectbox("Choose a contract topic to analyze:", list(topic_keywords.keys()))

    if uploaded_contract:
        # Extract and clean text
        with fitz.open(stream=uploaded_contract.read(), filetype="pdf") as doc:
            raw_text = "\n".join([page.get_text() for page in doc])
        full_text = clean_contract_text(raw_text)

        # Split using both headers and paragraphs
        raw_chunks = re.split(r'\n(?=(\d+\.\d+|ARTICLE \d+|Section \d+|PROJECT:|OWNER:|DESIGNER:))', full_text)
        paragraph_chunks = full_text.split("\n\n")
        chunks = list({chunk.strip() for chunk in raw_chunks + paragraph_chunks if len(chunk.strip()) > 50})

        # OPTIONAL DEBUG: Preview first 5 chunks
        st.markdown("**Previewing first 5 chunks (for debugging):**")
        for idx, c in enumerate(chunks[:5]):
            st.text(f"[Chunk {idx+1}]\n{c[:400]}\n---")

        # Match keywords
        keywords = topic_keywords[topic]
        exclusion_keywords = ["insurance", "deductible", "bond", "ocip", "liability"]

        matches = []
        for chunk in chunks:
            lowered = chunk.lower()
            match_score = sum(kw in lowered for kw in keywords)
            has_exclusion = any(ex_kw in lowered for ex_kw in exclusion_keywords)
            if match_score > 0 and not has_exclusion:
                matches.append(chunk.strip())

        # Show results
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


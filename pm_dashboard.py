import streamlit as st
import base64
import pdfplumber
import openai
import re

openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = "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"

st.set_page_config(page_title="AI Dashboard", layout="wide")

# --- Simple Password Gate ---
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

# Function to encode image in base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
        return f"data:image/jpeg;base64,{encoded}"

# Load and embed the image
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

# ✅ Create tabbed layout
tabs = st.tabs([
    "Forecast AI",
    "Compliance Checker",
    "Summarizer",
    "Contract Parsing",
    "More Coming Soon"
])

with tabs[0]:
    st.subheader("📈 Forecast AI")
    st.text_input("Enter project name:")
    st.button("Run Forecast")

with tabs[1]:
    st.subheader("📋 Compliance Checker")
    st.file_uploader("Upload civil plan PDF", type=["pdf"])
    st.button("Check Compliance")

with tabs[2]:
    st.subheader("📝 Document Summarizer")

    st.markdown("### ➕ Option 1: Paste text to summarize")
    pasted_text = st.text_area("Paste text here")
    if st.button("Summarize Pasted Text"):
        if pasted_text.strip():
            st.success("✅ Summarizing pasted text...")
            st.write(f"**Summary:** {pasted_text[:100]}... (summary placeholder)")
        else:
            st.warning("Please paste some text.")

    st.markdown("---")
    st.markdown("### ➕ Option 2: Upload a PDF and choose pages")

    uploaded_pdf = st.file_uploader("Upload a PDF file", type=["pdf"])
    page_option = st.radio("What do you want to summarize?", ["Whole document", "Select pages"])

    page_range = ""
    if page_option == "Select pages":
        page_range = st.text_input("Enter pages to summarize (e.g., 1-3,5)")

    if st.button("Summarize PDF"):
        if uploaded_pdf:
            st.success("✅ PDF uploaded. (Summary logic coming next...)")
            st.write(f"Summary from: `{uploaded_pdf.name}` — Pages: {page_range or 'All'}")
        else:
            st.warning("Please upload a PDF file first.")


with tabs[3]:
    st.subheader("📂 Contract Parsing – Section Lookup (AI Mode)")

    uploaded_pdf = st.file_uploader("Upload a contract PDF", type=["pdf"])

    topic_keywords = {
        "Liquidated Damages": [
           "liquidated damages", "liquidated amount", "penalty", "late delivery", "delay damages"
        ],
        "Payment Terms": [
            "payment request", "payment terms", "billing", "invoice", "progress payments",
            "final payment", "paid by owner", "schedule of values", "payment application"
        ],
        "Delays": [
            "delay", "extension of time", "force majeure", "project delay",
            "weather delay", "change order", "completion timeline", "time is of the essence"
        ],
        "Retention": [
            "retainage", "retained", "withheld", "10%", "retention", "retainage percentage"
        ],
        "Schedule": [
            "progress schedule", "completion date", "timeline", "schedule of work",
            "project schedule", "construction timeline", "milestone"
        ],
        "Scope of Work": [
            "scope of work", "subcontract work", "work includes", "services include",
            "project scope", "work to be performed"
        ],
        "Contract Value": [
            "subcontract amount", "subcontract price", "contract value", "contract sum",
            "contract total", "total compensation", "base bid", "amount to be paid", "contractor agrees to pay subcontractor"
        ],
        "Safety Requirements": [
            "safety", "osha", "jobsite safety", "ppe", "site safety", "safety training",
            "safety program", "injury prevention"
        ]
    }



    topic = st.selectbox("Choose a contract topic to analyze:", list(topic_keywords.keys()))

    if uploaded_pdf:
        with pdfplumber.open(uploaded_pdf) as pdf:
            paragraphs = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    paragraphs.extend(text.split("\n\n"))  # split full page into blocks

        matches = []
        keywords = topic_keywords[topic]

        for para in paragraphs:
            match_count = sum(kw.lower() in para.lower() for kw in keywords)
            if match_count >= 2:
                matches.append(para.strip())

            if topic == "Contract Value":
                match_threshold = 1
            else:
                match_threshold = 2
    
            if match_count >= match_threshold:
                matches.append(para.strip())


        if matches:
            st.markdown(f"### 🔍 Found {len(matches)} section(s) related to **{topic}**:")
            for idx, section in enumerate(matches):
                with st.expander(f"Match {idx+1}"):
                    st.markdown(
                        f"<div style='overflow-x: auto; white-space: pre-wrap;'>{section}</div>",
                        unsafe_allow_html=True
                    )

            if st.button("Summarize All Matches with AI"):
                with st.spinner("Contacting OpenRouter..."):
                    combined_text = "\n\n".join(matches[:3])  # Limit to 3 to avoid token overflow
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


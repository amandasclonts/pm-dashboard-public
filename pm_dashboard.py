import streamlit as st
import base64
import pdfplumber
import openai

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
    st.subheader("📂 Contract Parsing – Section Lookup (Offline + AI Mode)")

    uploaded_pdf = st.file_uploader("Upload a contract PDF", type=["pdf"])

    topic_keywords = {
        "Liquidated Damages": ["liquidated damages", "penalty", "delay charge"],
        "Payment Terms": ["payment terms", "billing", "invoicing", "retention", "progress payment", "final payments"],
        "Delays": ["delay", "extension of time", "force majeure", "lateness", "time", "schedule", "change order"],
        "Retention": ["retention", "retainage", "withheld", "held payment", "deductible", "liability", "ocip", "ccip"],
        "Schedule": ["schedule", "completion date", "milestone", "timeline", "progress schedule", "schedule of values", "project schedule"],
        "Scope of Work": ["scope of work", "services to be performed", "work included", "deliverables"],
        "Contract Value": ["subcontract amount", "subcontract work", "$"],
        "Safety Requirements": ["safety", "osha", "ppe", "jobsite safety", "training", "safety program", "safety requirements"]
    }

    topic = st.selectbox("Choose a contract topic to analyze:", list(topic_keywords.keys()))

    if uploaded_pdf:
        with pdfplumber.open(uploaded_pdf) as pdf:
            all_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"

        st.success("✅ PDF uploaded and text extracted.")

        if st.button("Find Selected Section"):
            keywords = topic_keywords[topic]
            lines = all_text.split("\n")
            sections = []
            i = 0

            while i < len(lines):
                line = lines[i].strip()
                if any(keyword in line.lower() for keyword in keywords):
                    # Collect paragraph
                    paragraph = [line]
                    i += 1
                    while i < len(lines) and lines[i].strip() != "":
                        paragraph.append(lines[i].strip())
                        i += 1
                    sections.append("\n".join(paragraph))
                else:
                    i += 1

            if sections:
                st.markdown(f"### 🔍 Found the following paragraphs for **{topic}**:")
                for idx, section in enumerate(sections):
                    with st.expander(f"Match {idx+1}"):
                        st.write(section)

                if st.button("Summarize With AI"):
                    with st.spinner("Contacting OpenRouter..."):
                        combined_text = "\n\n".join(sections)
                        prompt = f"""
You are a contract analysis assistant. Summarize the following section from the contract.
Topic: {topic}
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
                st.warning(f"No matches found for **{topic}**.")
 
with tabs[4]:
    st.info("🚧 Stay tuned for more tools here!")


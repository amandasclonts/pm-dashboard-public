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
        "Payment Terms": ["payment terms", "billing", "invoicing", "retention", "progress payment"],
        "Delays": ["delays", "extension of time", "force majeure", "lateness"],
        "Retention": ["retention", "retainage", "withheld", "held payment"],
        "Schedule": ["schedule", "completion date", "milestone", "timeline"],
        "Scope of Work": ["scope of work", "services to be performed", "work included", "deliverables"],
        "Contract Value": ["contract value", "contract amount", "total cost", "lump sum", "$"],
        "Safety Requirements": ["safety", "osha", "ppe", "jobsite safety", "training"]
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
            matching_lines = []
            lines = all_text.split("\n")

            for line in lines:
                for keyword in keywords:
                    if keyword.lower() in line.lower():
                        matching_lines.append(line.strip())
                        break

            combined_text = "\n".join(matching_lines)

            if combined_text.strip():
                st.markdown(f"### 🔍 Extracted Text for **{topic}**:")
                with st.expander("Click to view extracted section"):
                    st.write(combined_text)

                if st.button("Summarize With AI"):
                    with st.spinner("Contacting OpenRouter..."):
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


import streamlit as st
import base64

st.set_page_config(page_title="AI Dashboard", layout="wide")

# --- Simple Password Gate ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "Wbg3033!":  # 👈 Change this!
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

# Create tabbed layout
tabs = st.tabs(["Forecast AI", "Compliance Checker", "Summarizer", "More Coming Soon"])

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
            # Replace with actual summary logic
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
            # Placeholder logic — this is where we'll read the file next
            st.write(f"Summary from: `{uploaded_pdf.name}` — Pages: {page_range or 'All'}")
        else:
            st.warning("Please upload a PDF file first.")

with tabs[3]:
    st.info("Stay tuned for more tools here!")

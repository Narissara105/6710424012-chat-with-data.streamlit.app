import streamlit as st
import pandas as pd
import google.generativeai as genai
import re

# --- Page setup ---
st.set_page_config(page_title="Chat with Data 🤖", layout="wide")
st.title("🤖 My Chatbot and Data Analysis App")
st.subheader("ChatGPT-style Experience with Business Insights")

# --- Gemini API Key ---
key = st.secrets["gemini_api_key"]
genai.configure(api_key=key)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# --- Initialize session state ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None
if "uploaded_metadata" not in st.session_state:
    st.session_state.uploaded_metadata = None

# --- Sidebar Upload Section ---
with st.sidebar:
    st.header("📂 Upload Files")
    uploaded_file = st.file_uploader("Upload Data CSV", type=["csv"])
    if uploaded_file:
        try:
            st.session_state.uploaded_data = pd.read_csv(uploaded_file)
            st.success("✅ Data uploaded successfully")
        except Exception as e:
            st.error(f"❌ Failed to read data: {e}")

    uploaded_metadata = st.file_uploader("Upload Metadata CSV (optional)", type=["csv"])
    if uploaded_metadata:
        try:
            st.session_state.uploaded_metadata = pd.read_csv(uploaded_metadata)
            st.success("✅ Metadata uploaded successfully")
        except Exception as e:
            st.error(f"❌ Failed to read metadata: {e}")

    analyze_data_checkbox = st.checkbox("🔍 Analyze CSV Data with AI", value=True)

# --- Optional Data Preview ---
if st.session_state.uploaded_data is not None:
    with st.expander("📊 Data Preview"):
        st.dataframe(st.session_state.uploaded_data.head())

if st.session_state.uploaded_metadata is not None:
    with st.expander("📄 Metadata Preview"):
        st.dataframe(st.session_state.uploaded_metadata.head())

# --- Show chat history ---
for role, message in st.session_state.chat_history:
    avatar = "🙂" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message)

# --- Function: Summarize as Business Analyst ---
def summarize_result_as_analyst(result: str) -> str:
    summary_prompt = (
        "You are a senior business analyst. Based on the following analysis result, "
        "write a clear, formal, and insightful summary for a business decision-maker.\n\n"
        f"Result:\n{result}"
    )
    summary = model.generate_content(summary_prompt)
    return summary.text

# --- User input ---
if user_input := st.chat_input("Ask a question about your data..."):
    st.chat_message("user", avatar="🙂").markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))

    bot_response = ""
    try:
        df = st.session_state.uploaded_data

        if df is None:
            bot_response = "📂 Please upload a CSV file before asking about the data."
        elif not analyze_data_checkbox:
            bot_response = "🛑 Data analysis is disabled. Please check the 'Analyze CSV Data with AI' option."
        else:
            # Build the prompt: ask for pandas code only (internal)
            columns_info = ", ".join(df.columns)
            prompt = (
                f"The dataset has these columns: {columns_info}.\n"
                f"

import streamlit as st
import pandas as pd
import google.generativeai as genai

# Page config
st.set_page_config(page_title="Chat with Data 🤖", layout="wide")

# Title
st.title("🤖 My Chatbot and Data Analysis App")
st.subheader("ChatGPT-style Experience + CSV Insight")

# --- Configure Gemini API Key ---
key = st.secrets["gemini_api_key"]
genai.configure(api_key=key)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# --- Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # List of tuples (role, message)
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None
if "uploaded_metadata" not in st.session_state:
    st.session_state.uploaded_metadata = None

# --- Upload Section ---
with st.sidebar:
    st.header("📂 Upload Files")
    uploaded_file = st.file_uploader("Upload Data CSV", type=["csv"])
    if uploaded_file:
        try:
            st.session_state.uploaded_data = pd.read_csv(uploaded_file)
            st.success("✅ Data uploaded")
        except Exception as e:
            st.error(f"❌ Failed to read data: {e}")

    uploaded_metadata = st.file_uploader("Upload Metadata CSV (optional)", type=["csv"])
    if uploaded_metadata:
        try:
            st.session_state.uploaded_metadata = pd.read_csv(uploaded_metadata)
            st.success("✅ Metadata uploaded")
        except Exception as e:
            st.error(f"❌ Failed to read metadata: {e}")

    analyze_data_checkbox = st.checkbox("🔍 Analyze CSV Data with AI", value=True)

# --- Show Uploaded Previews
if st.session_state.uploaded_data is not None:
    with st.expander("📊 Data Preview"):
        st.dataframe(st.session_state.uploaded_data.head())

if st.session_state.uploaded_metadata is not None:
    with st.expander("📄 Metadata Preview"):
        st.dataframe(st.session_state.uploaded_metadata.head())

# --- Chat History with Avatars ---
for role, message in st.session_state.chat_history:
    avatar = "🙂" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message)

# --- Chat Input ---
if user_input := st.chat_input("Ask me something or request analysis..."):
    # Show user message with emoji
    st.chat_message("user", avatar="🙂").markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))

    bot_response = ""

    try:
        if st.session_state.uploaded_data is not None:
            if analyze_data_checkbox:
                # Optional metadata
                metadata_info = ""
                if st.session_state.uploaded_metadata is not None:
                    metadata_info = "\n\nHere is the metadata (column descriptions):\n"
                    metadata_info += st.session_state.uploaded_metadata.to_string(index=False)

                if "analyze" in user_input.lower() or "insight" in user_input.lower():
                    data_description = st.session_state.uploaded_data.describe().to_string()
                    prompt = (
                        f"Analyze the following dataset and provide insights:\n\n"
                        f"{data_description}"
                        f"{metadata_info}"
                    )
                else:
                    prompt = user_input

                response = model.generate_content(prompt)
                bot_response = response.text
            else:
                bot_response = "🛑 Data analysis is disabled. Please check the 'Analyze CSV Data with AI' option."
        else:
            bot_response = "📂 Please upload a CSV data file first."

    except Exception as e:
        bot_response = f"⚠️ Error during response generation: {e}"

    # Show assistant message with emoji
    st.chat_message("assistant", avatar="🤖").markdown(bot_response)
    st.session_state.chat_history.append(("assistant", bot_response))

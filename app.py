import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- Configure Gemini API Key ---
key = st.secrets["gemini_api_key"]
genai.configure(api_key=key)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# --- Initialize Streamlit App ---
st.title("🤖 Chatbot with Data Analysis")
st.subheader("Upload Required Files")

# --- Session state initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "transactions" not in st.session_state:
    st.session_state.transactions = None

if "data_dict" not in st.session_state:
    st.session_state.data_dict = None

# --- File uploader ---
uploaded_files = st.file_uploader(
    "Upload 'transactions.csv' and 'data_dict.csv'",
    type=["csv"],
    accept_multiple_files=True
)

# --- File processing logic ---
required_files = {"transactions.csv": "transactions", "data_dict.csv": "data_dict"}

for uploaded_file in uploaded_files or []:
    if uploaded_file.name in required_files:
        try:
            setattr(st.session_state, required_files[uploaded_file.name], pd.read_csv(uploaded_file))
            st.success(f"✅ {uploaded_file.name} loaded successfully.")
            st.write(f"### {uploaded_file.name.split('.')[0].title()} Preview")
            st.dataframe(getattr(st.session_state, required_files[uploaded_file.name]).head())
        except Exception as e:
            st.error(f"❌ Failed to load {uploaded_file.name}: {e}")
    else:
        st.warning(f"⚠️ Unexpected file '{uploaded_file.name}' uploaded.")

# --- Checkbox to control AI analysis ---
analyze_data_checkbox = st.checkbox("Analyze uploaded CSV data with AI", value=True)

# --- Chat Input and Processing ---
user_input = st.chat_input("Type your message here...")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    if not model:
        st.error("❌ Gemini API model is not properly configured.")
    else:
        prompt = f"User: {user_input}\n"

        if analyze_data_checkbox:
            if st.session_state.transactions is not None:
                data_summary = st.session_state.transactions.describe(include='all').to_string()
                prompt += f"\nDataset Summary:\n{data_summary}\n"
            if st.session_state.data_dict is not None:
                metadata_info = st.session_state.data_dict.to_string()
                prompt += f"\nMetadata:\n{metadata_info}\n"

        elif not (st.session_state.transactions and st.session_state.data_dict):
            prompt += "\nNote: Required data files are not uploaded or fully loaded yet.\n"

        try:
            response = model.generate_content(prompt)
            bot_response = response.text
        except Exception as e:
            bot_response = f"⚠️ Error generating response: {e}"

        st.session_state.chat_history.append(("assistant", bot_response))
        st.chat_message("assistant").markdown(bot_response)

# --- Display previous chat history ---
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

import streamlit as st
import pandas as pd
import google.generativeai as genai

# Set up the Streamlit app layout
st.title("🤖 My Chatbot and Data Analysis App")
st.subheader("Upload your data files below")

# Configure Gemini API Key
key = st.secrets["gemini_api_key"]
genai.configure(api_key=key)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None
if "metadata" not in st.session_state:
    st.session_state.metadata = None

# --- FILE UPLOAD ---
st.subheader("Upload Required Files")

uploaded_files = st.file_uploader(
    "Upload 'transactions.csv' and 'data_dict.csv'",
    type=["csv"],
    accept_multiple_files=True
)

# Process uploaded files
for uploaded_file in uploaded_files or []:
    if uploaded_file.name == "transactions.csv":
        try:
            st.session_state.uploaded_data = pd.read_csv(uploaded_file)
            st.success("✅ transactions.csv loaded successfully.")
            st.write("### Transactions Preview")
            st.dataframe(st.session_state.uploaded_data.head())
        except Exception as e:
            st.error(f"❌ Failed to read transactions.csv: {e}")
    elif uploaded_file.name == "data_dict.csv":
        try:
            st.session_state.metadata = pd.read_csv(uploaded_file)
            st.success("✅ data_dict.csv (metadata) loaded successfully.")
            st.write("### Metadata Preview")
            st.dataframe(st.session_state.metadata.head())
        except Exception as e:
            st.error(f"❌ Failed to read data_dict.csv: {e}")
    else:
        st.warning(f"⚠️ Unexpected file: {uploaded_file.name}. Expected 'transactions.csv' or 'data_dict.csv'")

# --- CHECKBOX TO ENABLE ANALYSIS ---
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# --- CHAT INPUT ---
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    if model:
        try:
            if st.session_state.uploaded_data is not None:
                data_description = st.session_state.uploaded_data.describe().to_string()
                prompt = f"The user says: '{user_input}'\n\nHere is the dataset description:\n{data_description}"

                if st.session_state.metadata is not None:
                    metadata_description = st.session_state.metadata.to_string()
                    prompt += f"\n\nMetadata:\n{metadata_description}"

                if not analyze_data_checkbox:
                    prompt += "\n\nNote: The user has not requested analysis, but this data may help your response."

                response = model.generate_content(prompt)
                bot_response = response.text
            else:
                # No dataset uploaded
                bot_response = "Please upload 'transactions.csv' to enable analysis or contextual chat."

            st.session_state.chat_history.append(("assistant", bot_response))
            st.chat_message("assistant").markdown(bot_response)

        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
    else:
        st.warning("Please configure the Gemini API Key to enable chat responses.")

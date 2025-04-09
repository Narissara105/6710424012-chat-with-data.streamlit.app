import streamlit as st
import pandas as pd
import google.generativeai as genai

# Set up the Streamlit app layout
st.title("🤖 My Chatbot and Data Analysis App")
st.subheader("Conversation and Data Analysis")

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

# Display previous chat messages
for role, message in st.session_state.chat_history:
    st.chat_message(role).markdown(message)

# --- MAIN DATA FILE UPLOADER ---
st.subheader("Upload CSV for Analysis")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], key="main_csv")

if uploaded_file is not None:
    try:
        st.session_state.uploaded_data = pd.read_csv(uploaded_file)
        st.success("File successfully uploaded and read.")

        st.write("### Uploaded Data Preview")
        st.dataframe(st.session_state.uploaded_data.head())
    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")

# --- METADATA FILE UPLOADER ---
st.subheader("Upload Metadata for Dataset")
metadata_file = st.file_uploader("Choose a Metadata CSV file", type=["csv"], key="metadata_csv")

if metadata_file is not None:
    try:
        st.session_state.metadata = pd.read_csv(metadata_file)
        st.success("Metadata file successfully uploaded and read.")

        st.write("### Metadata Preview")
        st.dataframe(st.session_state.metadata.head())
    except Exception as e:
        st.error(f"An error occurred while reading the metadata file: {e}")

# --- ANALYSIS TOGGLE ---
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# --- CHATBOT INPUT ---
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    if model:
        try:
            if st.session_state.uploaded_data is not None and analyze_data_checkbox:
                if "analyze" in user_input.lower() or "insight" in user_input.lower():
                    # Prepare data and metadata description
                    data_description = st.session_state.uploaded_data.describe().to_string()

                    if st.session_state.metadata is not None:
                        metadata_description = st.session_state.metadata.to_string()
                        prompt = (
                            f"Analyze the dataset below and provide insights. "
                            f"Here is the dataset description:\n{data_description}\n\n"
                            f"And here is the metadata information:\n{metadata_description}"
                        )
                    else:
                        prompt = f"Analyze the following dataset and provide insights:\n\n{data_description}"

                    response = model.generate_content(prompt)
                    bot_response = response.text
                else:
                    response = model.generate_content(user_input)
                    bot_response = response.text

            elif not analyze_data_checkbox:
                bot_response = (
                    "Data analysis is disabled. Please select the 'Analyze CSV Data with AI' checkbox to enable analysis."
                )
            else:
                bot_response = "Please upload a CSV file first, then ask me to analyze it."

            st.session_state.chat_history.append(("assistant", bot_response))
            st.chat_message("assistant").markdown(bot_response)

        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
    else:
        st.warning("Please configure the Gemini API Key to enable chat responses.")

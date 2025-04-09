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

# --- MAIN CSV FILE UPLOADER ---
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
st.subheader("Upload Metadata for Dataset (Optional)")
metadata_file = st.file_uploader("Choose a Metadata CSV file", type=["csv"], key="metadata_csv")

if metadata_file is not None:
    try:
        st.session_state.metadata = pd.read_csv(metadata_file)
        st.success("Metadata file successfully uploaded and read.")
        st.write("### Metadata Preview")
        st.dataframe(st.session_state.metadata.head())
    except Exception as e:
        st.error(f"An error occurred while reading the metadata file: {e}")

# --- ENABLE/DISABLE DATA ANALYSIS ---
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# --- USER CHAT INPUT ---
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    if model:
        try:
            # If CSV uploaded, use data in every prompt
            if st.session_state.uploaded_data is not None:
                data_description = st.session_state.uploaded_data.describe().to_string()
                prompt = (
                    f"The user says: '{user_input}'\n\n"
                    f"Here is the dataset description:\n{data_description}"
                )

                # If metadata exists, add it too
                if st.session_state.metadata is not None:
                    metadata_description = st.session_state.metadata.to_string()
                    prompt += f"\n\nAnd here is the metadata:\n{metadata_description}"

                # Add a note if checkbox is off
                if not analyze_data_checkbox:
                    prompt += "\n\nNote: The user has not requested analysis, but this data may help your response."

                response = model.generate_content(prompt)
                bot_response = response.text

            else:
                # No CSV: normal conversation
                response = model.generate_content(user_input)
                bot_response = response.text

            st.session_state.chat_history.append(("assistant", bot_response))
            st.chat_message("assistant").markdown(bot_response)

        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
    else:
        st.warning("Please configure the Gemini API Key to enable chat responses.")

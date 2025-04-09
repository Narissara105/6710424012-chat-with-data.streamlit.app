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

# ---------- Function to Build Prompt ----------
def generate_code_prompt(question, df_name, data_df, metadata_df):
    data_dict_text = metadata_df.to_string(index=False) if metadata_df is not None else "No metadata provided."
    example_record = data_df.head(2).to_string(index=False)

    prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user's question and the provided DataFrame information.

Here's the context:
**User Question:**
{question}
**DataFrame Name:**
{df_name}
**DataFrame Details:**
{data_dict_text}
**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that addresses the user's question by querying or manipulating the DataFrame.
2. **Crucially, use the `exec()` function to execute the generated code.**
3. Do not import pandas
4. Change date column type to datetime
5. **Store the result of the executed code in a variable named `ANSWER`.**
6. Assume the DataFrame is already loaded into a pandas DataFrame object named `{df_name}`.
7. Keep the generated code concise and focused on answering the question.
8. If the question requires a specific output format (e.g., a list, a single value), ensure `ANSWER` holds that format.
"""
    return prompt

# ---------- File Upload Section ----------
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

# ---------- Checkbox to toggle AI code generation ----------
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# ---------- Chat Section ----------
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    if model:
        try:
            if st.session_state.uploaded_data is not None:
                df_name = "df"
                df = st.session_state.uploaded_data.copy()
                globals()[df_name] = df

                if analyze_data_checkbox:
                    # Generate Python code with full context
                    prompt = generate_code_prompt(
                        question=user_input,
                        df_name=df_name,
                        data_df=st.session_state.uploaded_data,
                        metadata_df=st.session_state.metadata,
                    )

                    response = model.generate_content(prompt)
                    generated_code = response.text

                    st.markdown("#### 🧠 Generated Python Code")
                    st.code(generated_code, language="python")

                    try:
                        exec(generated_code, globals())
                        st.success("✅ Code executed successfully.")
                        st.markdown("#### 📊 Result (from `ANSWER`):")
                        st.write(globals().get("ANSWER", "No variable `ANSWER` was defined."))
                    except Exception as e:
                        st.error(f"⚠️ Error while executing the code:\n\n{e}")
                else:
                    # General chat with data context
                    data_description = df.describe().to_string()
                    prompt = (
                        f"The user says: '{user_input}'\n\n"
                        f"Here is the dataset description:\n{data_description}"
                    )

                    if st.session_state.metadata is not None:
                        metadata_description = st.session_state.metadata.to_string()
                        prompt += f"\n\nAnd here is the metadata:\n{metadata_description}"

                    prompt += "\n\nNote: The user has not requested code, but data context may help."

                    response = model.generate_content(prompt)
                    bot_response = response.text
                    st.session_state.chat_history.append(("assistant", bot_response))
                    st.chat_message("assistant").markdown(bot_response)
            else:
                st.warning("Please upload 'transactions.csv' to enable chat or analysis.")
        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
    else:
        st.warning("Please configure the Gemini API Key to enable chat responses.")

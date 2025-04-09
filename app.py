import streamlit as st
import pandas as pd
import google.generativeai as genai

# Layout
st.title("🤖 My Chatbot and Data Analysis App")
st.subheader("Upload your data files below")

# API config
key = st.secrets["gemini_api_key"]
genai.configure(api_key=key)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None
if "metadata" not in st.session_state:
    st.session_state.metadata = None

# Prompt generator
def generate_code_prompt(question, df_name, data_df, metadata_df):
    data_dict_text = metadata_df.to_string(index=False) if metadata_df is not None else "No metadata provided."
    example_record = data_df.head(2).to_string(index=False)

    return f"""
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

# -------- FILE UPLOAD --------
st.subheader("Upload Required Files")

# Upload transactions.csv
transactions_file = st.file_uploader("Upload transactions.csv", type=["csv"], key="transactions")
if transactions_file:
    try:
        st.session_state.uploaded_data = pd.read_csv(transactions_file)
        st.success("✅ transactions.csv loaded successfully.")
        st.write("### Transactions Preview")
        st.dataframe(st.session_state.uploaded_data.head())
    except Exception as e:
        st.error(f"Error loading transactions.csv: {e}")

# Upload data_dict.csv
data_dict_file = st.file_uploader("Upload data_dict.csv (Metadata)", type=["csv"], key="dictionary")
if data_dict_file:
    try:
        st.session_state.metadata = pd.read_csv(data_dict_file)
        st.success("✅ data_dict.csv loaded successfully.")
        st.write("### Metadata Preview")
        st.dataframe(st.session_state.metadata.head())
    except Exception as e:
        st.error(f"Error loading data_dict.csv: {e}")

# -------- CHECKBOX (Auto-checked) --------
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI", value=st.session_state.uploaded_data is not None)

# -------- CHAT --------
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    if model:
        try:
            if st.session_state.uploaded_data is not None:
                df_name = "df"
                df = st.session_state.uploaded_data.copy()
                globals()[df_name] = df  # For exec()

                if analyze_data_checkbox:
                    # Generate Python code with context
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
                        prompt += f"\n\nMetadata:\n{st.session_state.metadata.to_string()}"

                    prompt += "\n\nNote: The user has not requested code, but data context may help."

                    response = model.generate_content(prompt)
                    bot_response = response.text
                    st.session_state.chat_history.append(("assistant", bot_response))
                    st.chat_message("assistant").markdown(bot_response)
            else:
                st.warning("⚠️ Please upload transactions.csv to begin.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

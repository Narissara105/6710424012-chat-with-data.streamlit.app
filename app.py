import streamlit as st
import pandas as pd
import google.generativeai as genai
import numpy as np
import datetime
from dateutil import parser as dateparser
import math
import re

# -------------------------------
# ฟังก์ชันโหลด CSV แบบยืดหยุ่น
# -------------------------------
def load_flexible_csv(uploaded_file):
    tried_encodings = ["utf-8", "utf-8-sig", "iso-8859-1", "windows-874"]
    delimiters = [",", ";", "\t", "|"]
    for encoding in tried_encodings:
        for sep in delimiters:
            try:
                df = pd.read_csv(
                    uploaded_file,
                    encoding=encoding,
                    sep=sep,
                    engine="python",
                    skipinitialspace=True,
                    na_values=["", "NA", "N/A", "-", "--", "null"],
                    keep_default_na=True
                )
                if df.shape[1] >= 2:
                    return df
            except Exception:
                continue
    raise ValueError("❌ ไม่สามารถอ่านไฟล์ CSV ได้")

# -------------------------------
# ตั้งค่า Gemini
# -------------------------------
st.set_page_config(page_title="Chat with Data 🤖", layout="wide")
st.title("🤖 My Chatbot and Data Analysis App")
st.subheader("ถามคำถามเชิงธุรกิจ แล้วรับคำตอบสั้น กระชับ เหมาะกับผู้บริหาร")

key = st.secrets["gemini_api_key"]
genai.configure(api_key=key)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# -------------------------------
# Session State
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None
if "uploaded_dictionary" not in st.session_state:
    st.session_state.uploaded_dictionary = None
if "analyze_data_checkbox" not in st.session_state:
    st.session_state.analyze_data_checkbox = False

# -------------------------------
# Upload Files
# -------------------------------
uploaded_file = st.file_uploader("📁 Upload CSV for analysis", type=["csv"])
if uploaded_file:
    try:
        df = load_flexible_csv(uploaded_file)
        st.session_state.uploaded_data = df
        st.success("✅ File uploaded successfully.")
        st.write("### Uploaded Data Preview")
        st.dataframe(df.head())
        st.session_state.analyze_data_checkbox = True
    except Exception as e:
        st.error(f"❌ Failed to read CSV: {e}")

uploaded_dict = st.file_uploader("📄 Upload Data Dictionary (optional)", type=["csv"])
if uploaded_dict:
    try:
        dictionary_df = pd.read_csv(uploaded_dict)
        st.session_state.uploaded_dictionary = dictionary_df
        st.success("✅ Data dictionary uploaded.")
        with st.expander("📋 Data Dictionary Preview"):
            st.dataframe(dictionary_df)
    except Exception as e:
        st.error(f"❌ Failed to read data dictionary: {e}")

# -------------------------------
# Checkbox วิเคราะห์ด้วย AI
# -------------------------------
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI", value=st.session_state.analyze_data_checkbox)

# -------------------------------
# Show Chat History
# -------------------------------
for role, message in st.session_state.chat_history:
    avatar = "🙂" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message)

# -------------------------------
# สรุปคำตอบแบบผู้บริหาร (กระชับมาก)
# -------------------------------
def summarize_as_analyst(answer: str) -> str:
    summary_prompt = (
        """You are a business analyst. 
Summarize this result for executives level for making decision. 
Make it briefly with significant information. 
Answer the best answer without requesting other information.

"""
        + answer
    )
    response = model.generate_content(summary_prompt)
    return response.text.strip()

# -------------------------------
# รับคำถามจากผู้ใช้
# -------------------------------
if user_input := st.chat_input("Type your business question about the data..."):
    st.chat_message("user", avatar="🙂").markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))

    try:
        if model and st.session_state.uploaded_data is not None and analyze_data_checkbox:
            df = st.session_state.uploaded_data
            df_name = "df"
            question = user_input
            data_dict_text = df.dtypes.astype(str).to_string()
            example_record = df.head(2).to_string(index=False)

            dict_text = ""
            if st.session_state.uploaded_dictionary is not None:
                dict_text = "\n\n**Data Dictionary:**\n" + st.session_state.uploaded_dictionary.to_string(index=False)

            prompt = f"""
You are a helpful Python code generator. 
Your job is to write Python code based on the question and DataFrame.

**User Question:** {question}

**DataFrame Name:** {df_name}
**DataFrame Info:** {data_dict_text}
**Sample Rows:**\n{example_record}
{dict_text}

**Instructions:**
- Write Python code using the dataframe `df`
- Use `exec()` to execute the code
- Do NOT import pandas
- Use `pd.to_datetime()` for dates
- Save the result in a variable called `ANSWER`
- Keep it short, focused, and avoid undefined variables
"""

            code_response = model.generate_content(prompt)
            raw_code = code_response.text
            match = re.search(r"```python(.*?)```", raw_code, re.DOTALL)
            generated_code = match.group(1).strip() if match else raw_code.strip()

            try:
                # ✅ รองรับ built-in + ตัวแปรสะกดผิด
                local_vars = {
                    df_name: df.copy(),
                    "pd": pd,
                    "datetime": datetime,
                    "dt": pd.to_datetime,
                    "np": np,
                    "math": math,
                    "dateparser": dateparser,
                    "__builtins__": __builtins__,
                    "datetim": datetime,
                    "dateime": datetime,
                    "dtt": pd.to_datetime,
                }

                exec(generated_code, {}, local_vars)

                answer = local_vars.get("ANSWER", "No variable named 'ANSWER' was created.")

                if isinstance(answer, pd.DataFrame):
                    try:
                        answer_text = answer.head(5).to_string(index=False)
                    except:
                        answer_text = str(answer.head(5))
                else:
                    answer_text = str(answer)

                bot_response = summarize_as_analyst(answer_text)

                styled_bot_response = f"""
<div style="background-color:#fff9db; padding: 1rem; border-radius: 0.5rem; border: 1px solid #f1e6b8;">
{bot_response}
</div>
"""
                st.chat_message("assistant", avatar="🤖").markdown(styled_bot_response, unsafe_allow_html=True)

            except NameError as name_err:
                bot_response = f"⚠️ Variable not defined in code: `{name_err}`. Please rephrase your question or be more specific."
                st.chat_message("assistant", avatar="🤖").markdown(bot_response)

            except Exception as exec_error:
                bot_response = f"⚠️ Code execution error:\n`{exec_error}`"
                st.chat_message("assistant", avatar="🤖").markdown(bot_response)

            st.session_state.chat_history.append(("assistant", bot_response))

        elif not analyze_data_checkbox:
            bot_response = "📌 Please enable the analysis checkbox."
            st.chat_message("assistant", avatar="🤖").markdown(bot_response)
        else:
            bot_response = "📂 Please upload a CSV file first."
            st.chat_message("assistant", avatar="🤖").markdown(bot_response)

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

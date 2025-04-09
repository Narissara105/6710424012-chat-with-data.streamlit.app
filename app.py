import streamlit as st
import pandas as pd
import google.generativeai as genai
import numpy as np
import datetime
from dateutil import parser as dateparser
import math
import re

try:
    from rapidfuzz import process
except ModuleNotFoundError:
    process = None

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
st.set_page_config(page_title="Chat with Your Data", layout="wide")
st.title("🤖 My Chatbot and Data Analysis App")
st.subheader("ถามมาตอบไป กับ Chat with Your Data")

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
if "qa_memory" not in st.session_state:
    st.session_state.qa_memory = {}

# -------------------------------
# Upload Files
# -------------------------------
uploaded_file = st.file_uploader("📁 อัปโหลดไฟล์ CSV สำหรับวิเคราะห์", type=["csv"])
if uploaded_file:
    try:
        df = load_flexible_csv(uploaded_file)
        st.session_state.uploaded_data = df
        st.success("✅ อัปโหลดข้อมูลสำเร็จ")
        st.write("### ตัวอย่างข้อมูล")
        st.dataframe(df.head())
        st.session_state.analyze_data_checkbox = True
    except Exception as e:
        st.error(f"❌ ไม่สามารถอ่านไฟล์ได้: {e}")

uploaded_dict = st.file_uploader("📄 อัปโหลด Data Dictionary (ถ้ามี)", type=["csv"])
if uploaded_dict:
    try:
        dictionary_df = pd.read_csv(uploaded_dict)
        st.session_state.uploaded_dictionary = dictionary_df
        st.success("✅ อัปโหลด Data Dictionary สำเร็จ")
        with st.expander("📋 แสดง Data Dictionary"):
            st.dataframe(dictionary_df)
    except Exception as e:
        st.error(f"❌ ไม่สามารถอ่าน Dictionary: {e}")

# -------------------------------
# Checkbox วิเคราะห์ด้วย AI
# -------------------------------
analyze_data_checkbox = st.checkbox("วิเคราะห์ข้อมูลด้วย AI", value=st.session_state.analyze_data_checkbox)

# -------------------------------
# Show Chat History
# -------------------------------
for role, message in st.session_state.chat_history:
    avatar = "🙂" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message)

# -------------------------------
# รับคำถามจากผู้ใช้
# -------------------------------
if user_input := st.chat_input("พิมพ์คำถามของคุณที่นี่"):
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

            # ตรวจสอบว่าเคยตอบคำถามนี้หรือคำถามใกล้เคียงแล้วหรือยัง (fuzzy match)
            if process and st.session_state.qa_memory:
                similar_question, score, _ = process.extractOne(
                    question,
                    list(st.session_state.qa_memory.keys()),
                    score_cutoff=90
                )
                if similar_question:
                    cached_answer = st.session_state.qa_memory[similar_question]
                    st.chat_message("assistant", avatar="🤖").markdown(cached_answer, unsafe_allow_html=True)
                    st.session_state.chat_history.append(("assistant", cached_answer))
                    raise Exception("✅ คำถามซ้ำ ตอบจาก cache")

            prompt = f"""
You are a multilingual data analyst assistant who writes Python code to answer user questions based on a pandas DataFrame.

**User Question:** {question}

**DataFrame Name:** {df_name}
**DataFrame Info:**\n{data_dict_text}
**Sample Rows:**\n{example_record}
{dict_text}

**Instructions:**
- Write Python code using the dataframe `df`
- Use `exec()` to execute the code
- Convert date columns using `pd.to_datetime()`
- Save the result in a variable named `ANSWER`
- If the question asks for ranking or top N, return a DataFrame with name/value
- If the question asks for total/sum, return a single number
- DO NOT import pandas or datetime
- Do NOT use undefined variables
- Be brief, accurate, and business-relevant in your result
"""

            code_response = model.generate_content(prompt)
            raw_code = code_response.text
            match = re.search(r"```python(.*?)```", raw_code, re.DOTALL)
            generated_code = match.group(1).strip() if match else raw_code.strip()

            local_vars = {
                df_name: df.copy(),
                "df": df,
                "data": df,
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
                "datetime_module": datetime,
                "datetime_now": datetime.datetime.now,
            }

            exec(generated_code, {}, local_vars)
            answer = local_vars.get("ANSWER", "No variable named 'ANSWER' was created.")

            if isinstance(answer, pd.DataFrame):
                answer_text = answer.head(5).to_string(index=False)
            else:
                answer_text = str(answer)

            def summarize_as_analyst(answer: str) -> str:
                summary_prompt = f"ตอบคำถามต่อไปนี้แบบสั้น กระชับ และเหมาะกับผู้บริหาร:\n{answer}"
                response = model.generate_content(summary_prompt)
                return response.text.strip()

            bot_response = summarize_as_analyst(answer_text)
            styled_bot_response = bot_response
            st.chat_message("assistant", avatar="🤖").markdown(styled_bot_response, unsafe_allow_html=True)
            st.session_state.chat_history.append(("assistant", styled_bot_response))
            st.session_state.qa_memory[question] = styled_bot_response

        elif not analyze_data_checkbox:
            bot_response = "📌 โปรดเปิดใช้งานกล่องวิเคราะห์ข้อมูลก่อน"
            st.chat_message("assistant", avatar="🤖").markdown(bot_response)
        else:
            bot_response = "📂 โปรดอัปโหลดไฟล์ CSV ก่อนเริ่มวิเคราะห์"
            st.chat_message("assistant", avatar="🤖").markdown(bot_response)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")

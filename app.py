import streamlit as st
import fitz
import pandas as pd
import google.generativeai as genai
from io import BytesIO
import re

st.set_page_config(page_title="CNU Translation LQA", layout="wide", page_icon="📘")

st.title("📘 CNU TRANSLATION LQA SOFTWARE")
st.markdown("**Kiểm định chất lượng dịch thuật chuyên sâu - Format báo cáo chi tiết**")

with st.sidebar:
    st.header("🔑 API Key")
    gemini_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("gemini_key", ""))
    if st.button("Lưu Key"):
        st.session_state.gemini_key = gemini_key
        if gemini_key:
            genai.configure(api_key=gemini_key)
            st.success("✅ Key đã lưu!")

col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("📤 File NGUỒN (Anh)", type=["pdf"], key="source")
with col2:
    trans_file = st.file_uploader("📤 File DỊCH (Việt)", type=["pdf"], key="trans")

if source_file and trans_file and st.session_state.get("gemini_key"):
    with st.spinner("Đang trích xuất văn bản..."):
        doc_src = fitz.open(stream=source_file.read(), filetype="pdf")
        src_text = "".join([doc_src[i].get_text() for i in range(len(doc_src))])
        doc_src.close()

        doc_trans = fitz.open(stream=trans_file.read(), filetype="pdf")
        trans_text = "".join([doc_trans[i].get_text() for i in range(len(doc_trans))])
        doc_trans.close()

    st.success("✅ Đã xử lý cả hai file!")

    if st.button("🚀 Tạo Báo cáo Kiểm định Chi Tiết (giống Excel của bạn)"):
        with st.spinner("Gemini đang phân tích sâu từng đoạn..."):
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""Bạn là chuyên gia kiểm duyệt dịch Anh-Việt chuyên nghiệp. 
Phân tích so sánh từng đoạn giữa bản gốc và bản dịch. Trả về **dạng bảng** với các cột sau:

STT | Nguyên tác (Tiếng Anh) | Bản dịch (Tiếng Việt) | Kết quả kiểm định

Yêu cầu:
- Phân tích chi tiết, nghiêm ngặt
- Chỉ ra rõ: sót ý, dịch máy móc, sai thuật ngữ, câu dịch quá ngắn/dài, không tự nhiên, sai ngữ pháp, sai ngữ cảnh học thuật/pháp lý
- Dùng các nhận xét cụ thể như: "Đạt yêu cầu", "👉 Nghi ngờ sót ý (Câu dịch quá ngắn)", "👉 Sai thuật ngữ", "👉 Dịch tự nhiên tốt", v.v.
- Phân tích ít nhất 20-30 đoạn quan trọng nhất

Bản gốc:
{src_text[:35000]}

Bản dịch:
{trans_text[:35000]}"""

            response = model.generate_content(prompt)
            
            st.subheader("📊 Báo cáo Kiểm định Chất lượng")
            st.markdown(response.text)

            # Tạo Excel giống báo cáo của bạn
            # (Chúng ta có thể parse bảng Markdown thành DataFrame nếu cần, nhưng tạm export text trước)
            excel_buffer = BytesIO()
            # Có thể cải tiến sau để tự động tạo Excel đầy đủ
            df_simple = pd.DataFrame({"Báo cáo": [response.text]})
            df_simple.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            
            st.download_button("📥 Tải báo cáo Excel", excel_buffer, "Bao_cao_kiem_dinh.xlsx", 
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.info("Vui lòng tải lên cả hai file PDF và nhập API Key.")

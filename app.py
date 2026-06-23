import streamlit as st
import fitz
import pandas as pd
import google.generativeai as genai
from io import BytesIO

st.set_page_config(page_title="CNU Translation LQA", layout="wide", page_icon="📘")

st.title("📘 CNU TRANSLATION LQA SOFTWARE")
st.markdown("**Kiểm định chất lượng dịch thuật chuyên sâu**")

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

    if st.button("🚀 Tạo Báo cáo Kiểm định Chi Tiết"):
        with st.spinner("Gemini đang phân tích sâu..."):
            try:
                # Model đã sửa
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""Bạn là chuyên gia kiểm duyệt dịch Anh-Việt. Phân tích so sánh chi tiết và trả về **bảng** với cấu trúc:

STT | Nguyên tác (Tiếng Anh) | Bản dịch (Tiếng Việt) | Kết quả kiểm định

Yêu cầu:
- Nhận xét cụ thể, chuyên nghiệp
- Dùng các cụm: "Đạt yêu cầu", "👉 Nghi ngờ sót ý (Câu dịch quá ngắn)", "👉 Sai thuật ngữ", "👉 Dịch máy móc", "👉 Tốt, tự nhiên"...

Bản gốc: {src_text[:32000]}

Bản dịch: {trans_text[:32000]}"""

                response = model.generate_content(prompt)
                st.subheader("📊 Báo cáo Kiểm định")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Lỗi API: {str(e)}")
                st.info("Nếu vẫn lỗi, thử model 'gemini-pro' thay vì 'gemini-1.5-flash'")

else:
    st.info("Vui lòng tải lên cả hai file PDF và nhập API Key.")

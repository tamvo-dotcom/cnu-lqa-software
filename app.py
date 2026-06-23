import streamlit as st
import fitz
import pandas as pd
import google.generativeai as genai
from io import BytesIO

st.set_page_config(page_title="CNU Translation LQA", layout="wide")

st.title("📘 CNU TRANSLATION LQA SOFTWARE")
st.markdown("**Kiểm định chất lượng dịch thuật**")

with st.sidebar:
    st.header("🔑 API Key")
    gemini_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("gemini_key", ""))
    if st.button("Lưu Key"):
        st.session_state.gemini_key = gemini_key
        if gemini_key:
            genai.configure(api_key=gemini_key)
            st.success("✅ Key đã lưu!")

    if st.button("🔍 Kiểm tra Model Khả Dụng"):
        try:
            models = genai.list_models()
            st.write("Các model khả dụng:")
            for m in models:
                if 'generateContent' in m.supported_generation_methods:
                    st.write(f"✅ {m.name}")
        except Exception as e:
            st.error(f"Lỗi: {e}")

col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("📤 File NGUỒN (Anh)", type=["pdf"], key="source")
with col2:
    trans_file = st.file_uploader("📤 File DỊCH (Việt)", type=["pdf"], key="trans")

if source_file and trans_file and st.session_state.get("gemini_key"):
    with st.spinner("Đang trích xuất..."):
        doc_src = fitz.open(stream=source_file.read(), filetype="pdf")
        src_text = "".join([doc_src[i].get_text() for i in range(len(doc_src))])
        doc_src.close()

        doc_trans = fitz.open(stream=trans_file.read(), filetype="pdf")
        trans_text = "".join([doc_trans[i].get_text() for i in range(len(doc_trans))])
        doc_trans.close()

    st.success("✅ Đã xử lý cả hai file!")

    if st.button("🚀 Tạo Báo cáo Kiểm định"):
        with st.spinner("Đang phân tích..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')  # Thử model này trước
                prompt = f"""Phân tích so sánh bản dịch. Trả về bảng:
STT | Gốc | Dịch | Kết quả kiểm định

Bản gốc: {src_text[:25000]}
Bản dịch: {trans_text[:25000]}"""
                response = model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Lỗi: {str(e)}")
                st.info("Nhấn nút 'Kiểm tra Model Khả Dụng' ở sidebar để xem model nào dùng được.")

else:
    st.info("Tải 2 file PDF và nhập API Key.")

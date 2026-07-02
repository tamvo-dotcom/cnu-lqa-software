import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="CNU Translation LQA", layout="wide", page_icon="📘")
st.title("📘 CNU TRANSLATION LQA SOFTWARE")
st.markdown("**Tiền kiểm định chất lượng dịch thuật Anh - Việt**")

# Sidebar API Key
with st.sidebar:
    st.header("🔑 API Key")
    gemini_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("gemini_key", ""))
    if st.button("Lưu Key"):
        st.session_state.gemini_key = gemini_key
        if gemini_key:
            genai.configure(api_key=gemini_key)
            st.success("✅ Key đã lưu!")

# Upload files
col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("📤 File NGUỒN (Tiếng Anh - PDF)", type=["pdf"], key="source")
with col2:
    trans_file = st.file_uploader("📤 File DỊCH (Tiếng Việt - PDF)", type=["pdf"], key="trans")

if source_file and trans_file and st.session_state.get("gemini_key"):
    with st.spinner("Đang trích xuất văn bản từ PDF..."):
        try:
            # Đọc file nguồn
            doc_src = fitz.open(stream=source_file.read(), filetype="pdf")
            src_text = "".join([page.get_text() for page in doc_src])
            doc_src.close()
            
            # Đọc file dịch
            doc_trans = fitz.open(stream=trans_file.read(), filetype="pdf")
            trans_text = "".join([page.get_text() for page in doc_trans])
            doc_trans.close()
            
            st.success(f"✅ Đã xử lý xong!\nNguồn: {len(src_text):,} ký tự | Dịch: {len(trans_text):,} ký tự")
        except Exception as e:
            st.error(f"Lỗi đọc PDF: {e}")
            st.stop()

    tab1, tab2 = st.tabs(["📊 Báo cáo Gemini", "🔍 Kiểm tra nhanh"])

    with tab1:
        if st.button("🚀 Tạo Báo cáo Kiểm định Chi Tiết (Gemini)"):
            with st.spinner("Gemini đang phân tích sâu (có thể mất 15-40 giây)..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""Bạn là chuyên gia kiểm duyệt dịch Anh-Việt cao cấp.
Hãy so sánh bản gốc và bản dịch một cách nghiêm ngặt và chi tiết.
Trả về dưới dạng bảng Markdown với các cột: STT | Nguyên tác (Anh) | Bản dịch (Việt) | Đánh giá & Gợi ý sửa.

Bản gốc:
{src_text[:28000]}

Bản dịch:
{trans_text[:28000]}"""
                    
                    response = model.generate_content(prompt)
                    st.subheader("📊 Báo cáo Kiểm định Chất lượng")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Lỗi khi gọi Gemini: {str(e)}")

    with tab2:
        st.info("📌 Bạn có thể dán đoạn văn bản để kiểm tra nhanh ở đây (tính năng mở rộng sau).")
        quick_text = st.text_area("Dán đoạn bản dịch tiếng Việt", height=200)
        if st.button("Kiểm tra nhanh"):
            st.write("Tính năng này sẽ được bổ sung sau khi app ổn định.")

else:
    st.info("👆 Vui lòng tải lên **cả hai file PDF** và nhập **Gemini API Key** ở sidebar.")

st.caption("Developed with ❤️ for CNU Translation Team")

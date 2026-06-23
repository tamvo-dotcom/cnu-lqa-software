import streamlit as st
import fitz
import pandas as pd
import google.generativeai as genai
from io import BytesIO

st.set_page_config(page_title="CNU Translation LQA", layout="wide", page_icon="📘")

st.title("📘 CNU TRANSLATION LQA SOFTWARE")
st.markdown("**Kiểm định chất lượng dịch + Tra cứu pháp lý + Thuật ngữ chuyên ngành**")

# Sidebar
with st.sidebar:
    st.header("🔑 API Key")
    gemini_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("gemini_key", ""))
    
    if st.button("Lưu Key"):
        st.session_state.gemini_key = gemini_key
        if gemini_key:
            genai.configure(api_key=gemini_key)
            st.success("✅ API Key đã lưu!")

# Upload files
col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("📤 File NGUỒN (tiếng Anh)", type=["pdf"], key="source")
with col2:
    trans_file = st.file_uploader("📤 File DỊCH (tiếng Việt)", type=["pdf"], key="trans")

if source_file and trans_file and st.session_state.get("gemini_key"):
    with st.spinner("Đang trích xuất văn bản..."):
        # Extract source
        doc_src = fitz.open(stream=source_file.read(), filetype="pdf")
        src_text = "".join([doc_src[i].get_text() for i in range(len(doc_src))])
        doc_src.close()

        # Extract translation
        doc_trans = fitz.open(stream=trans_file.read(), filetype="pdf")
        trans_text = "".join([doc_trans[i].get_text() for i in range(len(doc_trans))])
        doc_trans.close()

    # So sánh song song
    st.success("✅ Đã xử lý cả hai file!")
    
    # Tạo bảng so sánh (theo trang)
    # (Giản lược để nhanh)
    df = pd.DataFrame({
        "Trang": range(1, min(len(src_text.split('\n---')), 20)+1),
        "Gốc (Anh)": [src_text[:500] + "..."],  # Thực tế nên cắt theo trang
        "Dịch (Việt)": [trans_text[:500] + "..."]
    })
    st.dataframe(df, use_container_width=True)

    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    st.download_button("📥 Tải Excel so sánh", buffer, "so_sanh_dich.xlsx")

    st.divider()

    # === Các nút chức năng AI ===
    st.header("🤖 Phân tích nâng cao")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        if st.button("📊 Chấm điểm & So sánh tổng quát"):
            with st.spinner("Đang phân tích..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""Chuyên gia kiểm duyệt dịch Anh-Việt. So sánh và chấm điểm (1-10):
                - Độ chính xác
                - Tự nhiên
                - Nhất quán
                - Thuật ngữ chuyên ngành
                
                Gốc: {src_text[:28000]}
                Dịch: {trans_text[:28000]}
                Đưa ra bảng điểm và gợi ý cụ thể."""
                response = model.generate_content(prompt)
                st.markdown(response.text)

    with col_b:
        if st.button("⚖️ Tra cứu pháp lý / Học thuật"):
            with st.spinner("Đang tra cứu pháp lý..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""Đọc sách gốc và đưa ra các vấn đề pháp lý, học thuật, bản quyền, trích dẫn quan trọng cần chú ý khi dịch:
                {src_text[:25000]}
                
                Đưa ra lời khuyên cụ thể cho người dịch."""
                response = model.generate_content(prompt)
                st.markdown("### 📜 Kết quả tra cứu pháp lý / Học thuật")
                st.markdown(response.text)

    with col_c:
        if st.button("🔤 Trích xuất Thuật ngữ chuyên ngành"):
            with st.spinner("Đang trích xuất glossary..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""Trích xuất các thuật ngữ chuyên ngành quan trọng từ sách gốc. 
                Trả về dạng bảng: 
                | Thuật ngữ tiếng Anh | Gợi ý dịch tiếng Việt | Giải thích ngắn |
                
                Sách gốc: {src_text[:25000]}"""
                response = model.generate_content(prompt)
                st.markdown("### 📋 Danh sách Thuật ngữ chuyên ngành")
                st.markdown(response.text)

else:
    st.info("Vui lòng tải lên **cả hai file PDF** và nhập API Key để sử dụng đầy đủ tính năng.")

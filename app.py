import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import google.generativeai as genai
from io import BytesIO

# Cấu hình trang
st.set_page_config(page_title="CNU Translation LQA Software", layout="wide", page_icon="📘")

st.title("📘 CNU TRANSLATION LQA SOFTWARE")
st.markdown("**Hệ thống kiểm định chất lượng học thuật và tra cứu pháp lý giáo trình mở trường CNU**")

# Sidebar API Key
with st.sidebar:
    st.header("🔑 Cài đặt API")
    gemini_key = st.text_input("Nhập Gemini API Key", type="password", value=st.session_state.get("gemini_key", ""))
    
    if st.button("Lưu Key"):
        st.session_state.gemini_key = gemini_key
        if gemini_key:
            genai.configure(api_key=gemini_key)
            st.success("✅ API Key đã được lưu!")
        else:
            st.error("Vui lòng nhập API Key")

    st.divider()
    st.info("Mọi người có thể dùng key chung của bộ phận.")

uploaded_file = st.file_uploader("📤 Tải lên file PDF nguồn (tiếng Anh hoặc song ngữ)", type=["pdf"])

if uploaded_file:
    with st.spinner("Đang trích xuất văn bản từ PDF..."):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = ""
        pages_data = []
        
        for i in range(len(doc)):
            page_text = doc[i].get_text()
            full_text += f"\n--- Trang {i+1} ---\n{page_text}"
            pages_data.append({"Trang": i+1, "Văn bản gốc": page_text.strip()})
        doc.close()

    st.success(f"✅ Đã trích xuất {len(pages_data)} trang!")

    df = pd.DataFrame(pages_data)
    st.dataframe(df, use_container_width=True)

    # Tải Excel
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    st.download_button(
        label="📥 Tải file Excel văn bản gốc",
        data=excel_buffer,
        file_name="van_ban_goc.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()

    # Phần AI
    if st.session_state.get("gemini_key"):
        st.header("🤖 Phân tích bằng Gemini AI")

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🌐 Dịch toàn bộ sang tiếng Việt"):
                with st.spinner("Đang dịch..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""Dịch chính xác, tự nhiên sang tiếng Việt. Giữ nguyên thuật ngữ chuyên ngành và pháp lý.
                    Văn bản:\n\n{full_text[:30000]}"""
                    response = model.generate_content(prompt)
                    translation = response.text
                    
                    st.subheader("Bản dịch")
                    st.text_area("Kết quả dịch", translation, height=400)

        with col2:
            if st.button("⭐ Chấm điểm chất lượng & Gợi ý"):
                with st.spinner("Đang phân tích..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""Bạn là chuyên gia kiểm duyệt dịch Anh-Việt. Đánh giá chất lượng văn bản sau theo thang 1-10:
                    - Độ chính xác
                    - Tự nhiên văn phong
                    - Nhất quán thuật ngữ
                    - Phù hợp pháp lý/học thuật
                    
                    Văn bản: {full_text[:25000]}
                    Trả về bảng Markdown + gợi ý cải thiện."""
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
    else:
        st.warning("Vui lòng nhập Gemini API Key ở sidebar để sử dụng tính năng AI.")

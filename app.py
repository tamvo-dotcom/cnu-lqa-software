import streamlit as st
import pandas as pd
import re
import collections
import time
import os
from pypdf import PdfReader

# Cấu hình tiêu đề trang web hiển thị trên trình duyệt
st.set_page_config(page_title="CNU LQA Software", page_icon="📊", layout="wide")

# ==========================================
# 1. CORE LOGIC: PHÁP LÝ & KIỂM ĐỊNH CHẤT LƯỢNG
# ==========================================
def analyze_legal(reader):
    intro_text = ""
    for i in range(min(5, len(reader.pages))):
        text = reader.pages[i].extract_text()
        if text: intro_text += text.lower() + "\n"
    
    license_name = "Bản quyền chuẩn (All Rights Reserved) hoặc Chưa xác định"
    rules = ["Cần liên hệ tác giả để xin phép chuyển ngữ trước khi phát hành công khai."]
    
    if "creative commons" in intro_text or "cc by" in intro_text:
        if "by-nc-sa" in intro_text or "noncommercial-sharealike" in intro_text:
            license_name = "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)"
            rules = [
                "<b>GHI CÔNG (BY):</b> Bắt buộc ghi rõ tên tác giả gốc và trường phát hành.",
                "<b>PHI THƯƠNG MẠI (NC):</b> Chỉ phân phối MIỄN PHÍ, nghiêm cấm in ấn thương mại kiếm lời.",
                "<b>CHIA SẺ TƯƠNG ĐƯƠNG (SA):</b> Bản dịch đầu ra bắt buộc phải áp dụng cùng loại giấy phép mở này."
            ]
        elif "by-nc" in intro_text or "noncommercial" in intro_text:
            license_name = "Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0)"
            rules = [
                "<b>GHI CÔNG (BY):</b> Bắt buộc ghi rõ tên tác giả gốc và trường phát hành.",
                "<b>PHI THƯƠNG MẠI (NC):</b> Chỉ phân phối MIỄN PHÍ hoặc lưu hành nội bộ học thuật.",
                "<b>LOẠI TRỪ THƯƠNG HIỆU:</b> Không tự ý dùng logo trường đối tác trên bìa bản dịch."
            ]
    return license_name, rules

def run_qa_engine(reader_eng, reader_vie, glossary_df):
    glossary = {}
    if glossary_df is not None:
        try:
            glossary = dict(zip(glossary_df.iloc[:, 0].str.lower().str.strip(), glossary_df.iloc[:, 2].str.lower().str.strip()))
        except: pass

    txt_eng = "".join([p.extract_text() or "" for p in reader_eng.pages]).replace('\n', ' ')
    txt_vie = "".join([p.extract_text() or "" for p in reader_vie.pages]).replace('\n', ' ')
    
    sens_eng = [s.strip() for s in re.split(r'(?<=[.!?])\s+', txt_eng) if len(s.strip()) > 15]
    sens_vie = [s.strip() for s in re.split(r'(?<=[.!?])\s+', txt_vie) if len(s.strip()) > 15]
    
    min_len = min(len(sens_eng), len(sens_vie))
    report_data, error_count = [], 0

    for i in range(min_len):
        en_s, vi_s = sens_eng[i], sens_vie[i]
        errors = []

        for eng_term, vie_term in glossary.items():
            if re.search(r'\b' + re.escape(str(eng_term)) + r'\b', en_s.lower()):
                if str(vie_term) != 'nan' and str(vie_term) not in vi_s.lower():
                    errors.append(f"Bất nhất: Chưa dùng từ '{vie_term}' cho '{eng_term.title()}'")

        if len(en_s) > 130 and len(vi_s) < 40: errors.append("Nghi ngờ sót ý (Câu dịch quá ngắn)")
        elif len(vi_s) > 230 and len(en_s) < 45: errors.append("Nghi ngờ AI tự bịa ý (Câu dịch quá dài)")

        status = "Đạt yêu cầu"
        if errors:
            status = "👉 " + " | ".join(errors)
            error_count += 1

        report_data.append({"STT Câu": i + 1, "Nguyên tác (EN)": en_s, "Bản dịch (VI)": vi_s, "Kết quả kiểm định": status})

    df_final = pd.DataFrame(report_data)
    rate = round(((min_len - error_count) / min_len) * 100, 2) if min_len > 0 else 0
    return df_final, {"total": min_len, "passed": min_len - error_count, "failed": error_count, "rate": rate}

# ==========================================
# 2. GIAO DIỆN WEB PHẦN MỀM (STREAMLIT UI)
# ==========================================
st.title("📊 CNU TRANSLATION LQA SOFTWARE")
st.caption("Hệ thống kiểm định chất lượng học thuật và tra cứu pháp lý giáo trình mở trường CNU")
st.hr()

# Thanh cấu hình bên trái (Sidebar)
with st.sidebar:
    st.header("🔑 Cấu hình AI")
    api_key = st.text_input("Gemini API Key:", type="password", help="Lấy mã khóa từ Google AI Studio")
    st.header("⚙️ Bộ lọc thuật ngữ")
    freq_limit = st.number_input("Tần suất xuất hiện từ (>= lần):", min_value=10, max_value=200, value=100)

# Khung giao diện chính chia làm 2 cột để upload file
col1, col2 = st.columns(2)
with col1:
    file_eng = st.file_uploader("📥 Tải sách gốc (PDF):", type=["pdf"])
with col2:
    file_vie = st.file_uploader("📥 Tải bản dịch tiếng Việt (PDF):", type=["pdf"])

file_glo = st.file_uploader("📋 Tải kho thuật ngữ sẵn có (Excel) - Không bắt buộc:", type=["xlsx"])

# Thao tác xử lý kiểm định
if st.button("🚀 KÍCH HOẠT THẨM ĐỊNH TOÀN DIỆN", type="primary"):
    if file_eng and file_vie:
        try:
            r_eng = PdfReader(file_eng)
            r_vie = PdfReader(file_vie)
            
            # 1. Chạy Module Pháp lý
            lic_name, rules = analyze_legal(r_eng)
            st.success("⚖️ BÁO CÁO PHÁP LÝ TỰ ĐỘNG (LEGAL DISCLOSURE)")
            st.write(f"🔹 **Giấy phép mở phát hiện:** {lic_name}")
            for r in rules: st.markdown(f"- {r}")
            st.hr()
            
            # 2. Chạy Module QA Học thuật
            glo_df = pd.read_excel(file_glo) if file_glo else None
            df_res, metrics = run_qa_engine(r_eng, r_vie, glo_df)
            
            st.info("🎯 CHỈ SỐ CHẤT LƯỢNG HỌC THUẬT (METRICS)")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Tổng số câu đối sánh", f"{metrics['total']} câu")
            m_col2.metric("Số câu đạt chuẩn", metrics['passed'])
            m_col3.metric("Số câu dính sai sót", metrics['failed'])
            m_col4.metric("Tỷ lệ tương thích", f"{metrics['rate']}%")
            
            # Hiển thị bảng câu lỗi trực quan
            st.subheader("⚠️ DANH SÁCH CÁC CÂU LỖI TRỌNG ĐIỂM CẦN HIỆU ĐÍNH")
            df_errors = df_res[df_res["Kết quả kiểm định"] != "Đạt yêu cầu"]
            if not df_errors.empty:
                st.dataframe(df_errors, use_container_width=True)
            else:
                st.balloons()
                st.success("Tuyệt vời! Không phát hiện lỗi cấu trúc nghiêm trọng nào.")
                
            # Tạo nút bấm tải file báo cáo Excel về máy tính người dùng trực tiếp trên web
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_res.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 TẢI BÁO CÁO KIỂM ĐỊNH TỔNG THỂ (EXCEL)",
                data=buffer.getvalue(),
                file_name="Bao_cao_kiem_dinh_CNU.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Có lỗi xảy ra trong quá trình bóc tách: {e}")
    else:
        st.warning("Vui lòng tải lên đầy đủ cả file Sách gốc và Bản dịch tiếng Việt để phần mềm hoạt động.")

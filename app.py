import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
from vietquill import AutoModelForControllableParaphraseGeneration, ParaphraseStyle
from vietquill import AutoModelForParaphraseQualityEstimation

class PreTranslationVerifier:
    def __init__(self):
        self.paraphraser = None
        self.quality_estimator = None
        self.gemini_model = None

    def load_vietquill(self):
        if self.paraphraser is None:
            self.paraphraser = AutoModelForControllableParaphraseGeneration()
        if self.quality_estimator is None:
            self.quality_estimator = AutoModelForParaphraseQualityEstimation()

    def improve_vietnamese_translation(self, viet_text: str, style="BALANCED", num_candidates=3):
        self.load_vietquill()
        candidates = self.paraphraser.paraphrase(
            viet_text,
            style=ParaphraseStyle[style] if isinstance(style, str) else style,
            num_candidates=num_candidates
        )
        
        evaluations = []
        for cand in candidates:
            score = self.quality_estimator.estimate(viet_text, cand)
            evaluations.append({
                "paraphrase": cand,
                "scores": score
            })
        
        return {
            "original": viet_text,
            "improved_candidates": candidates,
            "evaluations": evaluations
        }

# ====================== STREAMLIT APP ======================
st.set_page_config(page_title="CNU Translation LQA", layout="wide", page_icon="📘")
st.title("📘 CNU TRANSLATION LQA SOFTWARE")
st.markdown("**Tiền kiểm định chất lượng dịch thuật Anh - Việt**")

# Sidebar
with st.sidebar:
    st.header("🔑 API Key")
    gemini_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("gemini_key", ""))
    if st.button("Lưu Key"):
        st.session_state.gemini_key = gemini_key
        if gemini_key:
            genai.configure(api_key=gemini_key)
            st.success("✅ Key đã lưu!")

verifier = PreTranslationVerifier()

# Upload files
col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("📤 File NGUỒN (Tiếng Anh)", type=["pdf"], key="source")
with col2:
    trans_file = st.file_uploader("📤 File DỊCH (Tiếng Việt)", type=["pdf"], key="trans")

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
            
            st.success(f"✅ Đã xử lý xong! Nguồn: {len(src_text):,} ký tự | Dịch: {len(trans_text):,} ký tự")
        except Exception as e:
            st.error(f"Lỗi đọc PDF: {e}")
            st.stop()

    # Nút chính
    tab1, tab2, tab3 = st.tabs(["📊 Báo cáo Gemini", "✍️ Cải thiện Bản dịch (VietQuill)", "🔍 Kiểm tra nhanh"])

    with tab1:
        if st.button("🚀 Tạo Báo cáo Kiểm định Chi Tiết (Gemini)"):
            with st.spinner("Gemini đang phân tích (có thể mất 15-40 giây)..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')  # Hoặc gemini-pro
                    prompt = f"""Bạn là chuyên gia kiểm duyệt dịch Anh-Việt cao cấp.
Hãy so sánh bản gốc và bản dịch, trả về dưới dạng bảng Markdown.

Bản gốc (Anh):
{src_text[:25000]}

Bản dịch (Việt):
{trans_text[:25000]}

Yêu cầu: Phân tích chi tiết, chỉ ra lỗi thuật ngữ, sót ý, dịch máy móc, không tự nhiên..."""
                    
                    response = model.generate_content(prompt)
                    st.subheader("📊 Báo cáo Kiểm định Chất lượng")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Lỗi Gemini: {str(e)}")

    with tab2:
        st.header("Cải thiện Bản dịch Tiếng Việt bằng VietQuill")
        sample_text = st.text_area("Dán đoạn bản dịch tiếng Việt cần cải thiện", height=150, value=trans_text[:1000] if 'trans_text' in locals() else "")
        
        col_a, col_b = st.columns(2)
        with col_a:
            style = st.selectbox("Phong cách paraphrase", ["CONSERVATIVE", "BALANCED", "DIVERSE"], index=1)
        with col_b:
            num_cand = st.slider("Số lượng gợi ý", 1, 5, 3)
        
        if st.button("✨ Cải thiện bằng VietQuill"):
            with st.spinner("VietQuill đang xử lý..."):
                result = verifier.improve_vietnamese_translation(sample_text, style, num_cand)
                
                st.subheader("Kết quả cải thiện")
                for i, ev in enumerate(result["evaluations"]):
                    st.info(f"**Phiên bản {i+1}**: {ev['paraphrase']}")
                    scores = ev['scores']
                    st.caption(f"Lexical: {scores.get('lexical_score', 'N/A')} | Semantic: {scores.get('semantic_score', 'N/A')}")

    with tab3:
        st.info("Tab này bạn có thể thêm các kiểm tra nhanh khác sau.")

else:
    st.info("👆 Vui lòng tải lên cả 2 file PDF và nhập Gemini API Key.")

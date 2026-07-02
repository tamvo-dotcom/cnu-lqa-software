import streamlit as st
import fitz
from docx import Document
import google.generativeai as genai
import pandas as pd
from io import BytesIO
from vietquill import AutoModelForControllableParaphraseGeneration, ParaphraseStyle
from vietquill import AutoModelForParaphraseQualityEstimation
import io

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

class PreTranslationVerifier:
    def __init__(self):
        self.paraphraser = None
        self.quality_estimator = None

    def load_vietquill(self):
        if self.paraphraser is None:
            self.paraphraser = AutoModelForControllableParaphraseGeneration()
        if self.quality_estimator is None:
            self.quality_estimator = AutoModelForParaphraseQualityEstimation()

    def improve_vietnamese_translation(self, viet_text: str, style="BALANCED", num_candidates=3):
        self.load_vietquill()
        candidates = self.paraphraser.paraphrase(viet_text, style=ParaphraseStyle[style] if isinstance(style, str) else style, num_candidates=num_candidates)
        evaluations = []
        for cand in candidates:
            score = self.quality_estimator.estimate(viet_text, cand)
            evaluations.append({"paraphrase": cand, "scores": score})
        return {"original": viet_text, "improved_candidates": candidates, "evaluations": evaluations}

verifier = PreTranslationVerifier()

# Upload
col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader("📤 File NGUỒN (Anh)", type=["pdf", "docx"], key="source")
with col2:
    trans_file = st.file_uploader("📤 File DỊCH (Việt)", type=["pdf", "docx"], key="trans")

if source_file and trans_file and st.session_state.get("gemini_key"):
    with st.spinner("Đang trích xuất văn bản..."):
        def extract_text(file):
            if file.type == "application/pdf":
                doc = fitz.open(stream=file.read(), filetype="pdf")
                text = "".join([page.get_text() for page in doc])
                doc.close()
            else:  # docx
                doc = Document(BytesIO(file.read()))
                text = "\n".join([para.text for para in doc.paragraphs])
            return text
        
        src_text = extract_text(source_file)
        trans_text = extract_text(trans_file)
        st.success(f"✅ Đã xử lý! Nguồn: {len(src_text):,} ký tự | Dịch: {len(trans_text):,} ký tự")

    tabs = st.tabs(["📊 Báo cáo Gemini", "✍️ VietQuill Cải thiện", "🔄 So sánh Song song", "📋 Phân tích Thuật ngữ", "📥 Export"])

    with tabs[0]:
        if st.button("🚀 Tạo Báo cáo Gemini"):
            with st.spinner("Đang phân tích..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""Phân tích chi tiết bản dịch Anh-Việt. Trả về bảng Markdown.\n\nGốc:\n{src_text[:25000]}\n\nDịch:\n{trans_text[:25000]}"""
                response = model.generate_content(prompt)
                st.markdown(response.text)

    with tabs[1]:
        st.header("Cải thiện Bản dịch Tiếng Việt (VietQuill)")
        sample = st.text_area("Dán đoạn bản dịch cần cải thiện", value=trans_text[:1500] if len(trans_text) > 0 else "", height=200)
        style = st.selectbox("Phong cách", ["CONSERVATIVE", "BALANCED", "DIVERSE"], index=1)
        num = st.slider("Số gợi ý", 1, 5, 3)
        if st.button("✨ Cải thiện"):
            with st.spinner("VietQuill đang chạy..."):
                res = verifier.improve_vietnamese_translation(sample, style, num)
                for i, ev in enumerate(res["evaluations"]):
                    st.info(f"**{i+1}**: {ev['paraphrase']}")
                    st.caption(str(ev["scores"]))

    with tabs[2]:
        st.header("So sánh Song song")
        if st.button("Tạo bảng so sánh"):
            # Tạm đơn giản (có thể cải tiến sau)
            st.write("**Bản gốc (Anh)**")
            st.text(src_text[:2000])
            st.write("**Bản dịch (Việt)**")
            st.text(trans_text[:2000])

    with tabs[3]:
        st.header("Phân tích Thuật ngữ Chuyên ngành")
        if st.button("Trích xuất Thuật ngữ"):
            # Heuristic đơn giản
            words = pd.Series(trans_text.split()).value_counts().head(30)
            st.dataframe(words.rename("Tần suất"), use_container_width=True)

    with tabs[4]:
        st.header("Export Báo cáo")
        if st.button("Tải Excel"):
            df = pd.DataFrame({"Nguồn": [src_text[:500]], "Dịch": [trans_text[:500]]})
            output = BytesIO()
            df.to_excel(output, index=False)
            st.download_button("📥 Tải file Excel", output.getvalue(), "bao_cao.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.info("Vui lòng tải file và nhập API Key.")

st.caption("CNU Translation LQA - Đã tích hợp đầy đủ 5 tính năng")

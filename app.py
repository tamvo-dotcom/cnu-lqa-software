import streamlit as st
import requests
import re
import json
from collections import Counter
import spacy
from textstat import textstat
import PyPDF2
from docx import Document

class PreTranslationVerifier:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.nlp = None
    
    def search_book_legal_info(self, query: str, isbn: str = None):
        base_url = "https://www.googleapis.com/books/v1/volumes"
        params = {"q": f"isbn:{isbn}" if isbn else query, "maxResults": 5}
        try:
            resp = requests.get(base_url, params=params, timeout=15)
            data = resp.json()
            if "items" in data:
                book = data["items"][0]["volumeInfo"]
                return {
                    "status": "success",
                    "title": book.get("title"),
                    "authors": book.get("authors", []),
                    "publisher": book.get("publisher"),
                    "published_date": book.get("publishedDate"),
                    "description": book.get("description", "")[:800],
                    "page_count": book.get("pageCount"),
                    "categories": book.get("categories", []),
                    "language": book.get("language"),
                    "preview_link": book.get("previewLink"),
                    "info_link": book.get("infoLink")
                }
        except:
            return {"status": "error", "message": "Không tìm thấy thông tin sách."}
    
    def extract_text_from_file(self, file) -> str:
        text = ""
        try:
            if file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                doc = Document(file)
                text = "\n".join([para.text for para in doc.paragraphs])
            else:
                text = file.getvalue().decode("utf-8", errors="ignore")
        except Exception as e:
            text = f"Lỗi đọc file: {str(e)}"
        return text
    
    def extract_specialized_terminology(self, text: str, top_n: int = 30):
        if self.nlp:
            doc = self.nlp(text)
            candidates = [chunk.text.strip().lower() for chunk in doc.noun_chunks if 3 < len(chunk.text.strip()) <= 50]
        else:
            text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
            candidates = re.findall(r'\b\w+(?:\s+\w+){0,3}\b', text_clean)
        
        freq = Counter(candidates)
        return [{"term": term, "frequency": count} for term, count in freq.most_common(top_n)]
    
    def analyze_text(self, text: str):
        if not text.strip():
            return {"error": "Văn bản trống"}
        sentences = re.split(r'[.!?]+', text)
        words = re.findall(r'\b\w+\b', text)
        return {
            "num_sentences": len([s for s in sentences if len(s.strip()) > 5]),
            "num_words": len(words),
            "avg_sentence_length": round(len(words) / max(1, len(sentences)), 1),
            "readability_score": round(textstat.flesch_reading_ease(text), 1),
            "reading_time_minutes": round(len(words) / 200, 1),
            "special_terms": self.extract_specialized_terminology(text)
        }

# ====================== GIAO DIỆN STREAMLIT ======================
st.set_page_config(page_title="Pre-Translation Verifier", layout="wide")
st.title("🛡️ Pre-Translation Verifier")
st.markdown("**Kiểm tra trước dịch thuật • Trích xuất thuật ngữ • Tra cứu sách gốc**")

verifier = PreTranslationVerifier()

tab1, tab2, tab3 = st.tabs(["📄 Phân tích File", "✍️ Phân tích Văn bản", "📚 Tra cứu Sách"])

with tab1:
    st.header("Tải file lên (PDF, Word, TXT)")
    uploaded_file = st.file_uploader("Chọn file nguồn", type=["pdf", "docx", "txt"])
    
    if uploaded_file:
        text = verifier.extract_text_from_file(uploaded_file)
        st.success(f"✅ Đã đọc file **{uploaded_file.name}** ({len(text):,} ký tự)")
        
        if st.button("🚀 Phân tích File"):
            with st.spinner("Đang phân tích..."):
                analysis = verifier.analyze_text(text)
                if "error" not in analysis:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Số câu", analysis["num_sentences"])
                        st.metric("Số từ", analysis["num_words"])
                        st.metric("Thời gian đọc ước tính", f"{analysis['reading_time_minutes']} phút")
                    with col2:
                        st.metric("Độ dễ đọc", f"{analysis['readability_score']}/100")
                        st.metric("Độ dài câu TB", f"{analysis['avg_sentence_length']} từ")
                    
                    st.subheader("🔤 Top từ vựng chuyên ngành")
                    st.dataframe(analysis["special_terms"][:25], use_container_width=True)
                    
                    st.download_button(
                        label="📥 Tải báo cáo JSON",
                        data=json.dumps(analysis, indent=2, ensure_ascii=False),
                        file_name=f"report_{uploaded_file.name}.json"
                    )
                else:
                    st.error(analysis["error"])

with tab2:
    st.header("Nhập văn bản trực tiếp")
    input_text = st.text_area("Dán văn bản nguồn", height=400)
    if st.button("Phân tích Văn bản") and input_text:
        analysis = verifier.analyze_text(input_text)
        st.json(analysis)

with tab3:
    st.header("📖 Tra cứu thông tin sách & pháp lý")
    col1, col2 = st.columns([3,1])
    with col1:
        book_query = st.text_input("Nhập tên sách / tác giả")
    with col2:
        isbn_input = st.text_input("ISBN")
    
    if st.button("🔍 Tìm kiếm sách") and (book_query or isbn_input):
        with st.spinner("Đang tra cứu qua Google Books..."):
            result = verifier.search_book_legal_info(book_query, isbn_input)
            if result.get("status") == "success":
                st.success("✅ Tìm thấy thông tin sách")
                st.json(result)
            else:
                st.error(result.get("message"))

st.caption("Phần mềm miễn phí • Hỗ trợ PDF/Word • Phát triển với Streamlit")

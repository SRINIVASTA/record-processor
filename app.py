import io
import streamlit as st
from pypdf import PdfReader
from src.option1_summarizer import extract_digital_pdf_text, generate_by_pages
from src.option2_ocr import extract_text_from_scanned_pdf
from src.humanizer import rewrite_human_style
from src.pdf_exporter import create_clean_pdf

st.set_page_config(page_title="Groq Record Processor", page_icon="📄", layout="centered")

st.title("📄 Record Processor (Groq + OCR)")
st.caption("Generate multi-page handwritten PDFs or convert scanned PDFs into clean handwritten records.")

# Initialize session state
for key in ["opt1_result", "opt1_pdf", "opt1_pages", "opt2_clean_text", "opt2_ocr_text", "opt2_pdf"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Sidebar Settings
with st.sidebar:
    st.header("Settings")
    model_choice = st.selectbox(
        "Groq Model",
        [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b"
        ],
        index=0
    )

    ink_choice = st.radio(
        "Pen Ink Color (PDF Output):",
        ["Blue", "Black"],
        horizontal=True
    )

    st.info("Add your `GROQ_API_KEY` in Streamlit Secrets (Cloud) or `.env` (Local).")

tab1, tab2 = st.tabs(["Option 1: Generate by Pages", "Option 2: Scanned PDF to Clean PDF"])

# ==========================================
# OPTION 1: GENERATE BY PAGE COUNT -> HANDWRITTEN PDF
# ==========================================
with tab1:
    st.subheader("Option 1: Generate Handwritten Record by Page Count")

    input_method = st.radio(
        "Choose input source:",
        ["Enter Topic / Paste Text", "Upload Digital PDF"],
        horizontal=True
    )
    raw_text = ""
    is_source = False

    if input_method == "Enter Topic / Paste Text":
        raw_text = st.text_area(
            "Enter your topic (e.g., Digital Flash) or paste full source text:",
            height=180
        )
        # Treat inputs over 80 words as source text to summarize/expand; short inputs as a topic
        is_source = len(raw_text.split()) > 80
    else:
        digital_pdf = st.file_uploader("Upload a standard PDF", type=["pdf"], key="opt1_pdf_uploader")
        if digital_pdf:
            raw_text = extract_digital_pdf_text(digital_pdf)
            is_source = True
            st.success(f"Extracted {len(raw_text.split())} words from PDF.")

    col1, col2 = st.columns(2)
    with col1:
        target_pages = st.number_input(
            "How many PDF pages do you want?",
            min_value=1,
            max_value=50,
            value=30,
            step=1
        )
    with col2:
        summary_title = st.text_input("Document Title for PDF:", value="Official Record")

    if st.button("Generate Handwritten PDF", type="primary"):
        if not raw_text.strip():
            st.warning("Please enter a topic, paste text, or upload a PDF first.")
        else:
            try:
                progress_bar = st.progress(0, text="Starting record generation...")

                def update_progress(current, total, status_text):
                    pct = min(1.0, current / max(1, total))
                    progress_bar.progress(pct, text=f"[{current}/{total}] {status_text[:55]}")

                result = generate_by_pages(
                    content_or_topic=raw_text,
                    target_pages=target_pages,
                    is_source_text=is_source,
                    model=model_choice,
                    progress_callback=update_progress
                )
                progress_bar.empty()

                pdf_bytes = create_clean_pdf(
                    result["summary"],
                    title=summary_title,
                    ink_color=ink_choice
                )
                actual_pages = len(PdfReader(io.BytesIO(pdf_bytes)).pages)

                st.session_state.opt1_result = result
                st.session_state.opt1_pdf = pdf_bytes
                st.session_state.opt1_pages = actual_pages
            except Exception as e:
                st.error(f"Error: {e}")

    # Display Option 1 Result & Download Button
    if st.session_state.opt1_result and st.session_state.opt1_pdf:
        res = st.session_state.opt1_result
        st.success(f"Generated {st.session_state.opt1_pages}-page handwritten PDF ({ink_choice} ink)!")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("PDF Pages", st.session_state.opt1_pages)
        m2.metric("Word Count", res["words"])
        m3.metric("Chars (with spaces)", res["chars_with_spaces"])
        m4.metric("Chars (no spaces)", res["chars_no_spaces"])

        with st.expander("Preview Generated Text"):
            st.text_area("Record Content:", value=res["summary"], height=220)

        st.download_button(
            label=f"⬇️ Download {st.session_state.opt1_pages}-Page PDF ({ink_choice} Ink)",
            data=st.session_state.opt1_pdf,
            file_name=f"record_{st.session_state.opt1_pages}pages_{ink_choice.lower()}_ink.pdf",
            mime="application/pdf",
            key="download_opt1_pdf"
        )

# ==========================================
# OPTION 2: SCANNED PDF -> HUMAN STYLE PDF
# ==========================================
with tab2:
    st.subheader("Option 2: Scanned PDF to Human-Written PDF")

    scanned_pdf = st.file_uploader("Upload your scanned PDF", type=["pdf"], key="opt2_pdf_uploader")
    doc_title = st.text_input("Document Title for Output PDF:", value="Official Record Document")

    if st.button("Scan & Generate Human-Style PDF", type="primary"):
        if not scanned_pdf:
            st.warning("Please upload a scanned PDF file first.")
        else:
            try:
                with st.spinner("Step 1/3: Running OCR on scanned pages..."):
                    ocr_text = extract_text_from_scanned_pdf(scanned_pdf.read())

                if not ocr_text.strip():
                    st.error("No readable text could be detected in this scan.")
                else:
                    with st.spinner("Step 2/3: Rewriting in natural human-written style via Groq..."):
                        clean_text = rewrite_human_style(ocr_text, model=model_choice)

                    with st.spinner("Step 3/3: Building handwritten PDF for records..."):
                        pdf_bytes = create_clean_pdf(
                            clean_text,
                            title=doc_title,
                            ink_color=ink_choice
                        )

                    st.session_state.opt2_ocr_text = ocr_text
                    st.session_state.opt2_clean_text = clean_text
                    st.session_state.opt2_pdf = pdf_bytes
            except Exception as e:
                st.error(f"Processing failed: {e}")

    # Display Option 2 Result & Download Button
    if st.session_state.opt2_clean_text and st.session_state.opt2_pdf:
        st.success(f"Your clean, handwritten-style PDF ({ink_choice} ink) is ready!")

        with st.expander("View Raw OCR Text"):
            st.text(st.session_state.opt2_ocr_text)

        st.markdown("### Human-Written Record Preview")
        st.text_area("Edited Text:", value=st.session_state.opt2_clean_text, height=250)

        st.download_button(
            label=f"⬇️ Download Clean Record PDF ({ink_choice} Ink)",
            data=st.session_state.opt2_pdf,
            file_name=f"clean_record_{ink_choice.lower()}_ink.pdf",
            mime="application/pdf",
            key="download_opt2_pdf"
        )

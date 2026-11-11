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

# Initialize session state so outputs and download buttons persist on rerun
session_keys = [
    "opt1_result",
    "opt1_pdf",
    "opt1_pages",
    "opt2_clean_text",
    "opt2_ocr_text",
    "opt2_pdf",
    "opt2_pages",
]
for key in session_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# ==========================================
# SIDEBAR SETTINGS
# ==========================================
with st.sidebar:
    st.header("Settings")
    model_choice = st.selectbox(
        "Groq Model (for Option 1 / Optional Cleanup)",
        [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b",
        ],
        index=0,
        help="gpt-oss-20b is fastest and has higher free-tier token limits; gpt-oss-120b gives highest writing quality.",
    )

    ink_choice = st.radio(
        "Pen Ink Color (PDF Output):",
        ["Blue", "Black"],
        horizontal=True,
    )

    st.info("Add your `GROQ_API_KEY` in Streamlit Secrets (Cloud) or `.env` (Local) when using Groq.")

tab1, tab2 = st.tabs(["Option 1: Generate by Pages", "Option 2: Scanned PDF to Handwritten PDF"])

# ==========================================
# OPTION 1: GENERATE BY PAGE COUNT -> HANDWRITTEN PDF
# ==========================================
with tab1:
    st.subheader("Option 1: Generate Handwritten Record by Page Count")

    input_method = st.radio(
        "Choose input source:",
        ["Enter Topic / Paste Text", "Upload Digital PDF"],
        horizontal=True,
    )
    raw_text = ""
    is_source = False

    if input_method == "Enter Topic / Paste Text":
        raw_text = st.text_area(
            "Enter your topic (e.g., Digital Flash) or paste full source text:",
            height=180,
        )
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
            value=1,
            step=1,
        )
    with col2:
        summary_title = st.text_input("Document Title for PDF (Optional):", value="")

    if st.button("Generate Handwritten PDF", type="primary"):
        if not raw_text.strip():
            st.warning("Please enter a topic, paste text, or upload a valid PDF first.")
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
                    progress_callback=update_progress,
                )
                progress_bar.empty()

                pdf_bytes = create_clean_pdf(
                    result["summary"],
                    title=summary_title,
                    ink_color=ink_choice,
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
            key="download_opt1_pdf",
        )

# ==========================================
# OPTION 2: SCANNED PDF -> HANDWRITTEN PDF (DIRECT BY DEFAULT)
# ==========================================
with tab2:
    st.subheader("Option 2: Scanned PDF to Handwritten PDF")

    scanned_pdf = st.file_uploader("Upload your scanned PDF", type=["pdf"], key="opt2_pdf_uploader")
    doc_title = st.text_input("Document Title for Output PDF (Optional):", value="")

    use_groq_cleanup = st.checkbox(
        "Optional: Rewrite & fix OCR typos using Groq AI (leave unchecked for direct OCR to handwritten PDF)",
        value=False,
    )

    if st.button("Scan & Generate Handwritten PDF", type="primary"):
        if not scanned_pdf:
            st.warning("Please upload a scanned PDF file first.")
        else:
            try:
                with st.spinner("Step 1/2: Extracting text from scanned pages via OCR..."):
                    ocr_text = extract_text_from_scanned_pdf(scanned_pdf.read())

                if not ocr_text.strip():
                    st.error("No readable text could be detected in this scan.")
                else:
                    if use_groq_cleanup:
                        opt2_bar = st.progress(0, text="Rewriting OCR text in safe chunks via Groq...")

                        def update_opt2_progress(current, total):
                            pct = min(1.0, current / max(1, total))
                            opt2_bar.progress(
                                pct,
                                text=f"Cleaning chunk {current}/{total} via Groq...",
                            )

                        clean_text = rewrite_human_style(
                            ocr_text,
                            model=model_choice,
                            progress_callback=update_opt2_progress,
                        )
                        opt2_bar.empty()
                    else:
                        clean_text = ocr_text

                    with st.spinner("Step 2/2: Building handwritten PDF for records..."):
                        pdf_bytes = create_clean_pdf(
                            clean_text,
                            title=doc_title,
                            ink_color=ink_choice,
                        )
                        opt2_page_count = len(PdfReader(io.BytesIO(pdf_bytes)).pages)

                    st.session_state.opt2_ocr_text = ocr_text
                    st.session_state.opt2_clean_text = clean_text
                    st.session_state.opt2_pdf = pdf_bytes
                    st.session_state.opt2_pages = opt2_page_count
            except Exception as e:
                st.error(f"Processing failed: {e}")

    # Display Option 2 Result & Download Button
    if st.session_state.opt2_clean_text and st.session_state.opt2_pdf:
        st.success(
            f"Your {st.session_state.opt2_pages}-page handwritten PDF ({ink_choice} ink) is ready!"
        )

        with st.expander("View Raw OCR Text"):
            st.text(st.session_state.opt2_ocr_text)

        st.markdown("### Handwritten Record Preview")
        st.text_area("Extracted Text:", value=st.session_state.opt2_clean_text, height=250)

        st.download_button(
            label=f"⬇️ Download {st.session_state.opt2_pages}-Page Record PDF ({ink_choice} Ink)",
            data=st.session_state.opt2_pdf,
            file_name=f"handwritten_record_{ink_choice.lower()}_ink.pdf",
            mime="application/pdf",
            key="download_opt2_pdf",
        )

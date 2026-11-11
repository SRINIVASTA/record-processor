import streamlit as st
from src.option1_summarizer import extract_digital_pdf_text, summarize_for_records
from src.option2_ocr import extract_text_from_scanned_pdf
from src.humanizer import rewrite_human_style
from src.pdf_exporter import create_clean_pdf

st.set_page_config(page_title="Groq Record Processor", page_icon="📄", layout="centered")

st.title("📄 Record Processor (Groq + OCR)")
st.caption("Generate exact-count summaries or convert scanned PDFs into clean, handwritten-style PDF records.")

# Initialize session state so generated results and PDFs stay visible on rerun
if "opt1_result" not in st.session_state:
    st.session_state.opt1_result = None
if "opt1_pdf" not in st.session_state:
    st.session_state.opt1_pdf = None

if "opt2_clean_text" not in st.session_state:
    st.session_state.opt2_clean_text = None
if "opt2_ocr_text" not in st.session_state:
    st.session_state.opt2_ocr_text = None
if "opt2_pdf" not in st.session_state:
    st.session_state.opt2_pdf = None

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

tab1, tab2 = st.tabs(["Option 1: Summary & Counts", "Option 2: Scanned PDF to Clean PDF"])

# ==========================================
# OPTION 1: SUMMARY + COUNTS + PDF DOWNLOAD
# ==========================================
with tab1:
    st.subheader("Option 1: Groq Summary with Word & Character Counts")

    input_method = st.radio("Choose input source:", ["Paste Text", "Upload Digital PDF"], horizontal=True)
    raw_text = ""

    if input_method == "Paste Text":
        raw_text = st.text_area("Paste your text here:", height=200)
    else:
        digital_pdf = st.file_uploader("Upload a standard PDF", type=["pdf"], key="opt1_pdf_uploader")
        if digital_pdf:
            raw_text = extract_digital_pdf_text(digital_pdf)
            st.success(f"Extracted {len(raw_text.split())} words from PDF.")

    col1, col2 = st.columns(2)
    with col1:
        limit_type = st.selectbox("Limit unit for records:", ["words", "characters"])
    with col2:
        target_limit = st.number_input(f"Maximum {limit_type}:", min_value=10, max_value=5000, value=150, step=10)

    summary_title = st.text_input("Document Title for Summary PDF:", value="Record Summary")

    if st.button("Generate Record Summary", type="primary"):
        if not raw_text.strip():
            st.warning("Please enter text or upload a valid PDF first.")
        else:
            with st.spinner("Generating summary and building handwritten PDF..."):
                try:
                    result = summarize_for_records(
                        text=raw_text,
                        target_limit=target_limit,
                        limit_type=limit_type,
                        model=model_choice
                    )

                    pdf_body = (
                        f"{result['summary']}\n\n"
                        f"--------------------------------------------------\n"
                        f"Record Metrics:\n"
                        f"Words: {result['words']} | "
                        f"Characters (with spaces): {result['chars_with_spaces']} | "
                        f"Characters (no spaces): {result['chars_no_spaces']}"
                    )
                    pdf_bytes = create_clean_pdf(
                        pdf_body,
                        title=summary_title,
                        ink_color=ink_choice
                    )

                    st.session_state.opt1_result = result
                    st.session_state.opt1_pdf = pdf_bytes
                except Exception as e:
                    st.error(f"Error: {e}")

    # Display Option 1 Result & Download Button
    if st.session_state.opt1_result and st.session_state.opt1_pdf:
        res = st.session_state.opt1_result
        st.markdown("### Generated Summary")
        st.text_area("Copy Summary for Records:", value=res["summary"], height=180)

        m1, m2, m3 = st.columns(3)
        m1.metric("Word Count", res["words"])
        m2.metric("Characters (with spaces)", res["chars_with_spaces"])
        m3.metric("Characters (no spaces)", res["chars_no_spaces"])

        st.download_button(
            label=f"⬇️ Download Summary PDF ({ink_choice} Ink)",
            data=st.session_state.opt1_pdf,
            file_name=f"record_summary_{ink_choice.lower()}_ink.pdf",
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

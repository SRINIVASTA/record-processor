import streamlit as st
from src.option1_summarizer import extract_digital_pdf_text, summarize_for_records
from src.option2_ocr import extract_text_from_scanned_pdf
from src.humanizer import rewrite_human_style
from src.pdf_exporter import create_clean_pdf

st.set_page_config(page_title="Groq Record Processor", page_icon="📄", layout="centered")

st.title("📄 Record Processor (Groq + OCR)")
st.caption("Generate exact-count summaries or convert scanned PDFs into clean, human-written PDF records.")

# Sidebar Settings
with st.sidebar:
    st.header("Settings")
    model_choice = st.selectbox(
        "Groq Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        index=0
    )
    st.info("Add your `GROQ_API_KEY` in Streamlit Secrets (Cloud) or `.env` (Local).")

tab1, tab2 = st.tabs(["Option 1: Summary & Counts", "Option 2: Scanned PDF to Clean PDF"])

# ==========================================
# OPTION 1: SUMMARY + WORD/CHARACTER COUNTS
# ==========================================
with tab1:
    st.subheader("Option 1: Groq Summary with Word & Character Counts")

    input_method = st.radio("Choose input source:", ["Paste Text", "Upload Digital PDF"], horizontal=True)
    raw_text = ""

    if input_method == "Paste Text":
        raw_text = st.text_area("Paste your text here:", height=200)
    else:
        digital_pdf = st.file_uploader("Upload a standard PDF", type=["pdf"], key="opt1_pdf")
        if digital_pdf:
            raw_text = extract_digital_pdf_text(digital_pdf)
            st.success(f"Extracted {len(raw_text.split())} words from PDF.")

    col1, col2 = st.columns(2)
    with col1:
        limit_type = st.selectbox("Limit unit for records:", ["words", "characters"])
    with col2:
        target_limit = st.number_input(f"Maximum {limit_type}:", min_value=10, max_value=5000, value=150, step=10)

    if st.button("Generate Record Summary", type="primary"):
        if not raw_text.strip():
            st.warning("Please enter text or upload a valid PDF first.")
        else:
            with st.spinner("Generating summary with Groq..."):
                try:
                    result = summarize_for_records(
                        text=raw_text,
                        target_limit=target_limit,
                        limit_type=limit_type,
                        model=model_choice
                    )

                    st.markdown("### Generated Summary")
                    st.text_area("Copy Summary for Records:", value=result["summary"], height=180)

                    # Exact Metric Counters
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Word Count", result["words"])
                    m2.metric("Characters (with spaces)", result["chars_with_spaces"])
                    m3.metric("Characters (no spaces)", result["chars_no_spaces"])

                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================================
# OPTION 2: SCANNED PDF -> HUMAN STYLE PDF
# ==========================================
with tab2:
    st.subheader("Option 2: Scanned PDF to Human-Written PDF")

    scanned_pdf = st.file_uploader("Upload your scanned PDF", type=["pdf"], key="opt2_pdf")
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

                    with st.spinner("Step 3/3: Building clean PDF for records..."):
                        pdf_bytes = create_clean_pdf(clean_text, title=doc_title)

                    st.success("Your clean, human-written PDF is ready!")

                    with st.expander("View Raw OCR Text"):
                        st.text(ocr_text)

                    st.markdown("### Human-Written Record Preview")
                    st.text_area("Edited Text:", value=clean_text, height=250)

                    st.download_button(
                        label="⬇️ Download Clean Record PDF",
                        data=pdf_bytes,
                        file_name="clean_record.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Processing failed: {e}")

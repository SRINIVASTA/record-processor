import gc
import io
import pytesseract
from pypdf import PdfReader
from pdf2image import convert_from_bytes

def extract_text_from_scanned_pdf(pdf_bytes: bytes, dpi: int = 150) -> str:
    """
    Memory-safe OCR: converts and reads ONE page at a time so large scanned PDFs
    never exceed Streamlit Cloud's 1 GB RAM limit.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    extracted_pages = []

    for page_num in range(1, total_pages + 1):
        # Convert 1 page at a time to keep RAM usage low
        images = convert_from_bytes(
            pdf_bytes,
            dpi=dpi,
            first_page=page_num,
            last_page=page_num,
        )
        for img in images:
            page_text = pytesseract.image_to_string(img).strip()
            if page_text:
                extracted_pages.append(page_text)
            img.close()

        del images
        gc.collect()

    return "\n\n".join(extracted_pages).strip()

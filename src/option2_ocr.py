import pytesseract
from pdf2image import convert_from_bytes

def extract_text_from_scanned_pdf(pdf_bytes: bytes, dpi: int = 250) -> str:
    """Converts scanned PDF pages to images and extracts text using Tesseract OCR."""
    images = convert_from_bytes(pdf_bytes, dpi=dpi)
    extracted_pages = []

    for idx, img in enumerate(images, start=1):
        page_text = pytesseract.image_to_string(img)
        extracted_pages.append(f"--- Page {idx} ---\n{page_text.strip()}")

    return "\n\n".join(extracted_pages).strip()

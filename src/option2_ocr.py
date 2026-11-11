import gc
import io
import cv2
import numpy as np
import pytesseract
from pypdf import PdfReader
from pdf2image import convert_from_bytes

def _preprocess_notebook_page(pil_img) -> list[np.ndarray]:
    """
    1. Converts scanned page to grayscale.
    2. Removes faint ink bleed-through from the back of the paper.
    3. Splits two-column notebook pages into Left and Right halves if wide.
    """
    gray = np.array(pil_img.convert("L"))

    # Check if page is completely blank (> 99.2% white pixels)
    if np.mean(gray > 235) > 0.992:
        return []

    # Denoise and apply adaptive thresholding to erase faint back-page bleed-through
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    cleaned = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15,
    )

    # Split into Left & Right columns if it's a standard two-column notebook scan
    height, width = cleaned.shape
    mid = width // 2
    left_col = cleaned[:, :mid]
    right_col = cleaned[:, mid:]

    # Only include columns that actually contain ink
    columns = []
    if np.mean(left_col < 128) > 0.003:
        columns.append(left_col)
    if np.mean(right_col < 128) > 0.003:
        columns.append(right_col)

    return columns if columns else [cleaned]

def extract_text_from_scanned_pdf(
    pdf_bytes: bytes,
    start_page: int = 1,
    end_page: int = None,
    dpi: int = 200,
    progress_callback=None,
) -> str:
    """
    100% Free Local OCR (Zero Groq API usage).
    Cleans back-page bleed-through, splits notebook columns, and skips blank pages.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pdf_pages = len(reader.pages)

    first = max(1, start_page)
    last = min(total_pdf_pages, end_page) if end_page else total_pdf_pages
    total_to_process = max(1, last - first + 1)

    extracted_pages = []
    tess_config = "--oem 3 --psm 6"

    for idx, page_num in enumerate(range(first, last + 1), start=1):
        if progress_callback:
            progress_callback(idx, total_to_process, page_num)

        images = convert_from_bytes(
            pdf_bytes,
            dpi=dpi,
            first_page=page_num,
            last_page=page_num,
        )
        for img in images:
            columns = _preprocess_notebook_page(img)
            col_texts = []
            for col_img in columns:
                txt = pytesseract.image_to_string(col_img, config=tess_config).strip()
                if txt:
                    col_texts.append(txt)
            if col_texts:
                extracted_pages.append("\n\n".join(col_texts))
            img.close()

        del images
        gc.collect()

    return "\n\n".join(extracted_pages).strip()

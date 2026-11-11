import os
from fpdf import FPDF

FONT_PATH = os.path.join("fonts", "Caveat-Regular.ttf")

def create_clean_pdf(
    text: str,
    title: str = "Official Record Document",
    ink_color: str = "Blue"
) -> bytes:
    """Generates a PDF rendered in a realistic human handwriting font with Blue or Black pen ink."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Set realistic pen ink color
    if ink_color.strip().lower() == "blue":
        pdf.set_text_color(18, 52, 130)   # Classic royal/ballpoint blue pen ink
    else:
        pdf.set_text_color(28, 28, 30)    # Classic natural black pen ink

    # Load custom handwriting TTF font if available
    if os.path.exists(FONT_PATH):
        pdf.add_font("Handwriting", "", FONT_PATH, uni=True)
        font_family = "Handwriting"
        title_size = 22
        body_size = 16
        line_height = 9
        safe_title = title
        safe_text = text
    else:
        # Fallback if .ttf font file is missing
        font_family = "Times"
        title_size = 16
        body_size = 12
        line_height = 7
        safe_title = title.encode("latin-1", "replace").decode("latin-1")
        safe_text = text.encode("latin-1", "replace").decode("latin-1")

    # Document Title
    pdf.set_font(font_family, size=title_size)
    pdf.cell(0, 12, safe_title, ln=True, align="L")
    pdf.ln(4)

    # Handwritten Body Text
    pdf.set_font(font_family, size=body_size)
    pdf.multi_cell(0, line_height, safe_text)

    return bytes(pdf.output())

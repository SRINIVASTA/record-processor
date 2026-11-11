import os
from fpdf import FPDF

FONT_PATH = os.path.join("fonts", "Caveat-Regular.ttf")

def _clean_unsupported_glyphs(text: str) -> str:
    """Replaces special Unicode spaces, hyphens, and math glyphs missing in Caveat font."""
    replacements = {
        "\u2011": "-",          # Non-breaking hyphen
        "\u2013": "-",          # En-dash
        "\u2014": " - ",        # Em-dash
        "\u202f": " ",          # Narrow no-break space
        "\u00a0": " ",          # Non-breaking space
        "∂": "d",               # Partial derivative
        "∮": "contour integral ",
        "∫": "integral ",
        "∇": "del ",
        "π": "pi",
        "∞": "infinity",
        "λ": "lambda",
        "θ": "theta",
        "α": "alpha",
        "β": "beta",
        "γ": "gamma",
        "δ": "delta",
        "Δ": "Delta",
        "ε": "epsilon",
        "σ": "sigma",
        "Σ": "Sum",
        "∑": "Sum",
        "√": "sqrt",
        "×": " x ",
        "÷": " / ",
        "±": "+/-",
        "≈": "~=",
        "≠": "!=",
        "≤": "<=",
        "≥": ">=",
        "→": "->",
        "⇒": "=>",
        "∈": " in ",
        "⁻": "^-",
        "⁺": "^+",
        "⁰": "^0",
        "¹": "^1",
        "²": "^2",
        "³": "^3",
        "⁴": "^4",
        "⁵": "^5",
    }
    for bad_char, good_char in replacements.items():
        text = text.replace(bad_char, good_char)
    return text

def create_clean_pdf(
    text: str,
    title: str = "",
    ink_color: str = "Blue"
) -> bytes:
    """Generates a PDF rendered in a realistic human handwriting font without missing glyph warnings."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Set realistic pen ink color
    if ink_color.strip().lower() == "blue":
        pdf.set_text_color(18, 52, 130)   # Classic royal/ballpoint blue pen ink
    else:
        pdf.set_text_color(28, 28, 30)    # Classic natural black pen ink

    clean_title = _clean_unsupported_glyphs(title)
    clean_text = _clean_unsupported_glyphs(text)

    # Load custom handwriting TTF font if available
    if os.path.exists(FONT_PATH):
        pdf.add_font("Handwriting", "", FONT_PATH, uni=True)
        font_family = "Handwriting"
        title_size = 22
        body_size = 16
        line_height = 9
        safe_title = clean_title
        safe_text = clean_text
    else:
        # Fallback if .ttf font file is missing
        font_family = "Times"
        title_size = 16
        body_size = 12
        line_height = 7
        safe_title = clean_title.encode("latin-1", "replace").decode("latin-1")
        safe_text = clean_text.encode("latin-1", "replace").decode("latin-1")

    # Document Title (rendered ONLY if a title is provided)
    if safe_title and safe_title.strip():
        pdf.set_font(font_family, size=title_size)
        pdf.cell(0, 12, safe_title.strip(), ln=True, align="L")
        pdf.ln(4)

    # Handwritten Body Text
    pdf.set_font(font_family, size=body_size)
    pdf.multi_cell(0, line_height, safe_text)

    return bytes(pdf.output())

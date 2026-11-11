from fpdf import FPDF

def create_clean_pdf(text: str, title: str = "Official Record Document") -> bytes:
    """Generates a clean, well-formatted PDF in memory and returns raw bytes."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title Header
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, title, ln=True, align="L")
    pdf.ln(4)

    # Body Text (sanitize unsupported characters for standard Helvetica)
    pdf.set_font("Helvetica", size=11)
    safe_text = text.encode("latin-1", "replace").decode("latin-1")
    pdf.multi_cell(0, 7, safe_text)

    return bytes(pdf.output())

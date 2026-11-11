from pypdf import PdfReader
from src.groq_client import get_groq_client

def extract_digital_pdf_text(uploaded_file) -> str:
    """Extracts selectable text from a standard (non-scanned) PDF."""
    reader = PdfReader(uploaded_file)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()

def summarize_for_records(
    text: str,
    target_limit: int = 150,
    limit_type: str = "words",
    model: str = "openai/gpt-oss-120b"
) -> dict:
    """Generates a record summary via Groq and computes exact word/character counts."""
    client = get_groq_client()

    prompt = (
        f"Summarize the following text clearly and accurately for official records. "
        f"Keep the summary strictly under {target_limit} {limit_type}. "
        f"Use plain, clear language and do not include introductory filler like 'Here is a summary':\n\n"
        f"{text}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an accurate record-keeping assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    summary = response.choices[0].message.content.strip()
    word_count = len(summary.split())
    char_count_with_spaces = len(summary)
    char_count_no_spaces = len(summary.replace(" ", ""))

    return {
        "summary": summary,
        "words": word_count,
        "chars_with_spaces": char_count_with_spaces,
        "chars_no_spaces": char_count_no_spaces,
    }

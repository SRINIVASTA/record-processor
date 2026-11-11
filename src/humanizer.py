from src.groq_client import get_groq_client

def rewrite_human_style(raw_ocr_text: str, model: str = "openai/gpt-oss-120b") -> str:
    """Cleans OCR artifacts and rewrites text into natural, human-written prose for records."""
    client = get_groq_client()

    prompt = (
        "Below is raw text extracted via OCR from a scanned document. "
        "Please fix any scanning typos, broken line wraps, and formatting errors. "
        "Rewrite the content so it reads smoothly in a clear, natural, human-written style suitable for official records. "
        "Preserve all factual details, dates, names, and numbers accurately. "
        "Output only the cleaned document text without commentary:\n\n"
        f"{raw_ocr_text}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert editor preparing clean, human-written documents for permanent records."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content.strip()

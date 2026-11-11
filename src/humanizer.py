import time
from src.groq_client import get_groq_client

def _split_into_chunks(text: str, max_words: int = 1800) -> list[str]:
    """Splits large OCR text into safe chunks under Groq's 8,000 TPM limit."""
    words = text.split()
    return [
        " ".join(words[i : i + max_words])
        for i in range(0, len(words), max_words)
    ]

def rewrite_human_style(
    raw_ocr_text: str,
    model: str = "openai/gpt-oss-120b",
    progress_callback=None
) -> str:
    """Cleans OCR artifacts in safe chunks so large PDFs never hit Error 413."""
    client = get_groq_client()
    chunks = _split_into_chunks(raw_ocr_text, max_words=1800)
    cleaned_parts = []

    for idx, chunk in enumerate(chunks, start=1):
        if progress_callback:
            progress_callback(idx, len(chunks))

        prompt = (
            "Below is raw text extracted via OCR from a scanned document. "
            "Fix scanning typos, broken line wraps, and formatting errors. "
            "Rewrite it cleanly in natural human-written prose while keeping all maths formulas, "
            "numbers, and definitions accurate. Do not add headers, dates, or markdown symbols:\n\n"
            f"{chunk}"
        )

        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an expert editor preparing clean, human-written documents for permanent records."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 3500,
        }
        if "gpt-oss" in model or "qwen" in model:
            kwargs["reasoning_effort"] = "low"

        # Retry automatically if TPM rate limit triggers between chunks
        for attempt in range(4):
            try:
                resp = client.chat.completions.create(**kwargs)
                part = (resp.choices[0].message.content or "").strip()
                cleaned_parts.append(part)
                break
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    time.sleep(20 * (attempt + 1))
                else:
                    raise e

        # Pause between large chunks to respect the 8,000 Tokens-Per-Minute limit
        if idx < len(chunks):
            time.sleep(25)

    return "\n\n".join(cleaned_parts)

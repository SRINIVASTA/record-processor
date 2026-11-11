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

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert editor preparing clean, human-written documents for permanent records."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 4096,
    }
    if "gpt-oss" in model or "qwen" in model:
        kwargs["reasoning_effort"] = "low"

    response = client.chat.completions.create(**kwargs)
    return (response.choices[0].message.content or "").strip()

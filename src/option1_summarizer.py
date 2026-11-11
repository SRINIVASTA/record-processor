import time
from pypdf import PdfReader
from src.groq_client import get_groq_client

def extract_digital_pdf_text(uploaded_file) -> str:
    """Extracts selectable text from a standard (non-scanned) PDF."""
    reader = PdfReader(uploaded_file)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()

def _call_groq_with_retry(client, model: str, messages: list, temperature: float = 0.4, max_retries: int = 4) -> str:
    """Calls Groq API with enough max_tokens for reasoning models and retries on 429 rate limits."""
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4096,
            }
            if "gpt-oss" in model or "qwen" in model:
                kwargs["reasoning_effort"] = "low"

            resp = client.chat.completions.create(**kwargs)
            msg = resp.choices[0].message
            content = (msg.content or "").strip()

            if not content and getattr(msg, "reasoning", None):
                content = msg.reasoning.strip()

            return content
        except Exception as e:
            err_msg = str(e).lower()
            if "reasoning_effort" in err_msg:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=4096,
                )
                return (resp.choices[0].message.content or "").strip()
            if "429" in err_msg or "rate_limit" in err_msg:
                wait_time = 12 * (attempt + 1)
                time.sleep(wait_time)
            else:
                raise e
    raise RuntimeError("Groq rate limit persisted after multiple retries. Please try again in a minute.")
def generate_by_pages(
    content_or_topic: str,
    target_pages: int = 30,
    is_source_text: bool = False,
    model: str = "openai/gpt-oss-120b",
    progress_callback=None
) -> dict:
    """
    Generates a handwritten-ready record scaled to the exact number of PDF pages requested.
    Works whether the user enters a short topic ('Digital Flash') OR pastes/uploads long notes.
    """
    client = get_groq_client()

    # ~275 words fills 1 page in Caveat size 16 font with line height 9
    words_per_page = 275
    total_target_words = target_pages * words_per_page

    # Single call for 1–3 pages; multi-section loop for 4+ pages (up to 30+ pages)
    if target_pages <= 3:
        if progress_callback:
            progress_callback(1, 1, f"Writing {target_pages}-page record...")

        task_instruction = (
            "Summarize and format the provided source material"
            if is_source_text
            else "Write a comprehensive, well-structured official record on the following topic"
        )
        prompt = (
            f"{task_instruction} so that it is approximately {total_target_words} words long "
            f"(to fill {target_pages} handwritten pages).\n"
            f"Use clear, natural, human-written paragraphs. Do not use markdown symbols like ** or ##.\n\n"
            f"Input:\n{content_or_topic[:15000]}"
        )
        text = _call_groq_with_retry(
            client,
            model,
            [
                {"role": "system", "content": "You write clean, natural human-style documents for official records."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return _build_metrics(text)

    # Multi-page generation (4 to 50 pages) in chunks of ~3 pages per API call
    pages_per_chunk = 3
    num_chunks = (target_pages + pages_per_chunk - 1) // pages_per_chunk

    if progress_callback:
        progress_callback(0, num_chunks, f"Creating {target_pages}-page outline...")

    outline_prompt = (
        f"Create a logical {num_chunks}-part section outline to write a complete "
        f"{target_pages}-page record document based on:\n{content_or_topic[:6000]}\n\n"
        f"Return ONLY {num_chunks} numbered section headings, one per line."
    )
    outline_raw = _call_groq_with_retry(
        client,
        model,
        [{"role": "user", "content": outline_prompt}],
        temperature=0.4
    )
    sections = [line.strip() for line in outline_raw.splitlines() if line.strip()]

    while len(sections) < num_chunks:
        sections.append(f"Part {len(sections) + 1}: Detailed Record Continuation")
    sections = sections[:num_chunks]

    full_parts = []
    words_per_chunk = int(total_target_words / num_chunks) + 30

    for idx, sec_title in enumerate(sections, start=1):
        if progress_callback:
            progress_callback(idx, num_chunks, sec_title)

        section_prompt = (
            f"Write Part {idx} of {num_chunks} for an official {target_pages}-page record on:\n"
            f"{content_or_topic[:6000]}\n\n"
            f"Current Section Heading: {sec_title}\n"
            f"Write approximately {words_per_chunk} words in clear, natural, human-written prose. "
            f"Include thorough explanations, details, and smooth transitions. "
            f"Do not use markdown symbols such as ** or ##."
        )
        part_text = _call_groq_with_retry(
            client,
            model,
            [
                {"role": "system", "content": "You write detailed, authentic human-written records in plain text."},
                {"role": "user", "content": section_prompt}
            ],
            temperature=0.5
        )
        full_parts.append(part_text)

        if idx < num_chunks:
            time.sleep(2)  # Smooth pacing for free-tier rate limits

    combined = "\n\n".join(full_parts)
    return _build_metrics(combined)

def _build_metrics(text: str) -> dict:
    return {
        "summary": text,
        "words": len(text.split()),
        "chars_with_spaces": len(text),
        "chars_no_spaces": len(text.replace(" ", "")),
    }

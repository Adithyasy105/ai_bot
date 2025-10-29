import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

# ----------------- Setup -----------------
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise RuntimeError("❌ Missing GEMINI_API_KEY in .env file")

genai.configure(api_key=GEMINI_KEY)

MAX_MEMORY_CHARS = 3000  # Maximum memory size before summarizing


# ----------------- Text Cleaner -----------------
def clean_text_for_summarization(text: str) -> str:
    """Cleans sensitive or policy-flagging words to reduce Gemini refusal."""
    sensitive_words = [
        r"\bsex\b", r"\bnude\b", r"\bnaked\b", r"\bsensual\b",
        r"\bexplicit\b", r"\bviolence\b", r"\bhate\b",
        r"\bracist\b", r"\btorture\b",
    ]
    clean_text = text
    for pattern in sensitive_words:
        clean_text = re.sub(pattern, "[redacted]", clean_text, flags=re.IGNORECASE)
    return clean_text


# ----------------- Summarizer -----------------
def summarize_text(text: str) -> str:
    """
    Summarizes memory safely using Gemini.
    Handles safety filters, blocked responses, and fallback cases.
    """
    if not text or len(text.strip()) < 50:
        return text.strip()

    cleaned_text = clean_text_for_summarization(text)

    prompt = (
        "You are a summarization system for an AI memory module.\n"
        "Summarize the following conversation history objectively and factually.\n"
        "List the key facts, user preferences, and important details only.\n"
        "Avoid any emotional or personal tone.\n"
        "Keep the summary under 100 words.\n\n"
        f"Conversation History:\n{cleaned_text}"
    )

    print("🧠 Summarizing memory...")

    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=200,
            ),
        )

        summary = None
        finish_reason = "UNKNOWN"

        # ---------- Extract text safely ----------
        if hasattr(response, "candidates") and response.candidates:
            for cand in response.candidates:
                finish_reason = getattr(cand, "finish_reason", "UNKNOWN")

                # 1️⃣ Direct text extraction (most common)
                if hasattr(response, "text") and response.text:
                    summary = response.text.strip()
                    break

                # 2️⃣ Fallback: extract from parts
                if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                    parts = [
                        getattr(part, "text", "")
                        for part in cand.content.parts
                        if getattr(part, "text", None)
                    ]
                    if parts:
                        summary = " ".join(parts).strip()
                        break

        # ---------- Handle missing or blocked output ----------
        if not summary:
            print(f"⚠️ Gemini returned no usable text (finish_reason={finish_reason}). Fallback applied.")
            summary = cleaned_text[:MAX_MEMORY_CHARS]

        return summary.strip()

    except Exception as e:
        print(f"⚠️ Gemini summarization skipped due to: {e}")
        return cleaned_text[:MAX_MEMORY_CHARS]


# ----------------- Memory Appender -----------------
def append_and_trim_memory(existing: str, new_pair: str) -> str:
    """
    Appends new conversation data to memory.
    If it exceeds size limit, summarize it.
    """
    combined = (existing + "\n" + new_pair).strip() if existing else new_pair.strip()

    # If within limits, just return
    if len(combined) <= MAX_MEMORY_CHARS:
        return combined

    # Otherwise summarize
    summary = summarize_text(combined)
    if len(summary) > MAX_MEMORY_CHARS:
        summary = summary[:MAX_MEMORY_CHARS]

    return summary.strip()

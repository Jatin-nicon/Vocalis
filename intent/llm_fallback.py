from __future__ import annotations
import json
import os
import re
import urllib.request
from typing import Optional
from config import settings

# API keys are read from the environment only (see .env.example). Never hardcode
# secrets in source control -- rotate any key that was ever committed.
OPENROUTER_FALLBACK_KEY = os.getenv("OPENROUTER_API_KEY", "")


import unicodedata

def clean_for_speech(text: str) -> str:
    """Strips markdown, reasoning tags, and normalizes unicode for clean TTS reading."""
    if not text:
        return ""
    # Strip <think>...</think> reasoning blocks
    t = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Strip safety banners like "User Safety: safe"
    t = re.sub(r"(?i)^(\s*user\s+safety\s*:\s*\w+\s*)+", "", t.strip())
    t = re.sub(r"(?i)^(\s*safety\s+evaluation\s*:\s*\w+\s*)+", "", t.strip())

    # Mathematical and common symbol replacements for spoken audio
    t = t.replace("\u2248", " approximately ")
    t = t.replace("\xd7", " times ")
    t = t.replace("\u00b0", " degrees ")
    t = t.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("\u2018", "'").replace("\u2019", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    t = t.replace("\u2026", "...")

    # Strip markdown syntax
    cleaned = re.sub(r"[*#_`$]+", "", t)
    cleaned = re.sub(r"\[.*?\]\(.*?\)", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Split into sentences and take up to 2 clear sentences
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
    selected = " ".join(sentences[:2]) if len(sentences) > 2 else cleaned

    # Normalize to safe ASCII to prevent Windows console cp1252 / SAPI5 crashes
    safe_text = unicodedata.normalize("NFKD", selected).encode("ascii", "ignore").decode("ascii").strip()
    return safe_text


def answer_question_with_llm(query: str) -> Optional[str]:
    """
    Queries an LLM (OpenRouter / Groq) to provide a direct spoken answer
    to any natural question or task.
    """
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "You are Jester, a helpful desktop voice assistant. "
                "Answer the user's question directly and concisely in 1 to 2 clear sentences. "
                "Do NOT include thinking, reasoning, or safety disclaimers in your answer. "
                "Do NOT use markdown, bullet points, asterisks, or lists, because your answer will be spoken aloud."
            ),
        },
        {"role": "user", "content": query},
    ]

    # 1. Try Groq if key is present
    groq_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            payload = {
                "model": settings.groq_model,
                "messages": prompt_messages,
                "max_tokens": 150,
                "temperature": 0.3,
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_answer = data["choices"][0]["message"]["content"]
                if raw_answer:
                    cleaned = clean_for_speech(raw_answer)
                    if cleaned:
                        return cleaned
        except Exception:
            pass

    # 2. Try OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY", OPENROUTER_FALLBACK_KEY)
    if openrouter_key:
        for model in ("openrouter/free", "liquid/lfm-2.5-2.6b:free", "inclusionai/ling-3.0-flash-sante:free", "qwen/qwen3.8-27b:free"):
            try:
                url = "https://openrouter.ai/api/v1/chat/completions"
                payload = {
                    "model": model,
                    "messages": prompt_messages,
                    "max_tokens": 250,
                    "temperature": 0.4,
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/voice-pc-assistant",
                        "X-Title": "Voice-PC-Assistant",
                    },
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    msg = data["choices"][0]["message"]
                    raw_answer = msg.get("content") or msg.get("reasoning", "")
                    if raw_answer:
                        cleaned = clean_for_speech(raw_answer)
                        if cleaned and len(cleaned) > 5:
                            return cleaned
            except Exception:
                continue

    return None

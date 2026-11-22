from __future__ import annotations
import re

PUNCTUATION_REPLACEMENTS = [
    (r"\bperiod\b", "."),
    (r"\bfull stop\b", "."),
    (r"\bcomma\b", ","),
    (r"\bquestion mark\b", "?"),
    (r"\bexclamation mark\b", "!"),
    (r"\bcolon\b", ":"),
    (r"\bsemicolon\b", ";"),
    (r"\bnew line\b", "\n"),
    (r"\bnew paragraph\b", "\n\n"),
]

FILLER_WORDS = [
    r"\bum\b",
    r"\buh\b",
    r"\buhh\b",
    r"\ber\b",
    r"\bah\b",
]


def clean_text(text: str) -> str:
    if not text:
        return ""

    result = text.strip()

    # Clean filler words
    for filler in FILLER_WORDS:
        result = re.sub(filler, "", result, flags=re.IGNORECASE)

    # Format spoken punctuation
    for pattern, repl in PUNCTUATION_REPLACEMENTS:
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)

    # Fix spacing around punctuation: e.g. "word ." -> "word."
    result = re.sub(r"\s+([.,!?:;])", r"\1", result)

    # Capitalize first letter of string
    if result:
        result = result[0].upper() + result[1:]

    # Capitalize after sentence-ending punctuation
    result = re.sub(r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), result)

    # Clean multiple spaces
    result = re.sub(r" +", " ", result).strip()

    return result

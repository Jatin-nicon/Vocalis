from __future__ import annotations
import re
from typing import Tuple

# Common interrogative starters for general knowledge / conversational questions
QUESTION_STARTERS = (
    "who was ", "who is ", "who were ", "who are ", "who created ",
    "who invented ", "who won ", "who discovered ", "who built ",
    "who directed ", "who wrote ", "who ",
    "why is ", "why was ", "why does ", "why did ", "why do ", "why are ", "why ",
    "how do ", "how does ", "how did ", "how is ", "how are ", "how can ",
    "how to ", "how come ", "how ",
    "what is ", "what was ", "what are ", "what were ", "what causes ",
    "what happened ", "what does ", "what do ", "what ",
    "when was ", "when did ", "when is ", "when were ", "when will ", "when ",
    "where is ", "where was ", "where are ", "where were ", "where do ", "where does ", "where ",
    "which is ", "which was ", "which are ", "which ",
    "tell me about ", "tell me more about ", "can you tell me about ",
    "explain ", "explain to me ", "can you explain ",
    "describe ", "define ", "meaning of ", "what is the meaning of ",
    "give me information about ", "give me facts about ",
)

# System / Hardware inquiries that should be answered by local knowledge rather than LLM
OFFLINE_SYSTEM_PATTERNS = (
    "what time is it", "what is the time", "current time", "tell me the time", "what's the time", "time now",
    "what is the date", "what's the date", "what is today's date", "what day is today", "what day is it", "today's date",
    "battery status", "check battery", "how is my battery", "battery percentage", "how much battery",
    "cpu usage", "ram usage", "system performance", "system status", "pc performance",
    "what is the volume", "what's the volume", "current volume", "check volume",
    "what is the brightness", "what's the brightness", "current brightness", "check brightness",
    "who are you", "what is your name", "what's your name", "who made you", "who created you",
    "how are you", "tell me a joke", "say a joke", "what can you do", "help",
)


def clean_conversational_prefix(text: str) -> str:
    """
    Strips leading polite prefixes, assistant names, and requests.
    E.g. 'Can you please tell me about Charles Babbage' -> 'tell me about Charles Babbage'
    E.g. 'Could you open up Chrome' -> 'open up Chrome'
    """
    s = text.strip()
    prefix_pattern = (
        r"^(?:"
        r"(?:hey\s+|hi\s+|ok\s+|okay\s+)?(?:jester|jarvis|assistant|computer)|"
        r"can\s+you(?:\s+please)?|"
        r"could\s+you(?:\s+please)?|"
        r"would\s+you(?:\s+please)?|"
        r"will\s+you(?:\s+please)?|"
        r"i\s+want\s+you\s+to|"
        r"i\s+need\s+you\s+to|"
        r"go\s+ahead\s+and|"
        r"just|"
        r"please"
        r")[,\s:;!]+"
    )
    while True:
        sub = re.sub(prefix_pattern, "", s, flags=re.IGNORECASE).strip()
        if sub == s:
            break
        s = sub

    suffix_pattern = r"[,\s]+(?:please|for me|right now|now|quick|quickly|a bit|a little|a little bit)\s*$"
    while True:
        sub = re.sub(suffix_pattern, "", s, flags=re.IGNORECASE).strip()
        if sub == s:
            break
        s = sub

    return s.rstrip(".?!,;:").strip()


def is_offline_system_query(text: str) -> bool:
    """Returns True if the utterance is a built-in PC/system state inquiry (time, battery, volume, etc.)."""
    s = clean_conversational_prefix(text).lower()
    return any(p in s for p in OFFLINE_SYSTEM_PATTERNS) or s in ("time", "date", "battery", "joke", "help")


def is_informational_question(text: str) -> Tuple[bool, str]:
    """
    Determines if an utterance is an informational question or inquiry to be answered aloud.
    Returns: (is_question, cleaned_query_for_llm)
    """
    s = clean_conversational_prefix(text).lower()

    # 1. System state inquiries are handled offline, not by LLM
    if is_offline_system_query(s):
        return False, s

    # 2. Check if user asked to search for or google a question
    # e.g., 'search for why the sky is blue', 'google who won the world cup'
    m_search = re.search(r"^(?:search google for|search the web for|search for|google|look up)\s+(.+)", s)
    if m_search:
        inner_query = m_search.group(1).strip()
        if any(inner_query.startswith(starter) for starter in QUESTION_STARTERS):
            return True, inner_query

    # 3. Direct question starters (who, why, how, what is, explain, etc.)
    if any(s.startswith(starter) for starter in QUESTION_STARTERS):
        return True, s

    # 4. Sentences ending with '?' that do not match action command patterns
    if text.strip().endswith("?"):
        # Ensure it is not an action phrased as a question (e.g. "Can you open Chrome?", "Could you mute?")
        action_verbs = ("open", "close", "shut", "kill", "mute", "unmute", "louder", "quieter", "type", "write", "delete", "backspace")
        if not any(s.startswith(v) for v in action_verbs):
            return True, s

    return False, s

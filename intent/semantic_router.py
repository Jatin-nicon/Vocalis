from __future__ import annotations
import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from config import settings
from .actions import execute_action, ActionResult, ACTION_REGISTRY
from .llm_fallback import clean_for_speech, OPENROUTER_FALLBACK_KEY
from .knowledge import match_knowledge_query
from .classifier import clean_conversational_prefix, is_informational_question


@dataclass
class SemanticDecision:
    intent_type: str  # "task", "mode", "dictate", "answer", "unknown"
    action_name: str
    message: str
    params: Dict[str, Any] = field(default_factory=dict)
    text_to_paste: str = ""


# ---------------------------------------------------------------------------
# Tier 1: Fast Local Semantic Heuristics (< 2ms)
# Handles hundreds of natural phrasing variations without needing network
# ---------------------------------------------------------------------------

def match_local_semantic_heuristic(raw: str) -> Optional[SemanticDecision]:
    s_clean = clean_conversational_prefix(raw).lower().strip()


    # 1. Type Last Answer ("can you type it down", "type that down", "type it", "paste it", etc.)
    type_answer_phrases = [
        "type it down", "type that down", "type it", "type that",
        "write it down", "write that down", "write down the answer", "type the answer",
        "paste it", "paste that", "paste the answer", "type what you said", "type what you just said",
        "write what you said", "type the last answer", "type response", "type the response",
    ]
    if any(s_clean == p or s_clean == (p + " please") or s_clean.startswith(p + " ") for p in type_answer_phrases):
        return SemanticDecision("type_last_answer", "type_last_answer", "Typing the answer down.")

    # 1.1 Active Text Editing & Deletion Controls
    # Backspace (e.g. "backspace", "backspace 5 times", "backspace twice")
    m_bs = re.search(r"^(?:press\s+|hit\s+)?backspace(?:\s+(?:(\d+|one|two|twice|three|four|five|six|seven|eight|nine|ten))\s*(?:times)?)?$", s_clean)
    if m_bs:
        raw_cnt = m_bs.group(1)
        cnt = int(raw_cnt) if (raw_cnt and raw_cnt.isdigit()) else ({"twice": 2, "two": 2, "three": 3, "four": 4, "five": 5}.get(raw_cnt or "", 1))
        res = execute_action("backspace", {"count": cnt})
        return SemanticDecision("task", "backspace", res.message)

    # Delete word (e.g. "delete word", "delete last word", "delete 3 words", "erase word")
    m_dw = re.search(r"^(?:delete|erase|remove)\s*(?:the\s+)?(?:last\s+|previous\s+)?(?:(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+)?words?$", s_clean)
    if m_dw:
        raw_cnt = m_dw.group(1)
        cnt = int(raw_cnt) if (raw_cnt and raw_cnt.isdigit()) else ({"two": 2, "three": 3, "four": 4, "five": 5}.get(raw_cnt or "", 1))
        res = execute_action("delete_word", {"count": cnt})
        return SemanticDecision("task", "delete_word", res.message)

    # Delete sentence / line
    if any(p in s_clean for p in [
        "delete sentence", "delete the sentence", "delete this sentence",
        "clear sentence", "clear the sentence", "erase sentence", "erase the sentence",
        "remove sentence", "delete line", "delete the line", "delete this line",
        "clear line", "clear the line", "erase line", "remove line",
    ]):
        res = execute_action("delete_sentence")
        return SemanticDecision("task", "delete_sentence", res.message)

    # Undo / Delete that
    if s_clean in ["delete that", "erase that", "undo that", "scratch that", "undo", "revert that"]:
        res = execute_action("undo")
        return SemanticDecision("task", "undo", res.message)

    # Delete all / Clear
    if any(p in s_clean for p in ["delete all", "clear all", "erase all", "select all and delete", "clear everything", "clear text"]):
        res = execute_action("delete_all")
        return SemanticDecision("task", "delete_all", res.message)

    # New line / Press enter
    if s_clean in ["new line", "next line", "press enter", "enter", "hit enter"]:
        res = execute_action("new_line")
        return SemanticDecision("task", "new_line", res.message)

    # 1.2 Typing Mode Toggles
    if any(p in s_clean for p in ["start typing", "begin typing", "start dictation", "typing mode on", "enable typing"]):
        return SemanticDecision("mode", "start_typing", "Typing mode activated. Speak freely to type. Say 'stop typing' to exit.")

    if any(p in s_clean for p in ["stop typing", "end typing", "exit typing", "stop dictation", "typing mode off", "disable typing"]):
        return SemanticDecision("mode", "stop_typing", "Typing mode deactivated. Returned to command mode.")

    # 1.3 Explicit Dictation & Typing
    m_dictate = re.search(r"^(?:type\s+down|write\s+down|type\s+out|write\s+out|type|write|dictate)\s+(.+)", s_clean)
    if m_dictate:
        text = m_dictate.group(1).strip()
        text_lower = text.lower().strip(" .?!,")
        if text_lower in (
            "it down", "that down", "it", "that", "the answer", "down the answer",
            "what you said", "what you just said", "the last answer", "the response",
        ):
            return SemanticDecision("type_last_answer", "type_last_answer", "Typing the answer down.")
        return SemanticDecision("dictate", "dictate", "Dictated text.", text_to_paste=text)

    # Mute / Unmute (Checked before general volume checks to prevent 'shut down the sound' from triggering volume down)
    if any(p in s_clean for p in ["unmute", "restore sound", "unmute sound", "turn sound back on", "restore audio", "turn on sound"]):
        res = execute_action("unmute")
        return SemanticDecision("task", "unmute", res.message)

    if any(p in s_clean for p in [
        "silence", "be quiet", "shut up", "shut down the sound",
        "turn off the sound", "turn off sound", "turn off audio",
        "kill sound", "kill the sound", "mute sound", "mute audio"
    ]) or re.search(r"\bmute\b", s_clean):
        res = execute_action("mute")
        return SemanticDecision("task", "mute", res.message)

    # 3. Generalized Volume Checks
    has_sound_word = any(w in s_clean for w in ["sound", "volume", "audio"])
    has_increase_word = any(w in s_clean for w in ["higher", "louder", "up", "raise", "increase", "boost", "more", "can't hear"])
    has_decrease_word = any(w in s_clean for w in ["lower", "quieter", "down", "reduce", "decrease", "less", "too loud", "noisy"])

    # Volume level
    m_vol = re.search(r"(?:set|change|put)?\s*(?:the\s+)?volume\s*(?:to|at)?\s*(\d+)", s_clean)
    if m_vol:
        lvl = int(m_vol.group(1))
        res = execute_action("set_volume", {"level": lvl})
        return SemanticDecision("task", "set_volume", res.message)

    if has_sound_word and has_increase_word:
        res = execute_action("volume_up")
        return SemanticDecision("task", "volume_up", res.message)

    if has_sound_word and has_decrease_word:
        res = execute_action("volume_down")
        return SemanticDecision("task", "volume_down", res.message)

    if any(p in s_clean for p in ["louder", "make it louder", "turn it up", "a bit louder", "pump up the volume"]):
        res = execute_action("volume_up")
        return SemanticDecision("task", "volume_up", res.message)

    if any(p in s_clean for p in ["quieter", "make it quieter", "turn it down", "a bit quieter", "too loud", "too noisy"]):
        res = execute_action("volume_down")
        return SemanticDecision("task", "volume_down", res.message)


    # 4. Media variations
    if any(p in s_clean for p in ["pause music", "stop music", "resume music", "play music", "pause video", "play video", "play pause", "pause", "resume"]):
        res = execute_action("media_play_pause")
        return SemanticDecision("task", "media_play_pause", res.message)

    if any(p in s_clean for p in ["next song", "skip song", "next track", "skip track", "next video", "skip this"]):
        res = execute_action("media_next")
        return SemanticDecision("task", "media_next", res.message)

    if any(p in s_clean for p in ["previous song", "prev song", "previous track", "last song", "previous video"]):
        res = execute_action("media_previous")
        return SemanticDecision("task", "media_previous", res.message)

    # 5. Window & Tab variations
    if any(p in s_clean for p in [
        "close tab", "close this tab", "shut tab", "shut this tab", "kill tab", "kill this tab",
        "close this page", "exit page", "close current tab", "exit tab",
    ]):
        res = execute_action("close_tab")
        return SemanticDecision("task", "close_tab", res.message)

    if any(p in s_clean for p in ["new tab", "open a new tab", "create a tab", "another tab"]):
        res = execute_action("new_tab")
        return SemanticDecision("task", "new_tab", res.message)

    if any(p in s_clean for p in ["reopen tab", "restore tab", "open closed tab"]):
        res = execute_action("reopen_tab")
        return SemanticDecision("task", "reopen_tab", res.message)

    if any(p in s_clean for p in ["minimize window", "minimize this", "hide window", "hide this window", "minimize"]):
        res = execute_action("minimize_window")
        return SemanticDecision("task", "minimize_window", res.message)

    if any(p in s_clean for p in ["maximize window", "maximize this", "full screen", "fullscreen"]):
        res = execute_action("maximize_window")
        return SemanticDecision("task", "maximize_window", res.message)

    if any(p in s_clean for p in ["switch window", "switch app", "alt tab", "next window"]):
        res = execute_action("switch_window")
        return SemanticDecision("task", "switch_window", res.message)

    if any(p in s_clean for p in ["show desktop", "go to desktop", "minimize all"]):
        res = execute_action("show_desktop")
        return SemanticDecision("task", "show_desktop", res.message)

    # Close active window / opened application
    if any(p in s_clean for p in [
        "close window", "close this window", "close active window", "close current window",
        "close this app", "close the app", "close app", "close this application",
        "close the application", "close opened application", "close open application",
        "close the opened app", "close opened app", "exit this app", "quit this app",
        "exit app", "quit app",
    ]):
        res = execute_action("close_window")
        return SemanticDecision("task", "close_window", res.message)

    # 6. Web & YouTube Search
    m_yt = re.search(r"(?:search youtube for|look up on youtube|play on youtube|find on youtube|listen to on youtube|youtube)\s+(.+)", s_clean)
    if not m_yt and "youtube" in s_clean:
        m_yt_end = re.search(r"^(?:search for|search|play|find|look up|listen to)\s+(.+?)(?:\s+(?:on|in)?\s*youtube)\s*$", s_clean)
        if m_yt_end:
            m_yt = m_yt_end
    if m_yt:
        q = m_yt.group(1).strip()
        res = execute_action("search_youtube", {"query": q})
        return SemanticDecision("task", "search_youtube", res.message)

    # 6. Applications Launch / Close
    m_open = re.search(r"^(?:open|launch|start|run|pull up|bring up)\s+([a-zA-Z0-9_\- ]+)", s_clean)
    if m_open:
        app = m_open.group(1).strip()
        # Ensure it's not a question like "open what"
        if len(app) > 1 and not any(app.startswith(w) for w in ["what", "why", "when", "how", "tab", "window"]):
            res = execute_action("open_app", {"app_name": app})
            return SemanticDecision("task", "open_app", res.message)

    m_close = re.search(r"^(?:close|quit|exit|kill)\s+([a-zA-Z0-9_\- ]+)", s_clean)
    if m_close:
        app = m_close.group(1).strip()
        if not any(w in app for w in ["tab", "page", "window"]):
            res = execute_action("close_app", {"app_name": app})
            return SemanticDecision("task", "close_app", res.message)

    # 7. Web & YouTube Search
    m_web = re.search(r"^(?:search google for|search the web for|search for|google|look up)\s+(.+)", s_clean)
    if m_web:
        q = m_web.group(1).strip()
        # Avoid trapping questions like "search for why the sky is blue" or "look up who was Einstein"
        is_q, _ = is_informational_question(q)
        if not is_q:
            res = execute_action("search_web", {"query": q})
            return SemanticDecision("task", "search_web", res.message)


    # 8. Brightness & Display
    has_disp_word = any(w in s_clean for w in ["brightness", "screen", "display"])
    has_bright_up = any(w in s_clean for w in ["higher", "brighter", "up", "raise", "increase", "boost", "more", "too dark", "dark"])
    has_bright_down = any(w in s_clean for w in ["lower", "dimmer", "down", "reduce", "decrease", "less", "too bright", "bright", "dim"])

    if has_disp_word and has_bright_up:
        res = execute_action("brightness_up")
        return SemanticDecision("task", "brightness_up", res.message)

    if has_disp_word and has_bright_down:
        res = execute_action("brightness_down")
        return SemanticDecision("task", "brightness_down", res.message)

    if any(p in s_clean for p in ["brightness up", "increase brightness", "more brightness", "brighter", "screen is too dark", "make it brighter"]):
        res = execute_action("brightness_up")
        return SemanticDecision("task", "brightness_up", res.message)

    if any(p in s_clean for p in ["brightness down", "decrease brightness", "lower brightness", "dimmer", "screen is too bright", "too bright", "dim screen"]):
        res = execute_action("brightness_down")
        return SemanticDecision("task", "brightness_down", res.message)

    if any(p in s_clean for p in ["lock screen", "lock computer", "lock pc", "lock the screen"]):
        res = execute_action("lock_screen")
        return SemanticDecision("task", "lock_screen", res.message)

    if any(p in s_clean for p in ["take screenshot", "take a screenshot", "screenshot", "capture screen", "snap screen"]):
        res = execute_action("take_screenshot")
        return SemanticDecision("task", "take_screenshot", res.message)

    return None


# ---------------------------------------------------------------------------
# Tier 2: Dynamic LLM Semantic Intent Classifier (~250-500ms)
# Employs fast structured reasoning to dynamically classify ANY task or answer
# ---------------------------------------------------------------------------

SEMANTIC_SYSTEM_PROMPT = """You are Jarvis, an intelligent Windows voice assistant.
Your job is to analyze the user's spoken utterance and classify it into either:
1. "task": The user wants you to control the PC or perform a system action.
2. "answer": The user is asking a question, seeking information, or chatting.

AVAILABLE PC TASK ACTIONS:
- "volume_up" (make sound louder, can't hear, raise volume)
- "volume_down" (make sound quieter, too loud, lower volume)
- "set_volume" (params: {"level": 0-100})
- "mute" (silence audio)
- "unmute" (restore audio)
- "media_play_pause" (play/pause video or music)
- "media_next" (skip to next track/video)
- "media_previous" (go to previous track/video)
- "close_tab" (close current browser tab/page)
- "new_tab" (open new browser tab)
- "minimize_window" (minimize current window)
- "maximize_window" (maximize or full screen current window)
- "switch_window" (alt-tab / switch between active apps)
- "show_desktop" (minimize all, show desktop)
- "open_app" (params: {"app_name": "<name>"})
- "close_app" (params: {"app_name": "<name>"})
- "search_youtube" (params: {"query": "<search terms>"})
- "search_web" (params: {"query": "<search terms>"})
- "brightness_up" (make screen brighter, too dark)
- "brightness_down" (dim screen, too bright)
- "set_brightness" (params: {"level": 0-100})
- "lock_screen" (lock Windows PC)
- "take_screenshot" (capture screen image)
- "start_typing" (enable continuous typing mode)
- "stop_typing" (disable continuous typing mode)
- "dictate" (params: {"text": "<text to type>"})

OUTPUT FORMAT:
Respond with ONLY a raw JSON object (no markdown, no backticks, no code fence).
If it is a PC task:
{"type": "task", "action": "<action_name>", "params": {}}

If it is a question, explanation, or conversational chat:
{"type": "answer", "response": "<1-2 clear, direct sentences to be spoken aloud via TTS>"}
"""


def call_semantic_llm(user_text: str) -> Optional[Dict[str, Any]]:
    """Calls Groq / OpenRouter with the structured semantic prompt."""
    payload_data = {
        "messages": [
            {"role": "system", "content": SEMANTIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.1,
        "max_tokens": 150,
    }

    # 1. Try Groq if key exists
    groq_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps({**payload_data, "model": settings.groq_model, "response_format": {"type": "json_object"}}).encode("utf-8"),
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception:
            pass

    # 2. Try OpenRouter free tier
    openrouter_key = os.getenv("OPENROUTER_API_KEY", OPENROUTER_FALLBACK_KEY)
    if openrouter_key:
        for model in ("openrouter/free", "liquid/lfm-2.5-2.6b:free", "inclusionai/ling-3.0-flash-sante:free", "qwen/qwen3.8-27b:free"):
            try:
                req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/chat/completions",
                    data=json.dumps({**payload_data, "model": model}).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/voice-pc-assistant",
                        "X-Title": "Voice-PC-Assistant",
                    },
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw = data["choices"][0]["message"]["content"].strip()
                    # Strip any markdown code formatting
                    clean_json = re.sub(r"^```(?:json)?\s*", "", raw)
                    clean_json = re.sub(r"\s*```$", "", clean_json).strip()
                    # Find JSON boundaries
                    m = re.search(r"\{.*\}", clean_json, flags=re.DOTALL)
                    if m:
                        return json.loads(m.group(0))
            except Exception:
                continue

    return None


def resolve_semantic_intent(user_text: str) -> SemanticDecision:
    """
    Unified entry point for dynamic semantic understanding:
    1. Instant local semantic heuristics (< 2ms)
    2. Instant local offline knowledge (time, battery, system)
    3. Dynamic LLM classification & action execution
    """
    raw = user_text.strip()
    if not raw:
        return SemanticDecision("unknown", "none", "No speech detected.")

    # 1. Check instant local heuristics
    local_match = match_local_semantic_heuristic(raw)
    if local_match:
        return local_match

    # 2. Check offline knowledge
    k_ans = match_knowledge_query(raw)
    if k_ans:
        return SemanticDecision("answer", "knowledge_answer", k_ans)

    # 3. Dynamic LLM Classifier
    llm_decision = call_semantic_llm(raw)
    if llm_decision and isinstance(llm_decision, dict):
        dec_type = llm_decision.get("type", "answer")

        if dec_type == "task":
            action_name = llm_decision.get("action", "")
            params = llm_decision.get("params", {})
            if action_name in ("start_typing", "stop_typing"):
                msg = "Typing mode activated." if action_name == "start_typing" else "Typing mode deactivated."
                return SemanticDecision("mode", action_name, msg)
            elif action_name == "dictate":
                text = params.get("text", raw)
                return SemanticDecision("dictate", "dictate", "Dictated text.", text_to_paste=text)
            elif action_name in ACTION_REGISTRY:
                action_res: ActionResult = execute_action(action_name, params)
                return SemanticDecision("task", action_name, action_res.message, params=params)
            else:
                resp = llm_decision.get("response") or f"Executed {action_name}"
                return SemanticDecision("answer", "ai_answer", clean_for_speech(resp))

        elif dec_type == "answer":
            spoken_ans = clean_for_speech(llm_decision.get("response", ""))
            if spoken_ans:
                return SemanticDecision("answer", "ai_answer", spoken_ans)

    # 4. Fallback: Default unrecognized guidance
    return SemanticDecision(
        "unknown",
        "unknown",
        "I'm not sure how to help with that. Say 'help' to hear what I can do.",
    )

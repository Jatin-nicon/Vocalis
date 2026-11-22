from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Callable, Any
from windows_controls import (
    change_volume,
    set_volume,
    mute,
    unmute,
    toggle_mute,
    max_volume,
    min_volume,
    play_pause,
    next_track,
    prev_track,
    forward_seconds,
    rewind_seconds,
    close_tab,
    new_tab,
    reopen_tab,
    minimize_window,
    maximize_window,
    switch_window,
    close_window,
    show_desktop,
    lock_screen,
    change_brightness,
    set_brightness,
    take_screenshot,
    open_app,
    close_app_by_name,
    search_web,
)
from dictation import (
    press_backspace,
    delete_word,
    delete_sentence_or_line,
    delete_all,
    undo_last,
    insert_new_line,
    paste_text,
)
from config import settings
from .classifier import clean_conversational_prefix, is_informational_question

WORD_TO_NUM = {
    "one": 1, "two": 2, "twice": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "twenty": 20, "thirty": 30, "fifty": 50,
}


def parse_count(val: str | None, default: int = 1) -> int:
    if not val:
        return default
    val = val.lower().strip()
    if val.isdigit():
        return int(val)
    return WORD_TO_NUM.get(val, default)


@dataclass
class IntentResult:
    matched: bool
    category: str  # "command", "dictate", "llm", "unknown"
    action_name: str
    execute: Callable[[], str] | None = None
    payload: str = ""


def clean_prefix(raw: str) -> str:
    return clean_conversational_prefix(raw)



def match_command(text: str) -> IntentResult:
    cleaned_text = clean_prefix(text)
    s = cleaned_text.lower().strip()

    # 1. Type Last Answer ("can you type it down", "type that down", "type it", "paste it", etc.)
    type_answer_phrases = [
        "type it down", "can you type it down", "type that down", "can you type that down",
        "type it", "can you type it", "type that", "can you type that",
        "write it down", "can you write it down", "write that down", "can you write that down",
        "type down the answer", "type the answer", "write down the answer", "write the answer",
        "paste it", "paste that", "paste the answer", "type what you said", "type what you just said",
        "write what you said", "write what you just said", "type the last answer",
        "type response", "type the response", "type down what you said",
    ]
    if any(s == p or s == (p + " please") or s.startswith(p + " ") for p in type_answer_phrases):
        return IntentResult(
            matched=True,
            category="type_last_answer",
            action_name="type_last_answer",
            payload="",
        )

    # 1.1 Active Text Editing & Deletion Controls
    # Backspace (e.g. "backspace", "backspace 5 times", "backspace twice")
    m_bs = re.search(r"^(?:press\s+)?backspace(?:\s+(?:(\d+|one|two|twice|three|four|five|six|seven|eight|nine|ten))\s*(?:times)?)?$", s)
    if m_bs:
        cnt = parse_count(m_bs.group(1), 1)
        return IntentResult(True, "command", "backspace", lambda: press_backspace(cnt))

    # Delete word (e.g. "delete word", "delete last word", "delete 3 words", "erase word")
    m_dw = re.search(r"^(?:delete|erase)\s*(?:the\s+)?(?:last\s+|previous\s+)?(?:(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+)?words?$", s)
    if m_dw:
        cnt = parse_count(m_dw.group(1), 1)
        return IntentResult(True, "command", "delete_word", lambda: delete_word(cnt))

    # Delete sentence / line (e.g. "delete sentence", "clear sentence", "delete this line", "erase sentence")
    if any(p in s for p in [
        "delete sentence", "delete the sentence", "delete this sentence",
        "clear sentence", "clear the sentence", "erase sentence", "erase the sentence",
        "remove sentence", "delete line", "delete the line", "delete this line",
        "clear line", "clear the line", "erase line", "remove line",
    ]):
        return IntentResult(True, "command", "delete_sentence", lambda: delete_sentence_or_line())

    # Undo / Delete that / Scratch that
    if s in ["delete that", "erase that", "undo that", "scratch that", "undo", "revert that"]:
        return IntentResult(True, "command", "undo", lambda: undo_last())

    # Delete all / Clear text
    if any(p in s for p in ["delete all", "clear all", "erase all", "select all and delete", "clear everything", "clear text"]):
        return IntentResult(True, "command", "delete_all", lambda: delete_all())

    # New line / Press enter
    if s in ["new line", "next line", "press enter", "enter", "hit enter"]:
        return IntentResult(True, "command", "new_line", lambda: insert_new_line())

    # 1.2 Typing Mode Toggles
    if any(p in s for p in ["start typing", "start dictation", "typing mode on", "begin typing"]):
        return IntentResult(True, "mode", "start_typing", payload="Typing mode activated. Speak freely to type. Say 'stop typing' to exit.")

    if any(p in s for p in ["stop typing", "stop dictation", "exit typing", "typing mode off", "end typing"]):
        return IntentResult(True, "mode", "stop_typing", payload="Typing mode deactivated. Returned to command mode.")

    # 1.3 Direct Dictation Trigger: "type ...", "type down ...", "write ...", "write down ..."
    m_dictate = re.search(
        r"^(?:can you\s+)?(?:type\s+down|write\s+down|type\s+out|write\s+out|type|write|dictate)\s+(.+)",
        cleaned_text,
        flags=re.IGNORECASE,
    )
    if m_dictate:
        content = m_dictate.group(1).strip()
        content_lower = content.lower().strip(" .?!,")
        if content_lower in (
            "it down", "that down", "it", "that", "the answer", "down the answer",
            "what you said", "what you just said", "the last answer", "the response",
            "it down for me", "that down for me", "it for me", "that for me",
        ):
            return IntentResult(True, "type_last_answer", "type_last_answer", payload="")
        return IntentResult(
            matched=True,
            category="dictate",
            action_name="dictate",
            payload=content,
        )

    # 1.5 Help & Capabilities
    if any(p in s for p in ["what can you do", "help", "show commands", "list commands", "what are your commands"]):
        help_msg = (
            "You can control volume, media playback, browser tabs, "
            "open apps, search Google or YouTube, adjust brightness, "
            "take screenshots, lock the screen, or dictate text."
        )
        return IntentResult(True, "command", "help", lambda: help_msg)

    # 2. Volume Controls (Unmute checked BEFORE Mute to prevent substring collision)
    unmute_phrases = [
        "unmute", "unmute sound", "unmute audio", "restore sound",
        "restore audio", "sound on", "turn sound back on", "turn on sound",
        "turn on audio", "bring sound back", "turn audio back on",
    ]
    if any(p in s for p in unmute_phrases) or s == "unmute":
        return IntentResult(True, "command", "unmute", lambda: unmute())

    mute_phrases = [
        "silence", "shut up", "be quiet", "shut down the sound",
        "turn off the sound", "turn off sound", "turn off audio",
        "kill sound", "kill the sound", "mute sound", "mute audio",
        "silence audio", "mute the computer", "mute pc",
    ]
    if any(p in s for p in mute_phrases) or re.search(r"\bmute\b", s):
        return IntentResult(True, "command", "mute", lambda: mute())

    m_vol = re.search(r"(?:set|put|turn|change)?\s*(?:the\s+)?volume\s*(?:to|at)?\s*(\d+)(?:\s*(?:percent|%))?", s)
    if m_vol:
        pct = int(m_vol.group(1))
        return IntentResult(True, "command", "set_volume", lambda: set_volume(pct))

    vol_up_phrases = [
        "volume up", "increase volume", "raise volume", "boost volume",
        "turn up volume", "turn up the volume", "turn up sound", "turn up the sound",
        "sound up", "raise sound", "raise the sound", "louder", "make it louder",
        "make the sound louder", "make audio louder", "a bit louder", "pump up the volume",
        "can't hear", "can't hear anything", "audio is too low", "sound is too low",
        "too quiet", "speak louder", "higher volume",
    ]
    if any(p in s for p in vol_up_phrases) or s in ["louder", "up"]:
        return IntentResult(True, "command", "volume_up", lambda: change_volume(settings.volume_step))

    vol_down_phrases = [
        "volume down", "decrease volume", "lower volume", "reduce volume",
        "turn down volume", "turn down the volume", "turn down sound", "turn down the sound",
        "sound down", "lower sound", "lower the sound", "quieter", "make it quieter",
        "make the sound quieter", "make audio quieter", "a bit quieter", "too loud",
        "sound is too loud", "audio is too high", "lower the audio", "lower the sound",
    ]
    if any(p in s for p in vol_down_phrases) or s in ["quieter", "down"]:
        return IntentResult(True, "command", "volume_down", lambda: change_volume(-settings.volume_step))

    if any(p in s for p in ["maximum volume", "max volume", "full volume", "100% volume"]):
        return IntentResult(True, "command", "max_volume", lambda: max_volume())

    if any(p in s for p in ["minimum volume", "min volume", "lowest volume", "zero volume"]):
        return IntentResult(True, "command", "min_volume", lambda: min_volume())

    # 3. Media Controls
    if any(p in s for p in [
        "play pause", "pause media", "pause music", "pause video",
        "play media", "play music", "play video", "resume music",
        "resume video", "resume playback", "stop music", "stop video",
        "stop playing", "start playing", "pause playback", "resume",
    ]) or s in ["play", "pause"]:
        return IntentResult(True, "command", "play_pause", lambda: play_pause())

    if any(p in s for p in [
        "next song", "next track", "skip song", "skip track",
        "next video", "skip this song", "skip this video", "skip this",
    ]) or s == "next":
        return IntentResult(True, "command", "next_track", lambda: next_track())

    if any(p in s for p in [
        "previous song", "previous track", "prev track", "prev song",
        "last song", "last track", "previous video", "go back a track", "go back a song",
    ]):
        return IntentResult(True, "command", "prev_track", lambda: prev_track())

    if any(p in s for p in ["skip forward", "fast forward", "forward", "go forward"]):
        return IntentResult(True, "command", "forward_seconds", lambda: forward_seconds())

    if any(p in s for p in ["rewind", "skip back", "go back", "rewind a bit"]):
        return IntentResult(True, "command", "rewind_seconds", lambda: rewind_seconds())

    # 4. Tab & Window Controls
    if any(p in s for p in [
        "new tab", "open a tab", "open tab", "open new tab", "open a new tab",
        "create a tab", "create new tab", "another tab",
    ]):
        return IntentResult(True, "command", "new_tab", lambda: new_tab())

    if any(p in s for p in [
        "close tab", "close this tab", "shut tab", "shut this tab",
        "kill tab", "kill this tab", "close current tab",
        "close page", "close this page", "exit tab",
    ]):
        return IntentResult(True, "command", "close_tab", lambda: close_tab())

    if any(p in s for p in [
        "reopen tab", "restore tab", "undo close tab",
        "reopen closed tab", "open closed tab",
    ]):
        return IntentResult(True, "command", "reopen_tab", lambda: reopen_tab())

    if any(p in s for p in [
        "minimize window", "minimize this window", "minimize this",
        "hide window", "hide this window", "minimize",
    ]):
        return IntentResult(True, "command", "minimize_window", lambda: minimize_window())

    if any(p in s for p in [
        "maximize window", "maximize this window", "maximize this",
        "fullscreen", "full screen", "maximize",
    ]):
        return IntentResult(True, "command", "maximize_window", lambda: maximize_window())

    if any(p in s for p in [
        "switch window", "next window", "switch app",
        "next app", "change window", "alt tab",
    ]):
        return IntentResult(True, "command", "switch_window", lambda: switch_window())

    if any(p in s for p in [
        "show desktop", "go to desktop", "minimize all",
        "minimize everything", "show the desktop",
    ]):
        return IntentResult(True, "command", "show_desktop", lambda: show_desktop())

    if any(p in s for p in [
        "close window", "close the window", "close this window", "close active window",
        "close current window", "close the current window",
        "close application", "close this application", "close the application",
        "close opened application", "close open application", "close the opened app",
        "close opened app", "close this app", "close the app", "close app",
        "exit this app", "quit this app", "exit app", "quit app",
    ]):
        return IntentResult(True, "command", "close_window", lambda: close_window())

    # 5. Display & Workstation
    if any(p in s for p in [
        "lock pc", "lock computer", "lock screen",
        "lock workstation", "lock the screen", "lock the pc",
    ]):
        return IntentResult(True, "command", "lock_screen", lambda: lock_screen())

    if any(p in s for p in [
        "take screenshot", "take a screenshot", "screenshot", "capture screen",
        "capture the screen", "snap screen", "take a snap of my screen",
        "snap my screen", "print screen",
    ]):
        return IntentResult(True, "command", "screenshot", lambda: take_screenshot())

    m_bright = re.search(r"(?:set\s+)?brightness\s*(?:to|at)?\s*(\d+)", s)
    if m_bright:
        pct = int(m_bright.group(1))
        return IntentResult(True, "command", "set_brightness", lambda: set_brightness(pct))

    if any(p in s for p in [
        "brightness up", "increase brightness", "raise brightness", "more brightness",
        "brighter", "make it brighter", "make screen brighter", "screen is too dark",
    ]):
        return IntentResult(True, "command", "brightness_up", lambda: change_brightness(settings.brightness_step))

    if any(p in s for p in [
        "brightness down", "decrease brightness", "lower brightness", "dimmer",
        "make it dimmer", "make screen dimmer", "screen is too bright", "dim the screen", "dim screen",
    ]):
        return IntentResult(True, "command", "brightness_down", lambda: change_brightness(-settings.brightness_step))

    # 6. Web Searches (Guarded against intercepting questions)
    m_yt = re.search(r"(?:search youtube for|look up on youtube|play on youtube|find on youtube|listen to on youtube|youtube)\s+(.+)", s)
    if not m_yt and "youtube" in s:
        m_yt_end = re.search(r"^(?:search for|search|play|find|look up|listen to)\s+(.+?)(?:\s+(?:on|in)?\s*youtube)\s*$", s)
        if m_yt_end:
            m_yt = m_yt_end
    if m_yt:
        q = m_yt.group(1).strip()
        return IntentResult(True, "command", "search_youtube", lambda: search_web(q, engine="youtube"))

    m_search = re.search(r"^(?:search google for|search the web for|search for|google|look up)\s+(.+)", s)
    if m_search:
        q = m_search.group(1).strip()
        if q not in ("chrome", "google chrome"):
            # Check if this query is an informational question: if so, DO NOT trap as web search!
            is_q, _ = is_informational_question(q)
            if not is_q:
                return IntentResult(True, "command", "search_google", lambda: search_web(q, engine="google"))


    # 7. Open Apps (Supports natural variations like "open up chrome for me", "open the calculator app")
    m_open = re.search(r"^(?:open|launch|start|run|pull up|bring up)\s+(.+)", s)
    if m_open:
        app_candidate = m_open.group(1).strip()
        # Avoid trapping question queries like "open what" or tabs
        # Guard against question queries ("open what...") and tab/window references.
        # NOTE: match on word boundaries -- a plain startswith() blocked "whatsapp",
        # because "whatsapp".startswith("what") is True.
        if not re.match(r"^(?:what|why|when|how|who)\b", app_candidate) and \
           not re.match(r"^(?:tabs?|windows?)\b", app_candidate):
            return IntentResult(True, "command", "open_app", lambda: open_app(app_candidate))

    # 8. Close Apps (Supports "close the chrome application", "close calculator", "quit notepad")
    m_close = re.search(r"^(?:close|quit|kill|exit|shut down)\s+(.+)", s)
    if m_close:
        app_candidate = m_close.group(1).strip()
        if not any(w in app_candidate for w in ["tab", "page", "window"]):
            return IntentResult(True, "command", "close_app", lambda: close_app_by_name(app_candidate))

    # No deterministic rule matched
    return IntentResult(
        matched=False,
        category="unknown",
        action_name="none",
        payload=s,
    )


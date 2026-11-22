from __future__ import annotations
import time

try:
    import keyboard
    _KEYBOARD_AVAILABLE = True
except ImportError:
    _KEYBOARD_AVAILABLE = False


def play_pause() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("play/pause media")
        return "Toggled media playback."
    return "Media control unavailable: keyboard library missing."


def next_track() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("next track")
        return "Skipped to next track."
    return "Media control unavailable."


def prev_track() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("previous track")
        return "Went to previous track."
    return "Media control unavailable."


def forward_seconds(seconds: int = 5) -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("right")
        return f"Skipped forward."
    return "Media control unavailable."


def rewind_seconds(seconds: int = 5) -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("left")
        return f"Rewound."
    return "Media control unavailable."

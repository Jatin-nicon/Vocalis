from __future__ import annotations
import time

try:
    import keyboard
    _KEYBOARD_AVAILABLE = True
except ImportError:
    _KEYBOARD_AVAILABLE = False


def close_tab() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("ctrl+w")
        return "Closed active tab."
    return "Window control unavailable."


def new_tab() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("ctrl+t")
        return "Opened new tab."
    return "Window control unavailable."


def reopen_tab() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("ctrl+shift+t")
        return "Reopened last closed tab."
    return "Window control unavailable."


def minimize_window() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("windows+down")
        return "Minimized window."
    return "Window control unavailable."


def maximize_window() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("windows+up")
        return "Maximized window."
    return "Window control unavailable."


def switch_window() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("alt+tab")
        return "Switched window."
    return "Window control unavailable."


def close_window() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("alt+f4")
        return "Closed active window."
    return "Window control unavailable."


def show_desktop() -> str:
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("windows+d")
        return "Toggled desktop view."
    return "Window control unavailable."

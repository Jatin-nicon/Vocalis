from __future__ import annotations
import threading
import time
from .text_cleaner import clean_text

try:
    import keyboard
    _KEYBOARD_AVAILABLE = True
except ImportError:
    _KEYBOARD_AVAILABLE = False

try:
    import pyperclip
    _PYPERCLIP_AVAILABLE = True
except ImportError:
    _PYPERCLIP_AVAILABLE = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    _PYAUTOGUI_AVAILABLE = True
except ImportError:
    _PYAUTOGUI_AVAILABLE = False


def paste_text(text: str, restore_clipboard: bool = True, clean: bool = True) -> str:
    """
    Pastes or types text into the currently focused window.
    Supports clean dictation formatting or raw multi-line text (e.g. answers).
    """
    text_content = clean_text(text) if clean else text.strip()
    if not text_content:
        return "Nothing to paste."

    # Append a trailing space if clean dictation sentence so subsequent sentences flow
    text_to_insert = (text_content + " ") if clean else text_content

    # 1. Primary method: Clipboard copy + Ctrl+V
    if _PYPERCLIP_AVAILABLE:
        old_clip = ""
        try:
            old_clip = pyperclip.paste()
        except Exception:
            pass

        try:
            pyperclip.copy(text_to_insert)
            time.sleep(0.06)
            if _KEYBOARD_AVAILABLE:
                keyboard.send("ctrl+v")
            elif _PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey("ctrl", "v")

            if restore_clipboard and old_clip:
                def _restore():
                    time.sleep(0.7)
                    try:
                        pyperclip.copy(old_clip)
                    except Exception:
                        pass
                threading.Thread(target=_restore, daemon=True).start()

            preview = text_content[:40] + "..." if len(text_content) > 40 else text_content
            return f"Typed: \"{preview}\""
        except Exception:
            pass

    # 2. Fallback method: Direct keyboard writing
    if _KEYBOARD_AVAILABLE:
        try:
            keyboard.write(text_to_insert)
            preview = text_content[:40] + "..." if len(text_content) > 40 else text_content
            return f"Typed: \"{preview}\""
        except Exception as e:
            return f"Typing failed: {e}"

    # 3. Fallback method: PyAutoGUI
    if _PYAUTOGUI_AVAILABLE:
        try:
            pyautogui.write(text_to_insert)
            preview = text_content[:40] + "..." if len(text_content) > 40 else text_content
            return f"Typed: \"{preview}\""
        except Exception as e:
            return f"Typing failed: {e}"

    return "Typing unavailable: neither keyboard nor pyautogui available."


def press_backspace(count: int = 1) -> str:
    """Sends Backspace key N times to delete characters."""
    count = max(1, min(count, 100))
    try:
        if _KEYBOARD_AVAILABLE:
            for _ in range(count):
                keyboard.send("backspace")
                if count > 1:
                    time.sleep(0.015)
        elif _PYAUTOGUI_AVAILABLE:
            pyautogui.press("backspace", presses=count, interval=0.015)
        return f"Backspaced {count} time{'s' if count > 1 else ''}."
    except Exception as e:
        return f"Backspace failed: {e}"


def delete_word(count: int = 1) -> str:
    """Deletes previous word(s) using Ctrl + Backspace."""
    count = max(1, min(count, 50))
    try:
        if _KEYBOARD_AVAILABLE:
            for _ in range(count):
                keyboard.send("ctrl+backspace")
                if count > 1:
                    time.sleep(0.03)
        elif _PYAUTOGUI_AVAILABLE:
            for _ in range(count):
                pyautogui.hotkey("ctrl", "backspace")
                if count > 1:
                    time.sleep(0.03)
        return f"Deleted {count} word{'s' if count > 1 else ''}."
    except Exception as e:
        return f"Delete word failed: {e}"


def delete_sentence_or_line() -> str:
    """
    Deletes the current sentence or line in the active window.
    Selects from cursor to beginning of line (Shift+Home) and backspaces.
    """
    try:
        if _KEYBOARD_AVAILABLE:
            keyboard.send("shift+home")
            time.sleep(0.04)
            keyboard.send("backspace")
        elif _PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey("shift", "home")
            time.sleep(0.04)
            pyautogui.press("backspace")
        return "Deleted sentence."
    except Exception as e:
        return f"Delete sentence failed: {e}"


def delete_all() -> str:
    """Selects all text and deletes it (Ctrl + A, Backspace)."""
    try:
        if _KEYBOARD_AVAILABLE:
            keyboard.send("ctrl+a")
            time.sleep(0.04)
            keyboard.send("backspace")
        elif _PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.04)
            pyautogui.press("backspace")
        return "Cleared all text."
    except Exception as e:
        return f"Clear text failed: {e}"


def undo_last() -> str:
    """Sends Ctrl + Z to undo the last typing action."""
    try:
        if _KEYBOARD_AVAILABLE:
            keyboard.send("ctrl+z")
        elif _PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey("ctrl", "z")
        return "Undid last text."
    except Exception as e:
        return f"Undo failed: {e}"


def insert_new_line() -> str:
    """Sends Enter key to insert a new line."""
    try:
        if _KEYBOARD_AVAILABLE:
            keyboard.send("enter")
        elif _PYAUTOGUI_AVAILABLE:
            pyautogui.press("enter")
        return "New line."
    except Exception as e:
        return f"New line failed: {e}"

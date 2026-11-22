from __future__ import annotations
import ctypes
import os
import time
from datetime import datetime
from pathlib import Path

try:
    import screen_brightness_control as sbc
    _SBC_AVAILABLE = True
except ImportError:
    _SBC_AVAILABLE = False

try:
    import pyautogui
    _PYAUTOGUI_AVAILABLE = True
except ImportError:
    _PYAUTOGUI_AVAILABLE = False


def lock_screen() -> str:
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked."
    except Exception as e:
        return f"Failed to lock screen: {e}"


def get_brightness() -> int | None:
    if not _SBC_AVAILABLE:
        return None
    try:
        current = sbc.get_brightness()
        if isinstance(current, list):
            return int(current[0])
        return int(current)
    except Exception:
        return None


def set_brightness(percent: int) -> str:
    if not _SBC_AVAILABLE:
        return "Brightness control unavailable: screen-brightness-control package not installed."
    try:
        target = max(0, min(100, percent))
        sbc.set_brightness(target)
        return f"Brightness set to {target}%."
    except Exception as e:
        return f"Failed to set brightness: {e}"


def change_brightness(delta: int) -> str:
    if not _SBC_AVAILABLE:
        return "Brightness control unavailable: screen-brightness-control package not installed."
    try:
        current = get_brightness()
        if current is not None:
            return set_brightness(current + delta)
        sbc.set_brightness(f"{'+' if delta > 0 else ''}{delta}")
        return f"Brightness adjusted by {delta}%."
    except Exception as e:
        return f"Failed to change brightness: {e}"


def take_screenshot(destination_folder: Path | None = None) -> str:
    if destination_folder is None:
        desktop = Path(os.path.expanduser("~/Desktop"))
        destination_folder = desktop if desktop.exists() else Path.cwd()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = destination_folder / f"screenshot_{timestamp}.png"

    # Try PIL ImageGrab directly
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        screenshot.save(filename)
        return f"Screenshot saved to {filename.name}."
    except Exception:
        pass

    # Try PyAutoGUI if available
    if _PYAUTOGUI_AVAILABLE:
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            return f"Screenshot saved to {filename.name}."
        except Exception:
            pass

    # Fallback to Windows native Snipping Tool
    try:
        os.startfile("ms-screenclip:")
        return "Opened Snipping Tool to take screenshot."
    except Exception as e:
        return f"Failed to take screenshot: {e}"


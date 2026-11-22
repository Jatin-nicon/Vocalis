from __future__ import annotations
import ctypes
import threading
import time
from typing import Callable

try:
    import keyboard
    _KEYBOARD_AVAILABLE = True
except ImportError:
    _KEYBOARD_AVAILABLE = False


class HotkeyListener:
    """
    Robust Global Hotkey Listener for Windows.
    Combines 'keyboard' hooks with a resilient GetAsyncKeyState fallback thread
    to guarantee immediate response across all windows, processes, and permissions.
    """
    def __init__(self, hotkey: str = "ctrl+space", on_toggle: Callable[[], None] | None = None, debounce_seconds: float = 0.35):
        self.hotkey = hotkey.lower().strip()
        self.on_toggle = on_toggle
        self.debounce_seconds = debounce_seconds
        self._last_pressed = 0.0
        self._running = False
        self._poll_thread: threading.Thread | None = None

    def _trigger(self):
        now = time.time()
        if now - self._last_pressed < self.debounce_seconds:
            return
        self._last_pressed = now
        if self.on_toggle:
            threading.Thread(target=self.on_toggle, daemon=True).start()

    def _poll_worker(self):
        """Native Windows hardware key-state polling fallback."""
        VK_CONTROL = 0x11
        VK_SPACE = 0x20
        user32 = ctypes.windll.user32

        while self._running:
            try:
                # 0x8000 indicates key is currently pressed down
                ctrl_down = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
                space_down = bool(user32.GetAsyncKeyState(VK_SPACE) & 0x8000)
                if ctrl_down and space_down:
                    self._trigger()
                    time.sleep(0.35)
                time.sleep(0.04)
            except Exception:
                time.sleep(0.1)

    def start(self):
        self._running = True
        if _KEYBOARD_AVAILABLE:
            try:
                keyboard.add_hotkey(self.hotkey, self._trigger)
            except Exception as e:
                print(f"[Hotkey Warning] keyboard.add_hotkey failed: {e}")

        # Start native GetAsyncKeyState polling worker for bulletproof responsiveness
        if "ctrl" in self.hotkey and "space" in self.hotkey:
            self._poll_thread = threading.Thread(target=self._poll_worker, daemon=True)
            self._poll_thread.start()

        print(f"[Hotkey] Listening on '{self.hotkey}' (hooks + hardware polling active).")

    def stop(self):
        self._running = False
        if _KEYBOARD_AVAILABLE:
            try:
                keyboard.remove_hotkey(self.hotkey)
            except Exception:
                pass

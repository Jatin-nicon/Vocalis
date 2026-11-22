from __future__ import annotations
import queue
import subprocess
import threading
import time
from typing import Optional

try:
    import pythoncom
    import win32com.client
    _WIN32COM_AVAILABLE = True
except ImportError:
    _WIN32COM_AVAILABLE = False

try:
    import pyttsx3
    _PYTTSX3_AVAILABLE = True
except ImportError:
    _PYTTSX3_AVAILABLE = False


class TextToSpeech:
    """
    Robust Windows Text-To-Speech engine.
    Uses native Windows SAPI5 (win32com) with pyttsx3 and PowerShell fallbacks.
    Guarantees audible, reliable voice output across all Windows threads.
    """
    def __init__(self, rate: int = 185, volume: float = 1.0, enabled: bool = True):
        self.rate = rate
        self.volume = volume
        self.enabled = enabled
        self.is_speaking = False
        self._queue: queue.Queue[str] = queue.Queue()
        self._running = True
        self._worker_thread: Optional[threading.Thread] = None

        if self.enabled:
            self._start_worker()

    def _start_worker(self):
        def _worker():
            # Try initializing native Windows SAPI5 via win32com
            sapi_engine = None
            if _WIN32COM_AVAILABLE:
                try:
                    pythoncom.CoInitialize()
                    sapi_engine = win32com.client.Dispatch("SAPI.SpVoice")
                    # Volume range: 0 - 100
                    sapi_engine.Volume = int(min(max(self.volume * 100, 0), 100))
                    # SAPI Rate range: -10 to +10 (1 is ~185 wpm)
                    sapi_engine.Rate = 1

                    # Prefer natural female voice (Zira) or default
                    voices = sapi_engine.GetVoices()
                    for i in range(voices.Count):
                        v = voices.Item(i)
                        desc = v.GetDescription().lower()
                        if any(fav in desc for fav in ["zira", "hazel", "female"]):
                            sapi_engine.Voice = v
                            break
                    print("[TTS] Native Windows SAPI5 voice engine active.")
                except Exception as ex:
                    print(f"[TTS Warning] SAPI5 COM init error: {ex}")
                    sapi_engine = None

            # Fallback pyttsx3 engine
            pyttsx_engine = None
            if sapi_engine is None and _PYTTSX3_AVAILABLE:
                try:
                    pyttsx_engine = pyttsx3.init()
                    pyttsx_engine.setProperty("rate", self.rate)
                    pyttsx_engine.setProperty("volume", self.volume)
                    print("[TTS] pyttsx3 fallback voice engine active.")
                except Exception as ex:
                    print(f"[TTS Warning] pyttsx3 init error: {ex}")
                    pyttsx_engine = None

            while self._running:
                try:
                    text = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if text == "__STOP__":
                    break

                self.is_speaking = True
                try:
                    if sapi_engine:
                        # Synchronous within worker thread
                        sapi_engine.Speak(text, 0)
                    elif pyttsx_engine:
                        pyttsx_engine.say(text)
                        pyttsx_engine.runAndWait()
                    else:
                        # PowerShell System.Speech ultimate fallback
                        safe_text = text.replace("'", "''").replace('"', '`"')
                        cmd = (
                            f'Add-Type -AssemblyName System.Speech; '
                            f'$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                            f'$s.Speak("{safe_text}")'
                        )
                        subprocess.run(
                            ["powershell", "-NoProfile", "-Command", cmd],
                            capture_output=True,
                            timeout=15,
                        )
                except Exception as err:
                    print(f"[TTS Speak Error] {err}")
                finally:
                    self.is_speaking = False
                    self._queue.task_done()

            if _WIN32COM_AVAILABLE:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

        self._worker_thread = threading.Thread(target=_worker, daemon=True)
        self._worker_thread.start()

    def speak(self, text: str, wait: bool = False):
        """
        Speaks the given text.
        If wait=True, blocks until speech is finished before returning.
        """
        cleaned = text.strip()
        if not self.enabled or not cleaned:
            return

        self._queue.put(cleaned)
        if wait:
            # Wait until queue drains and current speech completes
            time.sleep(0.05)
            while not self._queue.empty() or self.is_speaking:
                time.sleep(0.05)

    def wait_until_done(self, timeout: float = 10.0):
        start = time.time()
        while (not self._queue.empty() or self.is_speaking) and (time.time() - start < timeout):
            time.sleep(0.05)

    def stop(self):
        self._running = False
        self._queue.put("__STOP__")

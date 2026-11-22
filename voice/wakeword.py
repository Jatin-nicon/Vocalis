from __future__ import annotations
import queue
import sys
import threading
import time
from typing import Callable, Optional
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import openwakeword
    from openwakeword.model import Model as OWWModel
    _OWW_AVAILABLE = True
except ImportError:
    _OWW_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    _WHISPER_AVAILABLE = True
except ImportError:
    _WHISPER_AVAILABLE = False

try:
    import sounddevice as sd
    _SD_AVAILABLE = True
except ImportError:
    _SD_AVAILABLE = False


class WakeWordDetector:
    """
    High-accuracy, low-latency Hybrid Wake Word Detector.
    Supports "Hey Jarvis":
      1. OpenWakeWord ONNX acoustic model (instant 0ms trigger for "Hey Jarvis").
      2. Fast VAD + local tiny.en Whisper keyword spotter for "Hey Jarvis" (~300ms trigger).
    """
    def __init__(
        self,
        wake_word: str = "hey_jarvis",
        threshold: float = 0.45,
        speech_threshold: float = 0.012,
        on_wake_detected: Callable[[Optional[str]], None] | None = None,
        enabled: bool = True,
    ):
        self.wake_word = wake_word.lower().strip()
        self.threshold = threshold
        self.speech_threshold = speech_threshold
        self.on_wake_detected = on_wake_detected
        self.enabled = enabled and _SD_AVAILABLE

        self._oww_model: Optional[OWWModel] = None
        self._whisper_model: Optional[WhisperModel] = None
        self._running = False
        self._paused = False
        self._listen_thread: Optional[threading.Thread] = None
        self._verifier_thread: Optional[threading.Thread] = None
        self._verifier_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._last_wake_time = 0.0

        # Voice Activity Detection state for the streaming audio
        self._speech_buffer: list[np.ndarray] = []
        self._is_speech_burst = False
        self._last_speech_time = 0.0

    def _ensure_models_loaded(self):
        if not self.enabled:
            return

        # 1. Fast Whisper tiny.en for "Hey Jarvis" keyword spotting
        if self._whisper_model is None and _WHISPER_AVAILABLE:
            try:
                self._whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
                print("[WakeWord] Fast 'Hey Jarvis' acoustic verifier ready (tiny.en).")
            except Exception as e:
                print(f"[WakeWord Warning] Failed to initialize tiny.en verifier: {e}")

        # 2. openWakeWord for "Hey Jarvis"
        if self._oww_model is None and _OWW_AVAILABLE:
            try:
                openwakeword.utils.download_models()
                self._oww_model = OWWModel(
                    wakeword_models=["hey_jarvis"],
                    inference_framework="onnx",
                )
                print("[WakeWord] 'Hey Jarvis' detector ready (local ONNX).")
            except Exception as e:
                print(f"[WakeWord Warning] Failed to initialize openWakeWord: {e}")

    def start(self):
        if not self.enabled:
            return
        self._ensure_models_loaded()
        if not self.enabled:
            return

        self._running = True
        self._paused = False

        # Start verification worker thread
        self._verifier_thread = threading.Thread(target=self._verifier_loop, daemon=True)
        self._verifier_thread.start()

        # Start background microphone streaming thread
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()

        print("[WakeWord] Listening for \"Hey Jarvis\" in the background...")

    def pause(self):
        self._paused = True
        self._is_speech_burst = False
        self._speech_buffer.clear()
        while not self._verifier_queue.empty():
            try:
                self._verifier_queue.get_nowait()
            except Exception:
                break

    def resume(self):
        time.sleep(0.3)
        self._is_speech_burst = False
        self._speech_buffer.clear()
        while not self._verifier_queue.empty():
            try:
                self._verifier_queue.get_nowait()
            except Exception:
                break
        if self._oww_model:
            try:
                self._oww_model.reset()
            except Exception:
                pass
        self._paused = False

    def _trigger_wake(self, detected_phrase: Optional[str] = None):
        now = time.time()
        if now - self._last_wake_time < 1.8:
            return
        self._last_wake_time = now
        self.pause()
        if self.on_wake_detected:
            threading.Thread(target=self.on_wake_detected, args=(detected_phrase,), daemon=True).start()

    def _verifier_loop(self):
        """Processes buffered speech bursts and detects 'Hey Jarvis' with tiny.en in ~300ms."""
        target_keywords = {
            "jarvis", "hey jarvis",
            "jervis", "hey jervis", "jarviss", "hey jarviss"
        }

        while self._running:
            try:
                segment = self._verifier_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if self._paused or not self._running or self._whisper_model is None:
                continue

            # Peak normalize
            max_peak = float(np.max(np.abs(segment)))
            if max_peak > 0.01:
                segment = (segment / max_peak) * 0.95

            try:
                segs, _ = self._whisper_model.transcribe(
                    segment,
                    language="en",
                    beam_size=1,
                    temperature=0.0,
                    initial_prompt="Hey Jarvis, Jarvis",
                )
                text = " ".join(s.text for s in segs).strip().lower()
                if not text:
                    continue

                clean = "".join(c for c in text if c.isalnum() or c.isspace()).strip()
                if any(kw in clean for kw in target_keywords):
                    self._trigger_wake(text)
                    try:
                        print(f"\n⚡ [WakeWord Detected] Heard \"{text}\"")
                    except Exception:
                        print(f"\n[WakeWord Detected] Heard \"{text}\"")
            except Exception as e:
                print(f"[Verifier Transcribe Error] {e}")

    def feed_chunk(self, chunk_int16: np.ndarray):
        if not self._running or self._paused:
            return

        now = time.time()
        chunk_1d = np.ascontiguousarray(chunk_int16.flatten(), dtype=np.int16)

        # 1. Fast OpenWakeWord check ("Hey Jarvis")
        if self._oww_model is not None:
            try:
                prediction = self._oww_model.predict(chunk_1d)
                score = prediction.get("hey_jarvis", 0.0)
                if score >= self.threshold:
                    self._trigger_wake(None)
                    try:
                        print(f"\n⚡ [WakeWord Detected] Heard \"Hey Jarvis\" (confidence: {score:.2f})")
                    except Exception:
                        print(f"\n[WakeWord Detected] Heard \"Hey Jarvis\" (confidence: {score:.2f})")
                    return
            except Exception:
                pass

        # 2. Fast Voice Activity & Keyword Buffering for "Hey Jarvis"
        chunk_float = chunk_1d.astype(np.float32) / 32768.0
        amp = float(np.max(np.abs(chunk_float)))

        if amp >= self.speech_threshold:
            self._speech_buffer.append(chunk_float)
            self._is_speech_burst = True
            self._last_speech_time = now
        else:
            if self._is_speech_burst:
                # If 300ms of silence follows speech, package and queue speech burst
                if (now - self._last_speech_time) >= 0.30:
                    total_samples = sum(len(c) for c in self._speech_buffer)
                    # Between 0.35s and 4.0s
                    if 5600 <= total_samples <= 64000:
                        segment = np.ascontiguousarray(np.concatenate(self._speech_buffer).flatten(), dtype=np.float32)
                        self._verifier_queue.put(segment)
                    self._is_speech_burst = False
                    self._speech_buffer.clear()
                elif len(self._speech_buffer) * 1280 > 64000:
                    segment = np.ascontiguousarray(np.concatenate(self._speech_buffer).flatten(), dtype=np.float32)
                    self._verifier_queue.put(segment)
                    self._is_speech_burst = False
                    self._speech_buffer.clear()

    def _listen_loop(self):
        sample_rate = 16000
        block_size = 1280  # 80ms chunks

        def _audio_callback(indata, frames, time_info, status):
            chunk_int16 = np.frombuffer(indata, dtype=np.int16)
            self.feed_chunk(chunk_int16)

        try:
            with sd.RawInputStream(
                samplerate=sample_rate,
                blocksize=block_size,
                dtype="int16",
                channels=1,
                callback=_audio_callback,
            ):
                while self._running:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[WakeWord Error] Microphone stream interrupted: {e}")

    def stop(self):
        self._running = False
        self._paused = True

from __future__ import annotations
import queue
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable

try:
    import numpy as np
    import sounddevice as sd
    import soundfile as sf
    _AUDIO_LIBS_AVAILABLE = True
except ImportError:
    _AUDIO_LIBS_AVAILABLE = False

TEMP_WAV = Path(tempfile.gettempdir()) / "voice_pc_assistant_buffer.wav"


class AudioRecorder:
    """
    Audio recorder with real-time amplitude monitoring and dynamic
    silence detection (VAD). Allows speaking continuously until silence is detected.
    """
    def __init__(
        self,
        sample_rate: int = 16000,
        speech_threshold: float = 0.012,
        on_amplitude_callback: Callable[[float], None] | None = None,
    ):
        self.sample_rate = sample_rate
        self.channels = 1
        self.speech_threshold = speech_threshold
        self.is_recording = False
        self.audio_frames: list[np.ndarray] = []
        self.audio_queue: queue.Queue = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.on_amplitude_callback = on_amplitude_callback

        # Speech activity tracking
        self.has_speech_started = False
        self.last_speech_time = 0.0
        self.record_start_time = 0.0

    def _audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
            self.audio_queue.put(indata.copy())
            try:
                amp = float(np.max(np.abs(indata)))
                if amp >= self.speech_threshold:
                    self.has_speech_started = True
                    self.last_speech_time = time.time()
                if self.on_amplitude_callback:
                    self.on_amplitude_callback(amp)
            except Exception:
                pass

    def start(self):
        if not _AUDIO_LIBS_AVAILABLE:
            raise RuntimeError("Audio libraries (sounddevice, soundfile, numpy) not installed.")

        self.audio_frames.clear()
        while not self.audio_queue.empty():
            self.audio_queue.get()

        self.is_recording = True
        self.has_speech_started = False
        self.record_start_time = time.time()
        self.last_speech_time = self.record_start_time

        def _recorder_worker():
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=self._audio_callback,
            ):
                while self.is_recording:
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        self.audio_frames.append(data)
                    except queue.Empty:
                        continue

        self.worker_thread = threading.Thread(target=_recorder_worker, daemon=True)
        self.worker_thread.start()

    def has_captured_speech(self, min_peak: float = 0.008) -> bool:
        """Returns True if any captured audio frame had noticeable speech/energy above ambient."""
        if not self.audio_frames:
            return False
        for frame in self.audio_frames:
            if float(np.max(np.abs(frame))) >= min_peak:
                return True
        return False

    def wait_until_silence(
        self,
        silence_duration: float = 1.6,
        max_duration: float = 90.0,
        initial_timeout: float = 5.0,
    ) -> bool:
        """
        Blocks until speech finishes and subsequent silence is detected,
        or until initial/max timeouts expire. Returns True if speech occurred.
        """
        while self.is_recording:
            time.sleep(0.08)
            now = time.time()

            # 1. Check if user hasn't started talking yet
            if not self.has_speech_started:
                if (now - self.record_start_time) > initial_timeout:
                    # Fallback: check if quiet speech was captured in frames before giving up
                    if self.has_captured_speech(min_peak=0.008):
                        self.has_speech_started = True
                        return True
                    return False

            # 2. If user started talking, wait until they pause/stop
            if self.has_speech_started:
                if (now - self.last_speech_time) >= silence_duration:
                    return True

            # 3. Safety upper limit
            if (now - self.record_start_time) >= max_duration:
                return self.has_speech_started

        return self.has_speech_started

    def stop(self) -> Path | None:
        self.is_recording = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)

        # Drain remaining frames from queue
        while not self.audio_queue.empty():
            self.audio_frames.append(self.audio_queue.get())

        if not self.audio_frames:
            return None

        audio_data = np.concatenate(self.audio_frames, axis=0)
        # Peak normalize audio so Whisper receives consistent, clean volume levels
        max_peak = float(np.max(np.abs(audio_data))) if len(audio_data) > 0 else 0.0
        if max_peak > 0.01:
            audio_data = (audio_data / max_peak) * 0.95

        sf.write(str(TEMP_WAV), audio_data, self.sample_rate)
        return TEMP_WAV

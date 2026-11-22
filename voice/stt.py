from __future__ import annotations
from pathlib import Path
from typing import Optional

try:
    from faster_whisper import WhisperModel
    _WHISPER_AVAILABLE = True
except ImportError:
    _WHISPER_AVAILABLE = False

ASSISTANT_INITIAL_PROMPT = (
    "Jester, Windows desktop voice assistant. "
    "Commands: volume up, volume down, set volume, mute, unmute, "
    "play, pause, next track, previous track, close tab, new tab, "
    "minimize window, maximize window, open notepad, open chrome, "
    "search youtube for, search google for, lock screen, take screenshot, "
    "what time is it, tell me the time, what is the date, battery status, "
    "cpu usage, start typing, stop typing, type, dictate."
)


class SpeechToText:
    """
    High-accuracy local speech-to-text powered by faster-whisper.
    Uses English-optimized checkpoints (small.en) with initial prompt priming,
    zero repetition conditioning, and optimized VAD filtering.
    """
    def __init__(
        self,
        model_size: str = "small.en",
        compute_type: str = "int8",
        language: str = "en",
    ):
        self.model_size = model_size
        self.compute_type = compute_type
        self.language = language
        self._model: Optional[WhisperModel] = None

    def _ensure_model_loaded(self):
        if self._model is None:
            if not _WHISPER_AVAILABLE:
                raise RuntimeError("faster-whisper is not installed. Install with: pip install faster-whisper")
            print(f"[STT] Loading faster-whisper ({self.model_size}, {self.compute_type})...")
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type=self.compute_type,
            )
            print(f"[STT] faster-whisper model '{self.model_size}' ready.")

    def transcribe(self, audio_path: Path | str) -> str:
        self._ensure_model_loaded()
        path = str(audio_path)
        segments, _ = self._model.transcribe(
            path,
            language=self.language,
            beam_size=5,
            best_of=5,
            temperature=0.0,
            condition_on_previous_text=False,
            initial_prompt=ASSISTANT_INITIAL_PROMPT,
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.35,
                min_speech_duration_ms=150,
                min_silence_duration_ms=250,
                speech_pad_ms=200,
            ),
        )
        text = " ".join([seg.text for seg in segments]).strip()
        return text

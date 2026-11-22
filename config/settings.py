from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = CONFIG_DIR / "default_settings.json"
USER_SETTINGS_FILE = CONFIG_DIR / "user_settings.json"
ENV_FILE = BASE_DIR / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
except ImportError:
    pass


@dataclass
class AssistantConfig:
    assistant_name: str = "Jester"
    hotkey: str = "ctrl+space"
    wake_word_enabled: bool = True
    wake_word_model: str = "hey_jester"
    wake_word_threshold: float = 0.5
    whisper_model: str = "small.en"
    whisper_compute_type: str = "int8"
    sample_rate: int = 16000
    silence_duration: float = 1.6
    speech_threshold: float = 0.012
    auto_paste_unmatched: bool = False
    voice_feedback: bool = True
    speech_rate: int = 185
    speech_volume: float = 1.0
    volume_step: int = 5
    brightness_step: int = 10
    hud_enabled: bool = True
    groq_model: str = "llama-3.3-70b-versatile"
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))

    @classmethod
    def load(cls) -> AssistantConfig:
        config_data = {}

        if SETTINGS_FILE.exists():
            try:
                config_data.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
            except Exception as e:
                print(f"[Warning] Failed to read default_settings.json: {e}")

        if USER_SETTINGS_FILE.exists():
            try:
                config_data.update(json.loads(USER_SETTINGS_FILE.read_text(encoding="utf-8")))
            except Exception as e:
                print(f"[Warning] Failed to read user_settings.json: {e}")

        # Environment variable overrides
        if os.getenv("HOTKEY"):
            config_data["hotkey"] = os.getenv("HOTKEY")
        if os.getenv("WHISPER_MODEL"):
            config_data["whisper_model"] = os.getenv("WHISPER_MODEL")
        if os.getenv("GROQ_API_KEY"):
            config_data["groq_api_key"] = os.getenv("GROQ_API_KEY")

        return cls(**{k: v for k, v in config_data.items() if k in cls.__dataclass_fields__})


settings = AssistantConfig.load()

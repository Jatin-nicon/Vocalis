import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from voice.tts import TextToSpeech
from datetime import datetime

def main():
    print("=" * 60)
    print("🔊 Voice-PC-Assistant: Sound Output & TTS Verification Test")
    print("=" * 60)
    
    tts = TextToSpeech(enabled=True)
    now_str = datetime.now().strftime('%I:%M %p').lstrip('0')
    msg = f"Hello! The time is {now_str}. Your voice output is working properly."
    
    print(f"\n[Speaking Aloud] -> \"{msg}\"")
    tts.speak(msg, wait=True)
    print("\n[SUCCESS] Audio playback completed without errors.")

if __name__ == "__main__":
    main()

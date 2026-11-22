from __future__ import annotations
import argparse
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import subprocess
import threading
import time
from pathlib import Path

# Add project root to sys.path so modules import smoothly
PROJECT_ROOT = Path(__file__).resolve().parent

# Auto-switch to virtual environment python if not active
venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
    res = subprocess.run([str(venv_python)] + sys.argv)
    sys.exit(res.returncode)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from voice import AudioRecorder, SpeechToText, TextToSpeech, HotkeyListener, WakeWordDetector
from dictation import paste_text
from intent import IntentRouter, DispatchResult
from ui import VisualHUD


class VoicePCAssistant:
    def __init__(self):
        print("=" * 60)
        print("🎙️  Voice-PC-Assistant: Modular Windows Voice Controller")
        print("=" * 60)

        # 1. Initialize UI HUD
        self.hud = VisualHUD(enabled=settings.hud_enabled)
        if settings.hud_enabled:
            self.hud.start()
            print("[Init] Visual HUD overlay active.")

        # 2. Initialize Text-to-Speech
        self.tts = TextToSpeech(
            rate=settings.speech_rate,
            volume=settings.speech_volume,
            enabled=settings.voice_feedback,
        )

        # 3. Initialize Speech-to-Text
        self.stt = SpeechToText(
            model_size=settings.whisper_model,
            compute_type=settings.whisper_compute_type,
        )

        # 4. Initialize Intent Router & Dictation Handler
        self.router = IntentRouter(dictation_handler=paste_text)

        # 5. Initialize Audio Recorder with amplitude & silence detection
        self.recorder = AudioRecorder(
            sample_rate=settings.sample_rate,
            speech_threshold=settings.speech_threshold,
            on_amplitude_callback=self.hud.set_amplitude if settings.hud_enabled else None,
        )

        self.is_recording = False
        self.hotkey_listener = HotkeyListener(
            hotkey=settings.hotkey,
            on_toggle=self.toggle_recording,
        )

        # 6. Initialize Wake Word Detector
        self.wakeword = WakeWordDetector(
            wake_word=settings.wake_word_model,
            threshold=settings.wake_word_threshold,
            on_wake_detected=self.on_wake_word_triggered,
            enabled=settings.wake_word_enabled,
        )

    def on_wake_word_triggered(self, phrase: Optional[str] = None):
        if self.is_recording:
            return

        command_candidate = ""
        if phrase:
            cleaned = phrase.lower().strip()
            # Strip out leading wake keywords
            for kw in ["hey jester", "jester", "hey jarvis", "jarvis", "hey chester", "chester", "gesture", "tester"]:
                if cleaned.startswith(kw):
                    cleaned = cleaned[len(kw):].strip(" ,.?!")
                    break
                elif kw in cleaned:
                    idx = cleaned.find(kw)
                    cleaned = cleaned[idx + len(kw):].strip(" ,.?!")
                    break
            command_candidate = cleaned.strip(" ,.?!")

        # If user spoke command in same phrase (e.g., "Hey Jester open chrome")
        if command_candidate and len(command_candidate.split()) >= 1:
            print(f"\n⚡ [Wake Word + Command Detected] \"{phrase}\"")
            print(f"👉 Direct Command: \"{command_candidate}\"")
            self.execute_command_text(command_candidate)
            return

        # Otherwise standard wake: say "Yes?" and open listening
        print("\n⚡ [Wake Word] \"Hey Jester\" detected!")
        self.hud.set_state("listening", "Hey Jester detected")
        if settings.voice_feedback:
            self.tts.speak("Yes?", wait=True)
            time.sleep(0.15)
        self.start_listening(is_wake_word=True)

    def toggle_recording(self):
        if self.router.typing_mode:
            self.router.typing_mode = False
            self.is_recording = False
            self.recorder.stop()
            print("\n" + "=" * 60)
            print("🎙️  [COMMAND MODE RESTORED] (Hotkey Ctrl+Space)")
            print("=" * 60 + "\n")
            self.hud.set_state("idle", "Command Mode Restored")
            if settings.voice_feedback:
                self.tts.speak("Typing mode deactivated. Returned to command mode.", wait=True)
            self.wakeword.resume()
            return

        if not self.is_recording:
            self.wakeword.pause()
            self.start_listening(is_wake_word=False)
        else:
            self.stop_and_process()

    def start_listening(self, is_wake_word: bool = False):
        if self.is_recording:
            return
        self.is_recording = True

        if self.router.typing_mode:
            self.hud.set_state("typing", "Dictating... (Say 'stop typing')")
            print("\n✍️  [TYPING MODE ACTIVE] Listening to type... (Say 'stop typing' or press Ctrl+Space to exit)")
        else:
            self.hud.set_state("listening", "Listening for commands...")
            print("\n🎙️  [COMMAND MODE ACTIVE] Listening... (Speak command or question)")

        try:
            self.recorder.start()
        except Exception as err:
            print(f"[Record Error] {err}")
            self.is_recording = False
            self.hud.set_state("idle")
            self.wakeword.resume()
            return

        # Background watcher: monitors speech and triggers stop as soon as silence is detected
        def _silence_watcher():
            speech_occurred = self.recorder.wait_until_silence(
                silence_duration=settings.silence_duration,
                max_duration=90.0,
                initial_timeout=6.0,
            )
            if self.is_recording:
                if speech_occurred or self.recorder.has_captured_speech(min_peak=0.008):
                    self.stop_and_process()
                else:
                    # Initial timeout expired with no speech
                    if self.router.typing_mode:
                        print("✍️  [Typing Mode] Paused. Still listening to type...")
                        self.recorder.stop()
                        self.is_recording = False
                        time.sleep(0.1)
                        self.start_listening(is_wake_word=False)
                    else:
                        print("⚠️  No speech detected. Returning to standby.")
                        self.recorder.stop()
                        self.is_recording = False
                        self.hud.set_state("idle")
                        self.wakeword.resume()

        threading.Thread(target=_silence_watcher, daemon=True).start()

    def execute_command_text(self, text: str):
        try:
            result: DispatchResult = self.router.route_and_execute(text)
            print(f"⚡ Result [{result.category}]: {result.message}")

            if result.category == "mode":
                if result.action_name == "start_typing":
                    print("\n" + "=" * 60)
                    print("✍️  [TYPING MODE ACTIVATED]")
                    print("    Spoken speech will now auto-type directly into your focused window.")
                    print("    To return to commands: Say 'stop typing' or press Ctrl+Space.")
                    print("=" * 60 + "\n")
                    self.hud.set_state("typing", "Typing Mode Activated")
                    if settings.voice_feedback:
                        self.tts.speak(result.message, wait=True)
                    self.start_listening(is_wake_word=False)
                    return
                elif result.action_name == "stop_typing":
                    print("\n" + "=" * 60)
                    print("🎙️  [COMMAND MODE RESTORED]")
                    print("    Returned to standard command and question answering mode.")
                    print("=" * 60 + "\n")
                    self.hud.set_state("idle", "Command Mode Restored")
                    if settings.voice_feedback:
                        self.tts.speak(result.message, wait=True)
                    self.wakeword.resume()
                    return

            elif result.category == "command":
                self.hud.set_state("executed", result.message)
                if settings.voice_feedback:
                    self.hud.set_state("speaking", result.message)
                    self.tts.speak(result.message, wait=True)

            elif result.category == "answer":
                self.hud.set_state("speaking", result.message)
                if settings.voice_feedback:
                    self.tts.speak(result.message, wait=True)
                self.hud.set_state("executed", "Answered")

            elif result.category == "dictate":
                self.hud.set_state("typing_processing", "Text Pasted")
                time.sleep(0.12)
                if result.action_name == "type_last_answer" and settings.voice_feedback:
                    self.hud.set_state("speaking", result.message)
                    self.tts.speak(result.message, wait=True)

            elif result.category == "unknown":
                self.hud.set_state("idle", "Unrecognized")
                if settings.voice_feedback:
                    msg = "I didn't recognize that command. Say help to hear commands, or type to dictate."
                    self.hud.set_state("speaking", msg)
                    self.tts.speak(msg, wait=True)

            time.sleep(0.2)
            if self.router.typing_mode:
                self.start_listening(is_wake_word=False)
                return
            else:
                self.hud.set_state("idle")

        except Exception as e:
            print(f"[Error] Execution failed: {e}")
            if self.router.typing_mode:
                self.start_listening(is_wake_word=False)
            else:
                self.hud.set_state("idle")
        finally:
            if not self.router.typing_mode and not self.is_recording:
                self.wakeword.resume()

    def stop_and_process(self):
        if not self.is_recording:
            return
        self.is_recording = False

        if self.router.typing_mode:
            self.hud.set_state("typing_processing", "Transcribing dictation...")
            print("⏳ [Typing Mode] Transcribing text...")
        else:
            self.hud.set_state("processing", "Transcribing speech...")
            print("⏳ [Command Mode] Processing speech...")

        try:
            audio_path = self.recorder.stop()
            if not audio_path:
                print("⚠️  No audio captured.")
                if self.router.typing_mode:
                    self.start_listening(is_wake_word=False)
                else:
                    self.hud.set_state("idle")
                    self.wakeword.resume()
                return

            text = self.stt.transcribe(audio_path)
            print(f"🗣️  You said: \"{text}\"")

            if not text.strip():
                print("⚠️  No speech recognized.")
                if self.router.typing_mode:
                    self.start_listening(is_wake_word=False)
                else:
                    self.hud.set_state("idle")
                    self.wakeword.resume()
                return

            self.execute_command_text(text)

        except Exception as e:
            print(f"[Error] Execution failed: {e}")
            if self.router.typing_mode:
                self.start_listening(is_wake_word=False)
            else:
                self.hud.set_state("idle")
                self.wakeword.resume()

    def run_cli_mode(self):
        """Allows testing commands directly by typing without requiring microphone."""
        print("\n💬 Interactive CLI Mode (Type 'exit' to quit)")
        print("Commands: 'volume up', 'open chrome', 'start typing', 'stop typing', etc.\n")
        while True:
            try:
                prompt_label = "✍️ [TYPING MODE] Jester> " if self.router.typing_mode else "🎙️ [COMMAND MODE] Jester> "
                line = input(prompt_label).strip()
                if not line:
                    continue
                if line.lower() in ("exit", "quit", "q"):
                    break
                result = self.router.route_and_execute(line)
                print(f"⚡ [{result.category}] {result.message}")
                if (result.category in ("command", "answer", "mode", "unknown")) and settings.voice_feedback:
                    self.tts.speak(result.message, wait=True)
            except (KeyboardInterrupt, EOFError):
                break
        print("Exiting CLI mode.")

    def run(self):
        self.hotkey_listener.start()
        if settings.wake_word_enabled:
            self.wakeword.start()

        print(f"\n✅ Ready! Say \"Hey Jester\" or press '{settings.hotkey}' to give commands.")
        print("Press Ctrl+C in terminal to exit.\n")
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nShutting down Jester...")
        finally:
            self.wakeword.stop()
            self.hotkey_listener.stop()
            self.tts.stop()
            self.hud.stop()
            print("Shutdown complete.")


def main():
    parser = argparse.ArgumentParser(description="Voice-PC-Assistant: Windows Voice Controller")
    parser.add_argument("--cli", action="store_true", help="Run interactive CLI test mode without microphone")
    args = parser.parse_args()

    assistant = VoicePCAssistant()
    if args.cli:
        assistant.run_cli_mode()
    else:
        assistant.run()


if __name__ == "__main__":
    main()

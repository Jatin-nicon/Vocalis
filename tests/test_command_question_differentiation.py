from __future__ import annotations
import sys
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


from intent.router import IntentRouter, DispatchResult
from intent.classifier import is_informational_question, is_offline_system_query
from windows_controls.apps import normalize_app_name


class TestCommandQuestionDifferentiation(unittest.TestCase):
    def setUp(self):
        self.pasted_buffer = []

        def mock_dictate(text: str) -> str:
            self.pasted_buffer.append(text)
            return f"Mock pasted: {text}"

        self.router = IntentRouter(dictation_handler=mock_dictate)

    # -------------------------------------------------------------------------
    # 1. App Name Normalization Tests
    # -------------------------------------------------------------------------
    def test_app_name_normalization(self):
        self.assertEqual(normalize_app_name("up Chrome"), "chrome")
        self.assertEqual(normalize_app_name("up Chrome for me"), "chrome")
        self.assertEqual(normalize_app_name("the chrome application"), "chrome")
        self.assertEqual(normalize_app_name("the calculator app"), "calculator")
        self.assertEqual(normalize_app_name("my vscode"), "vscode")
        self.assertEqual(normalize_app_name("the notepad application"), "notepad")
        self.assertEqual(normalize_app_name("edge browser"), "edge")

    # -------------------------------------------------------------------------
    # 2. Natural Command Variations (Must execute PC tasks, NOT treated as questions)
    # -------------------------------------------------------------------------
    def test_natural_volume_commands(self):
        # Louder / Volume Up variations
        for cmd in [
            "volume up",
            "make the sound louder",
            "could you please turn up the sound a bit",
            "make it louder",
            "can't hear anything",
            "raise the volume",
            "turn up the volume please",
        ]:
            res = self.router.route_and_execute(cmd)
            self.assertEqual(res.category, "command", f"Failed for: {cmd}")
            self.assertEqual(res.action_name, "volume_up", f"Action mismatch for: {cmd}")

        # Quieter / Volume Down variations
        for cmd in [
            "volume down",
            "make the sound quieter",
            "turn down the sound a bit",
            "too loud",
            "lower the sound",
            "could you turn down the volume",
        ]:
            res = self.router.route_and_execute(cmd)
            self.assertEqual(res.category, "command", f"Failed for: {cmd}")
            self.assertEqual(res.action_name, "volume_down", f"Action mismatch for: {cmd}")

        # Mute variations (Must NOT collide with unmute!)
        for cmd in [
            "mute",
            "shut down the sound",
            "silence",
            "kill the sound",
            "mute audio",
            "shut up",
        ]:
            res = self.router.route_and_execute(cmd)
            self.assertEqual(res.category, "command", f"Failed for: {cmd}")
            self.assertEqual(res.action_name, "mute", f"Action mismatch for: {cmd}")

        # Unmute variations
        for cmd in [
            "unmute",
            "unmute audio",
            "restore sound",
            "turn sound back on",
            "turn on audio",
        ]:
            res = self.router.route_and_execute(cmd)
            self.assertEqual(res.category, "command", f"Failed for: {cmd}")
            self.assertEqual(res.action_name, "unmute", f"Action mismatch for: {cmd}")

        # Set volume
        res = self.router.route_and_execute("put volume to 65")
        self.assertEqual(res.category, "command")
        self.assertEqual(res.action_name, "set_volume")

    def test_natural_app_commands(self):
        # Open App with conversational noise words
        for cmd in [
            "could you open up Chrome for me",
            "open the calculator app",
            "launch notepad",
            "open chrome",
        ]:
            res = self.router.route_and_execute(cmd)
            self.assertEqual(res.category, "command", f"Failed for: {cmd}")
            self.assertEqual(res.action_name, "open_app", f"Action mismatch for: {cmd}")

        # Close App with conversational noise words
        for cmd in [
            "can you close the chrome application",
            "close calculator",
            "quit notepad",
        ]:
            res = self.router.route_and_execute(cmd)
            self.assertEqual(res.category, "command", f"Failed for: {cmd}")
            self.assertEqual(res.action_name, "close_app", f"Action mismatch for: {cmd}")

    def test_natural_window_and_tab_commands(self):
        for cmd, expected_act in [
            ("can you minimize this window", "minimize_window"),
            ("maximize this window please", "maximize_window"),
            ("switch to next window", "switch_window"),
            ("close this tab", "close_tab"),
            ("open a new tab", "new_tab"),
            ("show desktop", "show_desktop"),
            ("close opened application", "close_window"),
        ]:
            res = self.router.route_and_execute(cmd)
            self.assertEqual(res.category, "command", f"Failed for: {cmd}")
            self.assertEqual(res.action_name, expected_act, f"Action mismatch for: {cmd}")

    def test_natural_display_commands(self):
        for cmd, expected_act in [
            ("take a snap of my screen", "screenshot"),
            ("take a screenshot please", "screenshot"),
            ("screen is too dark make it brighter", "brightness_up"),
            ("dim the screen a bit", "brightness_down"),
            ("lock workstation", "lock_screen"),
        ]:
            res = self.router.route_and_execute(cmd)
            self.assertEqual(res.category, "command", f"Failed for: {cmd}")
            self.assertEqual(res.action_name, expected_act, f"Action mismatch for: {cmd}")

    def test_natural_text_editing_and_mode_commands(self):
        for cmd, expected_act in [
            ("delete this sentence", "delete_sentence"),
            ("delete the last 2 words", "delete_word"),
            ("backspace 3 times", "backspace"),
            ("undo that", "undo"),
            ("new line", "new_line"),
            ("start typing", "start_typing"),
            ("stop typing", "stop_typing"),
        ]:
            res = self.router.route_and_execute(cmd)
            self.assertIn(res.category, ["command", "mode"], f"Failed for: {cmd}")
            self.assertEqual(res.action_name, expected_act, f"Action mismatch for: {cmd}")

    # -------------------------------------------------------------------------
    # 3. Offline System Inquiries (Instant Local Answers)
    # -------------------------------------------------------------------------
    def test_offline_system_inquiries(self):
        queries = [
            ("what time is it", "It is"),
            ("what is the date", "Today is"),
            ("what is the battery status", "Battery"),
            ("what is the volume", "volume"),
            ("who are you", "I am Jarvis"),
        ]
        for q, expected_substr in queries:
            res = self.router.route_and_execute(q)
            self.assertEqual(res.category, "answer", f"Failed for: {q}")
            self.assertEqual(res.action_name, "knowledge_answer", f"Action mismatch for: {q}")
            self.assertIn(expected_substr.lower(), res.message.lower(), f"Answer missing '{expected_substr}' for: {q}")

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # 4. Informational Questions vs Commands
    # -------------------------------------------------------------------------
    def test_informational_questions_answered_aloud(self):
        import time
        questions = [
            "Who was Charles Babbage?",
            "Why is the sky blue?",
            "How do airplanes fly?",
            "What is quantum computing?",
            "Tell me about the Roman Empire",
            "Search for why the sky is blue",
            "Google who won the 2022 world cup",
        ]
        for q in questions:
            time.sleep(0.8)
            res = self.router.route_and_execute(q)
            # CRITICAL CHECK: Under NO circumstances should an informational question be misrouted as a PC command or browser search
            self.assertEqual(res.category, "answer", f"Question misclassified as command or search: {q}")
            self.assertIn(res.action_name, ["ai_answer", "ai_fallback", "knowledge_answer"], f"Expected spoken answer for: {q}")
            self.assertTrue(len(res.message) > 5, f"Answer too short or empty for: {q}")
            print(f"[Spoken Answer] '{q}':\n   \"{res.message}\"\n")

    # -------------------------------------------------------------------------
    # 5. Full Flow: Question -> Memory -> "Type it down" -> Active Editing
    # -------------------------------------------------------------------------
    def test_question_memory_and_type_it_down(self):
        import time
        time.sleep(0.8)
        # Step 1: User asks a question
        q_res = self.router.route_and_execute("Who was Charles Babbage?")
        self.assertEqual(q_res.category, "answer")

        # Verify router remembered the answer in self.last_answer
        saved_answer = self.router.last_answer
        self.assertTrue(len(saved_answer) > 5)

        # Step 2: User says "Can you type it down?"
        type_res = self.router.route_and_execute("Can you type it down?")
        self.assertEqual(type_res.category, "dictate")
        self.assertEqual(type_res.action_name, "type_last_answer")
        self.assertEqual(type_res.text_to_paste, saved_answer)
        self.assertIn(saved_answer, self.pasted_buffer)

        # Step 3: User says "Delete this sentence"
        del_res = self.router.route_and_execute("Delete this sentence")
        self.assertEqual(del_res.category, "command")
        self.assertEqual(del_res.action_name, "delete_sentence")



if __name__ == "__main__":
    unittest.main()

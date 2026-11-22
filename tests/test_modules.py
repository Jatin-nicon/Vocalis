import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def test_config():
    print("Testing config loading...")
    from config import settings
    assert settings.hotkey == "ctrl+space"
    assert settings.whisper_model == "small.en"
    print("  [OK] Config passed")

def test_text_cleaner():
    print("Testing dictation text cleaner...")
    from dictation import clean_text
    res = clean_text("hello world period this is a test comma right question mark")
    assert res == "Hello world. This is a test, right?", f"Got: {res}"
    print("  [OK] Text cleaner passed")

def test_intent_rules():
    print("Testing intent rules matching...")
    from intent.rules import match_command

    # Volume
    r = match_command("volume up")
    assert r.matched and r.action_name == "volume_up", f"Got: {r}"

    r = match_command("set volume to 65")
    assert r.matched and r.action_name == "set_volume", f"Got: {r}"

    r = match_command("mute")
    assert r.matched and r.action_name == "mute", f"Got: {r}"

    # Media
    r = match_command("pause video")
    assert r.matched and r.action_name == "play_pause", f"Got: {r}"

    r = match_command("next track")
    assert r.matched and r.action_name == "next_track", f"Got: {r}"

    # Tabs & Windows
    r = match_command("close tab")
    assert r.matched and r.action_name == "close_tab", f"Got: {r}"

    r = match_command("new tab")
    assert r.matched and r.action_name == "new_tab", f"Got: {r}"

    r = match_command("minimize window")
    assert r.matched and r.action_name == "minimize_window", f"Got: {r}"

    # Apps
    r = match_command("open notepad")
    assert r.matched and r.action_name == "open_app", f"Got: {r}"

    r = match_command("search youtube for lofi beats")
    assert r.matched and r.action_name == "search_youtube", f"Got: {r}"

    # Display
    r = match_command("lock screen")
    assert r.matched and r.action_name == "lock_screen", f"Got: {r}"

    r = match_command("take screenshot")
    assert r.matched and r.action_name == "screenshot", f"Got: {r}"

    # Dictation trigger
    r = match_command("type I will be late today")
    assert r.matched and r.category == "dictate" and r.payload == "I will be late today", f"Got: {r}"

    print("  [OK] All intent rules passed")

def test_router_dispatch():
    print("Testing router dispatch...")
    from intent import IntentRouter

    dispatched_dictation = []
    def mock_dictation(text):
        dispatched_dictation.append(text)
        return "Mock pasted"

    router = IntentRouter(dictation_handler=mock_dictation)

    # Command test
    res = router.route_and_execute("new tab")
    assert res.category == "command"

    # Explicit typing test
    res = router.route_and_execute("type meeting at 3pm")
    assert res.category == "dictate"
    assert len(dispatched_dictation) == 1

    # Unmatched speech when NOT in typing mode -> should NOT paste!
    res = router.route_and_execute("random chatter without type command")
    assert res.category in ("unknown", "answer"), f"Got: {res}"
    assert len(dispatched_dictation) == 1  # count unchanged!

    # Enable continuous typing mode
    res = router.route_and_execute("start typing")
    assert res.category == "mode" and router.typing_mode is True

    # Now speech is typed automatically
    res = router.route_and_execute("first sentence in typing mode")
    assert res.category == "dictate"
    assert len(dispatched_dictation) == 2

    # Disable continuous typing mode
    res = router.route_and_execute("stop typing")
    assert res.category == "mode" and router.typing_mode is False

    print("  [OK] Router dispatch passed")

def test_knowledge_and_qa():
    print("Testing knowledge and Q&A answering...")
    from intent.knowledge import match_knowledge_query
    from intent import IntentRouter

    router = IntentRouter()

    # Offline knowledge
    time_ans = match_knowledge_query("what is the time")
    assert time_ans is not None and ("it is" in time_ans.lower() or "am" in time_ans.lower() or "pm" in time_ans.lower()), f"Got: {time_ans}"

    battery_ans = match_knowledge_query("battery percentage")
    assert battery_ans is not None and ("battery" in battery_ans.lower() or "plugged in" in battery_ans.lower() or "power" in battery_ans.lower()), f"Got: {battery_ans}"

    identity_ans = match_knowledge_query("who are you")
    assert identity_ans is not None and "voice assistant" in identity_ans.lower(), f"Got: {identity_ans}"

    # Router handles question answering
    res = router.route_and_execute("what time is it")
    assert res.category == "answer"
    print("  [OK] Knowledge & Q&A passed")

if __name__ == "__main__":
    test_config()
    test_text_cleaner()
    test_intent_rules()
    test_router_dispatch()
    test_knowledge_and_qa()
    print("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")

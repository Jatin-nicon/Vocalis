import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from intent import IntentRouter, resolve_semantic_intent, execute_action

def test_semantic_tasks():
    print("Testing dynamic semantic task routing...")
    router = IntentRouter()

    # 1. Flexible Volume Phrasing
    res = router.route_and_execute("can you make the sound a bit higher")
    assert res.category == "command" and res.action_name == "volume_up", f"Got: {res}"

    res = router.route_and_execute("it's way too loud in here please turn it down")
    assert res.category == "command" and res.action_name == "volume_down", f"Got: {res}"

    res = router.route_and_execute("restore audio please")
    assert res.category == "command" and res.action_name == "unmute", f"Got: {res}"

    # 2. Flexible Browser/Tab Phrasing
    res = router.route_and_execute("kill this tab")
    assert res.category == "command" and res.action_name == "close_tab", f"Got: {res}"

    res = router.route_and_execute("open a new tab")
    assert res.category == "command" and res.action_name == "new_tab", f"Got: {res}"

    # 3. Flexible Media Phrasing
    res = router.route_and_execute("skip this track")
    assert res.category == "command" and res.action_name in ("media_next", "next_track"), f"Got: {res}"

    # 4. Flexible Web / YouTube Search
    res = router.route_and_execute("look up lofi hip hop on youtube")
    assert res.category == "command" and res.action_name == "search_youtube", f"Got: {res}"

    # 5. Flexible Display & System
    res = router.route_and_execute("screen is too dark make it brighter")
    assert res.category == "command" and res.action_name == "brightness_up", f"Got: {res}"

    print("  [OK] Dynamic semantic tasks passed.")

def test_semantic_answers():
    print("Testing dynamic semantic question answering...")
    router = IntentRouter()

    # Instant knowledge
    res = router.route_and_execute("what time is it right now")
    assert res.category == "answer"
    assert "it is" in res.message.lower() or "am" in res.message.lower() or "pm" in res.message.lower(), f"Got: {res}"

    res = router.route_and_execute("check battery level")
    assert res.category == "answer"
    assert "battery" in res.message.lower() or "plugged in" in res.message.lower(), f"Got: {res}"

    # Open-ended question
    res = router.route_and_execute("why is grass green")
    assert res.category == "answer", f"Got: {res}"
    assert len(res.message) > 5, f"Got: {res}"

    print("  [OK] Dynamic semantic questions passed.")

if __name__ == "__main__":
    test_semantic_tasks()
    test_semantic_answers()
    print("\n[SUCCESS] ALL SEMANTIC INTENT TESTS PASSED!")

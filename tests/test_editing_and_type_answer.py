import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intent.router import IntentRouter
from intent.rules import match_command

def test_charles_babbage_and_type_it_down():
    print("Testing 'Ask about Charles Babbage' -> 'Can you type it down' workflow...")
    pasted_items = []
    def mock_dictate(text):
        pasted_items.append(text)
        return f"Typed: {text[:30]}..."

    router = IntentRouter(dictation_handler=mock_dictate)
    
    # 1. Ask about Charles Babbage
    res1 = router.route_and_execute("tell me about Charles Babbage")
    assert res1.category == "answer", f"Expected answer, got: {res1}"
    assert "babbage" in res1.message.lower() or "computer" in res1.message.lower() or len(res1.message) > 20
    assert router.last_answer == res1.message
    print(f"  [Step 1 OK] Generated spoken answer: \"{res1.message[:60]}...\"")

    # 2. Ask "can you type it down"
    res2 = router.route_and_execute("can you type it down")
    assert res2.category == "dictate", f"Expected dictate, got: {res2}"
    assert res2.action_name == "type_last_answer", f"Expected type_last_answer, got: {res2}"
    assert len(pasted_items) == 1
    assert pasted_items[0] == res1.message
    print(f"  [Step 2 OK] 'can you type it down' successfully typed the previous answer!")

    # 3. Test variations: "type that down", "write it down", "paste it"
    res3 = router.route_and_execute("type that down")
    assert res3.action_name == "type_last_answer"

    res4 = router.route_and_execute("write it down")
    assert res4.action_name == "type_last_answer"

    res5 = router.route_and_execute("paste the answer")
    assert res5.action_name == "type_last_answer"
    print("  [Step 3 OK] All 'type it down' phrasing variations passed.")

def test_type_anything():
    print("Testing 'Type anything' explicit dictation...")
    pasted_items = []
    router = IntentRouter(dictation_handler=lambda t: pasted_items.append(t) or "Typed.")

    # Direct typing variations
    router.route_and_execute("type Charles Babbage was born in London")
    assert any("Charles Babbage was born in London" in item for item in pasted_items)

    router.route_and_execute("type down tomorrow morning at 9am")
    assert any("tomorrow morning at 9am" in item.lower() for item in pasted_items)

    router.route_and_execute("write down please review the document")
    assert any("review the document" in item.lower() for item in pasted_items)

    router.route_and_execute("can you write down hello world")
    assert any("hello world" in item.lower() for item in pasted_items)

    print("  [OK] 'Type anything' passed.")

def test_backspaces_and_deletions():
    print("Testing active backspaces and deletion controls...")
    
    # 1. Backspaces
    r1 = match_command("backspace")
    assert r1.matched and r1.action_name == "backspace"

    r2 = match_command("backspace 5 times")
    assert r2.matched and r2.action_name == "backspace"

    r3 = match_command("press backspace twice")
    assert r3.matched and r3.action_name == "backspace"

    # 2. Delete word
    r4 = match_command("delete word")
    assert r4.matched and r4.action_name == "delete_word"

    r5 = match_command("delete last word")
    assert r5.matched and r5.action_name == "delete_word"

    r6 = match_command("delete 3 words")
    assert r6.matched and r6.action_name == "delete_word"

    # 3. Delete sentence
    r7 = match_command("delete sentence")
    assert r7.matched and r7.action_name == "delete_sentence"

    r8 = match_command("clear sentence")
    assert r8.matched and r8.action_name == "delete_sentence"

    r9 = match_command("delete line")
    assert r9.matched and r9.action_name == "delete_sentence"

    # 4. Undo / Delete that
    r10 = match_command("delete that")
    assert r10.matched and r10.action_name == "undo"

    r11 = match_command("undo that")
    assert r11.matched and r11.action_name == "undo"

    # 5. Delete all & New line
    r12 = match_command("delete all")
    assert r12.matched and r12.action_name == "delete_all"

    r13 = match_command("new line")
    assert r13.matched and r13.action_name == "new_line"

    print("  [OK] Backspace and deletion rules passed.")

def test_editing_in_typing_mode():
    print("Testing editing controls while in continuous Typing Mode...")
    pasted = []
    router = IntentRouter(dictation_handler=lambda t: pasted.append(t) or "Typed.")
    
    # Enable typing mode
    router.route_and_execute("start typing")
    assert router.typing_mode is True

    # User says "delete sentence" -> should execute delete_sentence, NOT paste "delete sentence"
    res1 = router.route_and_execute("delete sentence")
    assert res1.category == "command" and res1.action_name == "delete_sentence"
    assert len(pasted) == 0  # Nothing was pasted!

    # User says "backspace 5 times" -> should execute backspace, NOT paste text
    res2 = router.route_and_execute("backspace 5 times")
    assert res2.category == "command" and res2.action_name == "backspace"
    assert len(pasted) == 0

    # User speaks normal text -> should paste
    res3 = router.route_and_execute("This is an actual sentence to type")
    assert res3.category == "dictate"
    assert len(pasted) == 1
    assert "actual sentence" in pasted[0].lower()

    # User exits typing mode
    res4 = router.route_and_execute("stop typing")
    assert router.typing_mode is False

    print("  [OK] In-typing editing controls passed.")

if __name__ == "__main__":
    test_charles_babbage_and_type_it_down()
    test_type_anything()
    test_backspaces_and_deletions()
    test_editing_in_typing_mode()
    print("\n[SUCCESS] ALL EDITING, DELETION & TYPE DOWN TESTS PASSED!")

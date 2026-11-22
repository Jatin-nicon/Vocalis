from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intent.classifier import is_informational_question, is_offline_system_query

test_queries = [
    ("Who was Charles Babbage?", True),
    ("What is quantum computing?", True),
    ("Why is the sky blue?", True),
    ("How do airplanes fly?", True),
    ("Tell me about the Roman Empire", True),
    ("Explain photosynthesis", True),
    ("Search for why the sky is blue", True),
    ("Google who won the 2022 world cup", True),
    ("Could you explain quantum entanglement", True),
    ("What time is it", False),
    ("What is the volume", False),
    ("What is the battery status", False),
    ("Can you open Chrome", False),
    ("Make the sound louder", False),
    ("Turn down the sound a bit", False),
    ("Shut down the sound", False),
    ("Unmute audio", False),
    ("Close the chrome application", False),
    ("Can you type it down", False),
    ("Delete this sentence", False),
    ("Take a snap of my screen", False),
]

for q, expected in test_queries:
    is_q, cleaned = is_informational_question(q)
    assert is_q == expected, f"FAILED: {q} -> got {is_q}, expected {expected}"
    print(f"PASS: {q:40} -> is_question={is_q} (cleaned: '{cleaned}')")

print("\nAll 21 classifier checks passed perfectly!")

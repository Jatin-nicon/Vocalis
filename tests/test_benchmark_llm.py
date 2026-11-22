import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intent.semantic_router import call_semantic_llm

test_queries = [
    'Can you please make it louder',
    'Why is the ocean salty',
    'Open the calculator app please',
    'How do birds fly in the sky',
    'Shut down the sound completely',
    'Tell me a summary of World War 2',
    'Take a picture of my screen'
]

for q in test_queries:
    t0 = time.time()
    res = call_semantic_llm(q)
    print(f'Query: "{q}" -> Took: {time.time()-t0:.2f}s -> Decision: {res}')

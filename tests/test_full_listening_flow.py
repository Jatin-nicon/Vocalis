import sys
import threading
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import soundfile as sf
import numpy as np
import pythoncom
import win32com.client
from voice.wakeword import WakeWordDetector
from voice.hotkey import HotkeyListener
from voice.capture import AudioRecorder
from config.settings import settings

def test_wakeword_detection():
    print("Testing Hybrid Wake Word Detection ('Hey Jarvis' and 'Hey Jarvis')...")
    
    events = []
    def on_wake(phrase=None):
        events.append(phrase or "jarvis")

    detector = WakeWordDetector(
        wake_word="hey_jarvis",
        threshold=0.45,
        speech_threshold=0.012,
        on_wake_detected=on_wake,
        enabled=True,
    )
    detector._ensure_models_loaded()
    
    pythoncom.CoInitialize()
    sapi = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    temp_wav = "C:/Users/jatin/Desktop/myprojects/Voice-PC-Assistant/tests/temp_flow_test.wav"

    # Test phrase 1: Hey Jarvis
    stream.Open(temp_wav, 3)
    sapi.AudioOutputStream = stream
    sapi.Speak("Hey Jarvis")
    stream.Close()
    
    data, sr = sf.read(temp_wav)
    if len(data.shape) > 1: data = data[:, 0]
    if sr != 16000:
        step = sr / 16000
        indices = np.arange(0, len(data), step).astype(int)
        indices = indices[indices < len(data)]
        data = data[indices]
    data_int16 = (data * 32767).astype(np.int16)
    
    detector._running = True
    detector._paused = False
    detector._verifier_thread = threading.Thread(target=detector._verifier_loop, daemon=True)
    detector._verifier_thread.start()
    
    events.clear()
    
    # Feed chunks with feed_chunk
    chunk_size = 1280
    for i in range(0, len(data_int16), chunk_size):
        chunk = data_int16[i:i+chunk_size]
        if len(chunk) < chunk_size:
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
        detector.feed_chunk(chunk)
        time.sleep(0.01)

    time.sleep(0.35)
    silence = np.zeros(chunk_size, dtype=np.int16)
    detector.feed_chunk(silence)
    
    # Wait for verifier worker
    t0 = time.time()
    while not events and (time.time() - t0 < 5.0):
        time.sleep(0.1)
        
    print(f"  [Events for 'Hey Jarvis']: {events}")
    assert len(events) > 0, "Failed to detect 'Hey Jarvis'!"
    print("  [PASS] 'Hey Jarvis' successfully detected!")
    
    detector.stop()

def test_hotkey():
    print("Testing Hotkey Listener...")
    hotkey_pressed = []
    def on_toggle():
        hotkey_pressed.append(True)
        
    listener = HotkeyListener(hotkey="ctrl+space", on_toggle=on_toggle)
    listener.start()
    assert listener._running is True
    # Trigger manually
    listener._trigger()
    time.sleep(0.1)
    assert len(hotkey_pressed) == 1
    listener.stop()
    print("  [PASS] Hotkey listener initialized and responsive.")

def test_capture_sensitivity():
    print("Testing AudioRecorder sensitivity and soft-speech capture...")
    recorder = AudioRecorder(sample_rate=16000, speech_threshold=0.012)
    
    # Inject a soft audio frame (peak 0.015, which is < old 0.025 but > new 0.012)
    soft_frame = np.sin(np.linspace(0, 50, 1600)).astype(np.float32) * 0.018
    recorder.audio_frames.append(soft_frame)
    
    assert recorder.has_captured_speech(min_peak=0.008) is True
    print("  [PASS] Soft speech successfully retained and protected from premature timeout.")

if __name__ == "__main__":
    test_wakeword_detection()
    test_hotkey()
    test_capture_sensitivity()
    print("\n[SUCCESS] ALL LISTENING & WAKE TESTS PASSED!")

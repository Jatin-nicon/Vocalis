import time
import queue
import threading
import numpy as np
import soundfile as sf
import pythoncom
import win32com.client
from faster_whisper import WhisperModel
from openwakeword.model import Model as OWWModel

class HybridWakeWordTester:
    def __init__(self):
        print("[Init] Loading models...")
        self.oww_model = OWWModel(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        self.whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        self.queue = queue.Queue()
        self.running = True
        self.detected_events = []
        
        self.worker = threading.Thread(target=self._verifier_loop, daemon=True)
        self.worker.start()

    def _verifier_loop(self):
        while self.running:
            try:
                audio = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue
            
            # Normalize
            max_peak = float(np.max(np.abs(audio)))
            if max_peak > 0.01:
                audio = (audio / max_peak) * 0.95
                
            segs, _ = self.whisper_model.transcribe(
                audio,
                language="en",
                beam_size=1,
                temperature=0.0,
                initial_prompt="Hey Jester, Jester, Hey Jarvis",
            )
            text = " ".join(s.text for s in segs).strip().lower()
            text_clean = "".join(c for c in text if c.isalnum() or c.isspace()).strip()
            keywords = {"jester", "hey jester", "chester", "gesture", "jasper", "tester", "jarvis"}
            if any(k in text_clean for k in keywords):
                self.detected_events.append(("whisper", text))

    def feed_audio(self, audio_data_int16, sample_rate=16000):
        # 1. Feed 1280 chunks to openwakeword
        for i in range(0, len(audio_data_int16) - 1280, 1280):
            chunk = audio_data_int16[i:i+1280]
            pred = self.oww_model.predict(chunk)
            score = pred.get("hey_jarvis", 0.0)
            if score >= 0.5:
                self.detected_events.append(("openwakeword", score))
                break
        
        # 2. Feed whole audio as float32 to verifier queue
        audio_float32 = (audio_data_int16.astype(np.float32) / 32768.0)
        self.queue.put(audio_float32)

def run_test():
    pythoncom.CoInitialize()
    sapi = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    test_file = "C:/Users/jatin/Desktop/myprojects/Voice-PC-Assistant/tests/temp_test_audio.wav"
    
    tester = HybridWakeWordTester()
    
    test_phrases = [
        ("Hey Jester", True),
        ("Hey Jarvis", True),
        ("Jester mute sound", True),
        ("Open notepad right now", False),
    ]
    
    for phrase, expected in test_phrases:
        tester.detected_events.clear()
        tester.oww_model.reset()
        stream.Open(test_file, 3)
        sapi.AudioOutputStream = stream
        sapi.Speak(phrase)
        stream.Close()
        
        data, sr = sf.read(test_file)
        if len(data.shape) > 1:
            data = data[:, 0]
        if sr != 16000:
            step = sr / 16000
            indices = np.arange(0, len(data), step).astype(int)
            indices = indices[indices < len(data)]
            data = data[indices]
        data_int16 = (data * 32767).astype(np.int16)
        
        t0 = time.time()
        tester.feed_audio(data_int16)
        
        # Wait up to 1.5s for worker
        time.sleep(0.8)
        detected = len(tester.detected_events) > 0
        status = "PASS" if detected == expected else "FAIL"
        print(f"[{status}] Phrase: '{phrase}' (Expected: {expected}) -> Events: {tester.detected_events} ({time.time()-t0:.2f}s)")

if __name__ == "__main__":
    run_test()

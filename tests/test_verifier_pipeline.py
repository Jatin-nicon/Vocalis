import soundfile as sf
import numpy as np
import pythoncom
import win32com.client
from faster_whisper import WhisperModel

m = WhisperModel('tiny.en', device='cpu', compute_type='int8')
pythoncom.CoInitialize()
sapi = win32com.client.Dispatch('SAPI.SpVoice')
stream = win32com.client.Dispatch('SAPI.SpFileStream')
test_file = 'C:/Users/jatin/Desktop/myprojects/Voice-PC-Assistant/tests/temp_test_jarvis.wav'

phrases = [
    'The weather is nice today',
    'Can you please play music',
    'Hey Jarvis what time is it',
    'Jarvis turn up volume',
    'Hey Jarvis mute sound',
    'Tell me a funny joke'
]

keywords = {'jarvis', 'hey jarvis', 'jervis', 'jarviss'}

for p in phrases:
    stream.Open(test_file, 3)
    sapi.AudioOutputStream = stream
    sapi.Speak(p)
    stream.Close()
    
    data, sr = sf.read(test_file)
    if len(data.shape) > 1:
        data = data[:, 0]
    if sr != 16000:
        step = sr / 16000
        indices = np.arange(0, len(data), step).astype(int)
        indices = indices[indices < len(data)]
        data = data[indices]
    data = data.astype(np.float32)
    
    segs, _ = m.transcribe(data, language='en', beam_size=1, initial_prompt='Hey Jarvis, Jarvis')
    text = ' '.join(s.text for s in segs).strip().lower()
    matched = any(k in text for k in keywords)
    print(f'Phrase: "{p}" -> Transcribed: "{text}" -> Wake Word Triggered: {matched}')

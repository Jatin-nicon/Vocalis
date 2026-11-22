import tempfile
import soundfile as sf
import numpy as np
import pythoncom
import win32com.client
from openwakeword.model import Model as OWWModel

pythoncom.CoInitialize()
sapi = win32com.client.Dispatch("SAPI.SpVoice")
stream = win32com.client.Dispatch("SAPI.SpFileStream")
model = OWWModel(wakeword_models=['hey_jarvis'], inference_framework='onnx')

temp_wav = tempfile.mktemp(suffix='.wav')

for phrase in ['Hey Jarvis', 'Jarvis']:
    stream.Open(temp_wav, 3)
    sapi.AudioOutputStream = stream
    sapi.Speak(phrase)
    stream.Close()
    
    data, sr = sf.read(temp_wav)
    if len(data.shape) > 1:
        data = data[:, 0]
    if sr != 16000:
        step = sr / 16000
        indices = np.arange(0, len(data), step).astype(int)
        indices = indices[indices < len(data)]
        data = data[indices]
    data_int16 = (data * 32767).astype(np.int16)
    
    model.reset()
    scores = []
    for i in range(0, len(data_int16) - 1280, 1280):
        chunk = data_int16[i:i+1280]
        pred = model.predict(chunk)
        scores.append(pred.get('hey_jarvis', 0.0))
        
    print(f'openwakeword hey_jarvis score for "{phrase}": max = {max(scores) if scores else 0.0:.4f}')

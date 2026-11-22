# Vocalis 🎙️💻

**Jarvis** is the voice assistant behind **Vocalis** - a modular, local-first voice assistant that controls your Windows PC with voice commands and provides fast speech-to-text dictation (Wispr Flow style). Wake word, speech-to-text and text-to-speech all run locally, so your audio never leaves your machine.

---

## 📁 Modular Architecture

Every subsystem is isolated in its own folder with single-responsibility design:

```text
Vocalis/
├── 📁 config/                 # Settings & defaults (hotkey, model sizes, steps)
│   ├── settings.py
│   └── default_settings.json
│
├── 📁 voice/                  # Speech input/output pipeline
│   ├── capture.py            # sounddevice microphone capture & amplitude
│   ├── stt.py                # faster-whisper local speech-to-text
│   ├── tts.py                # pyttsx3 asynchronous text-to-speech queue
│   ├── hotkey.py             # Global keyboard hotkey trigger (Ctrl+Space)
│   └── wakeword.py           # 100% local ONNX continuous "Hey Jarvis" wake word detector
│
├── 📁 windows_controls/       # Windows OS & hardware actions
│   ├── volume.py             # Master volume, mute, unmute, level % (pycaw)
│   ├── media.py              # Play, pause, skip, rewind media keys
│   ├── apps.py               # Launch apps, URI protocols, web searches
│   ├── window_manager.py     # Close tab, new tab, minimize, maximize, alt-tab
│   └── display.py            # Screen brightness, lock workstation, screenshot
│
├── 📁 intent/                 # Intent routing & classification
│   ├── rules.py              # Ultra-fast local regex/keyword matching (< 5ms)
│   ├── router.py             # Dispatches to command, dictation, or LLM
│   └── llm_fallback.py       # Cloud LLM classifier for complex queries (Groq)
│
├── 📁 dictation/              # Wispr Flow-style text insertion
│   ├── text_cleaner.py       # Punctuation formatting & filler removal
│   └── paste.py              # Safe clipboard copy & auto-typing
│
├── 📁 ui/                     # Visual status overlay
│   └── hud.py                # Floating translucent animated ring HUD
│
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── main.py                    # Orchestrator & CLI runner
```

---

## 🎙️ Supported Voice Commands

### 🔊 Volume Controls
* *"volume up"*, *"increase volume"*, *"louder"*
* *"volume down"*, *"decrease volume"*, *"quieter"*
* *"mute"*, *"silence"*
* *"unmute"*
* *"max volume"*, *"maximum volume"*
* *"set volume to 40"*, *"volume 75"*

### 🎵 Media Controls
* *"play"*, *"pause"*, *"resume"*
* *"next track"*, *"skip song"*
* *"previous track"*, *"last song"*
* *"skip forward"*, *"fast forward"*
* *"rewind"*, *"skip back"*

### 🗂️ Browser & Window Management
* *"new tab"*, *"open tab"* (`Ctrl+T`)
* *"close tab"* (`Ctrl+W`)
* *"reopen tab"* (`Ctrl+Shift+T`)
* *"minimize window"*, *"minimize"* (`Win+Down`)
* *"maximize window"*, *"maximize"* (`Win+Up`)
* *"switch window"* (`Alt+Tab`)
* *"close window"*, *"close app"* (`Alt+F4`)
* *"show desktop"* (`Win+D`)

### 🚀 Apps & Web Navigation
* *"open chrome"*, *"open notepad"*, *"open calculator"*, *"open whatsapp"*
* *"open settings"*, *"open terminal"*, *"open vscode"*, *"open task manager"*
* *"search google for [query]"*, *"search for [query]"*
* *"search youtube for [song or video]"*, *"youtube [topic]"*

### 🖥️ Display & System
* *"lock pc"*, *"lock screen"*, *"lock computer"*
* *"take screenshot"*, *"screenshot"*
* *"brightness up"*, *"increase brightness"*
* *"brightness down"*, *"decrease brightness"*
* *"set brightness to 60"*

### ✍️ Dictation (Wispr Flow Mode)
* *"type [anything you want to write]"*
* Or simply speak in any active text box: speech that isn't a command is cleaned, formatted, and pasted into the focused window. Spoken words like *"comma"*, *"period"*, and *"new line"* are automatically converted to punctuation!

---

## 🚀 Quick Start

### 1. Install Dependencies
Make sure your Python virtual environment is activated:
```bash
pip install -r requirements.txt
```

### 2. Test Commands without Microphone (CLI Mode)
You can verify and test all Windows controls instantly:
```bash
python main.py --cli
```
Try typing `volume up`, `open notepad`, `mute`, or `type hello from assistant`.

### 3. Run with Voice (Wake Word or Hotkey)
```bash
python main.py
```
* **Hands-free**: Simply say **`"Hey Jarvis"`** aloud! The assistant will say *"Yes?"* and listen for your command.
* **Hotkey**: Press **`Ctrl + Space`** at any time to toggle listening.
* Speak your command (e.g. *"volume up"*, *"open chrome"*, *"mute"*) or dictation.

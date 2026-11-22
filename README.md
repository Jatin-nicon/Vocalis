# Vocalis 🎙️💻

**Jarvis** — a local-first voice assistant for Windows that controls your PC, takes dictation straight into any text box, and answers you out loud.

Wake word, speech-to-text and text-to-speech all run **on your machine**. Your audio never leaves it.

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4)
![Privacy](https://img.shields.io/badge/audio-never%20leaves%20your%20PC-brightgreen)
![API keys](https://img.shields.io/badge/API%20keys-not%20required-blueviolet)

---

## Why this project exists

| | |
|---|---|
| 🔒 **Private** | Speech-to-text runs on local Whisper, the wake word on a local ONNX model, speech output on native SAPI5. Nothing is uploaded. |
| 💸 **Free** | Every command and every offline question below works with **zero API keys**. An optional free LLM tier adds chat if you want it. |
| ⚡ **Instant** | The wake word triggers in ~0 ms (ONNX), and command matching is a local regex pass in under 1 ms. |
| 🪟 **Windows-native** | Uses `pycaw` for audio, `pyautogui`/`comtypes` for input, `screen-brightness-control` for brightness — not a browser extension or a cloud service. |

---

## ✨ What you can do right now

All of the commands below are matched locally and work **without any API key**.

### 🎚️ Volume

| Say | Result |
|---|---|
| "volume up", "increase volume", "louder", "turn up the volume" | Raise by one step (5% by default) |
| "volume down", "decrease volume", "quieter", "turn down the volume" | Lower by one step |
| "set volume to 40", "volume 75" | Set an exact level |
| "max volume", "maximum volume" | Jump to 100% |
| "minimum volume", "min volume" | Drop to 0% |
| "mute", "silence", "shut up", "be quiet", "mute the computer" | Mute |
| "unmute", "turn on sound", "turn the sound on", "restore sound" | Unmute |
| "what is the volume", "current volume" | Report the current level |

### 🎵 Media & playback

| Say | Result |
|---|---|
| "play", "pause", "resume", "play pause" | Toggle media playback |
| "play video", "pause music", "stop playing" | Media phrasing variants |
| "next track", "next song", "next video", "skip this song" | Next track |
| "previous track", "last song", "previous video" | Previous track |
| "skip forward", "fast forward", "forward 10 seconds" | Skip ahead |
| "rewind", "skip back", "rewind 10 seconds" | Skip back |

### 🚀 Open apps

Say **"open"**, **"launch"**, **"start"**, **"run"**, **"pull up"** or **"bring up"** followed by the app.

**Installed programs**
> chrome · google chrome · browser · edge · microsoft edge · brave · firefox · notepad · calculator · settings · explorer · files · terminal · windows terminal · command prompt · cmd · powershell · task manager · vscode · vs code · visual studio code · code · paint · word · excel · powerpoint · snipping tool · camera · whatsapp · spotify

**Web apps** (open in your default browser)
> youtube · youtube music · gmail · maps · google maps · drive · google drive · github · stackoverflow · wikipedia · netflix · amazon · reddit · twitter · instagram · linkedin · twitch · chatgpt · claude · gemini · notion · figma · translate · web whatsapp · spotify web

**Close an app**
> "close chrome", "quit notepad", "kill the calculator application", "close the current window"

Closing uses a native tree-kill with a process-name sweep, so it works even when the app has no window handle.

### 🌐 Web search

| Say | Result |
|---|---|
| "search google for cats", "google cats", "look up cats" | Google search |
| "search youtube for lofi hip hop" | YouTube results page |
| "youtube lofi" | YouTube results page |
| "search the web for ..." | Google search |

### 🪟 Windows & window management

| Say | Result |
|---|---|
| "new tab", "open tab" | `Ctrl+T` |
| "close tab" | `Ctrl+W` |
| "reopen tab" | `Ctrl+Shift+T` |
| "minimize window", "minimize" | `Win+↓` |
| "maximize window", "maximize" | `Win+↑` |
| "switch window", "alt tab" | `Alt+Tab` |
| "close window", "close app" | `Alt+F4` |
| "show desktop" | `Win+D` |

### 🖥️ Display & system

| Say | Result |
|---|---|
| "brightness up", "increase brightness" | Raise brightness |
| "brightness down", "decrease brightness" | Lower brightness |
| "set brightness to 60" | Set exact brightness |
| "what is the brightness", "current brightness" | Report brightness |
| "take screenshot", "screenshot" | Save a PNG to your Desktop |
| "lock pc", "lock screen", "lock computer" | Lock the workstation |

### ✍️ Dictation — Wispr Flow style

Speak normally and the text is cleaned, punctuated and pasted into whatever window has focus.

| Say | Result |
|---|---|
| "type hello from assistant" | Types that exact text |
| "start typing" | Enter continuous dictation mode |
| "stop typing" | Leave dictation mode |
| *(anything else, in typing mode)* | Dictated straight into the focused text box |

Spoken **"comma"**, **"period"**, **"question mark"** and **"new line"** are converted to real punctuation. Filler words ("um", "uh", "er") are stripped.

### ⌨️ Dictation editing controls

These work while you are dictating, so you can correct mistakes without touching the keyboard.

| Say | Result |
|---|---|
| "backspace", "backspace 5 times", "backspace twice" | Delete backwards (also accepts "one" … "ten") |
| "delete word", "delete last word", "delete 3 words" | Delete whole words |
| "delete sentence", "clear sentence", "delete this line" | Delete a sentence or line |
| "undo", "undo that" | Undo the last edit |
| "new line", "press enter" | Insert a line break |
| "delete all" | Clear the field |

### 🧠 Offline Q&A — instant answers, no API key

| Say | Result |
|---|---|
| "what time is it", "tell me the time", "current time" | Current time |
| "what is the date", "what day is it", "today's date" | Current date |
| "battery status", "how is my battery" | Battery percentage |
| "cpu usage", "ram usage", "system status", "pc performance" | CPU + RAM usage |
| "what is the volume", "what is the brightness" | Current system state |
| "who are you", "what is your name" | Jarvis introduces itself |
| "tell me a joke", "make me laugh" | A random joke |
| "what is the weather" | Opens the forecast in your browser |
| "hello", "good morning" | Time-aware greeting |

### 💬 Conversational answers *(optional — free tier)*

Ask a general question and Jarvis answers it aloud using a free cloud LLM.

| Say | Result |
|---|---|
| "why is the ocean salty" | Spoken answer |
| "who won the 2022 world cup" | Spoken answer |

> **No paid key required.** This path uses Groq's or OpenRouter's *free* tiers. Without any key, Jarvis skips straight to the local rules and offline Q&A above — everything else keeps working.

### 🔁 "Type it down" — answer to text in one go

Ask a question, then say **"type it down"** (or "write it down", "paste it", "type the answer") and the spoken answer is pasted into your focused window instead of just being read aloud.

---

## ▶️ YouTube, end to end

Opening YouTube and playing videos is fully supported:

1. **"open youtube"** → YouTube opens in your default browser
2. **"search youtube for lofi hip hop"** → opens YouTube results for that query
3. **"play"** → the media key is sent to the active media session, and the browser starts the video
4. **"next track" / "previous track" / "pause"** → control playback without touching the keyboard

---

## 💸 What needs an API key?

| Capability | API key? | Notes |
|---|---|---|
| All voice commands | ❌ No | Local rules, under 1 ms |
| Dictation & editing controls | ❌ No | Local Whisper + pyautogui |
| Time, date, battery, CPU/RAM, jokes, identity | ❌ No | Local, instant |
| App launching, web search, YouTube | ❌ No | Local OS calls |
| Wake word + speech-to-text + speech output | ❌ No | Runs entirely on-device |
| General conversation | ⚠️ Optional | Free tier of Groq / OpenRouter |

**To enable conversation**, copy `.env.example` to `.env` and add one key:

```bash
GROQ_API_KEY=your_free_groq_key        # https://console.groq.com
# or
OPENROUTER_API_KEY=your_free_key       # https://openrouter.ai/keys
```

Both providers have free tiers with no credit card required.

---

## 🚀 Install

**Requirements:** Windows 10/11, Python 3.10+, a microphone.

```bash
git clone https://github.com/Jatin-nicon/Vocalis.git
cd Vocalis

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

Optionally create a `.env` for the free LLM tier:

```bash
copy .env.example .env
```

---

## 🎮 Run it

```bash
python main.py
```

- **Hands-free** — say **"Hey Jarvis"**. Jarvis answers *"Yes?"* and listens for your command.
- **Hotkey** — press **`Ctrl + Space`** at any time to toggle listening.

### CLI mode — test every command without a microphone

```bash
python main.py --cli
```

Type `volume up`, `open notepad`, `mute`, `type hello from assistant` and watch it work.

### Changing the hotkey

Set `HOTKEY` in `.env`, or change `hotkey` in `config/default_settings.json`.

---

## 🧠 How intent routing works

Every utterance goes through five tiers, cheapest first:

```
                    ┌──────────────────────────────────────┐
  your voice ──────▶│ 1. LOCAL RULES  (< 1 ms)             │──▶ command executed
                    │    regex + phrase matching          │
                    ├──────────────────────────────────────┤
                    │ 2. OFFLINE KNOWLEDGE  (instant)      │──▶ answer spoken
                    │    time, battery, CPU, jokes, weather │
                    ├──────────────────────────────────────┤
                    │ 3. TYPING MODE intercept             │──▶ edits + paste
                    │    backspace, delete word, undo …    │
                    ├──────────────────────────────────────┤
                    │ 4. QUESTION DETECTION                │──▶ answer spoken
                    │    "is this a question or a task?"    │    (needs free tier)
                    ├──────────────────────────────────────┤
                    │ 5. SEMANTIC ROUTER  (LLM)            │──▶ understood action
                    │    understands any phrasing           │    (needs free tier)
                    └──────────────────────────────────────┘
```

Tiers 1–3 are **100% local and free**. Tiers 4–5 only engage for free-form conversation and are skipped automatically when no key is configured.

---

## 📁 Project structure

```text
Vocalis/
├── config/                 # Settings & defaults (hotkey, model sizes, steps)
│   ├── settings.py
│   └── default_settings.json
│
├── voice/                  # Speech input/output pipeline
│   ├── capture.py          # sounddevice microphone capture & amplitude
│   ├── stt.py              # faster-whisper local speech-to-text
│   ├── tts.py              # Native SAPI5 + pyttsx3 asynchronous text-to-speech
│   ├── hotkey.py           # Global keyboard hotkey trigger (Ctrl+Space)
│   └── wakeword.py         # 100% local ONNX "Hey Jarvis" wake word detector
│
├── windows_controls/       # Windows OS & hardware actions
│   ├── volume.py           # Master volume, mute, unmute, level % (pycaw)
│   ├── media.py            # Play, pause, skip, rewind media keys
│   ├── apps.py             # Launch apps, web apps, URI protocols, web searches
│   ├── window_manager.py   # Close tab, new tab, minimize, maximize, alt-tab
│   └── display.py          # Brightness, lock workstation, screenshot
│
├── intent/                 # Intent routing & classification
│   ├── rules.py            # Ultra-fast local regex/keyword matching (< 5ms)
│   ├── knowledge.py        # Instant offline Q&A (time, battery, CPU, jokes)
│   ├── router.py           # Dispatches to command, dictation, or LLM
│   ├── classifier.py       # Question vs. task differentiation
│   ├── semantic_router.py  # LLM intent classifier for complex phrasing
│   ├── llm_fallback.py     # Free cloud LLM answers (Groq / OpenRouter)
│   ├── actions.py          # Action registry
│   └── knowledge.py
│
├── dictation/              # Wispr Flow-style text insertion
│   ├── text_cleaner.py     # Punctuation formatting & filler removal
│   └── paste.py            # Safe clipboard copy & auto-typing
│
├── ui/                     # Visual status overlay
│   └── hud.py              # Floating translucent animated ring HUD
│
├── tests/                  # Unit + hardware tests
├── requirements.txt
├── .env.example            # Environment variables template
├── main.py                 # Orchestrator & CLI runner
└── study.py                # Original 201-line prototype (superseded by main.py)
```

---

## 🎙️ The wake word engine

`voice/wakeword.py` runs a **hybrid two-path detector**, so nothing is sent anywhere:

| Path | Engine | Latency | Role |
|---|---|---|---|
| **A** | openWakeWord ONNX (`hey_jarvis`) | ~0 ms | Instant trigger, primary path |
| **B** | faster-whisper `tiny.en` keyword spotter | ~300 ms | Secondary confirmation path |

Both paths feed the same trigger. The ONNX model is pre-trained and downloaded on first run — **no custom wake-word training required**.

---

## 🧪 Tests

```bash
python tests\test_classifier.py
python tests\test_modules.py
python tests\test_semantic_intent.py
python tests\test_editing_and_type_answer.py
python tests\test_command_question_differentiation.py
```

The first four run fully offline. The last one needs a free LLM tier.

Hardware/audio tests (require a microphone and SAPI):

```bash
python tests\test_hybrid_wakeword.py
python tests\test_wakeword_eval.py
python tests\test_full_listening_flow.py
python tests\test_verifier_pipeline.py
```

---

## ⚙️ Configuration

`config/default_settings.json`:

| Key | Default | Meaning |
|---|---|---|
| `assistant_name` | `Jarvis` | Display name and spoken identity |
| `hotkey` | `ctrl+space` | Global push-to-talk hotkey |
| `wake_word_enabled` | `true` | Enable the "Hey Jarvis" listener |
| `wake_word_threshold` | `0.5` | ONNX trigger sensitivity |
| `whisper_model` | `small.en` | STT model size (`tiny` / `base` / `small`) |
| `silence_duration` | `1.6` | Seconds of silence that end an utterance |
| `speech_threshold` | `0.012` | Mic amplitude gate for speech detection |
| `auto_paste_unmatched` | `false` | Paste unrecognised speech instead of ignoring it |
| `voice_feedback` | `true` | Speak confirmations such as "Yes?" |
| `speech_rate` | `185` | TTS words per minute |
| `volume_step` | `5` | Percentage change per volume command |
| `brightness_step` | `10` | Percentage change per brightness command |
| `hud_enabled` | `true` | Show the floating HUD overlay |

Environment variables in `.env` (`GROQ_API_KEY`, `OPENROUTER_API_KEY`, `HOTKEY`, `WHISPER_MODEL`) override the JSON file. `.env` is git-ignored.

---

## 🛡️ Privacy & safety

- **Audio never leaves your machine.** Whisper runs locally; the wake word runs locally; TTS runs locally.
- **No telemetry.** The project sends nothing anywhere unless you configure a free cloud LLM for conversation.
- **Secrets live in `.env`**, which is git-ignored. Keys are read from the environment only — never hardcoded in source.
- **Locking and closing are explicit voice commands.** Nothing destructive happens passively.

---

## 🗺️ Roadmap

- [ ] Fix inline commands on the ONNX path — today *"Hey Jarvis, open chrome"* in one breath is dropped, because the instant trigger fires before the transcript is captured
- [x] Move the hardcoded API key into `.env`
- [x] Add missing runtime dependencies (`psutil`, `pywin32`, `pillow`) to `requirements.txt`
- [x] Fix web-app launching — *"open youtube"* previously reported success without opening anything
- [ ] Multi-user profiles and per-app command sets
- [ ] Custom wake-word training for a fully bespoke phrase
- [ ] Packaging as a `.exe` so it runs without a Python environment

---

## 🏷️ Repository topics

`voice-assistant` · `windows` · `whisper` · `speech-to-text` · `dictation` · `local-first` · `offline` · `privacy` · `wake-word` · `text-to-speech` · `pyttsx3` · `openwakeword` · `python` · `hotkey` · `assistant`

---

## 📄 License

Add a license file to make reuse explicit — MIT is the usual choice for this kind of project.

from __future__ import annotations
import random
from datetime import datetime
from typing import Optional

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False

from windows_controls import get_volume, get_brightness, search_web

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "There are 10 types of people in the world: those who understand binary, and those who don't.",
    "Why did the computer squeak? Because someone stepped on its mouse.",
    "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
    "Why was the JavaScript developer sad? Because they didn't Node how to Express themselves.",
    "Hardware is the part of a computer that you can kick; software is the part you can only curse at.",
]


def get_local_time() -> str:
    now = datetime.now()
    return f"It is {now.strftime('%I:%M %p').lstrip('0')}."


def get_local_date() -> str:
    now = datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."


def get_battery_status() -> str:
    if not _PSUTIL_AVAILABLE:
        return "Battery monitoring unavailable."
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "No battery detected (Desktop system)."
        pct = round(battery.percent)
        state = "charging" if battery.power_plugged else "on battery power"
        return f"Battery is at {pct}% and {state}."
    except Exception as e:
        return f"Could not read battery: {e}"


def get_system_stats() -> str:
    if not _PSUTIL_AVAILABLE:
        return "System monitoring unavailable."
    try:
        cpu = round(psutil.cpu_percent(interval=0.1))
        ram = round(psutil.virtual_memory().percent)
        return f"CPU usage is at {cpu}%, and RAM usage is at {ram}%."
    except Exception as e:
        return f"Could not read system stats: {e}"


def get_volume_status() -> str:
    vol = get_volume()
    if vol is not None:
        return f"System volume is currently at {vol}%."
    return "Could not retrieve volume level."


def get_brightness_status() -> str:
    b = get_brightness()
    if b is not None:
        return f"Screen brightness is currently at {b}%."
    return "Could not retrieve screen brightness."


def get_random_joke() -> str:
    return random.choice(JOKES)


def match_knowledge_query(text: str) -> Optional[str]:
    """
    Returns instant local offline answers for common questions without needing an LLM.
    """
    s = text.lower().strip()

    # Time queries
    time_triggers = [
        "what time is it", "what is the time", "current time", "tell me the time",
        "what's the time", "tell me time", "check time", "the time", "time now",
    ]
    if any(q in s for q in time_triggers) or s == "time":
        return get_local_time()

    # Date queries
    date_triggers = [
        "what is the date", "what's the date", "what is today's date",
        "what day is today", "what day is it", "today's date", "current date",
        "the date", "check date",
    ]
    if any(q in s for q in date_triggers) or s == "date":
        return get_local_date()

    # Battery queries
    if any(q in s for q in ["battery status", "battery percentage", "how is my battery", "check battery", "battery"]):
        return get_battery_status()

    # System performance
    if any(q in s for q in ["system status", "pc performance", "cpu usage", "ram usage", "memory usage"]):
        return get_system_stats()

    # Volume query
    if any(q in s for q in ["what is the volume", "what's the volume", "current volume"]):
        return get_volume_status()

    # Brightness query
    if any(q in s for q in ["what is the brightness", "what's the brightness", "current brightness"]):
        return get_brightness_status()

    # Identity
    if any(q in s for q in ["who are you", "what is your name", "what's your name", "who made you", "who created you"]):
        return "I am Jarvis, your personal voice assistant designed to control your Windows PC and execute tasks."

    # Chit-chat
    if any(q in s for q in ["how are you", "how are you doing", "how's it going"]):
        return "All systems operational and running smoothly! How can I help you?"

    if any(q in s for q in ["tell me a joke", "say a joke", "make me laugh", "say something funny"]):
        return get_random_joke()

    if s in ["hello", "hey", "hi", "good morning", "good afternoon", "good evening"]:
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
        return f"{greeting}! Jarvis is online and ready for your commands."

    # Weather shortcut
    if any(q in s for q in ["what is the weather", "what's the weather", "weather forecast"]):
        search_web("weather")
        return "Checking the weather forecast for you now."

    return None

from __future__ import annotations
import time

try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    _PYCAW_AVAILABLE = True
except ImportError:
    _PYCAW_AVAILABLE = False

try:
    import keyboard
    _KEYBOARD_AVAILABLE = True
except ImportError:
    _KEYBOARD_AVAILABLE = False


def _get_volume_endpoint():
    if not _PYCAW_AVAILABLE:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return interface.QueryInterface(IAudioEndpointVolume)
    except Exception:
        return None


def get_volume() -> int | None:
    endpoint = _get_volume_endpoint()
    if endpoint:
        try:
            return int(round(endpoint.GetMasterVolumeLevelScalar() * 100))
        except Exception:
            pass
    return None


def set_volume(percent: int) -> str:
    percent = max(0, min(100, percent))
    endpoint = _get_volume_endpoint()
    if endpoint:
        try:
            endpoint.SetMute(0, None)
            endpoint.SetMasterVolumeLevelScalar(percent / 100.0, None)
            return f"Volume set to {percent}%"
        except Exception as e:
            pass

    # Fallback to key presses if direct endpoint failed
    if _KEYBOARD_AVAILABLE:
        for _ in range(50):
            keyboard.press_and_release("volume down")
            time.sleep(0.01)
        steps = percent // 2
        for _ in range(steps):
            keyboard.press_and_release("volume up")
            time.sleep(0.01)
        return f"Volume set to approximately {percent}%"
    return "Could not adjust volume: no backend available."


def change_volume(delta: int) -> str:
    current = get_volume()
    if current is not None:
        target = current + delta
        return set_volume(target)

    # Fallback
    if _KEYBOARD_AVAILABLE:
        key = "volume up" if delta > 0 else "volume down"
        count = abs(delta) // 2 or 1
        for _ in range(count):
            keyboard.press_and_release(key)
            time.sleep(0.05)
        action = "increased" if delta > 0 else "decreased"
        return f"Volume {action}."
    return "Could not adjust volume."


def mute() -> str:
    endpoint = _get_volume_endpoint()
    if endpoint:
        try:
            endpoint.SetMute(1, None)
            return "Volume muted."
        except Exception:
            pass
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("volume mute")
        return "Volume muted."
    return "Mute failed."


def unmute() -> str:
    endpoint = _get_volume_endpoint()
    if endpoint:
        try:
            endpoint.SetMute(0, None)
            return "Volume unmuted."
        except Exception:
            pass
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("volume mute")
        return "Volume unmuted."
    return "Unmute failed."


def toggle_mute() -> str:
    endpoint = _get_volume_endpoint()
    if endpoint:
        try:
            current_mute = endpoint.GetMute()
            endpoint.SetMute(0 if current_mute else 1, None)
            return "Unmuted." if current_mute else "Muted."
        except Exception:
            pass
    if _KEYBOARD_AVAILABLE:
        keyboard.press_and_release("volume mute")
        return "Toggled mute."
    return "Toggle mute failed."


def max_volume() -> str:
    return set_volume(100)


def min_volume() -> str:
    return set_volume(0)

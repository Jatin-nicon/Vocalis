from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from config import settings
from windows_controls import (
    change_volume,
    set_volume,
    mute,
    unmute,
    toggle_mute,
    play_pause,
    next_track,
    prev_track,
    forward_seconds,
    rewind_seconds,
    open_app,
    close_app_by_name,
    search_web,
    close_tab,
    new_tab,
    reopen_tab,
    minimize_window,
    maximize_window,
    switch_window,
    close_window,
    show_desktop,
    lock_screen,
    change_brightness,
    set_brightness,
    take_screenshot,
)
from .knowledge import (
    get_local_time,
    get_local_date,
    get_battery_status,
    get_system_stats,
    get_random_joke,
    get_volume_status,
    get_brightness_status,
)
from dictation import (
    paste_text,
    press_backspace,
    delete_word,
    delete_sentence_or_line,
    delete_all,
    undo_last,
    insert_new_line,
)


@dataclass
class ActionResult:
    success: bool
    action_name: str
    message: str
    text_to_paste: str = ""


# Registry mapping action names to handler functions
# Handlers accept kwargs and return a spoken confirmation message
ACTION_REGISTRY: Dict[str, Callable[..., str]] = {
    # Volume Controls
    "volume_up": lambda **kw: change_volume(kw.get("step", settings.volume_step)),
    "volume_down": lambda **kw: change_volume(-kw.get("step", settings.volume_step)),
    "set_volume": lambda **kw: set_volume(int(kw.get("level", 50))),
    "mute": lambda **kw: mute(),
    "unmute": lambda **kw: unmute(),
    "toggle_mute": lambda **kw: toggle_mute(),
    "get_volume": lambda **kw: get_volume_status(),

    # Media Controls
    "media_play_pause": lambda **kw: play_pause(),
    "media_play": lambda **kw: play_pause(),
    "media_pause": lambda **kw: play_pause(),
    "media_next": lambda **kw: next_track(),
    "media_previous": lambda **kw: prev_track(),
    "media_forward": lambda **kw: forward_seconds(kw.get("seconds", 10)),
    "media_rewind": lambda **kw: rewind_seconds(kw.get("seconds", 10)),

    # Window & Browser Controls
    "close_tab": lambda **kw: close_tab(),
    "new_tab": lambda **kw: new_tab(),
    "reopen_tab": lambda **kw: reopen_tab(),
    "minimize_window": lambda **kw: minimize_window(),
    "maximize_window": lambda **kw: maximize_window(),
    "switch_window": lambda **kw: switch_window(),
    "show_desktop": lambda **kw: show_desktop(),
    "close_window": lambda **kw: close_window(),
    "close_active_app": lambda **kw: close_window(),

    # Applications & Web Search
    "open_app": lambda **kw: open_app(kw.get("app_name", "")),
    "close_app": lambda **kw: close_app_by_name(kw.get("app_name", "")),
    "search_web": lambda **kw: search_web(kw.get("query", ""), engine="google"),
    "search_youtube": lambda **kw: search_web(kw.get("query", ""), engine="youtube"),

    # Display & Hardware
    "brightness_up": lambda **kw: change_brightness(kw.get("step", settings.brightness_step)),
    "brightness_down": lambda **kw: change_brightness(-kw.get("step", settings.brightness_step)),
    "set_brightness": lambda **kw: set_brightness(int(kw.get("level", 50))),
    "get_brightness": lambda **kw: get_brightness_status(),
    "lock_screen": lambda **kw: lock_screen(),
    "take_screenshot": lambda **kw: take_screenshot(),

    # System & Offline Knowledge
    "get_time": lambda **kw: get_local_time(),
    "get_date": lambda **kw: get_local_date(),
    "get_battery": lambda **kw: get_battery_status(),
    "get_system_stats": lambda **kw: get_system_stats(),
    "tell_joke": lambda **kw: get_random_joke(),

    # Editing & Typing Controls
    "backspace": lambda **kw: press_backspace(int(kw.get("count", 1))),
    "delete_word": lambda **kw: delete_word(int(kw.get("count", 1))),
    "delete_sentence": lambda **kw: delete_sentence_or_line(),
    "delete_all": lambda **kw: delete_all(),
    "undo": lambda **kw: undo_last(),
    "new_line": lambda **kw: insert_new_line(),
    "type_text": lambda **kw: paste_text(kw.get("text", "")),
}


def execute_action(action_name: str, params: Optional[Dict[str, Any]] = None) -> ActionResult:
    """
    Executes a registered PC task action by name with the given parameters.
    """
    params = params or {}
    handler = ACTION_REGISTRY.get(action_name)
    if not handler:
        return ActionResult(
            success=False,
            action_name=action_name,
            message=f"Unknown action: {action_name}",
        )

    try:
        msg = handler(**params)
        return ActionResult(success=True, action_name=action_name, message=msg)
    except Exception as err:
        return ActionResult(
            success=False,
            action_name=action_name,
            message=f"Failed to execute {action_name}: {err}",
        )

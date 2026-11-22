from .volume import (
    get_volume,
    set_volume,
    change_volume,
    mute,
    unmute,
    toggle_mute,
    max_volume,
    min_volume,
)
from .media import (
    play_pause,
    next_track,
    prev_track,
    forward_seconds,
    rewind_seconds,
)
from .apps import (
    open_app,
    close_app_by_name,
    open_url,
    search_web,
)
from .window_manager import (
    close_tab,
    new_tab,
    reopen_tab,
    minimize_window,
    maximize_window,
    switch_window,
    close_window,
    show_desktop,
)
from .display import (
    lock_screen,
    get_brightness,
    set_brightness,
    change_brightness,
    take_screenshot,
)

__all__ = [
    "get_volume", "set_volume", "change_volume", "mute", "unmute", "toggle_mute", "max_volume", "min_volume",
    "play_pause", "next_track", "prev_track", "forward_seconds", "rewind_seconds",
    "open_app", "close_app_by_name", "open_url", "search_web",
    "close_tab", "new_tab", "reopen_tab", "minimize_window", "maximize_window", "switch_window", "close_window", "show_desktop",
    "lock_screen", "get_brightness", "set_brightness", "change_brightness", "take_screenshot",
]

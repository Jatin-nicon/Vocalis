from __future__ import annotations
import os
import re
import subprocess
import urllib.parse
import webbrowser

try:
    import winreg
    _WINREG_AVAILABLE = True
except ImportError:
    _WINREG_AVAILABLE = False


APP_ALIASES: dict[str, str] = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "browser": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "brave": "brave.exe",
    "firefox": "firefox.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "whatsapp": "whatsapp:",
    "settings": "ms-settings:",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "files": "explorer.exe",
    "terminal": "wt.exe",
    "windows terminal": "wt.exe",
    "command prompt": "cmd.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "vscode": "code.cmd",
    "vs code": "code.cmd",
    "visual studio code": "code.cmd",
    "code": "code.cmd",
    "spotify": "spotify:",
    "camera": "microsoft.windows.camera:",
    "paint": "mspaint.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "snipping tool": "ms-screenclip:",
    "snip": "ms-screenclip:",
}


def normalize_app_name(raw_name: str) -> str:
    """Strips leading articles, prepositions, and trailing noise like 'application', 'app', 'browser'."""
    s = raw_name.lower().strip().rstrip(".?!,:;")
    # Strip leading noise words: "up", "the", "my", "this", "a", "an"
    s = re.sub(r"^(?:up|the|my|this|a|an)\s+", "", s).strip()
    # Strip trailing noise words: "application", "app", "browser", "program", "software", "window"
    s = re.sub(r"\s+(?:application|app|browser|program|software|window)$", "", s).strip()
    # Strip trailing polite phrases: "for me", "please", "now"
    s = re.sub(r"\s+(?:for me|please|now)$", "", s).strip()
    return s.strip()


def _find_in_registry_app_paths(exe_name: str) -> str | None:
    """Checks Windows Registry App Paths for registered executable paths."""
    if not _WINREG_AVAILABLE:
        return None
    target_key = exe_name if exe_name.endswith(".exe") else f"{exe_name}.exe"
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(root, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{target_key}") as key:
                val, _ = winreg.QueryValueEx(key, "")
                if val and os.path.exists(val):
                    return val
        except Exception:
            continue
    return None


def open_app(name: str) -> str:
    cleaned = normalize_app_name(name)
    display_name = cleaned.title()
    if display_name.lower() == "chrome":
        display_name = "Chrome"
    elif display_name.lower() in ("vscode", "vs code", "code"):
        display_name = "VS Code"

    target = APP_ALIASES.get(cleaned, cleaned)

    # 1. URI schemes (e.g. spotify:, whatsapp:, ms-settings:, ms-screenclip:)
    if isinstance(target, str) and (":" in target or target.startswith("http")):
        try:
            os.startfile(target)
            return f"Opening {display_name}."
        except Exception as err:
            return f"Could not launch {display_name}: {err}"

    # 2. Try direct os.startfile
    try:
        os.startfile(target)
        return f"Opening {display_name}."
    except Exception:
        pass

    # 3. Try with .exe extension if missing
    if not target.endswith(".exe"):
        try:
            os.startfile(f"{target}.exe")
            return f"Opening {display_name}."
        except Exception:
            pass

    # 4. Check Windows Registry App Paths
    reg_path = _find_in_registry_app_paths(target)
    if reg_path:
        try:
            os.startfile(reg_path)
            return f"Opening {display_name}."
        except Exception:
            pass

    # 5. Fallback to start command via shell
    try:
        exe_cmd = target if target.endswith(".exe") else f"{target}.exe"
        subprocess.Popen(f'start "" "{exe_cmd}"', shell=True)
        return f"Opening {display_name}."
    except Exception:
        pass

    # 6. Final fallback: raw start
    try:
        subprocess.Popen(f'start "" "{target}"', shell=True)
        return f"Opening {display_name}."
    except Exception as e:
        return f"Could not launch {display_name}: {e}"



APP_PROCESS_MAP: dict[str, list[str]] = {
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "brave": ["brave.exe"],
    "firefox": ["firefox.exe"],
    "notepad": ["notepad.exe", "Notepad.exe"],
    "calculator": ["CalculatorApp.exe", "Calculator.exe", "calc.exe"],
    "calc": ["CalculatorApp.exe", "Calculator.exe", "calc.exe"],
    "spotify": ["Spotify.exe"],
    "whatsapp": ["WhatsApp.exe"],
    "terminal": ["WindowsTerminal.exe", "wt.exe"],
    "cmd": ["cmd.exe"],
    "command prompt": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "vscode": ["Code.exe", "code.exe"],
    "vs code": ["Code.exe", "code.exe"],
    "visual studio code": ["Code.exe", "code.exe"],
    "code": ["Code.exe", "code.exe"],
    "task manager": ["Taskmgr.exe", "taskmgr.exe"],
    "taskmgr": ["Taskmgr.exe", "taskmgr.exe"],
    "paint": ["mspaint.exe"],
    "word": ["WINWORD.EXE"],
    "excel": ["EXCEL.EXE"],
    "powerpoint": ["POWERPNT.EXE"],
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "files": ["explorer.exe"],
}


def close_app_by_name(process_name: str) -> str:
    cleaned = process_name.lower().strip().rstrip(".?!,:;")

    # If the user asked to close the current/opened application or window
    if cleaned in (
        "app", "application", "opened application", "opened app",
        "open application", "open app", "current application", "current app",
        "window", "active window", "current window", "this window",
        "this app", "this application", "program", "software",
    ):
        from .window_manager import close_window
        return close_window()

    base_name = normalize_app_name(process_name)
    if not base_name:
        base_name = cleaned

    # Collect target executable candidates
    candidates: list[str] = []
    if base_name in APP_PROCESS_MAP:
        candidates.extend(APP_PROCESS_MAP[base_name])
    elif cleaned in APP_PROCESS_MAP:
        candidates.extend(APP_PROCESS_MAP[cleaned])

    # Check APP_ALIASES fallback
    alias_target = APP_ALIASES.get(base_name, APP_ALIASES.get(cleaned, ""))
    if alias_target and alias_target.endswith(".exe") and alias_target not in candidates:
        candidates.append(alias_target)

    # If still empty, construct default exe
    if not candidates:
        default_exe = base_name if base_name.endswith(".exe") else f"{base_name}.exe"
        candidates.append(default_exe)

    display_name = base_name.title()
    if display_name.lower() == "chrome":
        display_name = "Chrome"

    # Strategy 1: Instant native tree termination via taskkill /f /t /im
    for exe in candidates:
        try:
            res = subprocess.run(["taskkill", "/f", "/t", "/im", exe], capture_output=True, text=True)
            if res.returncode == 0:
                return f"Closed {display_name}."
        except Exception:
            pass

    # Strategy 2: Deep search & termination via psutil (with fallback to kill)
    closed_count = 0
    try:
        import psutil
        search_terms = [base_name, cleaned] + [c.lower().replace(".exe", "") for c in candidates]
        for p in psutil.process_iter(['pid', 'name']):
            try:
                name = p.info.get('name')
                if not name:
                    continue
                pname = name.lower()
                for term in search_terms:
                    if term in pname or pname.startswith(term) or any(c.lower() == pname for c in candidates):
                        try:
                            p.kill()
                        except Exception:
                            p.terminate()
                        closed_count += 1
                        break
            except Exception:
                continue
    except ImportError:
        pass

    if closed_count > 0:
        return f"Closed {display_name}."

    return f"Failed to close {display_name}. Process may not be running."



def open_url(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url}."


def search_web(query: str, engine: str = "google") -> str:
    encoded = urllib.parse.quote_plus(query)
    if engine.lower() == "youtube":
        url = f"https://www.youtube.com/results?search_query={encoded}"
    else:
        url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    return f"Searching for {query}."

from __future__ import annotations
import math
import threading
import time
from typing import Optional

try:
    import tkinter as tk
    _TKINTER_AVAILABLE = True
except ImportError:
    _TKINTER_AVAILABLE = False


class VisualHUD:
    """
    Futuristic, borderless holographic floating HUD with animated sci-fi
    arc-reactor rings, real-time voice equalizer, and draggable repositioning.
    """
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and _TKINTER_AVAILABLE
        self.state = "idle"
        self.status_title = "JESTER ONLINE"
        self.status_detail = "Press [Ctrl + Space]"
        self.amplitude = 0.0
        self._root: Optional[tk.Tk] = None
        self._canvas: Optional[tk.Canvas] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        
        # Animation variables
        self._pulse = 0.0
        self._rot_outer = 0.0
        self._rot_mid = 0.0
        self._smooth_amp = 0.0

        # Drag tracking
        self._drag_x = 0
        self._drag_y = 0

    def start(self):
        if not self.enabled:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_tk, daemon=True)
        self._thread.start()

    def set_state(self, new_state: str, text: str = ""):
        self.state = new_state
        if new_state == "idle":
            self.status_title = "JESTER STANDBY"
            self.status_detail = text or "Press [Ctrl + Space]"
        elif new_state == "listening":
            self.status_title = "COMMAND LISTENING"
            self.status_detail = text or "Listening for PC commands..."
        elif new_state == "typing":
            self.status_title = "TYPING MODE ACTIVE"
            self.status_detail = text or "Dictating... (Say 'stop typing')"
        elif new_state == "typing_processing":
            self.status_title = "TYPING TEXT..."
            self.status_detail = text or "Formatting & pasting text"
        elif new_state == "processing":
            self.status_title = "THINKING..."
            self.status_detail = text or "Transcribing speech"
        elif new_state == "executed":
            self.status_title = "EXECUTED"
            self.status_detail = text or "Action complete"
        elif new_state == "speaking":
            self.status_title = "SPEAKING..."
            self.status_detail = text or "Responding"

    def set_amplitude(self, amp: float):
        self.amplitude = min(1.0, max(0.0, amp * 6.5))

    def _on_drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag_motion(self, event):
        if not self._root:
            return
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        new_x = self._root.winfo_x() + dx
        new_y = self._root.winfo_y() + dy
        self._root.geometry(f"+{new_x}+{new_y}")

    def _draw_rounded_pill(self, x1, y1, x2, y2, r, fill, outline):
        """Draws a smooth rounded pill rectangle for the status display."""
        canvas = self._canvas
        d = 2 * r
        # Background pill
        canvas.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, fill=fill, outline="")
        canvas.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, fill=fill, outline="")
        canvas.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, fill=fill, outline="")
        canvas.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, fill=fill, outline="")
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="")
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="")
        # Border lines
        canvas.create_line(x1 + r, y1, x2 - r, y1, fill=outline, width=1)
        canvas.create_line(x1 + r, y2, x2 - r, y2, fill=outline, width=1)
        canvas.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style="arc", outline=outline, width=1)
        canvas.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style="arc", outline=outline, width=1)
        canvas.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style="arc", outline=outline, width=1)
        canvas.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style="arc", outline=outline, width=1)

    def _run_tk(self):
        try:
            self._root = tk.Tk()
            self._root.title("Voice Assistant Hologram HUD")
            
            # Position at bottom-right of primary screen
            screen_w = self._root.winfo_screenwidth()
            screen_h = self._root.winfo_screenheight()
            hud_w, hud_h = 300, 310
            init_x = screen_w - hud_w - 35
            init_y = screen_h - hud_h - 75
            
            self._root.geometry(f"{hud_w}x{hud_h}+{init_x}+{init_y}")
            self._root.configure(bg="#000001")
            self._root.wm_attributes("-transparentcolor", "#000001")
            self._root.attributes("-topmost", True)
            self._root.overrideredirect(True)

            self._canvas = tk.Canvas(
                self._root,
                width=hud_w,
                height=hud_h,
                bg="#000001",
                highlightthickness=0,
            )
            self._canvas.pack(fill="both", expand=True)

            # Draggable binding
            self._canvas.bind("<ButtonPress-1>", self._on_drag_start)
            self._canvas.bind("<B1-Motion>", self._on_drag_motion)

            self._animate()
            self._root.mainloop()
        except Exception as e:
            print(f"[HUD Warning] UI could not initialize: {e}")

    def _animate(self):
        if not self._running or not self._canvas or not self._root:
            return

        canvas = self._canvas
        canvas.delete("all")

        cx, cy = 150, 115
        self._pulse += 0.08
        self._rot_outer = (self._rot_outer + 1.8) % 360
        self._rot_mid = (self._rot_mid - 2.6) % 360
        
        # Smooth interpolation for voice amplitude
        self._smooth_amp += (self.amplitude - self._smooth_amp) * 0.35

        # Theme color selection based on state
        if self.state in ("typing", "typing_processing"):
            primary_color = "#ff007f"    # Vibrant Neon Magenta / Hot Pink
            secondary_color = "#b5179e"  # Deep Electric Violet
            glow_color = "#550033"
            speed_mult = 2.2
        elif self.state == "listening":
            primary_color = "#00f0ff"    # Electric Cyan
            secondary_color = "#7000ff"  # Neon Violet
            glow_color = "#005566"
            speed_mult = 2.5
        elif self.state == "processing":
            primary_color = "#ffb703"    # Warm Amber Gold
            secondary_color = "#fb8500"  # Blaze Orange
            glow_color = "#553300"
            speed_mult = 3.5
        elif self.state == "executed":
            primary_color = "#00f5a0"    # Emerald Tech Green
            secondary_color = "#00d9f5"  # Aqua
            glow_color = "#004d33"
            speed_mult = 1.0
        elif self.state == "speaking":
            primary_color = "#9d4edd"    # Sci-Fi Lilac
            secondary_color = "#c77dff"
            glow_color = "#3c096c"
            speed_mult = 2.0
        else:  # idle
            primary_color = "#00a6fb"    # Soft Cyber Blue
            secondary_color = "#0582ca"
            glow_color = "#001e33"
            speed_mult = 1.0

        self._rot_outer = (self._rot_outer + 1.2 * speed_mult) % 360
        self._rot_mid = (self._rot_mid - 1.8 * speed_mult) % 360
        pulse_val = math.sin(self._pulse) * 4.5

        # 1. Subtle Radial Glow Backdrop
        is_active_audio = self.state in ("listening", "typing")
        glow_r = 75 + pulse_val + (self._smooth_amp * 22 if is_active_audio else 0)
        canvas.create_oval(
            cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r,
            fill=glow_color,
            outline="",
        )

        # 2. Outer Rotating Sci-Fi Arcs (8 segmented dashes)
        r_out = 66 + pulse_val * 0.5
        for i in range(8):
            start_deg = self._rot_outer + (i * 45)
            canvas.create_arc(
                cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                start=start_deg,
                extent=26,
                style="arc",
                outline=primary_color,
                width=2,
            )

        # 3. Middle Reverse-Rotating Orbital Ring with Tech Ticks
        r_mid = 52
        canvas.create_oval(
            cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid,
            outline=secondary_color,
            width=1,
        )
        for j in range(12):
            rad = math.radians(self._rot_mid + (j * 30))
            x_in = cx + math.cos(rad) * (r_mid - 4)
            y_in = cy + math.sin(rad) * (r_mid - 4)
            x_out = cx + math.cos(rad) * (r_mid + 4)
            y_out = cy + math.sin(rad) * (r_mid + 4)
            canvas.create_line(x_in, y_in, x_out, y_out, fill=secondary_color, width=1)

        # 4. Inner Energy Ring
        r_in = 36 + (self._smooth_amp * 8 if is_active_audio else 0)
        canvas.create_oval(
            cx - r_in, cy - r_in, cx + r_in, cy + r_in,
            outline=primary_color,
            width=2,
        )

        # 5. Core Voice Equalizer / Typing Caret Spectrum
        if self.state == "listening":
            # Command Listening: 7 Electric Equalizer Bars
            num_bars = 7
            bar_width = 3
            spacing = 7
            total_w = (num_bars * bar_width) + ((num_bars - 1) * (spacing - bar_width))
            start_x = cx - (total_w / 2)

            for b in range(num_bars):
                bx = start_x + b * spacing
                # Each bar gets unique harmonic vibration based on amplitude and sine phase
                harmonic = math.sin(self._pulse * 3.5 + b * 0.9)
                bar_h = 6 + (self._smooth_amp * 32 * max(0.2, (harmonic + 1.2) / 2))
                canvas.create_line(
                    bx, cy - bar_h / 2, bx, cy + bar_h / 2,
                    fill="#ffffff",
                    width=bar_width,
                    capstyle="round",
                )
        elif self.state in ("typing", "typing_processing"):
            # Typing Mode: Animated dictation wave + blinking caret cursor
            canvas.create_text(
                cx, cy - 16,
                text="DICTATING",
                fill="#ffffff",
                font=("Segoe UI", 7, "bold"),
            )
            # Animated sound-reactive text wave lines
            line_widths = [26, 38, 20]
            for idx, lw in enumerate(line_widths):
                ly = cy - 2 + (idx * 9)
                amp_w = lw + (self._smooth_amp * 16 * (1 if idx == 1 else 0.6))
                canvas.create_line(
                    cx - (amp_w / 2), ly, cx + (amp_w / 2), ly,
                    fill="#ffffff" if idx == 1 else primary_color,
                    width=2,
                    capstyle="round",
                )
            # Blinking text cursor caret
            if int(self._pulse * 3.2) % 2 == 0:
                cursor_x = cx + (line_widths[2] / 2) + 4
                canvas.create_line(
                    cursor_x, cy + 12, cursor_x, cy + 22,
                    fill="#ffffff",
                    width=2,
                )
        else:
            # Idle / Process / Executed Glowing Core Dot
            core_r = 10 + pulse_val * 0.8
            canvas.create_oval(
                cx - core_r, cy - core_r, cx + core_r, cy + core_r,
                fill=primary_color,
                outline="#ffffff",
                width=1,
            )

        # 6. Sleek Glassmorphic Status Pill Capsule (Below Arc Reactor)
        pill_w = 260
        pill_h = 62
        px1 = (300 - pill_w) / 2
        py1 = 220
        px2 = px1 + pill_w
        py2 = py1 + pill_h

        # Draw dark frosted capsule with neon rim
        self._draw_rounded_pill(
            px1, py1, px2, py2,
            r=14,
            fill="#0b0e17",
            outline=primary_color,
        )

        # Subtle neon header badge
        canvas.create_text(
            150, py1 + 18,
            text=self.status_title,
            fill=primary_color,
            font=("Segoe UI", 10, "bold"),
        )

        # Truncate detail text cleanly if too long
        display_detail = self.status_detail
        if len(display_detail) > 34:
            display_detail = display_detail[:31] + "..."

        canvas.create_text(
            150, py1 + 40,
            text=display_detail,
            fill="#e2e8f0",
            font=("Segoe UI", 8),
        )

        # Re-schedule frame (approx 40-45 FPS smooth animation)
        self._root.after(25, self._animate)

    def stop(self):
        self._running = False
        if self._root:
            try:
                self._root.quit()
            except Exception:
                pass

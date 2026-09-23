from datetime import datetime
import tkinter as tk
from tkinter import ttk

from .dashboard import CARD_GRID_COLUMNS, CARD_GRID_ROWS, CENTER_CARDS, CENTER_CORE_SIZE
from .left_display import LeftDisplay
from .monitors import MonitorLayout, discover_layout
from .state import DashboardPage, JarvisMode, UiState


BACKGROUND = "#050b18"
PANEL = "#0a1428"
TEXT = "#d9f5ff"
MUTED = "#7191a8"


def monitor_geometry(monitor) -> str:
    work_x, work_y, work_width, work_height = monitor.work_area
    x = f"+{work_x}" if work_x >= 0 else str(work_x)
    y = f"+{work_y}" if work_y >= 0 else str(work_y)
    return f"{work_width}x{work_height}{x}{y}"


class JarvisUiApp:
    def __init__(self, layout: MonitorLayout | None = None, state: UiState | None = None, on_ready=None):
        self.layout = layout or discover_layout()
        self.state = state or UiState()
        self.root: tk.Tk | None = None
        self.windows: dict[str, tk.Misc] = {}
        self.labels: dict[str, tk.Label] = {}
        self.dashboard_card_frames: list[tk.Frame] = []
        self.dashboard_card_labels: list[tuple[tk.Label, tk.Label, tk.Label]] = []
        self.left_display: LeftDisplay | None = None
        self.core_canvas: tk.Canvas | None = None
        self._pulse_phase = 0
        self.on_ready = on_ready

    def _make_window(self, parent, title: str, monitor):
        window = parent if title == "AYAKA JARVIS LEFT" else tk.Toplevel(parent)
        window.title(title)
        window.geometry(monitor_geometry(monitor))
        window.configure(bg=BACKGROUND)
        window.minsize(500, 400)
        window.protocol("WM_DELETE_WINDOW", self.close)
        return window

    def _label(self, parent, text: str, *, size=16, color=TEXT, bold=False):
        label = tk.Label(
            parent,
            text=text,
            fg=color,
            bg=parent.cget("bg"),
            font=("Consolas", size, "bold" if bold else "normal"),
            anchor="w",
        )
        label.pack(fill="x", padx=32, pady=5)
        return label

    def _build_left(self, window):
        _x, _y, work_width, work_height = self.layout.left.work_area
        self.left_display = LeftDisplay(window, (work_width, work_height))
        self.left_display.mount(self._build_left_fallback)

    def _build_left_fallback(self, window):
        fallback = tk.Frame(window, bg=BACKGROUND)
        self._label(fallback, "FIELD RISE", size=14, color=MUTED, bold=True)
        self.labels["left_title"] = self._label(fallback, "AYAKA", size=38, color="#68e8ff", bold=True)
        self._label(fallback, "SYSTEM CORE / VOICE INTERFACE", size=12, color=MUTED)
        character = tk.Frame(fallback, bg=PANEL, highlightbackground="#1c6682", highlightthickness=1)
        character.pack(fill="both", expand=True, padx=32, pady=28)
        tk.Label(character, text="◈", fg="#68e8ff", bg=PANEL, font=("Consolas", 96, "normal")).pack(expand=True)
        tk.Label(character, text="AYAKA // ACTIVE CHARACTER", fg="#68e8ff", bg=PANEL, font=("Consolas", 16, "bold")).pack(pady=(0, 36))
        return fallback

    def _build_center(self, window):
        self._label(window, "FIELD RISE // AYAKA JARVIS", size=18, color="#68e8ff", bold=True)
        self.labels["datetime"] = self._label(window, "", size=15, color=MUTED)
        self.labels["status"] = self._label(window, "SYSTEM ONLINE / STANDBY", size=18, color="#68e8ff", bold=True)
        core = tk.Frame(window, bg=PANEL, highlightbackground="#1c6682", highlightthickness=1)
        core.pack(fill="both", expand=True, padx=32, pady=(20, 12))
        self.core_canvas = tk.Canvas(core, width=CENTER_CORE_SIZE[0], height=CENTER_CORE_SIZE[1], bg=PANEL, highlightthickness=0)
        self.core_canvas.pack(fill="both", expand=True, padx=16, pady=16)
        self.labels["core"] = tk.Label(core, text="AYAKA CORE", fg="#68e8ff", bg=PANEL, font=("Consolas", 18, "bold"))
        self.labels["core"].pack(pady=(0, 22))
        self.labels["page"] = self._label(window, "HOME", size=14, color=MUTED)
        metrics = tk.Frame(window, bg=BACKGROUND)
        metrics.pack(fill="x", padx=32, pady=(8, 28))
        for row in range(CARD_GRID_ROWS):
            metrics.grid_rowconfigure(row, weight=1, minsize=74)
        for column in range(CARD_GRID_COLUMNS):
            metrics.grid_columnconfigure(column, weight=1, uniform="dashboard-card")
        for index, card in enumerate(CENTER_CARDS):
            row, column = divmod(index, CARD_GRID_COLUMNS)
            box = tk.Frame(metrics, bg=PANEL, highlightbackground="#153c55", highlightthickness=1)
            box.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
            title_label = tk.Label(box, text=card.title, fg=MUTED, bg=PANEL, font=("Consolas", 11, "bold"), anchor="w")
            title_label.pack(fill="x", padx=14, pady=(8, 1))
            metric_label = tk.Label(box, text=card.metric, fg=MUTED, bg=PANEL, font=("Consolas", 9), anchor="w")
            metric_label.pack(fill="x", padx=14, pady=1)
            value_label = tk.Label(box, text=card.value, fg=TEXT, bg=PANEL, font=("Consolas", 12, "bold"), anchor="w")
            value_label.pack(fill="x", padx=14, pady=(1, 8))
            self.dashboard_card_frames.append(box)
            self.dashboard_card_labels.append((title_label, metric_label, value_label))

    def _build_right(self, window):
        self._label(window, "MOMOKA // DEVELOPER", size=22, color="#b56cff", bold=True)
        self._label(window, "DEVELOPER PANEL", size=13, color=MUTED)
        panel = tk.Frame(window, bg=PANEL, highlightbackground="#543a75", highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=32, pady=28)
        values = [
            ("STATUS", "READY"),
            ("CURRENT TASK", "AYAKA JARVIS v0.2"),
            ("GitHub", "FieldRiseJapan/AYAKA-JARVIS"),
            ("Branch", "feature/ayaka-ear-v0.1"),
            ("Tests", "14 PASS"),
            ("Commit", "aabce23"),
            ("Last Action", "STT benchmark"),
            ("Suggestion", "UI foundation"),
        ]
        for key, value in values:
            tk.Label(panel, text=key, fg=MUTED, bg=PANEL, font=("Consolas", 10, "bold"), anchor="w").pack(fill="x", padx=20, pady=(14, 0))
            tk.Label(panel, text=value, fg=TEXT, bg=PANEL, font=("Consolas", 12), anchor="w", wraplength=500, justify="left").pack(fill="x", padx=20)

    def refresh(self):
        if not self.root:
            return
        now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self.labels["datetime"].configure(text=now)
        self.labels["status"].configure(text=f"SYSTEM / {self.state.system_state.value}")
        self.labels["page"].configure(text=f"CENTER / {self.state.page.value}")
        accent = self.state.theme_accent
        self.labels["left_title"].configure(text="MOMOKA // DEVELOPER MODE" if self.state.mode is JarvisMode.MOMOKA else "AYAKA", fg=accent)
        if self.left_display:
            if self.state.mode is JarvisMode.MOMOKA:
                self.left_display.show_fallback()
            else:
                self.left_display.show_ayaka()
        self.labels["core"].configure(text=f"{self.state.theme_name} CORE", fg=accent)
        self.labels["status"].configure(fg=accent)
        for frame, (title_label, metric_label, value_label) in zip(self.dashboard_card_frames, self.dashboard_card_labels):
            frame.configure(highlightbackground=accent)
            title_label.configure(fg=accent)
            metric_label.configure(fg=MUTED)
            value_label.configure(fg=TEXT)
        if self.core_canvas:
            self.core_canvas.delete("all")
            self._pulse_phase = (self._pulse_phase + 1) % 40
            width = max(self.core_canvas.winfo_width(), CENTER_CORE_SIZE[0])
            height = max(self.core_canvas.winfo_height(), CENTER_CORE_SIZE[1])
            center_x, center_y = width // 2, height // 2
            pulse = self._pulse_phase if self._pulse_phase <= 20 else 40 - self._pulse_phase
            radius = min(width, height) // 4 + pulse
            for ring_radius, ring_width in ((radius + 52, 2), (radius + 28, 2), (radius, 4)):
                self.core_canvas.create_oval(center_x - ring_radius, center_y - ring_radius, center_x + ring_radius, center_y + ring_radius, outline=accent, width=ring_width)
            core_radius = max(56, radius // 2)
            self.core_canvas.create_oval(center_x - core_radius, center_y - core_radius, center_x + core_radius, center_y + core_radius, fill=accent, outline=accent)
        self.root.after(500, self.refresh)

    def run(self):
        self.root = tk.Tk()
        self.windows["left"] = self._make_window(self.root, "AYAKA JARVIS LEFT", self.layout.left)
        self.windows["center"] = self._make_window(self.root, "AYAKA JARVIS CENTER", self.layout.center)
        self.windows["right"] = self._make_window(self.root, "AYAKA JARVIS RIGHT", self.layout.right)
        self._build_left(self.windows["left"])
        self._build_center(self.windows["center"])
        self._build_right(self.windows["right"])
        if self.on_ready:
            self.on_ready(self)
        self.refresh()
        self.root.mainloop()

    def close(self):
        if self.root:
            self.root.destroy()
            self.root = None


def run_ui():
    JarvisUiApp().run()

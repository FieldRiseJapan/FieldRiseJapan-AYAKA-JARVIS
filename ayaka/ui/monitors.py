from dataclasses import dataclass
import ctypes
import sys
from typing import Callable
from ctypes import wintypes


class MonitorInfoStructure(ctypes.Structure):
    """Win32 MONITORINFO; ctypes.wintypes does not provide this type."""

    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


@dataclass(frozen=True)
class MonitorInfo:
    name: str
    x: int
    y: int
    width: int
    height: int
    primary: bool = False
    work_x: int | None = None
    work_y: int | None = None
    work_width: int | None = None
    work_height: int | None = None

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def work_area(self) -> tuple[int, int, int, int]:
        return (
            self.x if self.work_x is None else self.work_x,
            self.y if self.work_y is None else self.work_y,
            self.width if self.work_width is None else self.work_width,
            self.height if self.work_height is None else self.work_height,
        )


@dataclass(frozen=True)
class MonitorLayout:
    left: MonitorInfo
    center: MonitorInfo
    right: MonitorInfo


def assign_monitors(monitors: list[MonitorInfo]) -> MonitorLayout:
    if not monitors:
        raise ValueError("At least one monitor is required")
    primary = next((monitor for monitor in monitors if monitor.primary), monitors[0])
    others = sorted((monitor for monitor in monitors if monitor != primary), key=lambda item: (item.x, item.y, item.name))
    left = primary
    center = others[0] if len(others) >= 1 else left
    right = others[1] if len(others) >= 2 else center
    return MonitorLayout(left=left, center=center, right=right)


def _fallback_monitors() -> list[MonitorInfo]:
    return [MonitorInfo("primary", 0, 0, 1280, 800, True)]


def discover_monitors() -> list[MonitorInfo]:
    """Discover Windows displays without making imports or tests Windows-only."""
    if sys.platform != "win32":
        return _fallback_monitors()
    user32 = ctypes.windll.user32
    monitors: list[MonitorInfo] = []
    monitor_enum_proc = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        getattr(wintypes, "HMONITOR", wintypes.HANDLE),
        getattr(wintypes, "HDC", wintypes.HANDLE),
        ctypes.POINTER(wintypes.RECT),
        wintypes.LPARAM,
    )

    def callback(handle, _dc, rect_ptr, _data):
        rect = rect_ptr.contents
        info = MonitorInfoStructure()
        info.cbSize = ctypes.sizeof(MonitorInfoStructure)
        user32.GetMonitorInfoW(handle, ctypes.byref(info))
        monitors.append(
            MonitorInfo(
                name=f"monitor-{len(monitors) + 1}",
                x=rect.left,
                y=rect.top,
                width=rect.right - rect.left,
                height=rect.bottom - rect.top,
                primary=bool(info.dwFlags & 1),
                work_x=info.rcWork.left,
                work_y=info.rcWork.top,
                work_width=info.rcWork.right - info.rcWork.left,
                work_height=info.rcWork.bottom - info.rcWork.top,
            )
        )
        return 1

    user32.EnumDisplayMonitors(None, None, monitor_enum_proc(callback), 0)
    return monitors or _fallback_monitors()


def discover_layout(discover: Callable[[], list[MonitorInfo]] = discover_monitors) -> MonitorLayout:
    return assign_monitors(discover())

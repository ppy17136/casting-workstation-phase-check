from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

import win32api
import win32con
import win32gui
from PIL import ImageGrab


WINDOW_TITLE = "砂型铸造本地智能工作站"
WINDOW_RECT = (20, 20, 1280, 820)
NAV_X = 84
PAGE_WAIT = 1.3
PAGES = [
    ("dashboard", 95),
    ("project_center", 111),
    ("parts", 128),
    ("scheme", 144),
    ("parameters", 161),
    ("solidworks", 177),
    ("simulation", 194),
    ("results", 227),
    ("documents", 244),
    ("ai", 260),
    ("review", 277),
    ("export", 293),
    ("settings", 310),
]


def main() -> None:
    workspace = Path(__file__).resolve().parents[1]
    artifacts_dir = workspace / "artifacts" / "walkthrough"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    app_path = workspace / "dist" / "CastingWorkstation" / "CastingWorkstation.exe"
    video_path = workspace / "artifacts" / "demo_walkthrough.mp4"

    _kill_existing_app()
    recorder = _start_recording(video_path)
    app_process = subprocess.Popen([str(app_path)])
    try:
        hwnd = _wait_for_window(WINDOW_TITLE)
        _prepare_window(hwnd)
        time.sleep(1.0)
        for page_name, nav_y in PAGES:
            _click(hwnd, NAV_X, nav_y)
            time.sleep(PAGE_WAIT)
            _capture_window(hwnd, artifacts_dir / f"{page_name}.png")
        time.sleep(1.5)
    finally:
        _stop_recording(recorder)
        _kill_existing_app()
        if app_process.poll() is None:
            app_process.terminate()

    print(str(video_path))


def _kill_existing_app() -> None:
    subprocess.run(
        ["taskkill", "/F", "/IM", "CastingWorkstation.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def _start_recording(video_path: Path) -> subprocess.Popen[bytes]:
    ffmpeg_path = _locate_ffmpeg()
    command = [
        str(ffmpeg_path),
        "-y",
        "-f",
        "gdigrab",
        "-framerate",
        "12",
        "-draw_mouse",
        "1",
        "-offset_x",
        "0",
        "-offset_y",
        "0",
        "-video_size",
        "1366x900",
        "-i",
        "desktop",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        str(video_path),
    ]
    return subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _stop_recording(process: subprocess.Popen[bytes] | None) -> None:
    if process is None:
        return
    if process.poll() is not None:
        return
    try:
        if process.stdin:
            process.stdin.write(b"q")
            process.stdin.flush()
    except OSError:
        process.terminate()
    process.wait(timeout=15)


def _locate_ffmpeg() -> Path:
    candidates = [
        Path(r"D:\Users\BLL\AppData\Local\LAMMPS 64-bit 11Feb2026-MSMPI\bin\ffmpeg.exe"),
        Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
        Path("ffmpeg"),
    ]
    for candidate in candidates:
        if str(candidate) == "ffmpeg" or candidate.exists():
            return candidate
    raise FileNotFoundError("ffmpeg executable not found.")


def _wait_for_window(title: str, timeout: float = 20.0) -> int:
    deadline = time.time() + timeout
    hwnd = 0
    while time.time() < deadline:
        hwnd = win32gui.FindWindow(None, title)
        if hwnd:
            return hwnd
        time.sleep(0.5)
    raise TimeoutError(f"Window not found: {title}")


def _prepare_window(hwnd: int) -> None:
    left, top, width, height = WINDOW_RECT
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.MoveWindow(hwnd, left, top, width, height, True)
    _try_set_foreground(hwnd)


def _click(hwnd: int, relative_x: int, relative_y: int) -> None:
    left, top, _, _ = win32gui.GetWindowRect(hwnd)
    absolute_x = left + relative_x
    absolute_y = top + relative_y
    _try_set_foreground(hwnd)
    time.sleep(0.1)
    win32api.SetCursorPos((absolute_x, absolute_y))
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, absolute_x, absolute_y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, absolute_x, absolute_y, 0, 0)


def _capture_window(hwnd: int, path: Path) -> None:
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    ImageGrab.grab((left, top, right, bottom)).save(path)


def _try_set_foreground(hwnd: int) -> None:
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        raise

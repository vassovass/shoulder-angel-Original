"""Shoulder Buddy MVP for Windows 11.

This script monitors the active window on a Windows 11 machine and
uses the built in Windows OCR engine to read the screen. If the
extracted text and the active window title do not appear related to the
keywords provided by the user, a small telephone style toast
notification is displayed in the bottom right corner and a short beep
plays.  The goal is to gently remind the user to return to their task
without requiring a phone call or external services.
"""

import argparse
import asyncio
import time
from typing import List, Any
import logging
import os
from pathlib import Path
import datetime
import logging.handlers

import win32gui
import win32con
import win32api
from PIL import ImageGrab
from win10toast import ToastNotifier
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
from winrt.windows.storage.streams import Buffer
import winsound
from buddy_mvp import llm
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Logging setup (rotating)
LOG_PATH = Path(__file__).with_name('ocr.log')
logger = logging.getLogger("shoulder-buddy")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.handlers.RotatingFileHandler(str(LOG_PATH), maxBytes=1_000_000, backupCount=3)
    _handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(_handler)

# Prevent messages propagating to the root logger (which can cause UnicodeEncodeError
# on Windows consoles using cp1252) while still writing to our rotating file.
logger.propagate = False

# Additional runtime helpers ------------------------------------------------
import sys  # must be imported before we touch sys.stdout

# Standard TOML parser (Python 3.11+)
try:
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # Tomllib is stdlib 3.11+, but fallback handled below

# Ensure Unicode titles don't crash console output when users add their own
# console handlers or run with --debug.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

# imagehash is optional; used for perceptual diff
try:
    import imagehash  # type: ignore
except ImportError:  # pragma: no cover
    imagehash = None  # fallback for environments without the lib

# Optional colour support for nicer console logs. If colourama is not
# available (or logs are redirected to a file), we silently fall back to
# no-colour so output remains readable.
try:
    from colorama import Fore, Style, init as _colorama_init

    _colorama_init()  # initialise ANSI handling on Windows

    _C_ENABLED = True

    _CLR = {
        "interval": Fore.GREEN,
        "window-change": Fore.BLUE,
        "screen-change": Fore.YELLOW,
        "error": Fore.RED,
        "llm": Fore.CYAN,
        "summary": Fore.MAGENTA,
        "hint": Fore.LIGHTGREEN_EX if hasattr(Fore, "LIGHTGREEN_EX") else Fore.GREEN,
    }
    _RESET = Style.RESET_ALL
except ImportError:  # pragma: no cover – colourama optional

    class _Dummy:
        GREEN = BLUE = YELLOW = RED = CYAN = ""
        RESET_ALL = ""

    Fore = _Dummy()  # type: ignore
    Style = _Dummy()  # type: ignore

    _C_ENABLED = False
    _CLR = {k: "" for k in ("interval", "window-change", "screen-change", "error", "llm", "summary", "hint")}
    _RESET = ""

# Returns screenshot PIL.Image and window title
def grab_active_window() -> tuple[Any, str]:
    """Capture a screenshot of the currently active window across all monitors."""
    hwnd = win32gui.GetForegroundWindow()
    # Get window rectangle in virtual-screen coordinates (may include negatives)
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    # Pillow 8.2+ supports all_screens param. Use it if available.
    try:
        img = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    except TypeError:
        # older Pillow: fall back to global grab then crop
        full = ImageGrab.grab()
        img = full.crop((left, top, right, bottom))
    title = win32gui.GetWindowText(hwnd)
    return img, title


def pil_to_software_bitmap(img):
    # Windows OCR only supports Gray8 or Bgra8 pixel formats. Convert the
    # screenshot to 8-bit grayscale to keep the conversion simple and avoid
    # per-pixel channel shuffling.
    img = img.convert("L")  # 8-bit pixels, black and white
    width, height = img.size
    pixel_bytes = img.tobytes()
    buffer = Buffer(len(pixel_bytes))
    buffer.length = len(pixel_bytes)
    with memoryview(buffer) as mv:
        mv[:] = pixel_bytes
    return SoftwareBitmap.create_copy_from_buffer(
        buffer, BitmapPixelFormat.GRAY8, width, height
    )


def extract_text(img) -> str:
    """Use Windows built in OCR to extract text from a PIL image."""
    engine = OcrEngine.try_create_from_user_profile_languages()
    bitmap = pil_to_software_bitmap(img)

    # winrt's recognize_async returns a winrt._IAsyncOperation which is awaitable
    # but is not a coroutine object. ``asyncio.run`` expects a coroutine, so we
    # wrap the call in a small coroutine before executing it.

    async def _recognize():
        return await engine.recognize_async(bitmap)  # type: ignore[attr-defined]

    result = asyncio.run(_recognize())
    lines = [line.text for line in result.lines]
    return " ".join(lines)


def check_relevant(text: str, title: str, keywords: List[str]) -> bool:
    base = f"{title} {text}".lower()
    return any(k.lower() in base for k in keywords)


def notify(toaster: ToastNotifier):
    winsound.Beep(880, 400)
    toaster.show_toast(
        "Shoulder Buddy", "You seem off task 📞", duration=5, threaded=True
    )


def main():
    parser = argparse.ArgumentParser(description="Run Shoulder Buddy MVP")
    parser.add_argument("--keywords", type=str, default="", help="Comma separated keywords")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Seconds between checks",
    )
    parser.add_argument("--debug", action="store_true", help="Enable console debug output and save screenshots")
    parser.add_argument("--ai-debug", action="store_true", help="Show raw LLM/HTTP debug logs (very verbose)")
    parser.add_argument("--threshold", type=int, default=10, help="Perceptual hash difference to treat as screen change")
    parser.add_argument("--task", type=str, default="", help="Short description of your current work task")
    parser.add_argument("--task-file", type=str, default="", help="Path to a text file containing task description")
    parser.add_argument("--context", type=str, default="", help="Inline custom instruction for the LLM")
    parser.add_argument("--context-file", type=str, default="", help="Path to a file whose contents are sent as the custom instruction")
    parser.add_argument("--model", type=str, default="o4-mini", help="LLM model code (o4-mini, o4-mini-high, gpt-4.1, gpt-4o)")
    parser.add_argument("--config-file", type=str, default="", help="Path to a TOML config that sets defaults")
    args = parser.parse_args()

    # ---------------------------------------------------------------------
    # Load defaults from config file (if present) BEFORE applying CLI flags
    # ---------------------------------------------------------------------
    cfg_path: Path | None = None
    if args.config_file:
        cfg_path = Path(args.config_file)
    else:
        # Look for buddy_config.toml in the same folder as this script or in
        # user_data.
        default_path = Path(__file__).with_name("buddy_config.toml")
        if default_path.exists():
            cfg_path = default_path
        else:
            ud_path = Path(__file__).with_name("user_data") / "buddy_config.toml"
            if ud_path.exists():
                cfg_path = ud_path

    cfg: dict = {}
    if cfg_path and cfg_path.exists() and tomllib is not None:
        try:
            with cfg_path.open("rb") as fh:
                cfg = tomllib.load(fh)
        except Exception as exc:
            logger.error("Failed to read config file %s: %s", cfg_path, exc)
    elif cfg_path and cfg_path.exists():
        logger.warning("tomllib not available; skipping config file %s", cfg_path)

    # Helper to fetch setting from cfg dict, else CLI argument, else fallback
    def _get(name: str, cli_value, transform=lambda x: x):
        if name in cfg:
            return transform(cfg[name])
        return cli_value

    keywords = _get("keywords", [k.strip().lower() for k in args.keywords.split(",") if k.strip()], lambda v: [str(x).lower() for x in v])
    interval = _get("interval", args.interval, int)
    debug = _get("debug", args.debug, bool)
    ai_debug = _get("ai_debug", args.ai_debug, bool)
    threshold = _get("threshold", args.threshold, int)
    model_cfg = _get("model", args.model, str)
    if model_cfg:
        args.model = model_cfg

    model_code = args.model

    # --------------------------------------------------------------
    # Logging tweaks for friendlier console output
    # --------------------------------------------------------------

    # 1. Suppress extremely verbose external library debug logs unless
    #    the user explicitly requested them via --ai-debug.
    noisy_libs = [
        "openai",  # HTTP and retry debug
        "openai._base_client",
        "httpx",  # underlying HTTP client
    ]
    for name in noisy_libs:
        logging.getLogger(name).setLevel(logging.DEBUG if ai_debug else logging.WARNING)

    # 2. If --debug is supplied, attach a *console* handler to the
    #    shoulder-buddy logger with a concise, UTF-8-friendly format so
    #    the user can actually read the events in real time.
    if debug:
        _console = logging.StreamHandler(stream=sys.stdout)
        _console.setLevel(logging.INFO)
        # Use a simple format without module+lineno noise.
        _console.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
        # Ensure UTF-8 output even on Windows code pages that default to cp1252.
        if hasattr(_console.stream, "reconfigure"):
            try:
                _console.stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
            except Exception:
                pass
        logger.addHandler(_console)

    # ---------------- Load TASK description ----------------
    user_data_dir = Path(__file__).with_name('user_data')
    if not user_data_dir.exists():
        try:
            user_data_dir.mkdir()
            # create placeholder files
            (user_data_dir / 'task.txt').write_text("# Paste your current work-task description here\n", encoding="utf-8")
            (user_data_dir / 'ignore_rules.txt').write_text("# LLM extra instructions e.g.\nIgnore navigation menus and ads\n", encoding="utf-8")
        except Exception as exc:
            logger.error("Could not create user_data dir: %s", exc)

    task_text = args.task.strip()
    task_file_path = Path(args.task_file) if args.task_file else user_data_dir / 'task.txt'
    try:
        if task_file_path.exists():
            task_text = task_file_path.read_text(encoding="utf-8").strip() or task_text
    except Exception as exc:
        logger.error("Could not read task file %s: %s", task_file_path, exc)
    if not task_text:
        task_text = "Focus on the project-related work."  # fallback minimal

    # ---------------- Load CONTEXT instruction ----------------
    context_text = args.context.strip()
    context_file_path = Path(args.context_file) if args.context_file else user_data_dir / 'ignore_rules.txt'
    try:
        if context_file_path.exists():
            context_text = context_file_path.read_text(encoding="utf-8").strip() or context_text
    except Exception as exc:
        logger.error("Could not read context file %s: %s", context_file_path, exc)

    # ---------- Auto-generate keywords if none provided ----------
    if not keywords:
        auto_kw = llm.suggest_keywords(task_text, model_code, k=5)
        if auto_kw:
            keywords = auto_kw
            print("[Auto-keywords]", ", ".join(keywords))
            logger.info("Auto-generated keywords: %s", ", ".join(keywords))
        else:
            print("No keywords supplied or generated. Buddy will treat everything as off task.")

    toaster = ToastNotifier()
    screenshots_dir = Path(__file__).with_name('screenshots')
    try:
        screenshots_dir.mkdir(exist_ok=True)
    except Exception as exc:
        logger.error("Could not create screenshots directory: %s", exc)

    last_title: str | None = None
    last_hash = None
    last_ocr_ts = 0.0
    cycle_no = 0  # incremented on every OCR run for easy reference in logs

    POLL = 0.5  # seconds between lightweight checks (title/hash)

    while True:
        try:
            img, title = grab_active_window()
        except Exception as exc:
            logger.exception("Screenshot failed: %s", exc)
            time.sleep(POLL)
            continue

        run_reason = None
        if last_title is not None and title != last_title:
            run_reason = "window-change"
        elif time.time() - last_ocr_ts >= interval:
            run_reason = "interval"
        else:
            if imagehash is not None:
                try:
                    current_hash = imagehash.average_hash(img)
                    if last_hash is not None and (current_hash - last_hash) > threshold:
                        run_reason = "screen-change"
                except Exception as exc:
                    logger.exception("Hashing failed: %s", exc)

        if run_reason:
            cycle_no += 1  # ------------------ counter advance
            try:
                text = extract_text(img)
            except Exception as exc:
                logger.exception("OCR failed: %s", exc)
                time.sleep(POLL)
                continue

            preview = text[:200].replace('\n', ' ')
            now = datetime.datetime.now()
            date_str = now.strftime('%Y%m%d')
            time_str = now.strftime('%H%M%S')
            try:
                img.save(screenshots_dir / f'screen_{date_str}_{cycle_no:04d}_{time_str}.png')
            except Exception as exc:
                logger.error("Failed to save screenshot: %s", exc)
            if debug:
                _c = _CLR.get(run_reason, "")
                print(f"{_c}[#{cycle_no:04d} {run_reason}] {title}: {preview}{_RESET}")
            logger.info("Reason=%s | WindowTitle: %s | OCR: %s", run_reason, title, preview)

            # ---- LLM relevance ----
            relevance = 50
            summary = ""
            hint = ""
            cost_usd = 0.0
            model_used = model_code
            try:
                resp = llm.evaluate(task_text, text, context_text, model_code)
                relevance = int(resp.get("relevance", 50))
                summary = resp.get("summary", "")
                hint = resp.get("hint", "")
                cost_usd = resp.get("cost_usd", 0.0)
                model_used = resp.get("model", model_code)
            except Exception as exc:
                logger.exception("LLM evaluation failed: %s", exc)
                cost_usd = 0.0
                model_used = model_code

            if debug:
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                print(
                    f"{_CLR['llm']}[{ts}] ↳ [LLM] relevance={relevance:3d} cost=${cost_usd:8.5f}{_RESET} "
                    f"{_CLR['summary']}summary={summary}{_RESET} "
                    f"{_CLR['hint']}hint={hint}{_RESET}"
                )

            logger.info("Model=%s | Relevance=%s | CostUSD=%.5f | Summary=%s | Hint=%s", model_used, relevance, cost_usd, summary, hint)

            if relevance < 30 and not check_relevant(text, title, keywords):
                notify(toaster)
            last_ocr_ts = time.time()
            last_hash = current_hash if 'current_hash' in locals() else None
            last_title = title

        time.sleep(POLL)


if __name__ == "__main__":
    main()

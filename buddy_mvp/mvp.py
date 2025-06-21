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

# imagehash is optional; used for perceptual diff
try:
    import imagehash  # type: ignore
except ImportError:  # pragma: no cover
    imagehash = None  # fallback for environments without the lib

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
    parser.add_argument("--threshold", type=int, default=10, help="Perceptual hash difference to treat as screen change")
    parser.add_argument("--task", type=str, default="", help="Short description of your current work task")
    parser.add_argument("--task-file", type=str, default="", help="Path to a text file containing task description")
    parser.add_argument("--context", type=str, default="", help="Inline custom instruction for the LLM")
    parser.add_argument("--context-file", type=str, default="", help="Path to a file whose contents are sent as the custom instruction")
    parser.add_argument("--model", type=str, default="o4-mini", help="LLM model code (o4-mini, o4-mini-high, gpt-4.1, gpt-4o)")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    interval = args.interval
    debug = args.debug
    threshold = args.threshold

    if not keywords:
        print("No keywords supplied. Buddy will treat everything as off task.")

    toaster = ToastNotifier()
    screenshots_dir = Path(__file__).with_name('screenshots')
    try:
        screenshots_dir.mkdir(exist_ok=True)
    except Exception as exc:
        logger.error("Could not create screenshots directory: %s", exc)

    last_title: str | None = None
    last_hash = None
    last_ocr_ts = 0.0

    POLL = 0.5  # seconds between lightweight checks (title/hash)

    task_text = args.task
    if args.task_file:
        try:
            task_text = Path(args.task_file).read_text(encoding="utf-8")
        except Exception as exc:
            logger.error("Could not read task file %s: %s", args.task_file, exc)
    if not task_text:
        task_text = "Focus on the project-related work."  # default minimal

    model_code = args.model

    context_text = args.context
    if args.context_file:
        try:
            context_text = Path(args.context_file).read_text(encoding="utf-8")
        except Exception as exc:
            logger.error("Could not read context file %s: %s", args.context_file, exc)

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
            try:
                text = extract_text(img)
            except Exception as exc:
                logger.exception("OCR failed: %s", exc)
                time.sleep(POLL)
                continue

            preview = text[:200].replace('\n', ' ')
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            try:
                img.save(screenshots_dir / f'screen_{timestamp}.png')
            except Exception as exc:
                logger.error("Failed to save screenshot: %s", exc)
            if debug:
                print(f"[OCR:{run_reason}] {title}: {preview}")
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
                print(f"[LLM] model={model_used} relevance={relevance} cost=${cost_usd:.5f} summary={summary}")

            logger.info("Model=%s | Relevance=%s | CostUSD=%.5f | Summary=%s | Hint=%s", model_used, relevance, cost_usd, summary, hint)

            if relevance < 30 and not check_relevant(text, title, keywords):
                notify(toaster)
            last_ocr_ts = time.time()
            last_hash = current_hash if 'current_hash' in locals() else None
            last_title = title

        time.sleep(POLL)


if __name__ == "__main__":
    main()

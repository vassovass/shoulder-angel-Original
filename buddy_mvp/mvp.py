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
from typing import List

import win32gui
import win32con
import win32api
from PIL import ImageGrab
from win10toast import ToastNotifier
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
from winrt.windows.storage.streams import Buffer
import winsound


def grab_active_window() -> ImageGrab.Image:
    """Capture a screenshot of the currently active window."""
    hwnd = win32gui.GetForegroundWindow()
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    img = ImageGrab.grab(bbox=(left, top, right, bottom))
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
        return await engine.recognize_async(bitmap)

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
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        print("No keywords supplied. Buddy will treat everything as off task.")

    toaster = ToastNotifier()

    while True:
        img, title = grab_active_window()
        text = extract_text(img)
        if not check_relevant(text, title, keywords):
            notify(toaster)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

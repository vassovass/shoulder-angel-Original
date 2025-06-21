import time
import asyncio
import json
import os
from pathlib import Path
from typing import List

import pygetwindow as gw
from PIL import ImageGrab, Image
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
from winrt.windows.storage.streams import Buffer, DataWriter
import openai
import winsound
import tkinter as tk

CONFIG_PATH = Path("tasks.json")
CHECK_INTERVAL = 60  # seconds


def load_tasks() -> List[str]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("tasks", [])
    return []


def save_tasks(tasks: List[str]):
    CONFIG_PATH.write_text(json.dumps({"tasks": tasks}, indent=2))


def get_active_window_capture() -> tuple[Image.Image, str]:
    win = gw.getActiveWindow()
    if not win:
        raise RuntimeError("No active window found")
    box = (win.left, win.top, win.left + win.width, win.top + win.height)
    img = ImageGrab.grab(bbox=box)
    return img, win.title


def pil_to_software_bitmap(pil_image: Image.Image) -> SoftwareBitmap:
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    width, height = pil_image.size
    data = pil_image.tobytes()
    buffer = Buffer(len(data))
    writer = DataWriter(buffer)
    writer.write_bytes(data)
    writer.store_async().get()
    return SoftwareBitmap.create_copy_from_buffer(buffer, BitmapPixelFormat.Rgb8, width, height)


async def run_ocr(pil_image: Image.Image) -> str:
    engine = OcrEngine.try_create_from_user_profile_languages()
    sbmp = pil_to_software_bitmap(pil_image)
    result = await engine.recognize_async(sbmp)
    return result.text


def ask_tasks_interactively() -> List[str]:
    print("Enter your main tasks for today separated by commas:")
    tasks = input().split(",")
    tasks = [t.strip() for t in tasks if t.strip()]
    save_tasks(tasks)
    return tasks


def notify_user(root: tk.Tk):
    winsound.MessageBeep(winsound.MB_ICONASTERISK)
    root.deiconify()
    root.lift()
    root.after(5000, root.withdraw)  # hide after 5 seconds


def check_relevance(llm_client, tasks: List[str], file_title: str, screen_text: str) -> bool:
    prompt = (
        "\n".join([
            "You help the user stay focused on their tasks.",
            f"User tasks: {', '.join(tasks)}",
            f"Active window title: {file_title}",
            f"Screen text: {screen_text}",
            "Return True if the content seems related to the tasks, otherwise False. Only return the single word True or False."
        ])
    )
    resp = llm_client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    return resp.choices[0].message.content.strip().lower() == "true"


def main():
    tasks = load_tasks()
    if not tasks:
        tasks = ask_tasks_interactively()

    openai.api_key = os.environ.get("OPENAI_API_KEY")
    llm_client = openai

    root = tk.Tk()
    root.withdraw()
    root.title("Shoulder Buddy")
    canvas = tk.Canvas(root, width=80, height=80)
    canvas.pack()
    canvas.create_oval(20, 20, 60, 60, fill="yellow")
    canvas.create_text(40, 40, text="☎", font=("Arial", 24))
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.geometry("80x80+0+0")

    while True:
        try:
            img, title = get_active_window_capture()
            text = asyncio.run(run_ocr(img))
            relevant = check_relevance(llm_client, tasks, title, text)
            if not relevant:
                notify_user(root)
        except Exception as e:
            print(f"Error during check: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()

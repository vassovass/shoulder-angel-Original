# Shoulder Buddy MVP

A simplified on-device version of *Shoulder Angel* that runs entirely on a Windows 11 machine. The script monitors the active window, performs OCR using Windows' built‑in OCR engine, and notifies you with a small phone icon toast if your screen contents do not appear related to your current task.

## Installation

1. Install Python 3.11 or newer on Windows 11.
2. Install the required packages:

```bash
pip install -r requirements.txt
```

(Only Python packages are installed. The OCR engine itself is part of Windows and requires no additional setup.)

## Quick start (Windows 11, Python 3.11+)

```powershell
# 1. Open PowerShell in the project folder
py -3.11 -m venv .venv
.\.venv\Scripts\Activate

# 2. Install the pinned package versions
pip install -r buddy_mvp\requirements.txt

# 3. Register pywin32 DLLs (required once per venv)
python .\.venv\Scripts\pywin32_postinstall.py -install

# 4. Launch the MVP
py -3.11 buddy_mvp\mvp.py --keywords "report,excel" --interval 60
```

The script OCRs your active window every `--interval` seconds (default 60).
If none of the keywords appear in the window title or OCR text, it plays a
short beep and shows a toast notification.

## Usage

Run the script with a list of keywords that describe your current task:

```bash
python mvp.py --keywords "report,project,excel" --interval 60
```

- `--keywords` – comma‑separated list of words that should appear in the window title or OCR text when you are on task.
- `--interval` – how often to check the screen in seconds (default: 60).

If the active window's text and title do not contain any of the keywords, a short beep is played and a toast notification appears in the bottom right corner of the active screen.

## Notes

- Works on multi‑monitor setups – the active window is captured regardless of which display it is on.
- This is a minimal proof of concept. Future versions might integrate other language models, allow more sophisticated relevance checks, and offer a GUI for configuration.

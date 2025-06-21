Shoulder Angel!

Deploy server/main.py to Railway (or elsewhere).

## Getting started

- Ensure you have Vapi, Groq, and WandB Weave accounts set up.
- Fill out .env file.
- Start screenpipe.
- Run the server. `cd server && uvicorn src.main:app --reload`
- Run the client. `cd client && python main.py`

rzwnvk-codex/create-mvp-with-ai-based-task-relevance-notifications
## Shoulder Buddy MVP (Windows 11)
A minimal stand-alone version that monitors the active window with Windows' built in OCR. See `buddy_mvp/README.md` for setup and usage.
=======
## Windows 11 MVP

For a lightweight local version using the built‑in Windows OCR and desktop notifications:

1. Install Python 3.11 or later on Windows.
2. Install requirements from `client/requirements.txt`:
   ```bash
   pip install -r client/requirements.txt
   ```
3. Set `OPENAI_API_KEY` in your environment for LLM calls.
4. Run the script:
   ```bash
   cd client
   python windows_client.py
   ```
   On first run you'll be asked for your tasks. The app checks the active window periodically and shows a small vibrating phone icon with a sound when the content doesn't match your tasks.

This MVP relies on the Windows 11 OCR API via the `winrt` package and should work on multi‑monitor setups. Adjust `CHECK_INTERVAL` inside `windows_client.py` to change how often it checks.

## Development change log

All code changes to this repository **must** be recorded in `CHANGELOG.md` with a short description and date.  Automation tools (including LLM assistants) should append a new bullet to that file each time they modify the codebase.

## Cursor AI Setup

1. Install the Cursor editor (https://cursor.com) and open this repo.
2. Make sure **Rules** are enabled (Cmd ⇧ P → `Cursor: Enable Rules`).
3. Cursor will auto-load the Project Rules in `.cursor/rules/`:
   * `00-buddy-project.mdc` – core workflow
   * `10-debug-log.mdc`    – logging conventions
   * `20-error-history.mdc` – error diary
4. Optional: enable **YOLO mode** in Cursor settings for automatic test runs.
5. If the AI mis-behaves or context seems stale, run `Cursor: Clear Context & Re-Index`.

### Local requirements
* Python 3.11+
* `pillow >= 8.2` (needed for `all_screens=True` multi-monitor capture)

Install/update with:
```bash
pip install --upgrade pillow
```

### Additional CLI option

`--threshold <int>` – perceptual-hash difference that counts as a "screen change" (default 10).  Combine with the existing `--interval`, `--keywords`, and `--debug` flags to control behaviour entirely from the command line—no config file required.

The only new runtime dependencies added for recent features are:
* `imagehash` (screen-change detection)
* `numpy` (used by `imagehash`)

### LLM model selection

Use `--model` to pick which OpenAI model the buddy calls:

| Code            | OpenAI name        | Price (USD / 1K tokens)* |
|-----------------|--------------------|--------------------------|
| o4-mini         | o4-mini            | $0.0005 in / $0.0005 out |
| o4-mini-high    | o4-mini-high       | $0.001  in / $0.001  out |
| gpt-4.1         | gpt-4o-2025-04-15  | $0.005  in / $0.015 out  |
| gpt-4o          | gpt-4o-latest      | $0.005  in / $0.015 out  |

`--debug` mode prints the model used and the estimated cost per call so you can monitor usage.

*Prices sourced from OpenAI docs (links in CHANGELOG). They may change over time.

### Environment variables (.env)
Create a `.env` file in the repo root and put your API key (and optional default model) there:
```
OPENAI_API_KEY=sk-...
BUDDY_OPENAI_MODEL=o4-mini
```
The script automatically loads this file via `python-dotenv` so you no longer need to `set` the variable every session.

### Context instruction file
Instead of passing a long string via `--context "…"`, place the text in a file and run with
```
--context-file my_instruction.txt
```
This keeps the command line short and lets you version-control complex ignore rules.

### Where to put task & instruction files
The script looks in `buddy_mvp/user_data/` by default:
* `task.txt` – paste your current Jira / ClickUp task description.
* `ignore_rules.txt` – longer custom instruction for the LLM (e.g., ignore side menus).

Those files are created automatically the first time you run the script.  To use a different location pass `--task-file` / `--context-file` flags with an explicit path.

### Logging & Debug Flags

| Flag | Purpose |
|------|---------|
| `--debug` | Prints each OCR/LLM cycle to the console with colour-coding. |
| `--ai-debug` | Enables raw OpenAI / HTTPX debug logs (very noisy). Use together with `--debug` if needed. |

When `--debug` is active:
* OCR trigger lines are colour-coded (green = interval, blue = window-change, yellow = screen-change).
* The following LLM line shows **relevance**, **cost**, **summary** (magenta) and **hint** (green).
* Each cycle is numbered (`[ #0003 ]`) and the corresponding screenshot is saved as `buddy_mvp/screenshots/screen_<date>_<cycle>_<time>.png`.

#### Log files

Runtime events are written to `buddy_mvp/ocr.log`.
* Files rotate **daily at midnight**. Older logs are compressed to `.gz` and kept for 7 days.
* To change retention or disable compression, edit the `TimedRotatingFileHandler` block near the top of `buddy_mvp/mvp.py` (look for `backupCount=7`).

The console colours rely on `colorama` and automatically fall back to plain text if ANSI is not supported.

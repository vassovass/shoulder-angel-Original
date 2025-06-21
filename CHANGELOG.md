# Change Log

All notable changes to this project will be documented in this file.
This project adheres to the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) principles (simplified).

## [Unreleased]
- _Template section_: add your change above this line.

## 2025-06-21
### Added
- OCR output is now printed to the console and logged to `buddy_mvp/ocr.log` for every screen capture.
- Logging infrastructure (`logging` module) configured in `buddy_mvp/mvp.py`.

### Fixed
- Patched `win10toast` (`on_destroy` now returns `0`) to eliminate `WNDPROC`/`LRESULT` TypeError when notifications close.

## 2025-06-21 (second update)
### Added
- `--debug` CLI switch to enable console preview of OCR and (optionally) extra debugging in future.
- Automatic saving of each active-window screenshot as PNG in `buddy_mvp/screenshots/` (timestamped) for audit/debug.

### Changed
- Added `buddy_mvp/screenshots/` to `.gitignore` to prevent large image files from being committed.

## 2025-06-22
### Added
- Created `.cursor/rules/` with 3 project rules for Cursor AI guidance.
- Added `ERROR_HISTORY.md` and `TRY_LOG.md` helper docs.
- README now includes detailed "Cursor AI Setup" section.

## 2025-06-23
### Added
- YAML configuration support (`config.yaml`) with options: `keywords`, `interval`, `debug`, `threshold`.
- New CLI flag `--config <file>`; command-line arguments override YAML values.
- Perceptual change detection via `imagehash` to trigger OCR when > threshold difference.
- Immediate OCR when active window title changes (context switch).
- Robust error handling for screenshot, OCR, hashing, and filesystem failures.
- Rotating log handler (max 1 MB ×3) replaces basic log file.
- Dependencies: `PyYAML`, `imagehash`, `numpy` added to `buddy_mvp/requirements.txt`.

### Changed
- Multi-monitor capture improved: `all_screens=True` used when available; fallback crop otherwise.

### Removed
- YAML configuration file support; all options are now provided via CLI flags (`--keywords`, `--interval`, `--debug`, `--threshold`).

## 2025-06-24
### Added
- OpenAI LLM relevance evaluation (`buddy_mvp/llm.py`) with CLI flags `--task`, `--task-file`, `--context`.
- `--threshold` + debug now prints LLM relevance summary.
- Dependencies: `openai`, `tiktoken`, `python-dotenv` added.
- Script now auto-loads `.env`; new `--context-file` flag for supplying custom LLM instruction text via file.
- Model pricing table added to README (sources: [o4-mini](https://platform.openai.com/docs/models/o4-mini), [gpt-4o](https://platform.openai.com/docs/models/chatgpt-4o-latest), [gpt-4.1](https://platform.openai.com/docs/models/gpt-4.1)).
# Error History

A chronological list of unique exceptions encountered in development.

*(No entries yet – add one the next time you handle a new error)*

## 2025-06-21
- ModuleNotFoundError: `winrt.windows.foundation.collections`
  • Context: `buddy_mvp/mvp.py` startup
  • Cause   : Missing WinRT wheel for Windows.Foundation.Collections namespace
  • Fix     : Installed package `winrt-Windows.Foundation.Collections==3.2.1` via `pip`

- TypeError: `WNDPROC return value cannot be converted to LRESULT` (win10toast)
  • Context: Notification window destroy callback in `.venv/Lib/site-packages/win10toast/__init__.py: on_destroy`
  • Cause   : Library returned `None` instead of integer from window procedure
  • Fix     : Patched `on_destroy` to `return 0`.

## 2025-06-23
- ImportError: `imagehash` (optional dependency)
  • Context: Screen-change detection in `buddy_mvp/mvp.py`
  • Cause   : Library absent in some environments
  • Fix     : Wrapped import in `try/except` and disabled perceptual hash feature when unavailable.

## 2025-06-24
- openai.error.APIConnectionError (potential)
  • Context: Network failure during LLM relevance call
  • Cause   : Temporary connectivity or invalid proxy
  • Fix     : Wrapped LLM call in try/except; script falls back to keyword logic instead of crashing.
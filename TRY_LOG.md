# Experiment / Try Log

Use this file to jot down quick experiments, toggles, or failed attempts.
This keeps the main CHANGELOG clean and still preserves context for future debugging.

Format example:
```
## 2025-06-22
- Tried lowering OCR confidence threshold to 0.6 – no improvement, reverted.

## 2025-06-23
- Implemented YAML-based configuration (`config.yaml`, `PyYAML`) for keywords / interval / etc.  After hands-on testing it proved less convenient than CLI flags, so the approach was rolled back.  YAML support and the dependency were removed and replaced by a new `--threshold` flag.
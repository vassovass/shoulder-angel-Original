# Shoulder Buddy Sprint Plan

This document outlines potential future work for the Windows MVP.

## Sprint 1: Basic notifications (current MVP)
- Capture active window and perform OCR using Windows 11 API.
- Compare window title and screen text against user tasks using an LLM.
- Show vibrating phone icon and play a sound when off‑task.
- Allow editing `CHECK_INTERVAL` in the script.

## Sprint 2: Configurable checks
- Expose check interval and tasks via a settings UI or config file.
- Option to monitor percentage change in screen text before triggering OCR.
- Improved error handling for missing OCR or API failures.

## Sprint 3: Pluggable LLMs
- Abstract LLM calls to allow providers beyond OpenAI (e.g. Groq, local models).
- Caching of recent results to reduce API usage.

## Sprint 4: Advanced activity detection
- Detect screen switches or window changes to reduce unnecessary OCR.
- Consider using file paths or application metadata for more accurate context.
- Expand memory storage using a vector database for long‑term goals.

These sprints are a guideline and can be adjusted as the project evolves.

# Shoulder Buddy Roadmap

This file outlines a suggested set of development sprints for expanding the MVP.

## Sprint 1 – Basic MVP (current)
- Capture active window and extract text using Windows OCR.
- Keyword based relevance check.
- Toast notification and beep when off task.

## Sprint 2 – Configuration and Stability
- Add GUI or config file for setting keywords and check interval.
- Option to monitor for percentage change in screen content or detect window switches.
- Improve error handling around OCR failures and multi‑monitor edge cases.

## Sprint 3 – Language Model Integration
- Allow using different local or remote LLMs to analyse screen text more intelligently.
- Support summarising recent activity to give better recommendations.

## Sprint 4 – Expanded Context
- Analyse filenames and recently opened documents.
- Maintain simple on‑device history of recent activity to compare against goals.
- Option to snooze or pause notifications.

These sprints are intentionally lightweight so the project can evolve gradually without external services.

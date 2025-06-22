# Shoulder Buddy Roadmap

This file outlines the staged development plan. Each sprint lasts ≈1–2 weeks.

## Sprint 1 – Basic MVP (✓ complete)
- ~~Capture active window and extract text using Windows OCR.~~
- ~~Keyword-based relevance check.~~
- ~~Toast notification and beep when off task.~~

## Sprint 2 – MVP Polish & Interaction (current)
- Add GUI / config window for setting keywords and check interval.
- **Task input panel**: allow users to paste a task description (e.g. JIRA, ClickUp, Monday) directly into the GUI; Buddy saves it as the current WORK_TASK.
- **Desktop "vibrating-phone" icon** as an alternative to toast/beep.
- **Basic voice agent** using on-device TTS + speech-to-text: ask "Are you on task?" and adapt next check interval based on reply.
- Pause notifications automatically outside user-defined working hours (schedule checker).
- ~~Option to monitor for percentage change in screen content or detect window switches.~~
- ~~Improve error handling around OCR failures and multi-monitor edge cases.~~
- ~~Rotating log files with gzip compression and colour-coded console debug output.~~

## Sprint 3 – Intelligent Assistance
- ~~Basic LLM relevance scoring via OpenAI (JSON response).~~
- **Binary on-task classifier** (Groq) as secondary check.
- Generate first-message reminder text for UI nudge (prompt generator).
- **Toggle to use LLM vision model to interpret screenshots directly** (skip OCR; costly, so off by default).
- After a voice conversation confirms context, append summary to task file for future reference.
- Support multiple selectable voice personalities (friendly, strict, etc.).

## Sprint 4 – Expanded Context & Memory
- Analyse filenames and recently opened documents to improve relevance.
- Maintain simple on-device history of recent activity to compare against goals.
- Option to snooze or temporarily pause notifications.
- Persistent goal memory store (local replacement for Mem0/Qdrant).
- Aggregated focus statistics & conversation log for review in the GUI.
- **Task repository**: lightweight local DB (e.g. SQLite) storing past/pending tasks so the user can pick current task from a list.

## Sprint 5 – Engagement & Gamification
- Points, streaks, or levelling system for staying on task.
- Badges/achievements displayed in the UI.
- Weekly summary email / report card.
- **Time estimation & progress tracking**: track elapsed vs. estimated time for each task, feeding into points/stats.

These sprints remain flexible; items may shift as implementation details evolve.

# Legacy "Shoulder-Angel" Server – Prompts & Feature Ideas

_Last extracted: 2025-06-21_

## 1. Prompt Library

### 1.1 Voice-Call Assistant (`server/src/voice.py`)
- **First message**
  ```
  Hello Sam. This is your Shoulder Angel.
  ```
- **System: Phone call agent**
  ```
  Your name is Angel, short for Shoulder Angel. You are a voice agent on a phone call.
  Your goal is to help a user stay on track for their goals for the day.
  End the conversation if A) they were actually focused on the right thing and you
  called them in error, B) they were distracted and are refocusing, or C) they otherwise
  request the conversation to end. If you have no memories of their goals, ask what they are.
  ```
- **Dynamic context insert**
  ```
  Here is the most recent OCR of the user's screen: {recent_ocr}
  ```

### 1.2 GroqScheduler (`server/src/models.py`)
```
Your role is to check whether the user is working when they should be.
Compare their stated schedule with the current time.
```

### 1.3 GroqOnTaskAnalyzer
```
Your role is to analyze the user's OCR output and determine if it's relevant to their
stated goals (infer this from recent conversation). Return the single word 'True' if it is
otherwise return 'False', with nothing else. Use recent messages to understand a user's
goals, but only use the OCR for current activity.
```

### 1.4 GroqTaskReminderFirstMsg
```
You're having a voice conversation with Sam. Their recent activity seems unaligned with their goals.
You should ask about their current activities, and how it relates to their goals.
Keep it within two sentences. Reply directly to Sam.
```

### 1.5 BuddyMVP `_SYSTEM_TEMPLATE` (for reference)
```
You are a focus assistant. You receive (1) the user's WORK TASK description and (2) the TEXT
CURRENTLY VISIBLE on their screen. … Respond with JSON only, no extra commentary.
```

---

## 2. Features Found Only in Legacy Server

| Feature | File(s) | Notes / Possible Adaptation |
|---------|---------|-----------------------------|
| Phone-call alert via **Vapi** | `voice.py` | Replace with a vibrating/animated phone-icon overlay on the desktop. |
| **Schedule checker** (working hours) | `models.py` + APScheduler job | Pause BuddyMVP outside user-defined hours. |
| **Binary on-task classifier** | `GroqOnTaskAnalyzer` | Could complement current numeric relevance metric. |
| **Persistent memory store** | `memory.py` with Mem0/Qdrant | Swap to lightweight local storage to remember user goals. |
| **Conversation history** | `state.py` | Handy if a UI chat log is added. |
| **ScreenPipe OCR client** | `client/main.py` | Re-use if OCR moved to external service. |
| **Prompt generator for first reminder** | `GroqTaskReminderFirstMsg` | Reuse text beside vibrating icon. |

---

## 3. Potential TODOs for BuddyMVP Roadmap

1. **UI Nudge** – Build small always-on-top window/tray icon that "vibrates" when off-task; use first-message prompt as tooltip.
2. **Working-hours logic** – Integrate schedule checker so reminders only occur during work hours.
3. **Goal memory** – Adapt memory store for local persistence of daily goals.
4. **Conversation log/stats** – Persist reminders and acknowledgements similar to `state.py`.

Keep this document updated as you migrate or retire legacy features.
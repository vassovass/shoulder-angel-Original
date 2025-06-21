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
main

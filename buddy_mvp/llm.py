"""LLM helper for Shoulder Buddy.

Requires OPENAI_API_KEY in the environment.
"""
from __future__ import annotations

import os
import json
from typing import Dict, Tuple

import openai
import tiktoken
import re

# Supported models and pricing (USD per 1K tokens, May-2025 preview)
MODEL_INFO: Dict[str, Tuple[str, float, float]] = {
    # code  : (openai_name, price_in, price_out)
    "o4-mini": ("o4-mini", 0.0005, 0.0005),
    "o4-mini-high": ("o4-mini-high", 0.001, 0.001),
    "gpt-4.1": ("gpt-4o-2025-04-15", 0.005, 0.015),
    "gpt-4o": ("gpt-4o-latest", 0.005, 0.015),
    "gpt-3.5-turbo": ("gpt-3.5-turbo", 0.0005, 0.0015),
}

DEFAULT_MODEL_CODE = os.getenv("BUDDY_OPENAI_MODEL", "o4-mini")

_SYSTEM_TEMPLATE = (
    "You are a focus assistant. You receive (1) the user's WORK TASK description and (2) the TEXT CURRENTLY VISIBLE on their screen.\n"
    "Your job: return a JSON object with keys:\n"
    "  relevance: integer 0-100 (how related the screen is to the task; 0 = totally unrelated)\n"
    "  summary  : short (≤20 words) description of what the screen appears to show\n"
    "  hint     : (optional) short advice to regain focus if relevance is low.\n"
    "Respond with JSON only, no extra commentary."
)

# ---------------------------------------------------------------------------
# Helper to strip secrets (API keys, bearer tokens) from raw OCR before
# sending it to the OpenAI model.  We keep ordinary URLs because they're
# useful context, but redact anything that matches an OpenAI-style secret.
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    # Full or partial OpenAI user/org keys
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    # Project-scoped service account keys
    re.compile(r"sk-svcacct-[A-Za-z0-9_-]{8,}"),
    # Bearer tokens appearing in curl examples
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+"),
    # api_key query/path parameters
    re.compile(r"(?i)api_key[=:][A-Za-z0-9._-]+"),
]

def _sanitize(text: str) -> str:
    # Drop lines from Python tracebacks that start with 'openai.' – they
    # provide no useful context and often contain error codes.
    cleaned_lines = []
    for line in text.splitlines():
        if line.lstrip().startswith("openai."):
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)

    # Redact secrets but keep URLs and normal text intact
    for pat in _SECRET_PATTERNS:
        cleaned = pat.sub("[REDACTED]", cleaned)
    return cleaned

def _chat(messages, model_code: str, timeout: int = 15):
    if model_code not in MODEL_INFO:
        return openai.chat.completions.create(model=model_code, messages=messages, timeout=timeout)
    model_name, _, _ = MODEL_INFO[model_code]
    return openai.chat.completions.create(model=model_name, messages=messages, timeout=timeout)


def _count_tokens(text: str, model_name: str) -> int:
    enc = tiktoken.encoding_for_model(model_name.split(":")[0])
    return len(enc.encode(text))


def evaluate(task: str, screen_text: str, custom_instruction: str | None = None, model_code: str | None = None) -> Dict:
    """Return dict {relevance,int, summary,str, hint,str, cost_usd,float}."""

    code = model_code or DEFAULT_MODEL_CODE
    price_in = price_out = 0.0
    if code in MODEL_INFO:
        model_name, price_in, price_out = MODEL_INFO[code]
    else:
        model_name = code

    system_msg = _SYSTEM_TEMPLATE
    if custom_instruction:
        system_msg += "\nAdditional instruction: " + custom_instruction.strip()

    clean_window = _sanitize(screen_text)

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": f"WORK_TASK:\n{task.strip()}"},
        {"role": "assistant", "content": "Acknowledged."},
        {"role": "user", "content": f"WINDOW_TEXT:\n{clean_window[:4000]}"},
    ]

    try:
        resp = _chat(messages, code)
        content = (resp.choices[0].message.content or "").strip()
        data = json.loads(content)
        # cost calculation
        prompt_tokens = getattr(resp.usage, "prompt_tokens", 0)
        completion_tokens = getattr(resp.usage, "completion_tokens", 0)
        cost = (prompt_tokens * price_in + completion_tokens * price_out) / 1000
        data["cost_usd"] = round(cost, 6)
        data["model"] = code
        return data
    except Exception:
        return {"relevance": 50, "summary": "(failed)", "hint": "", "cost_usd": 0.0, "model": code}


# ---------------------------------------------------------------------------
# Utility: generate a list of keywords from the task description when the user
# hasn't provided any explicit ones.
# ---------------------------------------------------------------------------


def suggest_keywords(task: str, model_code: str, k: int = 5) -> list[str]:
    """Return up to *k* single-word keywords derived from the task text."""

    if not task.strip():
        return []

    if model_code not in MODEL_INFO:
        model_code = "o4-mini"
    model_name, price_in, price_out = MODEL_INFO[model_code]

    prompt = (
        "Extract the most important SINGLE-WORD keywords (nouns or verbs) that describe the user's task. "
        f"Return at most {k} lowercase words as a JSON array."
    )

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": task[:4000]},
    ]

    try:
        resp = _chat(messages, model_code)
        content = (resp.choices[0].message.content or "").strip()
        words = json.loads(content)
        if isinstance(words, list):
            # basic sanitation
            kw = [w.lower() for w in words if isinstance(w, str) and w.isascii()]
            return kw[:k]
    except Exception:
        pass
    return []
"""LLM helper for Shoulder Buddy.

Requires OPENAI_API_KEY in the environment.
"""
from __future__ import annotations

import os
import json
from typing import Dict, Tuple

import openai
import tiktoken

# Supported models and pricing (USD per 1K tokens, May-2025 preview)
MODEL_INFO: Dict[str, Tuple[str, float, float]] = {
    # code  : (openai_name, price_in, price_out)
    "o4-mini": ("o4-mini", 0.0005, 0.0005),
    "o4-mini-high": ("o4-mini-high", 0.001, 0.001),
    "gpt-4.1": ("gpt-4o-2025-04-15", 0.005, 0.015),
    "gpt-4o": ("gpt-4o-latest", 0.005, 0.015),
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


def _chat(messages, model_code: str, timeout: int = 15):
    if model_code not in MODEL_INFO:
        model_code = "o4-mini"
    model_name, _, _ = MODEL_INFO[model_code]
    return openai.ChatCompletion.create(model=model_name, messages=messages, timeout=timeout)


def _count_tokens(text: str, model_name: str) -> int:
    enc = tiktoken.encoding_for_model(model_name.split(":")[0])
    return len(enc.encode(text))


def evaluate(task: str, screen_text: str, custom_instruction: str | None = None, model_code: str | None = None) -> Dict:
    """Return dict {relevance,int, summary,str, hint,str, cost_usd,float}."""

    code = model_code or DEFAULT_MODEL_CODE
    if code not in MODEL_INFO:
        code = "o4-mini"
    model_name, price_in, price_out = MODEL_INFO[code]

    system_msg = _SYSTEM_TEMPLATE
    if custom_instruction:
        system_msg += "\nAdditional instruction: " + custom_instruction.strip()

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": f"WORK_TASK:\n{task.strip()}"},
        {"role": "assistant", "content": "Acknowledged."},
        {"role": "user", "content": f"WINDOW_TEXT:\n{screen_text[:4000]}"},
    ]

    try:
        resp = _chat(messages, code)
        choice = resp["choices"][0]
        content = choice["message"]["content"].strip()
        data = json.loads(content)
        # cost calculation
        prompt_tokens = resp["usage"]["prompt_tokens"]
        completion_tokens = resp["usage"]["completion_tokens"]
        cost = (prompt_tokens * price_in + completion_tokens * price_out) / 1000
        data["cost_usd"] = round(cost, 6)
        data["model"] = code
        return data
    except Exception:
        return {"relevance": 50, "summary": "(failed)", "hint": "", "cost_usd": 0.0, "model": code}
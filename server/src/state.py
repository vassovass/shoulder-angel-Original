from typing import List
import pickle
from src.types import LLMMessage, GroqMessage


convo_history: List[dict] = []
convo_history_file_path = "convo_history.pkl"


def save_convo():
    """Save convo_history to a pickled file"""
    with open(convo_history_file_path, "wb") as f:
        pickle.dump(convo_history, f)


def load_convo():
    """Load convo_history from a pickled file"""
    global convo_history
    try:
        with open(convo_history_file_path, "rb") as f:
            convo_history = pickle.load(f)
            return convo_history
    except FileNotFoundError:
        return []


def get_convo_history_as_groq():
    """Get the conversation history as Groq-compatible messages."""
    return [
        {
            "role": x["role"] if x["role"] != "bot" else "assistant",
            "content": x["message"],
        }
        for x in convo_history
        if "role" in x
        and "message" in x
        and x["role"] in ["user", "assistant", "system", "bot"]
    ]


def get_convo_history_as_vapi():
    """Get the conversation history as Vapi-compatible messages."""
    return [
        {
            "role": x["role"] if x["role"] != "bot" else "assistant",
            "content": x["message"],
        }
        for x in convo_history
        if "role" in x
        and "message" in x
        and x["role"] in ["user", "assistant", "function", "system", "tool"]
    ]

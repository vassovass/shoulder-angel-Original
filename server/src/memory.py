from mem0 import Memory
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import sqlite3

print(sqlite3.sqlite_version_info)

router = APIRouter()
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
        },
    },
}

m = Memory.from_config(config)


class FunctionArguments(BaseModel):
    category: str
    content: str


class FunctionCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolCall(BaseModel):
    id: str
    type: str
    function: FunctionCall


class Message(BaseModel):
    type: str
    toolCalls: List[ToolCall]


class RequestData(BaseModel):
    message: Message


def get_user_goals() -> str:
    # query Mem0 for goals
    relevant_m = m.search(
        "goals, tasks, and intentions for the day", user_id="samstowers", limit=50
    )

    print(f"relevant_m: {relevant_m}")
    print(f"type of relevant_m: {type(relevant_m)}")

    goal_m = [x for x in relevant_m if x["metadata"]["category"] == "goals"]

    print(f"goals: {goal_m}")

    return str(relevant_m)


@router.post("/add_memory")
async def add_memory(data: RequestData):
    """Add a memory to the user's memory store"""

    if not data.message.toolCalls:
        raise HTTPException(
            status_code=400, detail="No tool calls found in the request"
        )

    tool_call = data.message.toolCalls[0]
    if tool_call.function.name != "add_new_memory":
        raise HTTPException(status_code=400, detail="Unexpected function name")

    try:
        function_args = FunctionArguments(**tool_call.function.arguments)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid arguments structure")

    m.add(
        function_args.content,
        user_id="samstowers",
        metadata={"category": function_args.category},
    )

    return {"status": "success", "message": "Memory added successfully"}


@router.post("/fetch_memories")
async def fetch_memories(data: RequestData):
    """Fetch recent memories from the user's memory store"""

    if not data.message.toolCalls:
        raise HTTPException(
            status_code=400, detail="No tool calls found in the request"
        )

    tool_call = data.message.toolCalls[0]
    if tool_call.function.name != "fetch_recent_memories":
        raise HTTPException(status_code=400, detail="Unexpected function name")

    try:
        function_args = FunctionArguments(**tool_call.function.arguments)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid arguments structure")

    recent_memories = m.search(
        function_args.content,
        user_id="samstowers",
        # limit=function_args.limit if hasattr(function_args, "limit") else 5,
        limit=5,
        # metadata=(
        #     {"category": function_args.category}
        #     if hasattr(function_args, "category")
        #     else None
        # ),
    )

    return {"status": "success", "memories": str(recent_memories)}

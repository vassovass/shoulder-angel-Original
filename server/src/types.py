from pydantic import BaseModel
from typing import List, Dict, Literal, Any


class LLMMessage(BaseModel):
    role: str
    message: str


class GroqMessage(BaseModel):
    role: str
    content: str


# FUNCTION TYPES
class AddMemoryFunctionArgs(BaseModel):
    category: str
    content: str


class FetchMemoriesFunctionArgs(BaseModel):
    category: str
    content: str


#
# VAPI-SPECIFIC TYPES
class VapiFunctionCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class VapiToolCall(BaseModel):
    type: Literal["function-call"]
    id: str
    function: VapiFunctionCall


class ToolCallResult(BaseModel):
    role: Literal["tool_call_result"]
    time: int
    secondsFromStart: float
    name: str
    result: str
    toolCallId: str


class VapiToolCalls(BaseModel):
    toolCalls: List[VapiToolCall]
    role: Literal["tool_calls"]
    message: str
    time: int
    secondsFromStart: float


class VapiMessages(BaseModel):
    List[LLMMessage | VapiToolCalls | ToolCallResult]


class VapiCallEndReport(BaseModel):
    type: Literal["end-of-call-report"]
    endedReason: str
    call: dict
    recordingUrl: str
    summary: str
    transcript: str
    messages: VapiMessages


class VapiEvent(BaseModel):
    message: VapiCallEndReport | VapiToolCall | dict

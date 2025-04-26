from MCPLite.messages.MCPMessage import MCPMessage
from pydantic import BaseModel
from typing import Literal, Any
from uuid import uuid4


class JSONRPCResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: int | str
    result: Any | None = None


class MCPResponse(MCPMessage):
    result: BaseModel | dict | None = None

    def to_json_rpc(self) -> JSONRPCResponse:
        return JSONRPCResponse(
            jsonrpc="2.0",
            id=uuid4().hex,
            result=self.result,
        )


# Prompt
class PromptResponse(MCPResponse):
    class Result(BaseModel):
        class Message(BaseModel):
            class Content(BaseModel):
                type: str
                text: str

            role: str
            content: Content

        description: str
        messages: list[Message]

    result: Result


# Resource
class ResourceResponse(MCPResponse):
    result: dict


# Tool
class ToolResponse(MCPResponse):
    class Result(BaseModel):
        content: list[dict]

    result: Result


MCPResponses = [
    PromptResponse,
    ResourceResponse,
    ToolResponse,
]

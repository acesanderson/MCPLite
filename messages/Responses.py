from MCPMessage import MCPMessage
from pydantic import BaseModel


class MCPResponse(MCPMessage):
    pass


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

    jsonrpc: str
    id: int | str
    result: Result


# Resource
class ResourceResponse(MCPResponse):
    jsonrpc: str
    id: int | str
    result: dict


# Tool
class ToolResponse(MCPResponse):
    class Result(BaseModel):
        content: list[dict]

    jsonrpc: str
    id: int | str
    result: Result


MCPResponses = [
    PromptResponse,
    ResourceResponse,
    ToolResponse,
]

"""
Our message objects, keyed to MCP schema.
"""

from pydantic import BaseModel
from typing import Optional


class MCPMessage(BaseModel):
    pass


# Prompt
class PromptDefinition(MCPMessage):
    class Argument(BaseModel):
        name: str
        description: str
        required: bool

    name: str
    description: str
    arguments: list[Argument]


class PromptRequest(MCPMessage):
    class Params(BaseModel):
        name: str
        arguments: dict

    jsonrpc: str
    id: int
    method: str
    params: Params


class PromptResponse(MCPMessage):
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
    id: int
    result: Result


# Resource
class ResourceDefinition(MCPMessage):
    uri: str
    name: str
    description: str
    mimeType: str
    size: int


class ResourceTemplateDefinition(MCPMessage):
    """
    This is for dynamically generated resources; schema tells LLM how to make the query.
    """

    uriTemplate: str
    name: str
    description: str
    mimeType: str


class ResourceRequest(MCPMessage):
    jsonrpc: str
    id: int
    method: str
    params: dict


class ResourceResponse(MCPMessage):
    jsonrpc: str
    id: int
    result: dict


# Tool
class ToolRequest(MCPMessage):
    jsonrpc: str
    id: int
    method: str
    params: dict


class ToolResponse(MCPMessage):
    class Result(BaseModel):
        content: list[dict]

    jsonrpc: str
    id: int
    result: Result


class ToolDefinition(MCPMessage):
    class InputSchema(BaseModel):
        type: str
        properties: dict

    name: str
    description: str
    inputSchema: InputSchema


MCPMessages = [
    PromptDefinition,
    PromptRequest,
    PromptResponse,
    ResourceDefinition,
    ResourceTemplateDefinition,
    ResourceRequest,
    ResourceResponse,
    ToolRequest,
    ToolResponse,
    ToolDefinition,
]


def parse_message(json_str: str) -> Optional[MCPMessage]:
    """
    Takes an arbitary JSON string; if it matches the schema of the MCPMessage classes, return the object.
    """
    for message in MCPMessages:
        try:
            return message.model_validate_json(json_str)
        except Exception:
            continue
    return None

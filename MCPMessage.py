"""
Our message objects, keyed to MCP schema.
JSONRPC request ids generated here.
"""

from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
import json


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
    id: int | str
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
    id: int | str
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
    id: int | str
    method: str
    params: dict


class ResourceResponse(MCPMessage):
    jsonrpc: str
    id: int | str
    result: dict


# Tool
class ToolRequest(MCPMessage):
    class ToolParams(BaseModel):
        name: str
        arguments: dict

    jsonrpc: str
    id: int | str
    method: str
    params: ToolParams


class ToolResponse(MCPMessage):
    class Result(BaseModel):
        content: list[dict]

    jsonrpc: str
    id: int | str
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

MCPRequests = [
    PromptRequest,
    ResourceRequest,
    ToolRequest,
]


def parse_message(json_dict: dict) -> Optional[MCPMessage]:
    """
    Takes an arbitary JSON string; if it matches the schema of the MCPMessage classes, return the object.
    """
    breakpoint()
    # Add jsonrpc and a uuid to the json_dict if they are not present
    if "jsonrpc" not in json_dict:
        json_dict["jsonrpc"] = "2.0"
    if "id" not in json_dict:
        json_dict["id"] = uuid4().hex
    json_str = json.dumps(json_dict)
    for message in MCPRequests:
        try:
            return message.model_validate_json(json_str)
        except Exception:
            continue
    return None

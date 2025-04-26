"""
Our message objects, keyed to MCP schema.
"""

from pydantic import BaseModel


# Prompt
class PromptDefinition(BaseModel):
    class Argument(BaseModel):
        name: str
        description: str
        required: bool

    name: str
    description: str
    arguments: list[Argument]


class PromptRequest(BaseModel):
    class Params(BaseModel):
        name: str
        arguments: dict

    jsonrpc: str
    id: int
    method: str
    params: Params


class PromptResponse(BaseModel):
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
class ResourceDefinition(BaseModel):
    uri: str
    name: str
    description: str
    mimeType: str
    size: int


class ResourceTemplateDefinition(BaseModel):
    """
    This is for dynamically generated resources; schema tells LLM how to make the query.
    """

    uriTemplate: str
    name: str
    description: str
    mimeType: str


class ResourceRequest(BaseModel):
    jsonrpc: str
    id: int
    method: str
    params: dict


class ResourceResponse(BaseModel):
    jsonrpc: str
    id: int
    result: dict


# Tool
class ToolRequest(BaseModel):
    jsonrpc: str
    id: int
    method: str
    params: dict


class ToolResponse(BaseModel):
    class Result(BaseModel):
        content: list[dict]

    jsonrpc: str
    id: int
    result: Result


class ToolDefinition(BaseModel):
    class InputSchema(BaseModel):
        type: str
        properties: dict

    name: str
    description: str
    inputSchema: InputSchema

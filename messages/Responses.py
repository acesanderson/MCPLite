"""
This captures most rsponses, however note that there are Response types in the initialization for example that import from this script.
"""

from MCPLite.messages.MCPMessage import MCPMessage
from MCPLite.messages.Definitions import (
    ResourceDefinition,
    PromptDefinition,
    ToolDefinition,
)
from pydantic import BaseModel, Field
from typing import Literal, Any, Optional, Union
from uuid import uuid4


# JSON-RPC 2.0 response
class JSONRPCResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: int | str
    result: Any | None = None


# Base class for all MCP responses
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


# List results
class ListPromptsResult(MCPResponse):
    """
    TBD: This isn't right; need hierarchy of classes to be correct (this is not an MCPResponse, this is the result that should be assigned to an MCPResponse).
    The server's response to a prompts/list request from the client.
    """

    prompts: list[PromptDefinition]
    nextCursor: Optional[str] = Field(
        default=None,
        description="An opaque token representing the pagination position after the last returned result.",
    )
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        description="This result property is reserved by the protocol to allow clients and servers to attach additional metadata to their responses.",
        alias="_meta",
    )


class ListResourcesResult(MCPResponse):
    """
    The server's response to a resources/list request from the client.
    """

    resources: list[ResourceDefinition]
    nextCursor: Optional[str] = Field(
        default=None,
        description="An opaque token representing the pagination position after the last returned result.",
    )
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        description="This result property is reserved by the protocol to allow clients and servers to attach additional metadata to their responses.",
        alias="_meta",
    )


class ListToolsResult(MCPResponse):
    """
    The server's response to a tools/list request from the client.
    """

    tools: list[ToolDefinition]
    nextCursor: Optional[str] = Field(
        default=None,
        description="An opaque token representing the pagination position after the last returned result.",
    )
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        description="This result property is reserved by the protocol to allow clients and servers to attach additional metadata to their responses.",
        alias="_meta",
    )


MCPResponses = [
    PromptResponse,
    ResourceResponse,
    ToolResponse,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
]

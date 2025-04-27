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

from typing import Dict, List, Optional, Union, Any, Literal
from pydantic import BaseModel, Field


class Result(BaseModel):
    """
    Base result for all MCP responses.
    """

    _meta: Optional[Dict[str, Any]] = Field(
        None,
        description="This field is reserved by the protocol to allow clients and servers to attach additional metadata",
    )


# Our wrapper class for all Responses.
class JSONRPCResponse(MCPMessage):
    """
    A successful (non-error) response to a request.
    """

    id: Union[str, int]
    jsonrpc: Literal["2.0"] = "2.0"
    result: Result


# Prompts
class Role(str, Enum):
    """Roles in the MCP ecosystem."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ListPromptsResult(Result):
    """
    The server's response to a prompts/list request from the client.
    """

    prompts: List[PromptDefinition]
    nextCursor: Optional[str] = Field(
        None,
        description="An opaque token representing the pagination position after the last returned result",
    )


class PromptMessage(BaseModel):
    """
    A message in a prompt, with content and role.
    """

    role: Role
    content: List[Union[TextContent, ImageContent, EmbeddedResource]]


class GetPromptResult(Result):
    """
    The server's response to a prompts/get request from the client.
    """

    messages: List[Any]
    description: Optional[str] = None


# Resources
class ListResourcesResult(Result):
    """
    The server's response to a resources/list request.
    """

    resources: List[ResourceDefinition]
    nextCursor: Optional[str] = None


class ReadResourceResult(Result):
    """
    The server's response to a resources/read request.
    """

    class ResourceContents(BaseModel):
        """
        The contents of a resource.
        """

        uri: str
        contents: str

    resource: ResourceContents


# TBD: ResourceTemplate related stuff


# Tools
class ListToolsResult(Result):
    """
    The server's response to a tools/list request.
    """

    tools: List[ToolDefinition]
    nextCursor: Optional[str] = None


class CallToolResult(Result):
    """
    The server's response to a tool call.
    """

    content: list[str]
    isError: Optional[bool] = False


MCPResponses = [
    JSONRPCResponse,
    CallToolResult,
    GetPromptResult,
    ReadResourceResult,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
]

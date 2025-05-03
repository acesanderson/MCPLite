"""
This captures most rsponses, however note that there are Response types in the initialization for example that import from this script.
"""

from MCPLite.messages.MCPMessage import MCPMessage
from MCPLite.messages.Requests import Implementation
from MCPLite.messages.Definitions import (
    ResourceDefinition,
    PromptDefinition,
    ToolDefinition,
)
from pydantic import BaseModel, Field
from typing import Literal, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class MCPResult(BaseModel):
    """
    Base result for all MCP responses.
    """

    meta: Optional[dict[str, Any]] = Field(
        None,
        description="This field is reserved by the protocol to allow clients and servers to attach additional metadata",
        alias="_meta",
    )


# Our wrapper class for all Responses.
class JSONRPCResponse(MCPMessage):
    """
    A successful (non-error) response to a request.
    """

    id: Union[str, int]
    jsonrpc: Literal["2.0"] = "2.0"
    result: dict

    def from_json_rpc(
        self,
    ) -> MCPResult:
        """
        Convert this response's result to the appropriate Result object.

        Returns:
            The appropriate Result subclass instance
        """
        # Extract the result data
        result_data = self.result

        # Determine the appropriate result type based on method and/or content
        if isinstance(result_data, dict):
            # Check for fields specific to different result types
            if "serverInfo" in result_data and "protocolVersion" in result_data:
                return InitializeResult(**result_data)

            if "resource" in result_data:
                return ReadResourceResult(**result_data)

            elif "resources" in result_data:
                return ListResourcesResult(**result_data)

            # elif "resourceTemplates" in result_data:
            #     return ListResourceTemplatesResult(**result_data)

            elif "prompts" in result_data:
                return ListPromptsResult(**result_data)

            elif "messages" in result_data:
                return GetPromptResult(**result_data)

            elif "tools" in result_data:
                return ListToolsResult(**result_data)

            elif "content" in result_data and any(
                key in result_data for key in ["isError"]
            ):
                return CallToolResult(**result_data)

            # elif "completion" in result_data:
            #     return CompleteResult(**result_data)

            # elif "roots" in result_data:
            #     return ListRootsResult(**result_data)

        raise ValueError(
            f"Unknown result type: {result_data}. Please check the MCP protocol for updates."
        )


# Content types
class Role(str, Enum):
    """Roles in the MCP ecosystem."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Annotations(BaseModel):
    """Annotations provide metadata for protocol objects."""

    audience: Optional[list[Role]] = None
    priority: Optional[float] = Field(None, ge=0, le=1)


class Annotated(BaseModel):
    """Base for objects that include optional annotations."""

    annotations: Optional[Annotations] = None


class TextContent(Annotated):
    """
    Plain text content.
    """

    type: Literal["text"] = "text"
    text: str


class ImageContent(Annotated):
    """
    Image content.
    """

    type: Literal["image"] = "image"
    data: str = Field(..., description="The base64-encoded image data")
    mimeType: str = Field(..., description="The MIME type of the image")


class BlobResourceContents(BaseModel):
    """
    Binary content of a resource.
    """

    blob: str = Field(
        ..., description="A base64-encoded string representing binary data"
    )
    uri: str = Field(..., description="The URI of the resource")
    mimeType: Optional[str] = Field(
        None, description="The MIME type of this resource, if known"
    )


class TextResourceContents(BaseModel):
    """
    Text content of a resource.
    """

    text: str
    uri: str = Field(..., description="The URI of this resource")
    mimeType: Optional[str] = Field(
        None, description="The MIME type of this resource, if known"
    )


class EmbeddedResource(Annotated):
    """
    The contents of a resource, embedded into a prompt or tool call result.
    """

    type: Literal["resource"] = "resource"
    resource: Union[TextResourceContents, BlobResourceContents]


# Prompts
class ListPromptsResult(MCPResult):
    """
    The server's response to a prompts/list request from the client.
    """

    prompts: list[PromptDefinition]
    nextCursor: Optional[str] = Field(
        None,
        description="An opaque token representing the pagination position after the last returned result",
    )


class PromptMessage(BaseModel):
    """
    A message in a prompt, with content and role.
    """

    role: Role
    content: list[Union[TextContent, ImageContent, EmbeddedResource]]


class GetPromptResult(MCPResult):
    """The server's response to a prompts/get request from the client."""

    messages: list[PromptMessage]  # Changed from Any for type safety
    description: Optional[str] = None  # Changed from PromptMessage


# Resources
class ListResourcesResult(MCPResult):
    """
    The server's response to a resources/list request.
    """

    resources: list[ResourceDefinition]
    nextCursor: Optional[str] = None


class ResourceContents(BaseModel):
    """
    The contents of a resource.
    """

    uri: str
    contents: Union[TextResourceContents, BlobResourceContents]


class ReadResourceResult(MCPResult):
    """
    The server's response to a resources/read request.
    """

    resource: ResourceContents


# TBD: ResourceTemplate related stuff


# Tools
class ListToolsResult(MCPResult):
    """
    The server's response to a tools/list request.
    """

    tools: list[ToolDefinition]
    nextCursor: Optional[str] = None


class CallToolResult(MCPResult):
    """
    The server's response to a tool call.
    """

    content: list[Union[TextContent, ImageContent, EmbeddedResource]]
    isError: Optional[bool] = False


# Initialization Result
class ServerCapabilities(BaseModel):
    """
    Capabilities that a server may support. Known capabilities are defined here, in this schema, but this is not a closed set: any server can define its own, additional capabilities.
    """

    experimental: Optional[dict[str, dict[str, Any]]] = Field(
        default=None,
        description="Experimental, non-standard capabilities that the server supports.",
    )
    logging: Optional[dict[str, Any]] = Field(
        default=None,
        description="Present if the server supports sending log messages to the client.",
    )
    prompts: Optional[dict[str, bool]] = Field(
        default=None, description="Present if the server offers any prompt templates."
    )
    resources: Optional[dict[str, bool]] = Field(
        default=None, description="Present if the server offers any resources to read."
    )
    tools: Optional[dict[str, bool]] = Field(
        default=None, description="Present if the server offers any tools to call."
    )

    class Config:
        extra = "allow"  # Allows additional properties beyond those explicitly defined


class InitializeResult(MCPResult):
    """
    After receiving an initialize request from the client, the server sends this response.
    """

    capabilities: ServerCapabilities
    protocolVersion: str = Field(
        description="The version of the Model Context Protocol that the server wants to use. This may not match the version that the client requested. If the client cannot support this version, it MUST disconnect."
    )
    serverInfo: Implementation  # Using the Implementation class we defined earlier
    instructions: Optional[str] = Field(
        default=None,
        description="Instructions describing how to use the server and its features. This can be used by clients to improve the LLM's understanding of available tools, resources, etc. It can be thought of like a 'hint' to the model. For example, this information MAY be added to the system prompt.",
    )
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        description="This result property is reserved by the protocol to allow clients and servers to attach additional metadata to their responses.",
        alias="_meta",
    )


def minimal_server_initialization() -> InitializeResult:
    """
    Return the most minimal pydantic object that satisfies official schema:
    {
      "capabilities": {},
      "protocolVersion": "1.0.0",
      "serverInfo": {
        "name": "MyMinimalServer",
        "version": "0.1.0"
      }
    }
    """
    server_info = Implementation(name="MyMinimalServer", version="0.1.0")

    # Create minimal capabilities (empty object)
    capabilities = ServerCapabilities(
        prompts={
            "listChanged": True  # Server supports notifications for prompt list changes
        },
        resources={
            "listChanged": True,  # Server supports notifications for resource list changes
            "subscribe": True,  # Server supports subscribing to resource updates
        },
        tools={
            "listChanged": False  # Server doesn't support notifications for tool list changes
        },
    )
    # Create the full result
    result = InitializeResult(
        capabilities=capabilities, protocolVersion="1.0.0", serverInfo=server_info
    )

    # Return the result as a JSON string
    return result


MCPResults = [
    CallToolResult,
    GetPromptResult,
    ReadResourceResult,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
]

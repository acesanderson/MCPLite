from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
from MCPLite.messages import MCPMessage
from uuid import uuid4
import json
from enum import Enum


class Method(str, Enum):
    """
    Request methods are constrained to this list.
    """

    COMPLETION_COMPLETE = "completion/complete"
    INITIALIZE = "initialize"
    LOGGING_SET_LEVEL = "logging/setLevel"
    PING = "ping"
    PROMPTS_GET = "prompts/get"
    PROMPTS_LIST = "prompts/list"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_TEMPLATES_LIST = "resources/templates/list"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"
    ROOTS_LIST = "roots/list"
    SAMPLING_CREATE_MESSAGE = "sampling/createMessage"
    TOOLS_CALL = "tools/call"
    TOOLS_LIST = "tools/list"

    # This ensures the enum serializes to just the string value
    def __str__(self) -> str:
        return self.value

    # This helps with JSON serialization
    def __repr__(self) -> str:
        return repr(self.value)


class JSONRPCRequest(BaseModel):
    """
    JSON-RPC 2.0 request object.
    MCPRequests get blessed to this when it's time for transport.
    We don't worry about the pydantic subclasses (for Params, for example) -- this is just a dict and is created as such from MCPRequest.
    """

    jsonrpc: Literal["2.0"] = "2.0"
    id: int | str
    method: Method
    params: dict | None

    def from_json_rpc(
        self,
    ) -> "MCPRequest":
        """
        Convert this response's result to the appropriate Result object.

        Returns:
            The appropriate Result subclass instance
        """
        json_rpc_dict = self.model_dump()
        _ = json_rpc_dict.pop("jsonrpc")
        _ = json_rpc_dict.pop("id")
        mcprequest_dict = json_rpc_dict
        if mcprequest_dict["method"] in method_map:
            # Find the appropriate class based on the method, and create an instance
            mcprequest_obj = method_map[mcprequest_dict["method"]](**mcprequest_dict)
            return mcprequest_obj
        else:
            raise ValueError(
                f"Method {mcprequest_dict['method']} not found in method_map. Is this in MCP schema?"
            )


class MCPRequest(MCPMessage):
    method: Method
    params: BaseModel | dict | None

    def to_jsonrpc(self) -> JSONRPCRequest:
        """
        Convert this message object to a JSONRPCRequest.
        """
        # Make everything a dict, we shouldn't worry about nested classes here since the ultimate purpose is creating json.
        if self.params and isinstance(self.params, BaseModel):
            params_dict = self.params.model_dump() if self.params else None
        elif self.params:
            params_dict = self.params
        else:
            params_dict = None
        return JSONRPCRequest(
            jsonrpc="2.0",
            id=uuid4().hex,
            method=self.method,
            params=params_dict,
        )


# Some base definitions
class Role(str, Enum):
    """Defines the role of a participant in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


# Resources
class ResourceReference(BaseModel):
    """A reference to a resource."""

    uri: str


class ListResourcesRequestParams(BaseModel):
    """Parameters for listing resources."""

    cursor: Optional[str] = None


class ListResourcesRequest(MCPRequest):
    """Sent from client to request a list of resources the server has."""

    method: Method = Method("resources/list")
    params: Optional[ListResourcesRequestParams] = None


class ReadResourceRequestParams(BaseModel):
    """Parameters for reading a resource."""

    uri: str


class ReadResourceRequest(MCPRequest):
    """Sent from client to request the contents of a resource."""

    method: Method = Method("resources/read")
    params: ReadResourceRequestParams


# Resource Templates
## Resource Templates have a special list Request and Result, but ReadResource is used for both these and the regular resources.
class ListResourceTemplatesRequest(MCPRequest):
    """
    Sent from the client to request a list of resource templates the server has.
    """

    method: Method = Method("resources/templates/list")
    params: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Optional parameters for filtering the list"
    )


# Prompts


class PromptReference(BaseModel):
    """A reference to a prompt."""

    name: str


class ListPromptsRequestParams(BaseModel):
    """Parameters for listing prompts."""

    cursor: Optional[str] = None


class ListPromptsRequest(MCPRequest):
    """Sent from client to request a list of prompts and prompt templates."""

    method: Method = Method("prompts/list")
    params: Optional[ListPromptsRequestParams] = None


class GetPromptRequestParams(BaseModel):
    """Parameters for getting a prompt."""

    name: str
    arguments: Optional[Dict[str, str]] = None


class GetPromptRequest(MCPRequest):
    """Used by the client to get a prompt provided by the server."""

    method: Method = Method("prompts/get")
    params: GetPromptRequestParams


# Tools
class ListToolsRequestParams(BaseModel):
    """Parameters for listing tools."""

    cursor: Optional[str] = None


class ListToolsRequest(MCPRequest):
    """Sent from client to request a list of tools the server has."""

    method: Method = Method("tools/list")
    params: Optional[ListToolsRequestParams] = None


class CallToolRequestParams(BaseModel):
    """Parameters for calling a tool."""

    name: str
    arguments: Optional[Dict[str, Any]] = None


class CallToolRequest(MCPRequest):
    """Used by the client to invoke a tool provided by the server."""

    method: Method = Method("tools/call")
    params: CallToolRequestParams


# Our Initialization request
"""
Initialization messages.
Client sends InitializeRequest as first part of handshake.
Inherits from MCPRequest (and can be blessed to JSONRPCRequest).
"""


class Implementation(BaseModel):
    """
    Describes the name and version of an MCP implementation.
    """

    name: str
    version: str


class Roots(BaseModel):
    listChanged: Optional[bool] = Field(
        default=None,
        description="Whether the client supports notifications for changes to the roots list.",
    )


class ClientCapabilities(BaseModel):
    """
    Capabilities a client may support. Known capabilities are defined here, in this schema, but this is not a closed set: any client can define its own, additional capabilities.
    """

    experimental: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Experimental, non-standard capabilities that the client supports.",
    )
    roots: Optional[Roots] = Field(
        default=None, description="Present if the client supports listing roots."
    )
    sampling: Optional[Dict[str, Any]] = Field(
        default=None, description="Present if the client supports sampling from an LLM."
    )

    class Config:
        extra = "allow"  # Allows additional properties beyond those explicitly defined


class InitializeRequestParams(BaseModel):
    capabilities: ClientCapabilities
    clientInfo: Implementation
    protocolVersion: str = Field(
        description="The latest version of the Model Context Protocol that the client supports. The client MAY decide to support older versions as well."
    )


class InitializeRequest(MCPRequest):
    """
    This request is sent from the client to the server when it first connects, asking it to begin initialization.
    """

    method: Method = Method("initialize")
    params: InitializeRequestParams


def minimal_client_initialization() -> InitializeRequest:
    """
    Return pydantic object that meets the underlying schema:
    {
      "method": "initialize",
      "params": {
        "capabilities": {},
        "clientInfo": {
          "name": "MyMinimalClient",
          "version": "0.1.0"
        },
        "protocolVersion": "1.0.0"
      }
    }
    """
    client_info = Implementation(name="MyMinimalClient", version="0.1.0")

    # Create minimal capabilities (empty object)
    capabilities = ClientCapabilities()

    # Create the request parameters
    params = InitializeRequestParams(
        capabilities=capabilities, clientInfo=client_info, protocolVersion="1.0.0"
    )

    # Create the full request
    request = InitializeRequest(method="initialize", params=params)

    # Return the request as a JSON string
    return request


MCPRequests = [
    CallToolRequest,
    GetPromptRequest,
    ReadResourceRequest,
    ListResourcesRequest,
    ListResourceTemplatesRequest,
    ListPromptsRequest,
    ListToolsRequest,
    InitializeRequest,
]


def parse_request(json_dict: dict) -> Optional[MCPMessage]:
    """
    Takes an arbitary JSON string; if it matches the schema of the MCPMessage classes, return the object.
    """
    # Add jsonrpc and a uuid to the json_dict if they are not present
    json_str = json.dumps(json_dict)
    for message in MCPRequests:
        try:
            return message.model_validate_json(json_str)
        except Exception:
            continue
    return None


method_map = {
    "completion/complete": None,
    "initialize": InitializeRequest,
    "logging/setLevel": None,
    "ping": None,
    "prompts/get": GetPromptRequest,
    "prompts/list": ListPromptsRequest,
    "resources/list": ListResourcesRequest,
    "resources/read": ReadResourceRequest,
    "resources/subscribe": None,
    "resources/templates/list": ListResourceTemplatesRequest,
    "resources/unsubscribe": None,
    "roots/list": None,
    "sampling/createMessage": None,
    "tools/call": CallToolRequest,
    "tools/list": ListToolsRequest,
}

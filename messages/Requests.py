from pydantic import BaseModel, Field, RootModel
from typing import Literal, Optional, Dict, Any
from MCPLite.messages.MCPMessage import MCPMessage
from uuid import uuid4
import json
from enum import Enum


class Method(RootModel):
    """
    A class to represent the method of a request.
    """

    root: Literal[
        "completion/complete",
        "initialize",
        "logging/setLevel",
        "ping",
        "prompts/get",
        "prompts/list",
        "resources/list",
        "resources/read",
        "resources/subscribe",
        "resources/templates/list",
        "resources/unsubscribe",
        "roots/list",
        "sampling/createMessage",
        "tools/call",
        "tools/list",
    ]


class JSONRPCRequest(BaseModel):
    """
    JSON-RPC 2.0 request object.
    MCPRequests get blessed to this when it's time for transport.
    """

    jsonrpc: Literal["2.0"] = "2.0"
    id: int | str
    method: Method
    params: dict | None


class MCPRequest(MCPMessage):
    method: Method
    params: Optional[BaseModel] = Field(
        None,
        description="The parameters for the request. This is a dictionary of key-value pairs.",
    )

    def to_jsonrpc(self) -> JSONRPCRequest:
        """
        Convert this message object to a JSONRPCRequest.
        """
        return JSONRPCRequest(
            jsonrpc="2.0",
            id=uuid4().hex,
            method=self.method,
            params=self.params.model_dump() if self.params else None,
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


MCPRequests = [
    CallToolRequest,
    GetPromptRequest,
    ReadResourceRequest,
    ListResourcesRequest,
    ListPromptsRequest,
    ListToolsRequest,
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

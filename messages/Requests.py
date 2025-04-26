from pydantic import BaseModel, Field, RootModel
from typing import Literal, Optional, Dict, Any
from MCPLite.messages.MCPMessage import MCPMessage
from uuid import uuid4
import json


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


class PromptRequest(MCPRequest):
    class Params(BaseModel):
        name: str
        arguments: dict

    method: str = "prompts/get"
    params: Params


class ResourceRequest(MCPRequest):
    class ResourceParams(BaseModel):
        uri: str

    method: str = "resources/read"
    params: ResourceParams


class ToolRequest(MCPRequest):
    class ToolParams(BaseModel):
        name: str
        arguments: dict

    method: str = "tools/call"
    params: ToolParams


class ListResourcesRequest(MCPRequest):
    """
    Sent from the client to request a list of resources the server has.
    """

    method: str = "resources/list"
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Optional parameters for the request"
    )


class ListPromptsRequest(MCPRequest):
    """
    Sent from the client to request a list of prompts and prompt templates the server has.
    """

    method: str = "prompts/list"
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Optional parameters for the request"
    )


class ListToolsRequest(MCPRequest):
    """
    Sent from the client to request a list of tools the server has.
    """

    method: str = "tools/list"
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Optional parameters for the request"
    )


MCPRequests = [
    PromptRequest,
    ResourceRequest,
    ToolRequest,
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

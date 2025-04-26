from pydantic import BaseModel, Field
from typing import Literal, Optional
from MCPLite.messages.MCPMessage import MCPMessage
from uuid import uuid4
import json


class JSONRPCRequest(BaseModel):
    """
    JSON-RPC 2.0 request object.
    MCPRequests get blessed to this when it's time for transport.
    """

    jsonrpc: Literal["2.0"] = "2.0"
    id: int | str
    method: Literal["resources/read", "tools/call"]
    params: dict | None


class MCPRequest(MCPMessage):
    method: Literal["resources/read", "tools/call"]
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

    method: str
    params: Params


class ResourceRequest(MCPRequest):
    class ResourceParams(BaseModel):
        uri: str

    method: Literal["resources/read"]
    params: ResourceParams


class ToolRequest(MCPRequest):
    class ToolParams(BaseModel):
        name: str
        arguments: dict

    method: Literal["tools/call"]
    params: ToolParams


MCPRequests = [
    PromptRequest,
    ResourceRequest,
    ToolRequest,
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

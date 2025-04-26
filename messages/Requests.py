from pydantic import BaseModel
from typing import Literal, Optional
from MCPMessage import MCPMessage
from uuid import uuid4
import json


class MCPRequest(MCPMessage):
    pass


class PromptRequest(MCPRequest):
    class Params(BaseModel):
        name: str
        arguments: dict

    jsonrpc: str
    id: int | str
    method: str
    params: Params


class ResourceRequest(MCPRequest):
    class ResourceParams(BaseModel):
        uri: str

    jsonrpc: str
    id: int | str
    method: Literal["resources/read"]
    params: ResourceParams


class ToolRequest(MCPRequest):
    class ToolParams(BaseModel):
        name: str
        arguments: dict

    jsonrpc: str
    id: int | str
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

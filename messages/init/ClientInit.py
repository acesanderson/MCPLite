"""
Initialization messages.
Client sends InitializeRequest as first part of handshake.
Inherits from MCPRequest (and can be blessed to JSONRPCRequest).
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from MCPLite.messages.Requests import MCPRequest, Method


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


if __name__ == "__main__":
    i = minimal_client_initialization()
    print(i)
    print(i.model_dump_json(indent=2))

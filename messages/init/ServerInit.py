"""
This is the "InitializeResult" which responds to the Client's first initialize message.
NOTE: Capabilities is literally just a bunch of booleans saying whether the server has Tools, Resources, Prompts, etc.
Default is yes for all.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from MCPLite.messages.init.ClientInit import Implementation
from MCPLite.messages.Responses import MCPResult


class ServerCapabilities(BaseModel):
    """
    Capabilities that a server may support. Known capabilities are defined here, in this schema, but this is not a closed set: any server can define its own, additional capabilities.
    """

    experimental: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Experimental, non-standard capabilities that the server supports.",
    )
    logging: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Present if the server supports sending log messages to the client.",
    )
    prompts: Optional[Dict[str, bool]] = Field(
        default=None, description="Present if the server offers any prompt templates."
    )
    resources: Optional[Dict[str, bool]] = Field(
        default=None, description="Present if the server offers any resources to read."
    )
    tools: Optional[Dict[str, bool]] = Field(
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
    meta: Optional[Dict[str, Any]] = Field(
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


if __name__ == "__main__":
    i = minimal_server_initialization()
    print(i)
    print(i.model_dump_json(indent=2))

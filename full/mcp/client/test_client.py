"""
As I develop the server, this is literally just a script that sends a request to each endpoint.
`main` runs the dummy resource and tools requests.
TBD: clients should be objects that are coupled with specific MCP servers, handling json / transport etc.
Host can have a ClientEnvironment, which combines all resources from individual clients, as handles rendering / parsing of responses, crafts requests that are sent to client
"""

from Chain.mcp.messages.message_classes import (
    PromptDefinition,
    PromptRequest,
    PromptResponse,
    ResourceDefinition,
    ResourceRequest,
    ResourceResponse,
    ToolDefinition,
    ToolRequest,
    ToolResponse,
)
from pydantic import BaseModel
from typing import Optional


def send_json(endpoint: str, message: BaseModel) -> Optional[BaseModel]:
    """
    Send a message to a particular endpoint; transport implementation TBD.
    Returns either a request object or None (if it's a notification).
    """
    pass


## Core Lifecycle Methods
def initialize():
    """
    1. **initialize** - First endpoint called to initialize a connection between client and server. The client sends this request with its protocol version and capabilities. The server responds with its own protocol version and capabilities.
    """
    pass


def initialized():
    """
    2. **initialized** - A notification sent from client to server as an acknowledgment after initialization is complete.
    """
    pass


## Tool-Related Endpoints
"""
3. **notifications/tools/list_changed** - A notification endpoint that servers use to inform clients when the available tools have changed.
"""


def list_tools():
    """
    1. **tools/list** - An endpoint that allows clients to discover and list all available tools provided by the server.
    """
    pass


def tools_call() -> ToolResponse:
    """
    2. **tools/call** - Used to invoke a specific tool on the server, where the server performs the requested operation and returns results.
    """
    endpoint = "tools/list"
    tool_request = ToolRequest()  # What goes in here? (note jsonrpc object)
    tool_response = send_json(endpoint, tool_request)
    return tool_response


## Resource-Related Endpoints
def list_resources():
    """
    1. **resources/list** - Similar to tools/list, this endpoint allows clients to discover available resources.
    """
    pass


def subscribe_resources() -> ResourceResponse:
    """
    2. **resources/get** - Used to retrieve a specific resource from the server.
    """
    endpoint = "resources/get"
    resource_request = ResourceRequest()  # What goes in here?
    resource_response = send_json(endpoint, resource_request)
    return resource_response


def unsubscribe_resources():
    """
    4. **resources/unsubscribe** - Allows clients to unsubscribe from resource updates.
    """
    pass


def notifications_resources_changes():
    """
    5. **notifications/resources/changed** - A notification endpoint that servers use to inform clients when resources have changed.
    """
    pass


## Prompt-Related Endpoints
def list_prompts():
    """
    1. **prompts/list** - Allows clients to discover available prompts.
    """
    pass


def get_prompt():
    """
    2. **prompts/get** - Used to retrieve a specific prompt from the server.
    """
    pass


## Sampling-Related Endpoints
def request_sampling():
    """
    1. **sampling/request** - Allows servers to request that the client perform LLM sampling.
    """
    pass


def return_sampling():
    """
    2. **sampling/result** - Used by clients to return the results of an LLM sampling operation.
    """
    pass


## General Endpoints
def cancel():
    """
    1. **cancel** - Used to cancel an ongoing operation.
    """
    pass


def progress():
    """
    2. **$/progress** - Used to report progress on long-running operations.
    """
    pass


def close():
    """
    3. **close** - Used to terminate the connection cleanly.
    """
    pass


if __name__ == "__main__":
    tools_call()
    subscribe_resources()

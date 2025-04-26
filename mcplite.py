"""
MCPLite - The top-level class that users of your framework interact with. Similar to FastAPI's app = FastAPI(), users would do mcp = MCPLite(). This class would:

- Provide decorators for registering handler functions
- Hold the Server instance
- Provide the .run() method
- Manage configuration options

Server - The internal class that handles routing requests to the appropriate handlers. It would:

- Work with the registered methods
- Use the ServerTransport to receive requests
- Wouldn't be directly exposed to users of your framework
"""

from MCPTool import MCPTool
from MCPResource import MCPResource
from MCPPrompt import MCPPrompt
from MCPRegistry import Registry
from typing import Callable
from pathlib import Path
from Chain import Prompt

dir_path = Path(__file__).resolve().parent
system_prompt_path = dir_path / "mcp_system_prompt.jinja2"


registry: dict = {"tools": [], "resources": [], "prompts": []}


# Initialization functions
def generate_system_prompt():
    """
    Return the capabilities of this MCP implementation.
    This is a simplified version of the MCP capability negotiation.
    Specifically, this renders capabilities as a string for LLMs to use.
    """
    system_prompt = Prompt(system_prompt_path.read_text())
    # Check which capabilities we support based on registered items
    # Later implementation will require an entire initialization handshake, where servers and clients expose capabilities.
    # We want the definitions; we render pydantic Definition as JSON, assign [] if list is empty.
    input_variables = {
        k: [
            primitive.definition.model_dump_json(indent=2)
            for primitive in registry.get(k, [])
        ]
        for k in registry
    }
    rendered = system_prompt.render(input_variables)
    return rendered


# Add these functions to handle MCP protocol operations
def list_tools():
    """
    Return a list of all registered tools with their metadata.
    This corresponds to the MCP 'tool/list' method.
    Adding for MCP spec compliance, though not immediately used.
    """
    tool_list = []
    for item in registry:
        if isinstance(item, MCPTool):
            tool_list.append(
                {
                    "name": item.name,
                    "description": item.description,
                    "parameters": item.parameters_schema,
                }
            )
    return tool_list


def list_resources():
    """
    Return a list of all registered resources with their metadata.
    This corresponds to the MCP 'resource/list' method.
    Adding for MCP spec compliance, though not immediately used.
    """
    resource_list = []
    for item in registry:
        if isinstance(item, MCPResource):
            resource_list.append(
                {
                    "uri": item.uri,
                    "name": item.name,
                    "description": item.description,
                    "mimeType": item.mime_type,
                }
            )
    return resource_list


def list_prompts():
    """
    Return a list of all registered prompts with their metadata.
    This corresponds to the MCP 'prompt/list' method.
    Adding for MCP spec compliance, though not immediately used.
    """
    prompt_list = []
    for item in registry:
        if isinstance(item, Prompt):
            prompt_list.append(
                {
                    "name": item.name,
                    "description": item.description,
                    "parameters": item.parameters_schema,
                }
            )
    return prompt_list


# Client side functions -- (ai slop)
def get_resource(uri):
    """
    Get a resource by URI.
    This corresponds to the MCP 'resource/read' method.
    """
    for item in registry:
        if isinstance(item, Resource) and item.uri == uri:
            return item.read()
    raise ValueError(f"Resource not found: {uri}")


def call_tool(name, arguments):
    """
    Call a tool with the provided arguments.
    This corresponds to the MCP 'tool/call' method.
    """
    for item in registry:
        if isinstance(item, Tool) and item.name == name:
            return item.invoke(**arguments)
    raise ValueError(f"Tool not found: {name}")


def get_prompt(name, arguments=None):
    """
    Get a prompt with the provided arguments.
    This corresponds to the MCP 'prompt/get' method.
    """
    arguments = arguments or {}
    for item in registry:
        if isinstance(item, Prompt) and item.name == name:
            return item.render(**arguments)
    raise ValueError(f"Prompt not found: {name}")


# Our decorators -- for composing the server. Inspired by FastMCP/FastAPI.
def tool(func: Callable) -> Callable:
    """
    Decorator to register a tool.
    Example usage:

    ```python
    @mcp.tool()
    def my_tool(param1: str, param2: int):
        return param1 + str(param2)
    ```
    """
    registry["tools"].append(MCPTool(func))
    return func


def resource(uri: str, mime_type: str = "text/plain", size: int = 1024) -> Callable:
    """
    Decorator to register a resource.
    Example usage:
    ```python
    @mcp.resource(uri="/my-resource", mime_type="text/html")
    def my_resource():
        return "<html>This is my resource.</html>"
    ```
    """

    def decorator(func: Callable) -> Callable:
        registry["resources"].append(MCPResource(func, uri, mime_type, size))
        return func

    return decorator


def prompt(func: Callable) -> Callable:
    """
    Decorator to register a prompt.
    Example usage:

    ```python
    @mcp.prompt
    def my_prompt(param1: str, param2: int):
        return f"Prompt with {param1} and {param2}"
    ```
    """
    registry["prompts"].append(MCPPrompt(func))
    return func


"""
class Server:
    def __init__(self, transport: Transport = DirectServerTransport):
        ""
        Import this if DirectServerTransport; otherwise you will need to app.run() to start the server.
        (for HTTP, stdio, SSE, etc.)
        ""


Usage:
app = MCPLite() 

@app.tool
@app.resource
etc.
"""

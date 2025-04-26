from Tool import Tool, ToolRequest
from Resource import Resource, ResourceRequest
from Prompt import Prompt, PromptRequest
from typing import Callable

registry: list = []
schema_models = [
    ToolRequest,
    ResourceRequest,
    PromptRequest,
]


# Our decorators
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
    registry.append(Tool(func))
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
        registry.append(Resource(func, uri, mime_type, size))
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
    registry.append(Prompt(func))
    return func

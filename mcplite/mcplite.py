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

from MCPLite.primitives import (
    MCPTool,
    MCPResource,
    MCPResourceTemplate,
    MCPPrompt,
    ServerRegistry,
)
from MCPLite.server.Server import Server
from MCPLite.transport import (
    Transport,
    DirectTransport,
    StdioServerTransport,
    SSEServerTransport,
)
from typing import Callable, Optional
from MCPLite.logs.logging_config import get_logger

# Set up logger -- main config handled in mcpchat
logger = get_logger(__name__)
logger.info("Initializing MCPLite application")


class MCPLite:
    """
    The main class for the MCPLite framework.
    This class provides decorators for registering tools, resources, and prompts.
    It also manages the server instance and provides a run method.
    """

    def __init__(self, transport: Optional[Transport | str] = None):
        self.registry = ServerRegistry()
        self.server = Server(self.registry, transport=None)
        if transport == "DirectTransport":
            self.transport = DirectTransport(self.server.process_message)
            self.server.transport = self.transport
        elif isinstance(transport, Transport):
            self.server.transport = transport
        else:
            raise ValueError("Need to provide a Transport class to Server.")

    def run(self):
        """
        Start the server.
        If DirectTransport, just pass since the server is just imported application code.
        If SdtioServerTransport, start the server with the provided transport.
        """
        logger.info("Request made to Server from Client.")
        if self.server.transport is None:
            raise ValueError("Transport is not set. Cannot run the server.")
        elif self.server.transport == "DirectTransport":
            pass
        elif isinstance(self.server.transport, StdioServerTransport):
            # Start the server with the provided transport
            logger.info("Starting the server...")
            self.server.transport.run_server_loop(self.server.process_message)
        elif isinstance(self.server.transport, SSEServerTransport):
            # Start the server with the provided transport
            logger.info("Starting the server...")
            self.server.transport.start()
        else:
            raise ValueError("Invalid transport type. Cannot run the server.")

    # Our decorators -- for composing the server. Inspired by FastMCP/FastAPI.
    def tool(self, func: Callable) -> Callable:
        """
        Decorator to register a tool.
        Example usage:

        ```python
        @mcp.tool()
        def my_tool(param1: str, param2: int):
            return param1 + str(param2)
        ```
        """
        self.registry.tools.append(MCPTool(function=func))
        return func

    def resource(
        self, uri: str, mime_type: str = "text/plain", size: int = 1024
    ) -> Callable:
        """
        Decorator to register a resource or a resource template.

        Example usage for resource:
        ```python
        @mcp.resource(uri="/my-resource", mime_type="text/html")
        def my_resource():
            return "<html>This is my resource.</html>"
        ```

        Example usage for resource template:
        ```python
        @mcp.resource(uri="/my-resource/{param}", mime_type="text/html")
        def my_resource_template(param: str):
            return f"<html>This is my resource with parameter: {param}</html>"
        ```
        """

        def resource_decorator(func: Callable) -> Callable:
            self.registry.resources.append(
                MCPResource(function=func, uri=uri, mimeType=mime_type, size=size)
            )
            return func

        def resource_template_decorator(func: Callable) -> Callable:
            self.registry.resources.append(
                MCPResourceTemplate(function=func, uriTemplate=uri)
            )
            return func

        # Detect curly braces in the URI; if found, treat it as a resource template
        if "{" in uri and "}" in uri:
            # If the URI contains curly braces, treat it as a resource template
            logger.debug("Detected resource template.")
            return resource_template_decorator
        else:
            # Otherwise, treat it as a regular resource
            logger.debug("Detected regular resource.")
            return resource_decorator

    def prompt(self, func: Callable) -> Callable:
        """
        Decorator to register a prompt.
        Example usage:

        ```python
        @mcp.prompt
        def my_prompt(param1: str, param2: int):
            return f"Prompt with {param1} and {param2}"
        ```
        """
        self.registry.prompts.append(MCPPrompt(function=func))
        return func

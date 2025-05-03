"""
This is the meat of the server; all of the routes are defined and executed here.
Inherits the registry so we have access to primitives.
Import the routes dictionaries into the server and use them to route messages.

All of the Nonetypes in these functions below suggest I need to create more Pydantic classes.

First of functions to implement:
- resources/prompts/tools list functions
"""

from MCPLite.messages import *
from MCPLite.messages.init.ServerInit import Implementation, ServerCapabilities
from MCPLite.messages.Responses import (
    TextContent,
    ReadResourceResult,
    ResourceContents,
    TextResourceContents,
)
from MCPLite.primitives import ServerRegistry, MCPTool
from pydantic import ValidationError


class ServerRoute:

    def __init__(self, registry: ServerRegistry):
        self.registry = registry

    def __call__(self, request: MCPRequest) -> MCPResult:
        """
        Call the appropriate route based on the request method.
        Args:
            request (MCPRequest): The request to process.
        Returns:
            MCPMessage: The response to the request.
        """
        print(f"Routing request: {request}")
        # Check if the request is a notification or a request.
        if str(request.method) in self.routes:
            return self.routes[str(request.method)](self, request)
        else:
            raise ValueError(f"Invalid method: {request.method}")

    def initialize(self, request: InitializeRequest) -> InitializeResult:
        """
        Client may have something interesting to tell the server, but for now we just treat this is a ping.
        """
        # Build the initialize result
        server_info = Implementation(name="MyMinimalServer", version="0.1.0")

        # Create minimal capabilities (empty object)
        capabilities = ServerCapabilities(
            prompts={
                "listChanged": False  # Server supports notifications for prompt list changes
            },
            resources={
                "listChanged": False,  # Server supports notifications for resource list changes
                "subscribe": False,  # Server supports subscribing to resource updates
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

    def logging_setLevel(self, request) -> None:
        pass

    def ping(self, request) -> None:
        pass

    def prompts_get(self, request: GetPromptRequest) -> GetPromptResult:
        pass

    def prompts_list(self, request: ListPromptsRequest) -> ListPromptsResult:
        pass

    def resources_list(self, request: ListResourcesRequest) -> ListResourcesResult:
        pass

    def resources_read(self, request: ReadResourceRequest) -> ReadResourceResult | None:
        """
        Read a resource from the registry.
        Args:
            request (ResourceRequest): The request to read the resource.
        Returns:
            tuple[str, ResourceResponse]: The ID and the resource response.

        TBD: MATCH ON URI, NOT NAME
        """

        if len(self.registry.resources) == 0:
            raise ValueError("No resources found in registry.")
        if request.params.uri not in [
            resource.uri for resource in self.registry.resources
        ]:
            raise ValueError(f"Resource {request.params.uri} not found in registry.")
        for resource in self.registry.resources:
            if resource.uri == request.params.uri:
                try:
                    resource_data = resource()
                    contents = TextResourceContents(
                        uri=resource.uri, text=resource_data, mimeType="text/plain"
                    )
                    resource_content = ResourceContents(
                        uri=resource.uri, contents=contents
                    )
                    return ReadResourceResult(_meta=None, resource=resource_content)
                except ValidationError as e:
                    raise ValueError(f"Error reading resource {resource.uri}: {e}")

    def resources_subscribe(self, request) -> None:
        pass

    def resources_templates_list(self, request) -> None:
        pass

    def resources_unsubscribe(self, request) -> None:
        pass

    def roots_list(self, request) -> None:
        pass

    def sampling_createMessage(self, request) -> None:
        pass

    def tools_call(self, request: CallToolRequest) -> CallToolResult:
        """
        Call a tool from the registry.
        Args:
            request (CallToolRequest): The JSONRPC request to convert.
        Returns:
            tuple[str, CallToolResult]: The ID and the tool response.
        """
        print(f"Routed to tools_call route: {request}")
        try:
            tool_name = request.params.name
        except AttributeError:
            raise ValueError("Tool name not found in request parameters.")
        if len(self.registry.tools) == 0:
            raise ValueError("No tools found in registry.")
        if request.params.name not in [tool.name for tool in self.registry.tools]:
            raise ValueError(f"Tool {request.params.name} not found in registry.")
        for tool in self.registry.tools:
            if tool_name == request.params.name:
                request_dict = request.model_dump()
                # Call the tool with the provided arguments
                # TBD: we also have ImageContent and EmbeddedResource besides TextContent; implement later.
                print(
                    f"Calling tool: {tool_name} with arguments: {request_dict['params']['arguments']}"
                )
                tool_response: TextContent = tool(**request_dict["params"]["arguments"])
                content = [tool_response]
                print(f"Returning tool response: CallToolResult + content: {content}")
                return CallToolResult(
                    _meta=None,
                    content=content,
                )
        raise ValueError(f"Tool {tool_name} not found in registry.")

    def tools_list(self, request: ListToolsRequest) -> ListToolsResult:
        pass

    routes = {
        "completion/complete": tools_call,
        "initialize": initialize,
        "logging/setLevel": logging_setLevel,
        "ping": ping,
        "prompts/get": prompts_get,
        "prompts/list": prompts_list,
        "resources/list": resources_list,
        "resources/read": resources_read,
        "resources/subscribe": resources_subscribe,
        "resources/templates/list": resources_templates_list,
        "resources/unsubscribe": resources_unsubscribe,
        "roots/list": roots_list,
        "sampling/createMessage": sampling_createMessage,
        "tools/call": tools_call,
        "tools/list": tools_list,
    }

    # def initialized(self, request: MCPRequest) -> MCPMessage:
    #     pass
    #
    # notification_routes = {
    #     "initialized": initialized,
    # }

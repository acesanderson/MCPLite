"""
This is the meat of the server; all of the routes are defined and executed here.
Inherits the registry so we have access to primitives.
Import the routes dictionaries into the server and use them to route messages.

All of the Nonetypes in these functions below suggest I need to create more Pydantic classes.

First of functions to implement:
- resources/prompts/tools list functions
"""

from MCPLite.messages import *
from MCPLite.messages.Responses import (
    TextContent,
    ReadResourceResult,
    ResourceContents,
    ResourceDefinition,
    TextResourceContents,
    minimal_server_initialization,
)
from MCPLite.messages.Definitions import ToolDefinition
from MCPLite.primitives import ServerRegistry, MCPResource, MCPResourceTemplate
from pydantic import ValidationError

from MCPLite.logs.logging_config import get_logger

# Get logger with this module's name
logger = get_logger(__name__)


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
        logger.info(f"Routing request: {request}")
        # Check if the request is a notification or a request.
        if str(request.method) in self.routes:
            return self.routes[str(request.method)](self, request)
        else:
            raise ValueError(f"Invalid method: {request.method}")

    def initialize(self, request: InitializeRequest) -> InitializeResult:
        """
        Client may have something interesting to tell the server, but for now we just treat this is a ping.
        TBD: Eventually we should be interested about Client capabilities; for now it's just a howdy.
        """
        _ = request
        return minimal_server_initialization()

    def logging_setLevel(self, request) -> None:
        pass

    def ping(self, request) -> None:
        pass

    def prompts_get(self, request: GetPromptRequest) -> GetPromptResult:
        """
        Get a prompt from the registry.

        Args:
            request (GetPromptRequest): The request to get a prompt.
        Returns:
            GetPromptResult: The result containing the prompt.
        """
        logger.info(f"Routed to prompts_get route: {request}")
        try:
            prompt_name = request.params.name
        except AttributeError:
            raise ValueError("Prompt name not found in request parameters.")
        if len(self.registry.prompts) == 0:
            raise ValueError("No prompts found in registry.")
        if request.params.name not in [prompt.name for prompt in self.registry.prompts]:
            raise ValueError(f"Prompt {request.params.name} not found in registry.")
        for prompt in self.registry.prompts:
            if prompt_name == request.params.name:
                request_dict = request.model_dump()
                # Call the tool with the provided arguments
                # TBD: we also have ImageContent and EmbeddedResource besides TextContent; implement later.
                logger.info(
                    f"Getting prompt: {prompt_name} with arguments: {request_dict['params']['arguments']}"
                )
                prompt_response: GetPromptResult = prompt(
                    **request_dict["params"]["arguments"]
                )
                messages = prompt_response
                logger.info(
                    f"Returning prompt response: GetPromptResult + messages: {messages}"
                )
                return prompt_response
        raise ValueError(f"Prompt {prompt_name} not found in registry.")

    def prompts_list(self, request: ListPromptsRequest) -> ListPromptsResult:
        """
        List all prompts in the registry.

        Args:
            request (ListPromptsRequest): The request to list prompts.
        Returns:
            ListPromptsResult: The result containing the list of prompts.
        """
        logger.info(f"Routed to prompts_list route: {request}")
        if len(self.registry.prompts) == 0:
            raise ValueError("No prompts found in registry.")
        prompt_list: list[PromptDefinition] = [
            prompt.definition for prompt in self.registry.prompts
        ]
        logger.info(f"Returning prompt list: {prompt_list}")
        return ListPromptsResult(_meta=None, prompts=prompt_list, nextCursor=None)

    def resources_list(self, request: ListResourcesRequest) -> ListResourcesResult:
        """
        List all resources in the registry.
        Args:
            request (ListResourcesRequest): The request to list resources.
        Returns:
            ListResourcesResult: The result containing the list of resources.
        """
        logger.info(f"Routed to resources_list route: {request}")
        if len(self.registry.resources) == 0:
            raise ValueError("No resources found in registry.")
        if not any(
            [
                isinstance(resource, MCPResource)
                for resource in self.registry.resources
            ]
        ):
            raise ValueError("No resources found in registry.")
         resource_list: list[ResourceDefinition] = [
            resource.definition
            for resource in self.registry.resources
            if isinstance(resource, MCPResource)
        ]
        logger.info(f"Returning resource list: {resource_list}")
        return ListResourcesResult(_meta=None, resources=resource_list)

    def resources_templates_list(self, request) -> ListResourceTemplatesResult:
        """
        List all resource templates in the registry.
        """
        logger.info(f"Routed to resources_templates_list route: {request}")
        if len(self.registry.resources) == 0:
            raise ValueError("No resources found in registry.")
        if not any(
            [
                isinstance(resource, MCPResourceTemplate)
                for resource in self.registry.resources
            ]
        ):
            raise ValueError("No resource templates found in registry.")
        resource_template_list: list[ResourceTemplateDefinition] = [
            resource.definition
            for resource in self.registry.resources
            if isinstance(resource, MCPResourceTemplate)
        ]
        logger.info(f"Returning resource template list: {resource_template_list}")
        return ListResourceTemplatesResult(_meta=None, resourceTemplates=resource_template_list)


    def resources_read(self, request: ReadResourceRequest) -> ReadResourceResult | None:
        """
        Read a resource from the registry. Note: this handles both resources and templates.
        Args:
            request (ResourceRequest): The request to read the resource.
        Returns:
            tuple[str, ResourceResponse]: The ID and the resource response.
        """
        logger.info(f"Routed to resources_read route: {request}")
        if len(self.registry.resources) == 0:
            raise ValueError("No resources found in registry.")
        if request.params.uri not in [
            resource.uri for resource in self.registry.resources
        ]:
            raise ValueError(f"Resource {request.params.uri} not found in registry.")
        for resource in self.registry.resources:
            if resource.uri == request.params.uri:
                try:
                    logger.info("Reading resource: {resource.uri}")
                    resource_data = resource()
                    contents = TextResourceContents(
                        uri=resource.uri, text=resource_data, mimeType="text/plain"
                    )
                    resource_content = ResourceContents(
                        uri=resource.uri, contents=contents
                    )
                    logger.info(f"Returning resource content: {resource_content}")
                    return ReadResourceResult(_meta=None, resource=resource_content)
                except ValidationError as e:
                    raise ValueError(f"Error reading resource {resource.uri}: {e}")

    def resources_subscribe(self, request) -> None:
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
        logger.info(f"Routed to tools_call route: {request}")
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
                logger.info(
                    f"Calling tool: {tool_name} with arguments: {request_dict['params']['arguments']}"
                )
                tool_response: TextContent = tool(**request_dict["params"]["arguments"])
                content = [tool_response]
                logger.info(
                    f"Returning tool response: CallToolResult + content: {content}"
                )
                return CallToolResult(
                    _meta=None,
                    content=content,
                )
        raise ValueError(f"Tool {tool_name} not found in registry.")

    def tools_list(self, request: ListToolsRequest) -> ListToolsResult:
        """
        List all tools in the registry.
        Args:
            request (ListToolsRequest): The request to list tools.
        Returns:
            ListToolsResult: The result containing the list of tools.
        """
        logger.info(f"Routed to tools_list route: {request}")
        if len(self.registry.tools) == 0:
            raise ValueError("No tools found in registry.")
        tool_list: list[ToolDefinition] = [
            tool.definition for tool in self.registry.tools
        ]
        logger.info(f"Returning tool list: {tool_list}")
        return ListToolsResult(_meta=None, tools=tool_list)

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

from MCPLite.messages import (
    MCPRequest,
    InitializeRequest,
    InitializeResult,
    InitializedNotification,
    ListPromptsRequest,
    ListPromptsResult,
    ListToolsRequest,
    ListToolsResult,
    ListResourcesResult,
    ListResourcesRequest,
    ListResourceTemplatesRequest,
    ListResourceTemplatesResult,
    JSONRPCResponse,
    MCPResult,
    minimal_client_initialization,
    MCPNotification,
)
from MCPLite.logs.logging_config import get_logger
from MCPLite.primitives.MCPRegistry import ClientRegistry
from MCPLite.transport import DirectTransport, Transport, StdioClientTransport
from MCPLite.inventory.ServerInfo import ServerInfo
import json
from typing import Optional, Callable

# Get logger with this module's name
logger = get_logger(__name__)


class Client:
    def __init__(
        self,
        name: str = "Generic Client",
        transport: str | Transport | StdioClientTransport = "DirectTransport",
        server_function: Optional[Callable] = None,
    ):
        """
        Initialize the client.
        """
        self.name = name
        self.registry = ClientRegistry()
        self.transport = transport
        self.server_function = server_function
        # Currently, the only transport is DirectTransport.
        if self.transport == "DirectTransport" and server_function is None:
            raise ValueError(
                "DirectTransport requires a server_function to be provided."
            )
        if self.transport == "DirectTransport":
            self.transport = DirectTransport(self.server_function)  # type: ignore
        if isinstance(self.transport, StdioClientTransport):
            self.transport.start()
        self.initialized: bool = False

    def initialize(self):
        """
        Initialize the client.
        """
        logger.info("Client initializing")
        # Send the InitializeRequest to the server, receive the InitializeResponse, and update the registry.
        initialize_request: InitializeRequest = minimal_client_initialization()
        logger.info("Client sending InitializeRequest")
        initialize_result: InitializeResult = self.send_request(
            initialize_request
        )  # type:ignore
        if isinstance(initialize_result, InitializeResult):
            self.initialized = True
        logger.info("Client received InitializeResult")
        capabilities = initialize_result.capabilities
        # if capabilities.prompts:
        # prompts = self.send_request(ListPromptsRequest())
        # self.registry.prompts = prompts
        if capabilities.resources:
            # Resources have two parts: templates and resources. First, resources:
            logger.info("Client sending ListResourcesRequest")
            list_resources_request = ListResourcesRequest()
            list_resources_result: ListResourcesResult = self.send_request(  # type: ignore
                list_resources_request
            )
            logger.info("Client received ListResourcesResult")
            self.registry.resources += list_resources_result.resources
            logger.info("Client updated registry with resources")
            # Now, templates:
            logger.info("Client sending ListResourcesTemplateRequest")
            list_resource_templates_request = ListResourceTemplatesRequest()
            list_resources_templates_result: ListResourceTemplatesResult = (  # type: ignore
                self.send_request(list_resource_templates_request)
            )
            logger.info("Client received ListResourcesTemplateResult")
            self.registry.resources += list_resources_templates_result.resourceTemplates
        if capabilities.tools:
            logger.info("Client sending ListToolsRequest")
            list_tools_request = ListToolsRequest()
            list_tools_results: ListToolsResult = self.send_request(list_tools_request)  # type: ignore
            logger.info("Client received ListResourcesResult")
            self.registry.tools += list_tools_results.tools
            logger.info("Client updated registry with resources")
        if capabilities.prompts:
            logger.info("Client sending ListPromptsRequest")
            list_prompts_request = ListPromptsRequest()
            list_prompts_result: ListPromptsResult = self.send_request(  # type: ignore
                list_prompts_request
            )
            logger.info("Client received ListPromptsResult")
            self.registry.prompts += list_prompts_result.prompts
            logger.info("Client updated registry with prompts")
        # Send a notification to the server that the client is initialized.
        initialized_notification = InitializedNotification()
        logger.info("Client sending InitializedNotification")
        self.send_notification(initialized_notification)

    def send_request(self, request: MCPRequest) -> MCPResult:
        """
        Send a request to the server.
        """
        # Validate pydantic object matches the client/server schema.
        # Convert to JSON.
        jsonrpc_request = request.to_jsonrpc()
        json_str = jsonrpc_request.model_dump_json()
        logger.info("Client sending JSON-RPC request through transport")
        json_response = self.transport.send_json_message(json_str)  # type: ignore
        logger.info(
            f"Client received JSON-RPC response from transport: {json_response}"
        )
        json_obj = json.loads(json_response)
        try:
            logger.info(f"Client parsing JSON-RPC response: {json_obj}")
            jsonrpc_response = JSONRPCResponse(**json_obj)
            logger.info(
                f"Client converting JSON-RPC response to MCPResult object: {jsonrpc_response}"
            )
            mcp_result = jsonrpc_response.from_json_rpc()
            logger.info(
                f"Client converted JSON-RPC response to MCPResult object: {mcp_result}"
            )
            return mcp_result
        except ValueError as e:
            raise ValueError(f"Invalid JSON-RPC response from server: {e}")

    def send_notification(self, notification: MCPNotification):
        """
        Send a notification to the server.
        """
        # Validate pydantic object matches the client/server schema.
        # Convert to JSON.
        jsonrpc_notification = notification.to_json_rpc()
        json_str = jsonrpc_notification.model_dump_json()
        logger.info("Client sending JSON-RPC notification through transport")
        self.transport.send_json_message(json_str)  # type: ignore

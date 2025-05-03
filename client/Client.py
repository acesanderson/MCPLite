from MCPLite.messages.Requests import MCPRequest
from MCPLite.messages import (
    InitializeRequest,
    InitializeResult,
    ListPromptsRequest,
    ListToolsRequest,
    ListToolsResult,
    ListResourcesResult,
    ListResourcesRequest,
    JSONRPCResponse,
    JSONRPCRequest,
    MCPResult,
    minimal_client_initialization,
)
from MCPLite.logs.logging_config import get_logger
from MCPLite.primitives.MCPRegistry import ClientRegistry
from MCPLite.transport.Transport import DirectTransport
import json
from typing import Optional, Callable

# Get logger with this module's name
logger = get_logger(__name__)


class Client:
    def __init__(
        self,
        transport: str = "DirectTransport",
        server_function: Optional[Callable] = None,
    ):
        """
        Initialize the client.
        """
        self.registry = ClientRegistry()
        self.transport = transport
        self.server_function = server_function
        # Currently, the only transport is DirectTransport.
        if self.transport == "DirectTransport" and server_function is None:
            raise ValueError(
                "DirectTransport requires a server_function to be provided."
            )
        if self.transport == "DirectTransport":
            self.transport = DirectTransport(self.server_function)
        self.initialized: bool = False

    def initialize(self):
        """
        Initialize the client.
        """
        logger.info("Client initializing")
        # Send the InitializeRequest to the server, receive the InitializeResponse, and update the registry.
        initialize_request: InitializeRequest = minimal_client_initialization()
        logger.info("Client sending InitializeRequest")
        initialize_result: InitializeResult = self.send_request(initialize_request)
        if isinstance(initialize_result, InitializeResult):
            self.initialized = True
        logger.info("Client received InitializeResult")
        capabilities = initialize_result.capabilities
        # if capabilities.prompts:
        # prompts = self.send_request(ListPromptsRequest())
        # self.registry.prompts = prompts
        if capabilities.resources:
            logger.info("Client sending ListResourcesRequest")
            list_resources_request = ListResourcesRequest()
            list_resources_result: ListResourcesResult = self.send_request(
                list_resources_request
            )
            logger.info("Client received ListResourcesResult")
            self.registry.resources = list_resources_result.resources
            logger.info("Client updated registry with resources")
        if capabilities.tools:
            logger.info("Client sending ListToolsRequest")
            list_tools_request = ListToolsRequest()
            list_tools_results: ListToolsResult = self.send_request(list_tools_request)
            logger.info("Client received ListResourcesResult")
            self.registry.tools = list_tools_results.tools
            logger.info("Client updated registry with resources")
            print(self.registry)

    def send_request(self, request: MCPRequest) -> MCPResult:
        """
        Send a request to the server.
        """
        # Validate pydantic object matches the client/server schema.
        # Convert to JSON.
        jsonrpc_request = request.to_jsonrpc()
        json_str = jsonrpc_request.model_dump_json()
        print("Client sending JSON-RPC request through transport")
        json_response = self.transport.send_json(json_str)
        print(f"Client received JSON-RPC response from transport: {json_response}")
        json_obj = json.loads(json_response)
        try:
            print(f"Client parsing JSON-RPC response: {json_obj}")
            jsonrpc_response = JSONRPCResponse(**json_obj)
            print(
                f"Client converting JSON-RPC response to MCPResult object: {jsonrpc_response}"
            )
            mcp_result = jsonrpc_response.from_json_rpc()
            print(
                f"Client converted JSON-RPC response to MCPResult object: {mcp_result}"
            )
            return mcp_result
        except ValueError as e:
            raise ValueError(f"Invalid JSON-RPC response from server: {e}")
        # Convert JSONRPCResponse to the appropriate MCPResponse.

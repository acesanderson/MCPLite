"""
This takes the registry from mcplite.py.
This is the server class that will handle incoming requests and route them to the appropriate primitives. It handles all of the application logic as well (since the primitives are in the registry). Dependency injection pattern.
"""

from pydantic import Json
from typing import Optional
from MCPLite.messages import (
    MCPRequest,
    JSONRPCRequest,
    MCPResult,
    JSONRPCResponse,
    MCPNotification,
    JSONRPCNotification,
)
from MCPLite.primitives import ServerRegistry
from MCPLite.transport.Transport import Transport
from MCPLite.routes.ServerRoutes import ServerRoute
import json
from datetime import datetime

from MCPLite.logs.logging_config import get_logger

# Get logger with this module's name
logger = get_logger(__name__)


class Server:
    # Map method names to their corresponding handling functions.
    def __init__(self, registry: ServerRegistry, transport: Optional[Transport] = None):
        self.registry = registry
        self.transport = transport
        self.route = ServerRoute(self)
        self.initialized: bool = False
        self.initialization_time: Optional[float] = None
        self.client_info: Optional[dict] = None

    def process_message(
        self,
        json_str: Json,
    ) -> Json:
        """
        Receive JSON from the client, parse it, and return a response.
        """
        # Validate the JSON against our pydantic objects.
        # Process the request and return a response.
        logger.info(f"Server received JSON: {json_str}")
        json_obj = json.loads(json_str)
        if "method" in json_obj:
            # This is a JSON-RPC request.
            # Validate the request.
            try:
                if JSONRPCRequest.model_validate(json_obj):
                    logger.info("Valid JSON-RPC request, processing...")
                    response: Json = self._process_request(json_obj)
                    return response
            except:
                pass
            try:
                if JSONRPCNotification.model_validate(json_obj):
                    logger.info("Valid JSON-RPC notification, processing...")
                    self._process_notification(json_obj)
                    return json_obj
            except:
                pass
        raise ValueError("Invalid JSON-RPC request or notification")

    def _process_request(self, json_obj: dict) -> Json:
        # Process the request.
        json_rpc_request = JSONRPCRequest(**json_obj)
        mcp_request = json_rpc_request.from_json_rpc()
        logger.info(f"Routing request: {mcp_request}")
        response: MCPResult = self.route(mcp_request)
        # Convert the response to JSON-RPC format.
        # TBD: Implement actual indexing.
        json_rpc_response = JSONRPCResponse(
            id="blah", jsonrpc="2.0", result=response.model_dump()
        )
        logger.info(f"Server sending JSON-RPC response: {json_rpc_response}")
        return json_rpc_response.model_dump_json()

    def _process_notification(self, json_obj: dict) -> None:
        # Process the notification.
        json_rpc_notification = JSONRPCNotification(**json_obj)
        mcp_notification = json_rpc_notification.from_json_rpc()
        logger.info(f"Routing notification: {mcp_notification}")
        self.route(mcp_notification)

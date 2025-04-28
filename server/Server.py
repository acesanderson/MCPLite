"""
This takes the registry from mcplite.py.
This is the server class that will handle incoming requests and route them to the appropriate primitives. It handles all of the application logic as well (since the primitives are in the registry). Dependency injection pattern.
"""

from pydantic import Json
from typing import Optional
from MCPLite.messages import (
    MCPMessage,
    MCPRequest,
    JSONRPCRequest,
)
from MCPLite.primitives import ServerRegistry
from MCPLite.transport.Transport import Transport
from MCPLite.routes.ServerRoutes import ServerRoute
import json


class Server:
    # Map method names to their corresponding handling functions.
    def __init__(self, registry: ServerRegistry, transport: Optional[Transport] = None):
        self.registry = registry
        self.transport = transport
        self.route = ServerRoute(self.registry)

    def initialize(self, json_string: str):
        """
        Initialize the server.
        """
        # Send the server's registry to the client per MCP handshake.
        # For MVP, client will just grab the registry from the class :)
        pass

    def process_message(
        self,
        json_str: Json,
    ) -> Json:
        """
        Receive JSON from the client, parse it, and return a response.
        """
        # Validate the JSON against our pydantic objects.
        # Process the request and return a response.
        json_obj = json.loads(json_str)
        if "method" in json_obj:
            # This is a JSON-RPC request.
            # Validate the request.
            if not JSONRPCRequest.model_validate(json_obj):
                raise ValueError(
                    "Invalid JSON-RPC request, despite presence of 'method' key."
                )
            # Process the request.
            json_rpc_request = JSONRPCRequest(**json_obj)
            mcp_request = json_rpc_request.from_json_rpc()
            response = self.route_request(mcp_request)
            return response.model_dump_json()

    def route_request(self, request: MCPRequest) -> MCPMessage:
        """
        Route the request to the appropriate handler.
        """
        return self.route(request)

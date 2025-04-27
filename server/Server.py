"""
This takes the registry from mcplite.py.
This is the server class that will handle incoming requests and route them to the appropriate primitives. It handles all of the application logic as well (since the primitives are in the registry). Dependency injection pattern.
"""

from pydantic import Json
from typing import Optional
from MCPLite.messages.MCPMessage import MCPMessage
from MCPLite.messages.Requests import MCPRequest, JSONRPCRequest
from MCPLite.primitives.MCPRegistry import ServerRegistry
from MCPLite.transport.Transport import Transport
from MCPLite.server.Routes import Route
import json


class Server:
    # Map method names to their corresponding handling functions.
    def __init__(self, registry: ServerRegistry, transport: Optional[Transport] = None):
        self.registry = registry
        self.transport = transport
        self.route = Route(self.registry)

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
        The various requests:
        - [ ] clientinit
        - [ ] initialize
        - [ ] list prompts
        - [ ] list resources
        - [ ] list tools
        - [ ] tool request
        - [ ] prompt request
        - [ ] resource request

        Let's start with a tool call, then a resource call.
        This receives JSON, sends message to MCPLite.
        """
        # Validate the JSON against our pydantic objects.
        # Process the request and return a response.
        # For MVP, client will just run this method and get the json string back.
        json_obj = json.loads(json_str)
        if "method" in json_obj:
            # This is a JSON-RPC request.
            # Validate the request.
            if not JSONRPCRequest.model_validate(json_obj):
                raise ValueError(
                    "Invalid JSON-RPC request, despite presence of 'method' key."
                )
            # Process the request.
            if json_obj["method"] not in self.requests_routes:
                raise ValueError(
                    f"Invalid method: {json_obj['method']}. Valid methods are: {list(self.requests_routes.keys())}"
                )
            response = self.route_request(MCPRequest(**json_obj))
        # TBD: DETECT NOTIFICATIONS

    def route_request(self, request: MCPRequest) -> MCPMessage:
        """
        Route the request to the appropriate handler.
        """
        return self.route(request)


def tools_call(request: MCPRequest) -> MCPMessage:
    """
    Handle a tool call request.
    """
    # This is where we would call the tool with the request parameters.
    # For MVP, we'll just return a dummy response.
    return MCPMessage(
        id=request.id,
        method=request.method,
        params={"result": "Tool called successfully"},
    )

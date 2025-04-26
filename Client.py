from Chain.mcp.MCPMessage import MCPMessage
from Chain.mcp.Server import Server
from Chain.mcp.MCPRegistry import Registry

# from Chain.mcp.Transport import ClientTransport
from typing import Optional
import json


class Client:
    def __init__(self, server: Server):
        self.server: Server = Server()
        self.registry = Registry()
        # self.transport = ----- we can use DirectClientTransport as a dummy transport.

    def initialize(self):
        """
        Initialize the client.
        """
        # Validate that we've received JSON, and that the JSON matches the MCP schema for list_definitions.
        # Create tool, resource, prompt objects from the JSON received from the server.
        # Add the tools, resources, prompts to the registry.
        self.registry = (
            self.server.registry
        )  # purpose: this mocks network calll; we call this 'DirectClientTransport'
        pass

    def send_request(self, request: MCPMessage) -> Optional[MCPMessage]:
        """
        Send a request to the server.
        """
        # Validate pydantic object matches the client/server schema.
        # Convert to JSON.
        json_str = request.model_dump_json()
        # Send to the server.
        # If the server responds, parse the response and return it to the client as pydantic object.
        server_response_in_json = server.return_answer(json_str)
        # Convert to pydantic object.
        server_response_dict = json.loads(server_response_in_json)
        server_response_pydantic = ToolResponse(**server_response_dict)
        return server_response_pydantic

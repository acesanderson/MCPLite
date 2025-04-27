from MCPLite.messages.Requests import MCPRequest
from MCPLite.primitives.MCPRegistry import ClientRegistry
from MCPLite.transport.Transport import Transport, DirectTransport
from MCPLite.server.Server import Server

# from Chain.mcp.Transport import ClientTransport
from typing import Optional
import json


class Client:
    def __init__(self, transport: Transport):
        self.registry = ClientRegistry()
        self.transport = transport
        # self.transport = ----- we can use DirectClientTransport as a dummy transport.

    def initialize(self):
        """
        Initialize the client.
        """
        # Validate that we've received JSON, and that the JSON matches the MCP schema for list_definitions.
        # Create tool, resource, prompt objects from the JSON received from the server.
        # Add the tools, resources, prompts to the registry.
        # self.registry = (
        #     self.server.registry
        # )  # purpose: this mocks network calll; we call this 'DirectClientTransport'
        pass

    def send_request(self, request: MCPRequest) -> Optional[MCPRequest]:
        """
        Send a request to the server.
        """
        # Validate pydantic object matches the client/server schema.
        # Convert to JSON.
        jsonrpc_request = request.to_jsonrpc()
        json_str = jsonrpc_request.model_dump_json()
        self.transport.send_json(json_str)


if __name__ == "__main__":
    server = Server()
    transport = DirectTransport(server.process_message)

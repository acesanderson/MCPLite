"""
Building a minimal viable product (MVP) for the MCP protocol.
Working from the bottom of up:
    - object declarations
    - initializations
    - request/response

Protocol/Transport layers are not implemented, and this mocks the network call.
Here the client literally just calls the server's methods directly. What's important is that we use jsonrpc.
"""

from MCPMessage import (
    PromptRequest,
    PromptResponse,
    PromptDefinition,
    ResourceRequest,
    ResourceResponse,
    ResourceDefinition,
    ResourceTemplateDefinition,
    ToolRequest,
    ToolResponse,
    ToolDefinition,
)
from typing import Optional
from pydantic import BaseModel
import mcplite
import json


class Host:
    def __init__(self, llm_request: str):
        self.llm_request = llm_request
        self.client_environment = ClientEnvironment()

    # validate json and then send to ClientEnvironment.
    # this is streaming/parsing logic that matches json within the answer to general MCP schema.
    # if general MCP schema hit, send the json to ClientEnvironment.


class Server:
    def __init__(self):
        self.registry = Registry()

    def initialize(self, json: str):
        """
        Initialize the server.
        """
        # Send the server's registry to the client per MCP handshake.
        # For MVP, client will just grab the registry from the class :)
        pass

    def return_answer(
        self,
        json_str: str,
    ) -> str:
        """
        Receive JSON from the client, parse it, and return a response.
        """
        # Validate the JSON against our pydantic objects.
        # Process the request and return a response.
        # For MVP, client will just run this method and get the json string back.


class Client:
    def __init__(self, server: Server):
        self.server: Server = Server()
        self.registry = Registry()

    def initialize(self):
        """
        Initialize the client.
        """
        # Validate that we've received JSON, and that the JSON matches the MCP schema for list_definitions.
        # Create tool, resource, prompt objects from the JSON received from the server.
        # Add the tools, resources, prompts to the registry.
        self.registry = server.registry  # purpose: this mocks network call
        pass

    def send_request(
        self, request: ToolRequest | ResourceRequest | PromptRequest
    ) -> ToolResponse | ResourceResponse | PromptResponse | None:
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


class ClientEnvironment:
    def __init__(self):
        self.registry = Registry()
        self.clients: list[Optional[Client]] = []

    def add_client(self, client: Client):
        self.clients.append(client)
        self.registry += client.registry

    def route_request(self, json: str):
        """
        Receive JSON from the host, parse it, and route it to the appropriate client.
        """
        # Validate that we've received JSON, and that the JSON matches the MCP schema.
        # Then determine if it's a tool, resource, or prompt.
        # Convert to pydantic object.
        # if pydantic object in client.registry, send to client.
        pass

    def render_for_llm(self, message: MCPMessage):
        """
        Render the response for the LLM.
        """
        # Convert the pydantic object to JSON.
        json_message = message.model_dump_json(indent=2)
        # Convert the message to a string and send it to the LLM.
        # For MVP, just print it out.
        print(json_message)


if __name__ == "__main__":
    # Table setting
    ## Dummy data
    example_request = """
{
  "method": "tools/call",
  "name": "add",
  "arguments": {
    "a": 9801,
    "b": 1444
  }
}
"""

    # Dummy tool
    @mcplite.tool
    def add(a: int, b: int) -> int:
        """
        Add two numbers.
        """
        return a + b

    # The objects that will be working together
    tool = mcplite.registry["tools"][0]
    host = Host(example_request)
    host.client_environment = ClientEnvironment()
    server = Server()
    server.registry.tools.append(tool)
    # Initialization
    client = Client(server)
    client.initialize()
    # Mock network call for request
    json_obj = json.loads(example_request)
    example_request_pydantic = ToolRequest(**json_obj)
    answer_json = client.send_request(example_request_pydantic)
    answer_dict = answer_json.model_dump()
    answer_pydantic = ToolResponse(**answer_dict)
    host.client_environment.render_for_llm(answer_pydantic)
    # client environment

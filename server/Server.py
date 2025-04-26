"""
See notes in mcplite.py to see the distinction between Server and MCPLite classes.
This should mirror the Client class.
"""

from pydantic import Json
from MCPLite.transport.Transport import Transport, DirectTransport


class Server:
    def __init__(self, transport: Transport = "direct transport"):
        self.transport = transport

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
        # For MVP, client will just run this method and get the json string back.

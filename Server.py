"""
See notes in mcplite.py to see the distinction between Server and MCPLite classes.
This should mirror the Client class.
"""

from Chain.mcp.MCPRegistry import Registry


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

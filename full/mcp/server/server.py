"""
Our basic server implementation.
Use uvicorn.
"""

from typing import Optional, Literal
from MCP import registry
from MCP import Tool, Resource, Prompt


class Server:
    def __init__(
        self, transport: Literal["http", "sse", "stdio"], port: Optional[int] = 8000
    ):
        self.transport = transport
        self.port = port

    def process_input(self, input_data: str):
        # Process the input data here
        # For example, you can parse the JSON-RPC request and call the appropriate tool

        pass

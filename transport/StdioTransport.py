"""
Our first 
"""

from typing import Callable
from pydantic import Json
from MCPLite.transport.Transport import Transport
from MCPLite.logs.logging_config import get_logger

# Get logger with this module's name
logger = get_logger(__name__)


class StdioClientTransport(Transport):
    """
    Client spawns and manages server processes, communicating with them via stdio.
    """

    def __init__(self, server_command: list[str]):
        """
        Initialize the transport with the command to start the server.
        """
        self.server_command = server_command
        self.process = None

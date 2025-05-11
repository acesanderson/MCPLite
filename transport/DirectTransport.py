"""
Our dummy Transport class that sends JSON strings directly to a server function.
No client/server separation, just a direct call to the server function.
"""

from typing import Callable
from pydantic import Json
from MCPLite.transport.Transport import Transport
from MCPLite.logs.logging_config import get_logger

# Get logger with this module's name
logger = get_logger(__name__)


class DirectTransport(Transport):
    """
    Direct transport that sends JSON strings directly to a server function.
    Base implementation before we add other transports like HTTP, SSE, stdio
    """

    def start(self):
        pass

    def stop(self):
        pass

    def __init__(self, server_function: Callable):
        self.server_function = server_function

    def send_json_message(self, json_str: str) -> Json:
        # Directly send the JSON string, returning the response
        logger.info(f"Sending JSON from transport to server: {json_str}")
        json_response = self.server_function(json_str)
        if json_response:
            logger.info(
                f"Transport received JSON response from server: {json_response}; returning to client."
            )
            return json_response
        else:
            logger.info(
                f"Transport received no JSON response from server, likely because this was a Notification; returning None."
            )
            return None

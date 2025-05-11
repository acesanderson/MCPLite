"""
ABC and derivative classes for transport layer.
"""

from abc import ABC, abstractmethod
from pydantic import Json
from typing import Optional

from MCPLite.logs.logging_config import get_logger

# Get logger with this module's name
logger = get_logger(__name__)


class Transport(ABC):
    @abstractmethod
    def start(self):
        """
        Start the transport layer. This method should be called to initialize the transport.
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Stop the transport layer. This method should be called to clean up the transport.
        """
        pass

    @abstractmethod
    def send_json_message(self, json_string: str) -> Optional[Json]:
        pass

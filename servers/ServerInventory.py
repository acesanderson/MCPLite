"""
Creates a server inventory for a given server_directory.
"""

from MCPLite.servers.ServerInfo import ServerInfo, server_directory
from pydantic import BaseModel, Field
from pathlib import Path

# Constants
inventory_file = Path(__file__).parent / "available_servers.jsonl"


class ServerInventory(BaseModel):
    """
    Represents an inventory of servers in a given directory.
    Contains metadata about each server, including its name and address.
    """

    servers: list[ServerInfo] = Field(
        default_factory=list,
        description="List of ServerInfo objects representing available servers",
    )

    @classmethod
    def load(cls, directory: str = str(server_directory)) -> "ServerInventory":
        """
        Load the server inventory from the specified directory.
        """
        # Implementation to load servers from the directory
        return cls(servers=[])  # Placeholder for actual loading logic

"""
Simple CRUD operations for a JSONL file containing server metadata.
Serialization and deserialization are handled using the ServerInfo class and json.
"""

from pathlib import Path
import json
from MCPLite.inventory.ServerInfo import (
    ServerInfo,
)
from pydantic import ValidationError

# Constants
inventory_file = Path(__file__).parent / "available_servers.jsonl"


def load_inventory() -> list[ServerInfo]:
    """
    Load the server inventory from the JSONL file.

    Returns:
        list[dict]: A list of server metadata dictionaries.
    """
    if not inventory_file.exists() or inventory_file.read_text().strip() == "":
        return []

    try:
        with inventory_file.open("r") as file:
            servers = []
            for line in file:
                if line.strip():
                    try:
                        server_data = json.loads(line.strip())
                        servers.append(ServerInfo(**server_data))
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON line: {line.strip()}")
        return servers
    except FileNotFoundError:
        print(f"Inventory file not found: {inventory_file}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file: {e}")
        return []
    except ValidationError as e:
        print(f"Validation error, did you update your Pydantic models? {e}")
        return []


def save_inventory(servers: list[ServerInfo]) -> None:
    """
    Save the server inventory to the JSONL file.

    Args:
        servers (list[ServerInfo]): A list of ServerInfo objects to save.
    """
    with inventory_file.open("w") as file:
        for server in servers:
            file.write(server.model_dump_json() + "\n")


def add_server(server: ServerInfo) -> None:
    """
    Add a new server to the inventory.

    Args:
        server (ServerInfo): The ServerInfo object containing server metadata.
    """
    servers = load_inventory()
    servers.append(server)
    save_inventory(servers)


def remove_server(server_name: str) -> None:
    """
    Remove a server from the inventory by its name.

    Args:
        server_name (str): The name of the server to remove.
    """
    servers = load_inventory()
    servers = [s for s in servers if s.name != server_name]
    save_inventory(servers)


def update_server(server_name: str, updated_server: ServerInfo) -> None:
    """
    Update an existing server in the inventory.

    Args:
        server_name (str): The name of the server to update.
        updated_server (ServerInfo): The updated ServerInfo object.
    """
    servers = load_inventory()
    for i, server in enumerate(servers):
        if server.name == server_name:
            servers[i] = updated_server
            break
    save_inventory(servers)


def get_server(server_name: str) -> ServerInfo | None:
    """
    Retrieve a server from the inventory by its name.

    Args:
        server_name (str): The name of the server to retrieve.

    Returns:
        ServerInfo | None: The ServerInfo object if found, otherwise None.
    """
    servers = load_inventory()
    for server in servers:
        if server.name == server_name:
            return server
    return None

"""
Simple CRUD operations for a JSONL file containing server metadata.
Serialization and deserialization are handled using the ServerInfo class and json.
"""

from pathlib import Path
import json
from MCPLite.servers.ServerInfo import ServerInfo

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


def save_inventory(servers: list[ServerInfo]) -> None:
    """
    Save the server inventory to the JSONL file.

    Args:
        servers (list[ServerInfo]): A list of ServerInfo objects to save.
    """
    with inventory_file.open("w") as file:
        for server in servers:
            file.write(server.json() + "\n")


def add_server(server: dict) -> None:
    """
    Add a new server to the inventory.

    Args:
        server (dict): A dictionary containing server metadata.
    """
    servers = load_inventory()
    servers.append(ServerInfo(**server))
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


def update_server(server_name: str, updated_server: dict) -> None:
    """
    Update an existing server in the inventory.

    Args:
        server_name (str): The name of the server to update.
        updated_server (dict): A dictionary containing updated server metadata.
    """
    servers = load_inventory()
    for i, server in enumerate(servers):
        if server.name == server_name:
            servers[i] = ServerInfo(**updated_server)
            break
    save_inventory(servers)


def get_server(server_name: str) -> dict | None:
    """
    Get a server from the inventory by its name.

    Args:
        server_name (str): The name of the server to retrieve.

    Returns:
        dict | None: The server metadata if found, otherwise None.
    """
    servers = load_inventory()
    for server in servers:
        if server.name == server_name:
            return server.dict()
    return None

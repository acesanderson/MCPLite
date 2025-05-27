"""
Creates a server inventory for a given server_directory.
These are stdio servers for the time being, though we would eventually like to support direct, http/SSE, and other transports.
"""

from MCPLite.inventory.ServerInfo import (
    ServerInfo,
    server_directory,
    StdioServerAddress,
)
from MCPLite.inventory.JSONL_CRUD import (
    load_inventory,
    save_inventory,
    add_server,
    remove_server,
    update_server,
    get_server,
)
from rich.console import Console


console = Console()


class ServerInventory:
    """
    Represents an inventory of servers in a given directory.
    Contains metadata about each server, including its name and address.
    """

    def __init__(self):
        self.servers = self._get_servers()

    def _get_servers(self) -> list[ServerInfo]:
        """
        Retrieves the list of servers from the server directory.
        """
        file_paths = server_directory.glob("*.py")
        file_paths = list(file_paths)
        servers = []
        for file_path in file_paths:
            name = file_path.stem
            address = StdioServerAddress(commands=["python", str(file_path)])
            server_info = ServerInfo(name=name, address=address)
            servers.append(server_info)
        return servers

    def get_server(self, name: str, console: Console = console) -> ServerInfo | None:
        """
        Retrieves a server by its name.
        """
        for server in self.servers:
            if server.name == name:
                return server
        console.print(f"[bold red]Server '{name}' not found in inventory.[/bold red]")
        return None

    def view_servers(self, console: Console = console) -> None:
        """
        Prints the list of servers in the inventory.
        """
        for server in self.servers:
            console.print(
                f"[bold green]Server Name:[/bold green][green] {server.name}[/green]\n[bold yellow]Description: [/bold yellow][yellow]{server.description}[/yellow]\n"
            )


if __name__ == "__main__":
    s = ServerInventory()
    s.view_servers()

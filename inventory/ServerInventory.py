"""
Creates a server inventory for a given server_directory.
These are stdio servers for the time being, though we would eventually like to support direct, http/SSE, and other transports.
"""

from MCPLite.inventory.ServerInfo import (
    ServerInfo,
    server_directory,
    StdioServerAddress,
    DirectServerAddress,
)
from MCPLite.inventory.JSONL_CRUD import (
    load_inventory,
    save_inventory,
)
from rich.console import Console
from pydantic import ValidationError


console = Console()


class ServerInventory:
    """
    Represents an inventory of servers in a given directory.
    Contains metadata about each server, including its name and address.
    The inventory is stored in a JSONL file for easy access and manipulation.
    The inventory can be updated by scanning the server directory for Python files, by running the `update` method.
    """

    def __init__(self):
        self.servers = load_inventory()
        if self.servers == []:
            console.print(
                "[bold yellow]No servers found in inventory. Scanning server directory...[/bold yellow]"
            )
            self.update()

    def update(self) -> None:
        """
        Create a new server inventory by scanning the server directory.
        """
        self.servers = self._update_servers()
        console.print("[bold green]Server inventory updated successfully![/bold green]")
        # Update the JSONL file with the current inventory
        save_inventory(self.servers)
        # Print the updated inventory
        self.view_servers()

    def _update_servers(self) -> list[ServerInfo]:
        """
        Retrieves the list of servers from the server directory.
        In future, expand to other directories and transports.
        """
        file_paths = server_directory.glob("*.py")
        file_paths = list(file_paths)
        servers = []
        for file_path in file_paths:
            name = file_path.stem
            stdio_address = StdioServerAddress(commands=["python", str(file_path)])
            direct_address = DirectServerAddress(
                import_statement=f"from MCPLite.servers.{file_path.stem} import mcp"
            )
            server_info = ServerInfo(
                name=name, addresses=[stdio_address, direct_address]
            )
            servers.append(server_info)
        # TBD: Add HTTP/SSE servers
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
        console.print("\n")
        for server in self.servers:
            transports = ", ".join(
                [address.transport_type for address in server.addresses]
            )
            console.print(
                f"[green]Server Name:[/green][bold green] {server.name}[/bold green] [white]({transports})\n[bold yellow]Description: [/bold yellow][yellow]{server.description}[/yellow]\n"
            )


if __name__ == "__main__":
    s = ServerInventory()

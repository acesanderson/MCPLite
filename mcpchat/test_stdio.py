from mcpchat import (
    MCPChat,
    Client,
)
from MCPLite.transport import StdioClientTransport
from pathlib import Path


def main():
    """Example usage of MCPChat."""
    # Create MCP Chat instance
    chat = MCPChat(model="gpt")
    server_path = (
        Path.home() / "Brian_Code" / "MCPLite" / "tests" / "stdio" / "fetch_stdio.py"
    )

    # Create client connected to our server
    client = Client(transport=StdioClientTransport(["python", str(server_path)]))

    # Add client to our chat host
    chat.host.add_client(client)
    chat._update_system_message()  # Update with new capabilities

    # Start the chat
    chat.chat()


if __name__ == "__main__":
    main()

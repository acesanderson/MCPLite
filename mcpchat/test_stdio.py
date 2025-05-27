"""
Desired high level syntax:
    chat = MCPChat(model="gpt", server="obsidian")
"""

from mcpchat import (
    MCPChat,
    Client,
)
from MCPLite.transport import StdioClientTransport
from pathlib import Path


def main():
    """Example usage of MCPChat."""
    # Create MCP Chat instance
    chat = MCPChat(model="gpt", server="obsidian")
    chat._update_system_message()  # Update with new capabilities

    # Start the chat
    chat.chat()


if __name__ == "__main__":
    main()

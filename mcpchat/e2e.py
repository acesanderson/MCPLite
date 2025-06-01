"""
Desired high level syntax:
    chat = MCPChat(model="gpt", server="obsidian")
"""

from mcpchat import MCPChat


def main():
    """Example usage of MCPChat."""
    # Create MCP Chat instance
    chat = MCPChat(model="gpt", servers=["fetch", "obsidian"])

    # Start the chat
    chat.chat()


if __name__ == "__main__":
    main()

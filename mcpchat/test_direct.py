from mcpchat import (
    MCPChat,
    MCPResource,
    MCPTool,
    Server,
    ServerRegistry,
    Client,
    DirectTransport,
)


def main():
    """Example usage of MCPChat."""

    # Create a simple MCP setup for demonstration
    def name_of_sheepadoodle() -> str:
        """Returns the name of the sheepadoodle."""
        return "Otis"

    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    # Create MCP Chat instance
    chat = MCPChat(model="gpt")

    # Set up a simple MCP server and client for demonstration
    resource = MCPResource(function=name_of_sheepadoodle, uri="names://sheepadoodle")
    tool = MCPTool(function=add)

    # Create server with our tools/resources
    server = Server(registry=ServerRegistry())
    server.registry.tools.append(tool)
    server.registry.resources.append(resource)

    # Create client connected to our server
    client = Client(transport=DirectTransport(server.process_message))

    # Add client to our chat host
    chat.host.add_client(client)
    chat._update_system_message()  # Update with new capabilities

    # Start the chat
    chat.chat()


if __name__ == "__main__":
    main()

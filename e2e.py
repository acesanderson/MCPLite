from MCPLite.mcplite.mcplite import MCPLite
from MCPLite.transport.Transport import Transport, DirectTransport
from MCPLite.server.Server import Server
from MCPLite.host.Host import Host
from MCPLite.client.Client import Client


mcp = MCPLite()


# Dummy resource function
@mcp.resource(uri="names://sheepadoodle")
def name_of_sheepadoodle() -> str:
    """
    Returns the name of the sheepadoodle.
    """
    return "Otis"


# Dummy tool function
@mcp.tool
def add(a: int, b: int) -> int:
    """
    Add two numbers.
    """
    return a + b


if __name__ == "__main__":
    host = Host(model="gpt")
    server = Server(registry=mcp.registry)
    client = Client(transport=DirectTransport(server.process_message))
    host.add_client(client)
    stuff = host.query("What is 2333 + 1266? Use the add function.")

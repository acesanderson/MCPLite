from pydantic import BaseModel, Field
from typing import Literal
from pathlib import Path
from MCPLite.primitives.MCPRegistry import ClientRegistry
from Chain import Chain, Model, Prompt

# Constants
## Directory where server scripts are stored; this is imported by ServerInventory.py
server_directory = Path.home() / "Brian_Code" / "MCPLite" / "servers"
## Cache for storing chain results -- we don't want to recreate descriptions every time we access our inventory.
# cache = ChainCache(
#     db_name=str(
#         server_directory / ".chain_cache.db",
#     )
# )
# Model._chain_cache = cache


# Pydantic classes
class ServerAddress(BaseModel):
    """
    Represents the address of a server.
    This can be a list of commands for stdio, a URL and port, or a Python import.
    """


class StdioServerAddress(ServerAddress):
    """
    Represents a server address for stdio transport.
    Contains a list of commands to start the server.
    """

    commands: list[str] = Field(
        description="List of commands to start the server via stdio"
    )


class DirectServerAddress(ServerAddress):
    """
    Represents a server address for direct transport.
    Contains a Python import path to the server.
    """

    import_statement: str = Field(
        description="Python import statement to import the server, e.g., 'from mymodule import MyServer'"
    )


class SSEServerAddress(ServerAddress):
    """
    Represents a server address for SSE (Server-Sent Events) transport.
    Contains a URL and port to connect to the server.
    """

    url: str = Field(description="URL of the server")
    port: int = Field(description="Port of the server")


# Our main ServerInfo class
class ServerInfo(BaseModel):
    """
    Metadata about completed servers.
    Stored in available_servers.jsonl in the servers/ directory.
    Acessible through available_servers() class method of MCPChat.
    """

    name: str = Field(description="Name of the server -- first half of the file name")
    address: StdioServerAddress | DirectServerAddress | SSEServerAddress = Field(
        description="Address of the server, either as a list of commands for stdio, a URL and port, or as a Python import",
    )

    # Generated post-init
    capabilities: ClientRegistry | None = Field(
        description="Capabilities of the server, as a list of tools, resources, and prompts",
        default=None,
    )
    description: str | None = Field(
        description="Description of the server -- created programmatically",
        default=None,
    )
    available: bool = Field(
        description="Whether the server is available for use; this means a successful initialization",
        default=False,
    )

    def model_post_init(self, __context):
        if not self.capabilities:
            self.capabilities = self._get_capabilities()
            if not self.capabilities:
                raise RuntimeError("Failed to retrieve server capabilities.")
            print(f"Server {self.name} initialized with capabilities.")
        if not self.description:
            self.description = self._generate_description()
            if not self.description:
                raise RuntimeError("Failed to generate server description.")
            print(f"Server {self.name} description generated.")
        self.available = True

    @property
    def transport(self) -> Literal["stdio", "direct", "sse"]:
        match self.address:
            case StdioServerAddress():
                return "stdio"
            case DirectServerAddress():
                return "direct"
            case SSEServerAddress():
                return "sse"
            case _:
                raise ValueError("Unknown server address type")

    def _get_capabilities(self):
        """
        Retrieve the capabilities of the server.
        This serves as both a test of the server's functionality and a way to generate the description.
        """
        from MCPLite.client.Client import Client

        match self.transport:
            case "stdio":
                # For stdio, we need to start the server and send an initialization request.
                from MCPLite.transport import StdioClientTransport

                client = Client(transport=StdioClientTransport(self.address.commands))
                client.initialize()
                if client.initialized:
                    print("Server initialized successfully.")
                    return client.registry
                else:
                    raise RuntimeError(
                        "Failed to initialize the server via stdio transport."
                    )
            case "direct":
                # For direct transport, we import the server and initialize it.
                from importlib import import_module

                module_name, class_name = self.address.import_statement.rsplit(".", 1)
                module = import_module(module_name)
                server_class = getattr(module, class_name)
                client = Client(transport=server_class())
                client.initialize()
                if client.initialized:
                    print("Server initialized successfully.")
                    return client.registry
                else:
                    raise RuntimeError(
                        "Failed to initialize the server via direct transport."
                    )
            case "sse":
                # For SSE, we would need to implement a specific client for SSE transport.
                raise NotImplementedError("SSE transport is not yet implemented.")
            case _:
                raise ValueError("Unknown server address type")

    def _generate_description(self):
        """
        Generate a description for the server based on its capabilities.
        """

        description_prompt_file = (
            server_directory.parent / "prompts" / "server_description.jinja2"
        )
        if not description_prompt_file.exists():
            raise FileNotFoundError(
                f"Description prompt file not found: {description_prompt_file}"
            )
        # Our Chain for generating the description
        prompt = Prompt(description_prompt_file.read_text())
        model = Model("claude")
        chain = Chain(prompt=prompt, model=model)
        response = chain.run(input_variables={"capabilities": self.capabilities})
        if not response:
            raise RuntimeError("Failed to generate server description.")
        return response.content.strip()


if __name__ == "__main__":
    # Example usage
    server_path = server_directory / "fetch.py"
    print(server_path)
    server_info = ServerInfo(
        name="fetch",
        address=StdioServerAddress(commands=["python", str(server_path)]),
    )
    print(server_info)
    print(server_info.transport)
    print(server_info.capabilities)
    print(server_info.description)

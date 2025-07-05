from MCPLite.primitives.MCPRegistry import ClientRegistry
from MCPLite.transport import StdioClientTransport, DirectTransport
from MCPLite.client.Client import Client
from Chain import Chain, Model, Prompt
from importlib import import_module
from pydantic import BaseModel, Field
from typing import Literal
from pathlib import Path

# Constants
## Directory where server scripts are stored; this is imported by ServerInventory.py
server_directory = Path.home() / "Brian_Code" / "MCPLite" / "servers"

transport_types = Literal["stdio", "direct", "sse"]


# Pydantic classes
class ServerAddress(BaseModel):
    """
    Represents the address of a server.
    This can be a list of commands for stdio, a URL and port, or a Python import.
    Contains methods to get a client for the server.
    """

    transport_type: transport_types = Field(
        description="Type of transport for the server address: 'stdio', 'direct', or 'sse'"
    )


class StdioServerAddress(ServerAddress):
    """
    Represents a server address for stdio transport.
    Contains a list of commands to start the server.
    """

    transport_type: transport_types = "stdio"  # Override to specify stdio transport
    commands: list[str] = Field(
        description="List of commands to start the server via stdio"
    )

    def _get_client(self):
        """
        Get a client for the server using stdio transport.
        This is used internally to initialize the server and retrieve capabilities.
        """

        return Client(transport=StdioClientTransport(self.commands))


class DirectServerAddress(ServerAddress):
    """
    Represents a server address for direct transport.
    Contains a Python import path to the server.
    """

    transport_type: transport_types = "direct"  # Override to specify direct transport
    import_statement: str = Field(
        description="Python import statement to import the server, e.g., 'from mymodule import MyServer'"
    )

    def _get_client(self):
        """
        Get a client for the server using direct transport.
        This is used internally to initialize the server and retrieve capabilities.
        """

        # Parse the import statement
        if not self.import_statement.startswith("from "):
            raise ValueError("Import statement must start with 'from'")

        parts = self.import_statement.split(" import ")
        if len(parts) != 2:
            raise ValueError("Invalid import statement format")

        module_name = parts[0].replace("from ", "").strip()
        object_name = parts[1].strip()

        module = import_module(module_name)
        mcp_instance = getattr(module, object_name)

        return Client(transport=DirectTransport(mcp_instance.server.process_message))


class SSEServerAddress(ServerAddress):
    """
    Represents a server address for SSE (Server-Sent Events) transport.
    Contains a URL and port to connect to the server.
    """

    transport_type: transport_types = "sse"  # Override to specify SSE transport

    url: str = Field(description="URL of the server")
    port: int = Field(description="Port of the server")

    def _get_client(self):
        """
        Get a client for the server using SSE transport.
        This is used internally to initialize the server and retrieve capabilities.
        """
        # For SSE, we would need to implement a specific client for SSE transport.
        raise NotImplementedError("SSE transport is not yet implemented.")


# Our main ServerInfo class
class ServerInfo(BaseModel):
    """
    Metadata about completed servers.
    Stored in available_servers.jsonl in the servers/ directory.
    Acessible through available_servers() class method of MCPChat.
    """

    name: str = Field(description="Name of the server -- first half of the file name")
    addresses: list[StdioServerAddress | DirectServerAddress | SSEServerAddress] = (
        Field(
            description="List of addresses for the server, each with its own transport type",
        )
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
    def transport_types(self) -> list[transport_types]:
        """
        TBD as I am rearchitecting addresses to be a list of ServerAddress objects.
        """
        return [address.transport_type for address in self.addresses]

    def _get_capabilities(self) -> ClientRegistry | None:
        """
        Retrieve the capabilities of the server.
        This serves as both a test of the server's functionality and a way to generate the description.
        """
        # Grab each registry and compare them.
        client_registries = []
        if "stdio" in self.transport_types:
            address = [
                addr for addr in self.addresses if addr.transport_type == "stdio"
            ][0]
            if not address:
                raise ValueError("No stdio address found for the server.")
            client = address._get_client()
            client.initialize()
            if client.initialized:
                print("Server initialized successfully.")
                client_registries.append(client.registry)
            else:
                raise RuntimeError(
                    "Failed to initialize the server via stdio transport."
                )
        if "direct" in self.transport_types:
            address = [
                addr for addr in self.addresses if addr.transport_type == "direct"
            ][0]
            if not address:
                raise ValueError("No direct address found for the server.")
            client = address._get_client()
            client.initialize()
            if client.initialized:
                print("Server initialized successfully.")
                client_registries.append(client.registry)
            else:
                raise RuntimeError(
                    "Failed to initialize the server via direct transport."
                )

        if "sse" in self.transport_types:
            raise NotImplementedError("SSE transport is not yet implemented.")

        # If we have multiple registries, compare them to catch any discrepancies.
        # If no error captured, return the first registry.
        if len(client_registries) == 0:
            raise RuntimeError("No capabilities retrieved from the server.")
        if len(client_registries) == 1:
            return client_registries[0]
        if len(client_registries) > 1:
            # Compare the registries to ensure they are consistent.
            first_registry = client_registries[0]
            for registry in client_registries[1:]:
                if first_registry != registry:
                    raise ValueError(
                        "Inconsistent capabilities retrieved from the server."
                    )
            return first_registry

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
        return str(response.content).strip()

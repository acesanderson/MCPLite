"""
MCP-enhanced Chat class that inherits from Chain's Chat framework.
Provides all the familiar Chat commands and interface, but with sophisticated
MCP agent capabilities under the hood.
"""

from Chain import Message, Model, MessageStore, Chat
from pathlib import Path
from MCPLite.logs.logging_config import get_logger, configure_logging, logging
from MCPLite.host.Host import Host
from rich.markdown import Markdown

# Get logger with this module's name
logger = get_logger(__name__)

dir_path = Path(__file__).parent
mcpchat_log_path = dir_path.parent / ".mcpchat.log"
system_prompt_path = dir_path.parent / "prompts" / "mcp_system_prompt.jinja2"

# Configure logging for this module
configure_logging(
    log_file=mcpchat_log_path,
    level=logging.INFO,
)


class MCPChat(Chat):
    """
    MCP-enhanced chat interface that inherits from Chain's Chat framework.
    Provides familiar chat commands plus sophisticated MCP agent capabilities.
    """

    def __init__(
        self,
        servers: list[str],
        model: str = "gpt",
        preferred_transport: str = "stdio",
        **kwargs,
    ):
        # Initialize Chat parent class
        super().__init__(model=Model(model), **kwargs)

        # Initial variables
        self.servers = servers
        self.model = model
        self.preferred_transport = preferred_transport

        # Initialize MCP Host for orchestration
        self.host = Host(model=model, servers=self.servers, console=self.console)

        # Update welcome message to indicate MCP capabilities
        status = self.host._generate_mcp_status()
        self.welcome_message = (
            "[green]Hello! This is MCP-enhanced chat. Type /help for commands or /status for MCP info.[/green]"
            + "\n\n"
            + status
        )

    @property
    def available_servers(self):
        """Return a list of available MCP servers."""
        self.host.serverinventory.view_servers(self.console)

    def query_model(self, input: list[Message]) -> str | None:
        """
        Override Chat's query_model to use MCP agent capabilities.
        """
        if not self.messagestore:
            return None

        # Use Host's agent query instead of simple model query
        user_content = str(input[-1].content)

        # Use a temporary message store for the agent loop
        temp_store = MessageStore()

        # Copy existing conversation to temp store
        for message in self.messagestore.messages:
            temp_store.add(message)

        # Run the agent query
        result = self.host.agent_query(user_content, temp_store)

        # Update our main message store with any new messages
        # (excluding the initial system/user messages we added)
        if len(temp_store.messages) > len(self.messagestore.messages):
            new_messages = temp_store.messages[len(self.messagestore.messages) :]
            for msg in new_messages:
                if msg.role == "assistant":
                    # Don't add user messages (tool results) to main conversation
                    self.messagestore.add(msg)

        return result

    # MCP-specific commands
    def command_status(self):
        """Show MCP connection status and capabilities."""
        output = self.host._generate_mcp_status()
        self.console.print(output)

    def command_list_tools(self):
        """List available MCP tools."""
        if not self.host.registry.tools:
            self.console.print("No tools available.", style="yellow")
            return

        self.console.print("Available MCP Tools:", style="bold green")
        for tool in self.host.registry.tools:
            self.console.print(f"• {tool.name}: {tool.description}", style="blue")

    def command_list_resources(self):
        """List available MCP resources."""
        if not self.host.registry.resources:
            self.console.print("No resources available.", style="yellow")
            return

        self.console.print("Available MCP Resources:", style="bold green")
        for resource in self.host.registry.resources:
            if hasattr(resource, "uri"):
                self.console.print(f"• {resource.name}: {resource.uri}", style="blue")
            else:
                self.console.print(
                    f"• {resource.name}: {resource.uriTemplate}", style="blue"
                )

    def command_list_prompts(self):
        """List available MCP prompts."""
        if not self.host.registry.prompts:
            self.console.print("No prompts available.", style="yellow")
            return

        self.console.print("Available MCP Prompts:", style="bold green")
        for prompt in self.host.registry.prompts:
            self.console.print(f"• {prompt.name}: {prompt.description}", style="blue")

    def command_run_prompt(self, prompt_name: str):
        """Run an MCP prompt by name."""
        try:
            result = self.host._run_prompt(prompt_name)
            self.console.print("Prompt Result:", style="bold green")
            self.console.print(Markdown(result))
        except Exception as e:
            self.console.print(f"Error running prompt: {str(e)}", style="red")

    # MCP client management commands
    def command_list_servers(self):
        """List available MCP servers."""
        if not self.host.serverinventory.servers:
            self.console.print("No MCP servers available.", style="yellow")
            return

        self.console.print("Available MCP Servers:", style="bold green")
        self.host.serverinventory.view_servers(self.console)

    def command_add_client(self, client_info: str):
        """Add an MCP client. Usage: /add client <description>"""
        # This is a placeholder - in practice you'd need to specify how to create clients
        self.console.print(f"Adding MCP client: {client_info}", style="yellow")
        self.console.print(
            "Note: This is a placeholder command. Implement client creation logic.",
            style="yellow",
        )

    def command_refresh_capabilities(self):
        """Refresh MCP capabilities and update system prompt."""
        old_count = (
            len(self.host.registry.tools)
            + len(self.host.registry.resources)
            + len(self.host.registry.prompts)
        )

        # Regenerate system prompt
        self.host._update_system_message()

        new_count = (
            len(self.host.registry.tools)
            + len(self.host.registry.resources)
            + len(self.host.registry.prompts)
        )

        self.console.print(
            f"Capabilities refreshed. Total capabilities: {new_count}", style="green"
        )
        if new_count != old_count:
            self.console.print(
                f"Change detected: {old_count} -> {new_count}", style="yellow"
            )

"""
MCP-enhanced Chat class that inherits from Chain's Chat framework.
Provides all the familiar Chat commands and interface, but with sophisticated
MCP agent capabilities under the hood.
"""

import json
from Chain import Message, Model, Prompt, MessageStore, Chat
from MCPLite.messages import (
    MCPMessage,
    MCPResult,
    parse_request,
    GetPromptRequest,
    GetPromptResult,
    Method,
    GetPromptRequestParams,
    PromptMessage,
)
from MCPLite.primitives import ClientRegistry
from MCPLite.transport import DirectTransport, StdioClientTransport
from MCPLite.inventory.ServerInfo import (
    ServerInfo,
    StdioServerAddress,
    SSEServerAddress,
    DirectServerAddress,
)
from MCPLite.client.Client import Client
from MCPLite.inventory.ServerInventory import ServerInventory
from MCPLite.inventory.ServerInfo import ServerInfo
from MCPLite.messages import (
    MCPRequest,
    CallToolRequest,
    GetPromptRequest,
    ReadResourceRequest,
)
from pathlib import Path
from typing import Optional
from MCPLite.logs.logging_config import get_logger, configure_logging, logging
from rich.console import Console

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


class Host:
    """
    Internal MCP orchestration engine used by MCPChat and other LLM-based applications (like `twig`).
    Handles MCP protocol, client management, and agent loops.
    """

    def __init__(self, model: str = "gpt", console: Console | None = None):
        self.registry = ClientRegistry()  # This sums up all clients' registries.
        self.model = Model(model)
        self.system_prompt: str = ""
        self.clients: list[Optional[Client]] = []
        self.console: Console | None = console

    def add_client(self, client: Client):
        """
        Adds client to list and updates system prompt.
        """
        client.initialize()
        if client.initialized:
            self.clients.append(client)
            self.registry += client.registry
            self.system_prompt = self.generate_system_prompt()
        else:
            logger.error(f"Failed to initialize client:\n{client}")
            raise ValueError(f"Failed to initialize client:\n{client}")

    def generate_system_prompt(self):
        """
        Return the capabilities of this MCP implementation.
        This is a simplified version of the MCP capability negotiation.
        Specifically, this renders capabilities as a string for LLMs to use.
        """
        if not system_prompt_path.exists():
            # Fallback system prompt if template doesn't exist
            return "You are an AI assistant with access to various tools and resources. When you need to use a tool, format your request as JSON with the appropriate method and parameters."

        system_prompt = Prompt(system_prompt_path.read_text())
        # Check which capabilities we support based on registered items
        input_variables = self.registry.definitions
        rendered = system_prompt.render(input_variables)
        return rendered

    def process_stream(self, stream) -> tuple[str, MCPMessage | None | dict]:
        buffer = ""
        display_buffer = ""  # Separate buffer for what we've already displayed

        try:
            for chunk in stream:
                content = str(chunk.choices[0].delta.content)
                if content:
                    # Print new content
                    if self.console:
                        self.console.print(content, end="")
                    else:
                        print(content, end="", flush=True)

                    # Add to buffers
                    buffer += content
                    display_buffer += content

                    # Look for answer tags
                    if "<answer>" in buffer and "</answer>" in buffer:
                        start_idx = buffer.index("<answer>") + len("<answer>")
                        end_idx = buffer.index("</answer>")
                        answer = buffer[start_idx:end_idx]
                        return display_buffer, {"answer": answer}

                    # Look for JSON objects
                    json_objects = self._find_json_objects(buffer)
                    if json_objects:
                        for json_str in json_objects:
                            try:
                                json_data = json.loads(json_str)
                                mcpmessage = parse_request(json_data)
                                if mcpmessage:
                                    stream.close()
                                    return display_buffer, mcpmessage
                            except json.JSONDecodeError:
                                continue

        except KeyboardInterrupt:
            # Handle cancellation gracefully
            logger.info("Query cancelled by user")
            if stream:
                stream.close()
            return display_buffer, None
        except Exception as e:
            logger.error(f"Error in stream processing: {e}")
            if stream:
                stream.close()
            return display_buffer, None

        # Normal completion
        return display_buffer, None

    def _find_json_objects(self, text):
        """
        Find complete JSON objects in a text string, starting from the first opening brace.
        All MCP Request messages have 'method' fields.
        """
        if "{" not in text:
            return []

        start_idx = text.find("{")
        level = 0
        in_string = False
        escape_next = False
        json_objects = []

        for i in range(start_idx, len(text)):
            char = text[i]

            if char == "\\" and not escape_next:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string

            escape_next = False

            if not in_string:
                if char == "{":
                    level += 1
                elif char == "}":
                    level -= 1

                    if level == 0:
                        json_str = text[start_idx : i + 1]
                        try:
                            obj = json.loads(json_str)
                            if "method" in obj:
                                json_objects.append(json_str)
                                return json_objects
                        except json.JSONDecodeError:
                            pass

        return json_objects

    def process_message(self, message: MCPRequest) -> MCPResult | None:
        """
        Process the message received from the stream.
        This sends message to the appropriate client, and returns the response.
        """
        if not self.clients:
            raise ValueError("No clients available to process the message.")

        # Route the message to the appropriate tool
        client: Client = self._identify_client(message)

        response = client.send_request(message)
        return response

    def _identify_client(self, message: MCPRequest) -> Client:
        """
        For a given MCPMessage, identify the relevant client from self.clients.
        LLM requests are only the three Requests invoking each of the three primitives.
        """

        if isinstance(message, CallToolRequest):
            tool_name = message.params.name
            # Find which client has this tool
            for client in self.clients:
                if isinstance(client, Client) and client.initialized:
                    for tool in client.registry.tools:
                        if tool.name == tool_name:
                            return client

        elif isinstance(message, GetPromptRequest):
            prompt_name = message.params.name
            # Find which client has this prompt
            for client in self.clients:
                if isinstance(client, Client) and client.initialized:
                    for prompt in client.registry.prompts:
                        if prompt.name == prompt_name:
                            return client

        elif isinstance(message, ReadResourceRequest):
            resource_uri = message.params.uri
            # Find which client has this resource (including templates)
            for client in self.clients:
                if isinstance(client, Client) and client.initialized:
                    for resource in client.registry.resources:
                        # Handle both regular resources and resource templates
                        if hasattr(resource, "uri") and resource.uri == resource_uri:
                            return client
                        elif hasattr(resource, "uriTemplate"):
                            # Check if URI matches the template pattern
                            # You'll need to implement template matching logic
                            if self._uri_matches_template(
                                resource_uri, resource.uriTemplate
                            ):
                                return client
        else:
            # Raise an error if we can't match to the client.
            logger.warning(
                f"Unknown MCPRequest type: {type(message).__name__}. Cannot identify client."
            )
            raise ValueError(
                f"Unknown MCPRequest type: {type(message).__name__}. Cannot identify client."
            )

    def _uri_matches_template(self, uri: str, template: str) -> bool:
        """
        Check if a URI matches a template pattern.
        This is a simplified version - you might want more sophisticated matching.
        """
        import re

        # Convert template like "file://todos/{date}" to regex
        pattern = re.escape(template).replace(r"\{[^}]+\}", r"[^/]+")
        return re.match(f"^{pattern}$", uri) is not None

    def agent_query(self, prompt: str, message_store: MessageStore) -> str | None:
        """
        Enhanced query method that handles MCP agent loops.
        """
        # Initialize conversation with system prompt and user query
        message_store.clear()
        if self.system_prompt:
            message_store.add_new(role="system", content=self.system_prompt)
        message_store.add_new(role="user", content=prompt)

        # Agent loop
        while True:
            # Query model with streaming
            stream = self.model.stream(message_store.messages, verbose=False)
            buffer, special_catch = self.process_stream(stream)

            if isinstance(special_catch, dict):
                # Found answer tags - we're done
                answer = special_catch.get("answer")
                if answer:
                    return answer
                # No answer found, continue with buffer
                message_store.add_new(role="assistant", content=buffer)
                return buffer

            elif special_catch is None:
                # No special content found, just a normal response
                message_store.add_new(role="assistant", content=buffer)
                return buffer

            elif isinstance(special_catch, MCPMessage):
                # Found MCP request - process it
                message_store.add_new(role="assistant", content=buffer)
                # Print out the MCP message so user can see.
                request_text = (
                    f"[MCP Request]\n{special_catch.model_dump_json(indent=2)}"
                )
                self.console.print(f"[yellow]{request_text}[/yellow]")

                observation: MCPResult = self.process_message(special_catch)
                if observation:
                    # Check if this is an error result
                    is_error = getattr(observation, "isError", False)

                    if is_error:
                        # Display error result but continue conversation
                        observation_text = (
                            f"[Server Error]\n{observation.model_dump_json(indent=2)}"
                        )
                        self.console.print(f"[red]{observation_text}[/red]")
                    else:
                        # Display normal result
                        observation_text = (
                            f"[Tool Result]\n{observation.model_dump_json(indent=2)}"
                        )
                        self.console.print(f"[green]{observation_text}[/green]")

                    message_store.add_new(role="user", content=observation_text)
                    # Continue the loop to get the next response
                    continue

    def _convert_PromptMessage_to_Message(
        self, prompt_message: PromptMessage
    ) -> Message:
        """Convert a PromptMessage to a Message (Chain)."""
        role = prompt_message.role
        content = prompt_message.content
        text = content.text
        return Message(role=role, content=text)

    def run_prompt(self, prompt_name: str, **kwargs) -> str:
        """Run a prompt with the given arguments."""
        if len(self.registry.prompts) == 0:
            raise ValueError("No prompts found in registry.")
        if prompt_name not in [prompt.name for prompt in self.registry.prompts]:
            raise ValueError(f"Prompt {prompt_name} not found in registry.")

        for prompt in self.registry.prompts:
            if prompt_name == prompt.name:
                params = GetPromptRequestParams(name=prompt_name, arguments=kwargs)
                prompt_request = GetPromptRequest(
                    method=Method.PROMPTS_GET, params=params
                )

                prompt_result: GetPromptResult = self.clients[0].send_request(
                    prompt_request
                )
                if prompt_result:
                    # Convert prompt messages and return as formatted string
                    messages = []
                    for message in prompt_result.messages:
                        if isinstance(message, PromptMessage):
                            converted = self._convert_PromptMessage_to_Message(message)
                            messages.append(f"{converted.role}: {converted.content}")
                    return "\n".join(messages)

        return f"Prompt {prompt_name} not found."


class MCPChat(Chat):
    """
    MCP-enhanced chat interface that inherits from Chain's Chat framework.
    Provides familiar chat commands plus sophisticated MCP agent capabilities.
    """

    serverinventory: ServerInventory = ServerInventory()

    def __init__(self, model: str = "gpt", server: list | str = "", **kwargs):
        # Initialize Chat parent class
        super().__init__(model=Model(model), **kwargs)

        # Initialize MCP Host for orchestration
        self.host = Host(model=model, console=self.console)
        # Set system message from MCP capabilities (will be empty initially)
        self._update_system_message()

        # Set up any requested servers
        self._setup_servers(server)

        # Generate our welcome message -- we want to greet the user with the capabilities detected.
        status = self._generate_mcp_status()

        # Update welcome message to indicate MCP capabilities
        self.welcome_message = (
            "[green]Hello! This is MCP-enhanced chat. Type /help for commands or /status for MCP info.[/green]"
            + "\n\n"
            + status
        )

    def _update_system_message(self):
        """Update system message based on current MCP capabilities."""
        if self.host.system_prompt:
            self.system_message = Message(
                role="system", content=self.host.system_prompt
            )

    def _add_server(self, server: ServerInfo):
        """
        Add a single MCP server to Host's client list.
        This should parse by different transport types (e.g., Stdio, HTTP) and then create the right clients to sent to host's add_client method.
        """
        if isinstance(server, ServerInfo):
            match server.address:
                case StdioServerAddress():
                    # Create a Stdio client
                    client = Client(
                        name=server.name,
                        transport=StdioClientTransport(server.address.commands),
                    )
                    self.host.add_client(client)
                    self._update_system_message()  # Update with new capabilities

                case SSEServerAddress():
                    raise NotImplementedError(
                        "SSE transport is not yet implemented in MCPChat."
                    )
                case DirectServerAddress():
                    # Create a Direct transport client
                    import_statement = server.address.import_statement
                    # Execute the import statement to get the server function
                    if import_statement:
                        # Assuming import_statement is a callable function that can be used directly as a server function
                        if isinstance(import_statement, str):
                            try:
                                # If it's a string, assume it's a path to a server function
                                server_function = __import__(import_statement)
                                client = Client(
                                    name=server.name,
                                    transport=DirectTransport(server_function),
                                )
                                self.host.add_client(client)
                                self._update_system_message()  # Update with new capabilities
                            except ImportError as e:
                                raise ImportError(
                                    f"Failed to import server function from '{import_statement}': {str(e)}"
                                )

        else:
            raise ValueError("Server must be an instance of ServerInfo.")

    def _setup_servers(self, server: list | str):
        """
        Set up MCP servers based on provided server list or single server.
        """
        if isinstance(server, str):
            server = [server]

        if not server:
            # No servers specified, return None
            return

        for srv in server:
            for server_info in self.serverinventory.servers:
                if server_info.name == srv:
                    # Found matching server, add it
                    self._add_server(server_info)
                    break

    def _generate_mcp_status(self) -> str:
        """
        Generate a rich-formatted output string of the MCP status.
        Added to welcome message + accessable by user through mcp status command.
        """
        output = ""
        if not self.host.clients:
            output = "[red]No MCP clients connected.[/red]"
            return output

        # Summary
        valid_clients = [
            client for client in self.host.clients if isinstance(client, Client)
        ]
        initialized_clients = [client for client in valid_clients if client.initialized]

        output += (
            f"Clients: {len(initialized_clients)}/{len(valid_clients)} initialized\n\n"
        )
        self.console.print()

        # Show each client
        for client in self.host.clients:
            if not isinstance(client, Client):
                output += "[red]Invalid client (NoneType)[/red]\n"
                continue

            if client.initialized:
                # Get transport type
                transport_type = (
                    type(client.transport).__name__.replace("Transport", "")
                    if client.transport
                    else "Unknown"
                )

                # Get capability counts
                tools_count = (
                    len(client.registry.tools) if hasattr(client, "registry") else 0
                )
                resources_count = (
                    len(client.registry.resources) if hasattr(client, "registry") else 0
                )
                prompts_count = (
                    len(client.registry.prompts) if hasattr(client, "registry") else 0
                )

                # Client header with summary
                output += f"[bold green]{client.name}[/bold green] ({transport_type}) - [yellow]{tools_count} tools[/yellow], [blue]{resources_count} resources[/blue], [magenta]{prompts_count} prompts[/magenta]\n"

                if hasattr(client, "registry"):
                    # Tools - just names
                    if client.registry.tools:
                        tool_names = [tool.name for tool in client.registry.tools]
                        output += f"  [yellow]Tools:[/yellow] {', '.join(tool_names)}\n"

                    # Resources - just names
                    if client.registry.resources:
                        resource_names = [
                            resource.name for resource in client.registry.resources
                        ]
                        output += (
                            f"  [blue]Resources:[/blue] {', '.join(resource_names)}\n"
                        )

                    # Prompts - just names
                    if client.registry.prompts:
                        prompt_names = [
                            prompt.name for prompt in client.registry.prompts
                        ]
                        output += (
                            f"  [magenta]Prompts:[/magenta] {', '.join(prompt_names)}\n"
                        )

                    if not (
                        client.registry.tools
                        or client.registry.resources
                        or client.registry.prompts
                    ):
                        output += "  [dim]No capabilities[/dim]\n"

            else:
                # Not initialized - grayed out
                transport_type = (
                    type(client.transport).__name__.replace("Transport", "")
                    if client.transport
                    else "Unknown"
                )
                output += (
                    f"[dim]{client.name} ({transport_type}) - Not initialized[/dim]\n"
                )

            output += "\n"
        return output

    @property
    def available_servers(self):
        """Return a list of available MCP servers."""
        self.serverinventory.view_servers(self.console)

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
        output = self._generate_mcp_status()
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
            result = self.host.run_prompt(prompt_name)
            self.console.print("Prompt Result:", style="bold green")
            self.console.print(Markdown(result))
        except Exception as e:
            self.console.print(f"Error running prompt: {str(e)}", style="red")

    # MCP client management commands
    def command_list_servers(self):
        """List available MCP servers."""
        if not self.serverinventory.servers:
            self.console.print("No MCP servers available.", style="yellow")
            return

        self.console.print("Available MCP Servers:", style="bold green")
        self.serverinventory.view_servers(self.console)

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
        self.host.system_prompt = self.host.generate_system_prompt()
        self._update_system_message()

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

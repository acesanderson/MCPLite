"""
The Host class serves as the core orchestration engine for integrating Model Context Protocol (MCP)
capabilities into any LLM-powered application using Chain framework. It acts as a bridge between language models and
external tools, resources, and data sources through standardized MCP servers.

Host provides a complete MCP orchestration layer that:
- Manages connections to multiple MCP servers
- Aggregates capabilities (tools, resources, prompts) from all connected servers
- Generates system prompts that inform LLMs about available capabilities
- Routes LLM requests to the appropriate MCP servers
- Handles the agent loop for complex multi-step interactions

```python
from MCPLite.host.Host import Host

# Create host with specific servers
host = Host(model="gpt", servers=["fetch", "filesystem"])

# Ask a question that requires external capabilities
result = host.agent_query("What's the current weather in San Francisco?")
print(result)
```
"""

import json
from Chain import Message, Model, Prompt, MessageStore
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
from MCPLite.inventory.ServerInfo import (
    ServerInfo,
    StdioServerAddress,
    SSEServerAddress,
    DirectServerAddress,
    transport_types,
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


class Host:
    """
    Internal MCP orchestration engine used by MCPChat and other LLM-based applications (like `twig`).
    Handles MCP protocol, client management, and agent loops.
    """

    # This is the inventory of all available MCP servers.
    serverinventory: ServerInventory = ServerInventory()

    def __init__(
        self,
        servers: list[str],
        model: str = "gpt",
        preferred_transport: transport_types = "stdio",
        console: Console = Console(),
    ):
        # Init variables
        self.servers = servers
        self.model = Model(model)
        self.preferred_transport = preferred_transport

        # Our empty variables
        self.system_message: Message | None = None
        self.clients: list[Optional[Client]] = []
        self.console: Console = console
        self.registry = ClientRegistry()  # This sums up all clients' registries.
        self.initialized = False

        # Initialization
        self._initialize_host()

    def _initialize_host(self):
        """
        Initialize the MCP host by setting up servers and updating system message.
        This is called during Host instantiation.
        """
        # Set up servers based on provided list
        self._setup_servers(self.servers)
        # Update system message with current capabilities
        self._update_system_message()
        # Double check that initialization was successful
        if not self.clients:
            logger.error(
                "No valid MCP clients initialized. Check server configuration."
            )
            raise ValueError(
                "No valid MCP clients initialized. Check server configuration."
            )
        elif not self.system_message:
            logger.error(
                "MCP Host initialized but no system message generated. Check capabilities."
            )
            raise ValueError(
                "MCP Host initialized but no system message generated. Check capabilities."
            )
        elif not self.registry:
            logger.error(
                "MCP Host initialized but no registry found. Check client capabilities."
            )
            raise ValueError(
                "MCP Host initialized but no registry found. Check client capabilities."
            )
        else:
            # Successful initialization
            logger.info(
                "MCP Host initialized successfully with clients and system message."
            )
            self.initialized = True

    # Initialize servers
    def _setup_servers(self, servers: list[str]):
        """
        Set up MCP servers based on provided server list or single server.
        """
        for server_name in servers:
            server = self.serverinventory.get_server(server_name)
            if server:
                self._add_server(server)
        if not self.clients:
            logger.warning("No valid MCP servers found or added.")
            raise ValueError("No valid MCP servers found or added.")

    def _add_server(self, server_info: ServerInfo):
        """
        Add a single MCP server to Host's client list.
        This should parse by different transport types (e.g., Stdio, HTTP) and then create the right clients to sent to host's add_client method.
        """
        # We need to get the name from ServerInfo which we will assign to any Client we create.
        name = server_info.name
        # A reminder of the expected server_info structure:
        addresses: list[StdioServerAddress | DirectServerAddress | SSEServerAddress] = (
            server_info.addresses
        )
        # If we have multiple addresses, prioritize the preferred transport type.
        if len(addresses) == 1:
            # If only one address, use it directly
            address = addresses[0]
        elif len(addresses) > 1:
            # Filter by preferred transport type
            try:
                address = [
                    addr
                    for addr in addresses
                    if addr.transport_type == self.preferred_transport
                ][0]
            except:
                address = addresses[0]  # Fallback to first available if none match
        else:
            # No addresses available, raise an error
            raise ValueError(
                f"No valid addresses found for server {server_info.name} with transport type {self.preferred_transport}."
            )

        # Now add the client according to the address type
        try:
            match address:
                case StdioServerAddress():
                    # Create a Stdio client
                    client = address._get_client()
                    client.name = name  # Set the server name
                    self._add_client(client)
                    self._update_system_message()  # Update with new capabilities

                case DirectServerAddress():
                    # Create a Direct transport client
                    client = address._get_client()
                    client.name = name  # Set the server name
                    self._add_client(client)
                    self._update_system_message()  # Update with new capabilities

                case SSEServerAddress():
                    # Create an SSE transport client
                    raise NotImplementedError(
                        "SSE transport is not yet implemented in MCPChat."
                    )
        except Exception as e:
            logger.error(f"Failed to add server {server_info.name}: {e}")
            raise ValueError(f"Failed to add server {server_info.name}: {e}")

    def _add_client(self, client: Client):
        """
        Adds client to list and updates system prompt.
        """
        client.initialize()
        if client.initialized:
            self.clients.append(client)
            self.registry += client.registry
            self.system_message = self._update_system_message()
        else:
            logger.error(f"Failed to initialize client:\n{client}")
            raise ValueError(f"Failed to initialize client:\n{client}")

    # Generate system prompt based on capabilities
    def _update_system_message(self):
        """Update system message based on current MCP capabilities."""
        system_prompt = self._generate_system_prompt()
        self.system_message = Message(
            role="system",
            content=system_prompt,
        )

    def _generate_system_prompt(self):
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

    # Generate a rich-formatted output string of the MCP status
    def _generate_mcp_status(self) -> str:
        """
        Generate a rich-formatted output string of the MCP status.
        Added to welcome message + accessable by user through mcp status command.
        """
        output = ""
        if not self.clients:
            output = "[red]No MCP clients connected.[/red]"
            return output

        # Summary
        valid_clients = [
            client for client in self.clients if isinstance(client, Client)
        ]
        initialized_clients = [client for client in valid_clients if client.initialized]

        output += (
            f"Clients: {len(initialized_clients)}/{len(valid_clients)} initialized\n\n"
        )

        # Show each client
        for client in self.clients:
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

    # Our query logic, handling both streaming and MCP requests
    def _process_stream(self, stream) -> tuple[str, MCPMessage | None | dict]:
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

    def _process_message(self, message: MCPRequest) -> MCPResult | None:
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

    def agent_query(
        self, prompt: str, message_store: MessageStore = MessageStore()
    ) -> str | None:
        """
        Enhanced query method that handles MCP agent loops.
        Importable to Chat and one-off LLM applications like `twig`.
        """
        # Initialize conversation with system prompt and user query
        message_store.clear()
        if self.system_message:
            message_store.add(self.system_message)
        message_store.add_new(role="user", content=prompt)

        # Agent loop
        while True:
            # Query model with streaming
            stream = self.model.stream(message_store.messages, verbose=False)
            buffer, special_catch = self._process_stream(stream)

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

                observation: MCPResult = self._process_message(special_catch)
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

    def _run_prompt(self, prompt_name: str, **kwargs) -> str:
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


if __name__ == "__main__":
    console = Console()
    h = Host(model="gpt", servers=["fetch", "obsidian"])
    console.print(h._generate_mcp_status())

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
from MCPLite.primitives import ClientRegistry, ServerRegistry
from MCPLite.transport import DirectTransport
from MCPLite.server.Server import Server
from MCPLite.client.Client import Client
from MCPLite.inventory.ServerInventory import ServerInventory
from pathlib import Path
from typing import Optional
from MCPLite.logs.logging_config import get_logger
from rich.markdown import Markdown
from rich.console import Console

# Get logger with this module's name
logger = get_logger(__name__)

dir_path = Path(__file__).parent
system_prompt_path = dir_path.parent / "prompts" / "mcp_system_prompt.jinja2"


class Host:
    """
    Internal MCP orchestration engine used by MCPChat.
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
        self.clients.append(client)
        self.registry += client.registry
        self.system_prompt = self.generate_system_prompt()

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
        """
        Process LLM stream, looking for MCP requests and special answer tags.
        """
        buffer = ""

        for chunk in stream:
            content = str(chunk.choices[0].delta.content)
            if self.console:
                self.console.print(content, end="")
            buffer += content

            # Look for <answer> tags, if found, return the content
            if "<answer>" in buffer and "</answer>" in buffer:
                start_idx = buffer.index("<answer>") + len("<answer>")
                end_idx = buffer.index("</answer>")
                answer = buffer[start_idx:end_idx]
                return buffer, {"answer": answer}

            # Look for any complete JSON object
            json_objects = self.find_json_objects(buffer)

            if json_objects:
                # For each JSON object found, try to validate it
                for json_str in json_objects:
                    try:
                        json_data = json.loads(json_str)
                        mcpmessage = parse_request(json_data)

                        if mcpmessage:
                            print("\n[MCP Tool Call Detected]")
                            stream.close()
                            return buffer, mcpmessage

                    except json.JSONDecodeError:
                        continue

        # If we processed the entire stream without finding valid JSON
        return buffer, None

    def find_json_objects(self, text):
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

    def process_message(self, message: MCPMessage) -> MCPResult | None:
        """
        Process the message received from the stream.
        This sends message to the appropriate client, and returns the response.
        """
        if not self.clients:
            raise ValueError("No clients available to process the message.")

        response = self.clients[0].send_request(message)
        return response

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

                try:
                    observation: MCPResult = self.process_message(special_catch)
                    if observation:
                        # Add observation to conversation and continue
                        observation_text = f"\n[Tool Result]\n{observation.model_dump_json(indent=2)}\n"
                        message_store.add_new(role="user", content=observation_text)
                        # Continue the loop to get the next response
                        continue
                except Exception as e:
                    error_text = f"\n[Tool Error]\n{str(e)}\n"
                    message_store.add_new(role="user", content=error_text)
                    continue

    def convert_PromptMessage_to_Message(
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
                            converted = self.convert_PromptMessage_to_Message(message)
                            messages.append(f"{converted.role}: {converted.content}")
                    return "\n".join(messages)

        return f"Prompt {prompt_name} not found."


class MCPChat(Chat):
    """
    MCP-enhanced chat interface that inherits from Chain's Chat framework.
    Provides familiar chat commands plus sophisticated MCP agent capabilities.
    """

    def __init__(self, model: str = "gpt", **kwargs):
        # Initialize Chat parent class
        super().__init__(model=Model(model), **kwargs)

        # Initialize MCP Host for orchestration
        self.host = Host(model=model, console=self.console)

        # Update welcome message to indicate MCP capabilities
        self.welcome_message = "[green]Hello! This is MCP-enhanced chat. Type /help for commands or /mcp_status for MCP info.[/green]"

        # Set system message from MCP capabilities (will be empty initially)
        self._update_system_message()

    def _update_system_message(self):
        """Update system message based on current MCP capabilities."""
        if self.host.system_prompt:
            self.system_message = Message(
                role="system", content=self.host.system_prompt
            )

    # @property
    # def available_servers() -> list

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
    def command_mcp_status(self):
        """Show MCP connection status and capabilities."""
        if not self.host.clients:
            self.console.print("No MCP clients connected.", style="yellow")
            return

        self.console.print(
            f"Connected MCP clients: {len(self.host.clients)}", style="green"
        )
        self.console.print(
            f"Available tools: {len(self.host.registry.tools)}", style="blue"
        )
        self.console.print(
            f"Available resources: {len(self.host.registry.resources)}", style="blue"
        )
        self.console.print(
            f"Available prompts: {len(self.host.registry.prompts)}", style="blue"
        )

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

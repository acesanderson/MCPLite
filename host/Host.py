"""
MCP fun.
Complete refactor here; Agent class should inherit from Chat.
Host handles all LLM logic (prompt rendering + function parsing etc.).
Host takes optional clients.
"""

import json
from Chain import Message, Model, Prompt, MessageStore
from MCPLite.messages import MCPMessage, MCPResult, parse_request
from MCPLite.primitives import ClientRegistry, ServerRegistry
from MCPLite.transport.Transport import DirectTransport
from MCPLite.server.Server import Server
from MCPLite.client.Client import Client
from pathlib import Path
from typing import Optional

# For development, note that our Primitives are not actually used at all on client/host side.
from MCPLite.primitives import MCPTool, MCPResource

dir_path = Path(__file__).parent
system_prompt_path = dir_path.parent / "prompts" / "mcp_system_prompt.jinja2"


class Host:  # ineerit from Chat?
    def __init__(
        self,
        model: str = "gpt",
    ):
        self.registry = ClientRegistry()  # This sums up all clients' registries.
        self.model = Model(model)
        # self.system_prompt is generated when a client is added.
        self.system_prompt: str = ""
        self.message_store = MessageStore()
        self.clients: list[Optional[Client]] = []

    # Initialization functions
    def add_client(self, client: Client):
        """
        Adds client to list and updates system prompt.
        """
        self.clients.append(client)
        self.system_prompt = self.generate_system_prompt()

    def generate_system_prompt(self):
        """
        Return the capabilities of this MCP implementation.
        This is a simplified version of the MCP capability negotiation.
        Specifically, this renders capabilities as a string for LLMs to use.
        """
        system_prompt = Prompt(system_prompt_path.read_text())
        # Check which capabilities we support based on registered items
        # Later implementation will require an entire initialization handshake, where servers and clients expose capabilities.
        # We want the definitions; we render pydantic Definition as JSON, assign [] if list is empty.
        input_variables = self.registry.definitions
        rendered = system_prompt.render(input_variables)
        return rendered

    def process_stream(self, stream) -> tuple[str, MCPMessage | None]:
        buffer = ""

        for chunk in stream:
            print(str(chunk.choices[0].delta.content), end="", flush=True)
            # print(chunk.choices[0].delta.content.strip())
            buffer += str(chunk.choices[0].delta.content)

            # Look for any complete JSON object
            json_objects = self.find_json_objects(buffer)

            if json_objects:
                # For each JSON object found, try to validate it
                for json_str in json_objects:
                    try:
                        json_data = json.loads(json_str)

                        # Use a separate validation function
                        mcpmessage = parse_request(json_data)

                        if mcpmessage:
                            print("Valid MCP message found:", mcpmessage)
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
        # First, let's check if there's at least one opening brace
        if "{" not in text:
            return []

        # Find the position of the first opening brace
        start_idx = text.find("{")

        # Track brace nesting level
        level = 0
        in_string = False
        escape_next = False
        json_objects = []

        for i in range(start_idx, len(text)):
            char = text[i]

            # Handle string parsing with escape character support
            if char == "\\" and not escape_next:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string

            escape_next = False

            # Only count braces outside of strings
            if not in_string:
                if char == "{":
                    level += 1
                elif char == "}":
                    level -= 1

                    # If we've closed all open braces, we have a complete object
                    if level == 0:
                        json_str = text[start_idx : i + 1]

                        # Try to parse and validate
                        try:
                            obj = json.loads(json_str)
                            # Only include objects that contain the required fields
                            if "method" in obj:
                                json_objects.append(json_str)
                                return json_objects  # Return the first complete object
                            else:
                                pass
                        except json.JSONDecodeError:
                            pass

        return json_objects

    def process_message(self, message: MCPMessage) -> MCPResult | None:
        """
        Process the message received from the stream.
        This sends message to the appropriate client, and returns the response as a string to LLM.
        """
        if not self.clients:
            raise ValueError("No clients available to process the message.")
        print("Processing message:", message)
        response = self.clients[0].send_request(message)
        return response

    def return_observation(self, observation: str) -> Message:
        observation_string = f"<observation>{observation}</observation>"
        user_message = Message(role="user", content=observation_string)
        return user_message

    def query(self, prompt: str) -> str | None:
        # Load our prompts.
        self.message_store.clear()
        self.message_store.add_new(role="system", content=self.system_prompt)
        self.message_store.add_new(role="user", content=prompt)
        # Our main loop
        while True:
            # Query OpenAI with the messages so far
            stream = self.model.stream(self.message_store.messages, verbose=False)
            # Get the response and any mcpmessage
            buffer, mcpmessage = self.process_stream(stream)
            if buffer and not mcpmessage:
                # If we have a buffer but no mcpmessage, we can just return the buffer.
                self.message_store.add_new(role="assistant", content=buffer)
                break
            if mcpmessage:
                # If we have a mcpmessage, we need to process it and return the observation.
                self.message_store.add_new(role="assistant", content=buffer)
                # Process the message
                observation: MCPResult = self.process_message(mcpmessage)


if __name__ == "__main__":
    # Dummy resource function
    def name_of_sheepadoodle() -> str:
        """
        Returns the name of the sheepadoodle.
        """
        return "Otis"

    # Dummy tool function
    def add(a: int, b: int) -> int:
        """
        Add two numbers.
        """
        return a + b

    # The objects that will be working together
    resource = MCPResource(
        function=name_of_sheepadoodle,
        uri="names://sheepadoodle",
    )
    resource_definition = resource.definition
    tool = MCPTool(function=add)
    tool_definition = tool.definition
    host = Host(model="gpt")
    host.registry.tools.append(tool_definition)
    host.registry.resources.append(resource_definition)
    host.system_prompt = host.generate_system_prompt()
    print(host.system_prompt)
    server = Server(registry=ServerRegistry())
    server.registry.tools.append(tool)
    server.registry.resources.append(resource)
    client = Client(transport=DirectTransport(server.process_message))
    host.add_client(client)
    stuff = host.query("What is 2333 + 1266? Use the add function.")
    # stuff = host.query("What is the name of my cute sheepadoodle?")
    # print(type(stuff))
    # print(stuff)

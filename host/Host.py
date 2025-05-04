"""
MCP fun.
Complete refactor here; Agent class should inherit from Chat.
Host handles all LLM logic (prompt rendering + function parsing etc.).
Host takes optional clients.
"""

import json
from Chain import Chain, Message, Model, Prompt, MessageStore
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
from MCPLite.transport.Transport import DirectTransport
from MCPLite.server.Server import Server
from MCPLite.client.Client import Client
from pathlib import Path
from typing import Optional
from MCPLite.logs.logging_config import get_logger

# Get logger with this module's name
logger = get_logger(__name__)


# For development, note that our Primitives are not actually used at all on client/host side.
from MCPLite.primitives import MCPTool, MCPResource

dir_path = Path(__file__).parent
system_prompt_path = dir_path.parent / "prompts" / "mcp_system_prompt.jinja2"
message_store_log_path = dir_path / ".message_store_log"


class Host:  # ineerit from Chat?
    def __init__(
        self,
        model: str = "gpt",
    ):
        self.registry = ClientRegistry()  # This sums up all clients' registries.
        self.model = Model(model)
        # self.system_prompt is generated when a client is added.
        self.system_prompt: str = ""
        self.message_store = MessageStore(log_file=message_store_log_path)
        self.clients: list[Optional[Client]] = []

    # Initialization functions
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
        system_prompt = Prompt(system_prompt_path.read_text())
        # Check which capabilities we support based on registered items
        # Later implementation will require an entire initialization handshake, where servers and clients expose capabilities.
        # We want the definitions; we render pydantic Definition as JSON, assign [] if list is empty.
        input_variables = self.registry.definitions
        rendered = system_prompt.render(input_variables)
        return rendered

    def process_stream(self, stream) -> tuple[str, MCPMessage | None | dict]:
        buffer = ""

        for chunk in stream:
            # print(str(chunk.choices[0].delta.content), end="", flush=True)
            # print(chunk.choices[0].delta.content.strip())
            buffer += str(chunk.choices[0].delta.content)

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
        print("Sending request through Client:", message)
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
            buffer, special_catch = self.process_stream(stream)
            if isinstance(special_catch, dict):
                answer = special_catch.get("answer")
                print("Answer found:", answer)
                break
            elif special_catch is None:
                # If we have a buffer but no mcpmessage, we can just return the buffer.
                self.message_store.add_new(role="assistant", content=buffer)
                continue
            elif isinstance(special_catch, MCPMessage):
                # If we have a mcpmessage, we need to process it and return the observation.
                self.message_store.add_new(role="assistant", content=buffer)
                # Process the message
                print("Processing MCP message:", special_catch)
                observation: MCPResult = self.process_message(special_catch)
                print(
                    "Observation received, either None or valid MCPResult:", observation
                )
                if observation:
                    print("OBSERVATION RECEIVED:", observation)
                    # If we have an observation, we need to return it.
                    # This is a bit of a hack, but we can just return the observation as a string.
                    # In the future, we might want to return a more structured object.
                    if isinstance(observation, MCPResult):
                        print("Returning observation:", observation)
                        self.message_store.add_new(
                            role="assistant",
                            content=observation.model_dump_json(indent=2),
                        )

    def convert_PromptMessage_to_Message(
        self, prompt_message: PromptMessage
    ) -> Message:
        """
        Convert a PromptMessage to a Message (Chain).
        """
        role = prompt_message.role
        content = prompt_message.content
        text = content.text
        message = Message(role=role, content=text)
        return message

    def run_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Run a prompt with the given arguments.
        This is a simplified version of the MCP capability negotiation.
        Specifically, this renders capabilities as a string for LLMs to use.
        """
        if len(self.registry.prompts) == 0:
            raise ValueError("No prompts found in registry.")
        if prompt_name not in [prompt.name for prompt in self.registry.prompts]:
            raise ValueError(f"Prompt {prompt_name} not found in registry.")
        for prompt in self.registry.prompts:
            if prompt_name == prompt.name:
                params = GetPromptRequestParams(
                    name=prompt_name,
                    arguments=kwargs,
                )
                prompt_request = GetPromptRequest(
                    method=Method.PROMPTS_GET,
                    params=params,
                )
        logger.info(f"Running prompt: {prompt_request}")
        prompt_result: GetPromptResult = self.clients[0].send_request(prompt_request)
        if prompt_result:
            logger.info(f"Received result: {prompt_result}")
            messages = prompt_result.messages
            for message in messages:
                if isinstance(message, PromptMessage):
                    # Convert PromptMessage to Message (Chain)
                    message = self.convert_PromptMessage_to_Message(message)
                    self.message_store.add_new(
                        role=message.role, content=message.content
                    )
            logger.info("Running prompt result")
            # Now run the messages
            chain = Chain(model=self.model)
            response = chain.run(messages=self.message_store.messages)
            print(response.content)


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
    print("Running host.query ...")
    # stuff = host.query("What is 2333 + 1266? Use the add function.")
    stuff = host.query("What is the name of my cute sheepadoodle?")
    # print(type(stuff))
    # print(stuff)

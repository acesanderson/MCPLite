"""
MCP fun.
Complete refactor here; Agent class should inherit from Chat.
"""

import re, json
from Chain.message.message import Message
from Chain.model.model import Model
from Chain.prompt.prompt import Prompt
from Chain.message.messagestore import MessageStore
from Chain.mcp.MCPRegistry import Registry
from Chain.mcp.MCPMessage import MCPMessage, parse_message
from Chain.mcp.Client import Client
from pathlib import Path

dir_path = Path(__file__).parent
system_prompt_path = dir_path / "mcp_system_prompt.jinja2"


class Agent:
    def __init__(
        self,
        model: Model = Model("gpt"),
    ):
        self.registry = Registry()
        self.model = model
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


    def process_stream(self, stream) -> tuple[str, dict, str]:
        buffer = ""
        
        for chunk in stream:
            buffer += str(chunk.choices[0].delta.content)
            
            # Look for any complete JSON object
            json_objects = self.find_json_objects(buffer)
            
            if json_objects:
                # For each JSON object found, try to validate it
                for json_str in json_objects:
                    try:
                        json_data = json.loads(json_str)
                        
                        # Use a separate validation function
                        mcpmessage = parse_message(json_data)
                        
                        if mcpmessage:
                            self.process_message(mcpmessage)
                            # If validation passes, stop the stream and return the data
                            stream.close()
                            return 
                        
                        # If validation fails, continue with the stream
                        
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try the next object
                        continue
        
        # If we processed the entire stream without finding valid JSON
        return "", {}, buffer

    def find_json_objects(self, text):
        """Find all JSON objects in a text string."""
        # This regex pattern looks for matching curly braces with any content between them
        pattern = r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\})'
        return re.findall(pattern, text, re.DOTALL)


    def process_message(self, message: MCPMessage) -> MCPMessage | None:
        """
        Process the message received from the stream.
        This sends message to the appropriate client, and returns the response as a string to LLM.
        """
        if not self.clients:
            raise ValueError("No clients available to process the message.")
        # Assuming we have a single client for simplicity
        client = self.clients[0]
        # Send the message to the client
        response = client.send_request(message)
        # Process the response from the client
        response_string = response.model_dump_json(indent=2)
        # Feed it to the LLM somehow

        
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
            tool, args, buffer = self.process_stream(stream)
            # Determine if we have final answer
            if tool == "finish":
                final_answer = args["final_answer"]
                print(final_answer)
                self.message_store.add_new(role="assistant", content=final_answer)
                break
            self.message_store.add_new(role="assistant", content=buffer)
            # Generate observation on command
            observation = ""
            for tool_object in self.tool_objects:
                if tool_object.name == tool:
                    observation = str(tool_object(**args))
            if observation:
                user_message = self.return_observation(observation)
                self.message_store.add_new(user_message.role, str(user_message.content))
            else:
 


# class Agent:
#     """
#     A ReACT is a variant of Chain that defines a simple input-output ReACT workflow.
#     Parameters:
#     - input: str (this goes into system prompt, and tells the LLM what the input would be)
#     - output: str (same as above, but for output)
#     - tools: list[Callable] (a list of your functions; they should take parameters and have descriptive + short docstrings)
#     - model: a Model object (currently only Model('gpt') support streaming, that is default)
#     """
#
#     def __init__(
#         self,
#         input: str,
#         output: str,
#         tools: list[Callable],
#         model: Model = Model("gpt"),
#         log_file: str = "",
#     ):
#         self.input = input
#         self.output = output
#         self.tools = tools
#         self.model = model
#         # Add our default to logfile
#         if log_file == "":
#             dir_path = Path(__file__).parent / ".react.log"
#             self.log_file = str(dir_path)
#         else:
#             self.log_file = log_file
#         # Generate system prompt
#         self.tool_objects = [Tool(tool) for tool in tools]
#         self.system_prompt = self.render_system_prompt(input, output, self.tool_objects)
#         # Initialize MessageStore
#         self.message_store = MessageStore(log_file=self.log_file)
#
#     def load_system_prompt_template(self) -> Template:
#         # Load system prompt from jinja file
#         with open(system_prompt_path, "r") as file:
#             system_prompt_string = Template(file.read().strip())
#         return system_prompt_string
#
#     def render_system_prompt(self, input: str, output: str, tool_objects: list[Tool]):
#         system_prompt_string = self.load_system_prompt_template()
#         system_prompt = system_prompt_string.render(
#             input=input, output=output, tool_objects=tool_objects
#         )
#         return system_prompt
#
#     def process_stream(self, stream) -> tuple[str, dict, str]:
#         buffer = ""
#         for chunk in stream:
#             buffer += str(chunk.choices[0].delta.content)
#             if "</args>" in buffer:
#                 stream.close()
#                 break
#         # Process either the args or the finish tool
#         buffer = re.sub(r"</args>.*", "</args>", buffer, flags=re.DOTALL)
#         # Stop token gets rendered as None, so we need to remove the last 4 characters
#         if buffer.endswith("None"):
#             buffer = buffer[:-4]
#         # Grab two bits of data: <tool></tool> and <args></args>
#         try:
#             tool = re.search(
#                 r"<tool>(.*?)</tool>", buffer, re.DOTALL
#             ).group(  # type:ignore
#                 1
#             )
#             args = re.search(
#                 r"<args>(.*?)</args>", buffer, re.DOTALL
#             ).group(  # type:ignore
#                 1
#             )
#             args = literal_eval(args)
#             return tool, args, buffer
#         except AttributeError:
#             return "", {}, buffer
#
#     def return_observation(self, observation: str) -> Message:
#         observation_string = f"<observation>{observation}</observation>"
#         user_message = Message(role="user", content=observation_string)
#         return user_message
#
#     def query(self, prompt: str) -> str | None:
#         # Load our prompts.
#         self.message_store.clear()
#         self.message_store.add_new(role="system", content=self.system_prompt)
#         self.message_store.add_new(role="user", content=prompt)
#         # Our main loop
#         while True:
#             # Query OpenAI with the messages so far
#             stream = self.model.stream(self.message_store.messages, verbose=False)
#             tool, args, buffer = self.process_stream(stream)
#             # Determine if we have final answer
#             if tool == "finish":
#                 final_answer = args["final_answer"]
#                 print(final_answer)
#                 self.message_store.add_new(role="assistant", content=final_answer)
#                 break
#             self.message_store.add_new(role="assistant", content=buffer)
#             # Generate observation on command
#             observation = ""
#             for tool_object in self.tool_objects:
#                 if tool_object.name == tool:
#                     observation = str(tool_object(**args))
#             if observation:
#                 user_message = self.return_observation(observation)
#                 self.message_store.add_new(user_message.role, str(user_message.content))
#             else:
#                 print("No observation found")

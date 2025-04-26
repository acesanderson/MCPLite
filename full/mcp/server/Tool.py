from typing import Callable
from inspect import signature
import json
from Chain.mcp.messages.message_classes import ToolDefinition, ToolRequest, ToolResponse


# Tool class
class Tool:
    """
    Resources are parameterless functions that return a static resource (typically a string but could be anything that an LLM would interpret).

    Example usage:

    ```python
    tool_registry = ToolRegistry()

    @tool_registry.register
    def my_tool(param1: str, param2: int):
        "" This is a tool that returns an answer. ""
        return param1 + str(param2)
    ```
    name = my_tool (the function name)
    description = "This is a tool that returns a string." (the docstring)
    """

    def __init__(self, function: Callable):
        self.function = function
        try:
            self.description = function.__doc__.strip()  # type: ignore
        except AttributeError:
            print("Function needs a docstring")
        self.input_schema = self.get_input_schema()
        self.name = function.__name__

    def get_input_schema(self) -> dict:
        sig = signature(self.function)
        params = sig.parameters
        input_schema = {
            name: param.annotation.__name__ for name, param in params.items()
        }
        if "_empty" in input_schema.values():
            raise ValueError("Function parameters must have type annotations.")
        return input_schema

    def __call__(self, **kwargs):
        return self.function(**kwargs)

    @property
    def definition(self) -> ToolDefinition:
        """Return a dictionary representation of this tool for MCP compatibility.
        Per MCP spec, the tool should be represented as:
        {
          name: string;          // Unique identifier for the tool
          description?: string;  // Human-readable description
          inputSchema: {         // JSON Schema for the tool's parameters
            type: "object",
            properties: { ... }  // Tool-specific parameters
          }
        }
        """
        tool_definition = ToolDefinition(
            name=self.name,
            description=self.description,
            inputSchema=ToolDefinition.InputSchema(
                type="object", properties=self.input_schema
            ),
        )
        return tool_definition.model_dump_json(indent=2)  # type: ignore

    def request(self, tool_request_json: str) -> str:
        """
        This is where all the tool queries are processed.
        Will throw a ValidationError if the json is not valid.
        """
        # Validate the json against the ToolRequest schema
        tool_request = ToolRequest.model_validate_json(tool_request_json)

        pass

    def __repr__(self):
        """Return a string representation of this tool."""
        params_str = json.dumps(self.input_schema)
        return f"<Tool: {self.name}, Description: {self.description}, Parameters: {params_str}>"

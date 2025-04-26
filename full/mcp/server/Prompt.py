from typing import Callable
from inspect import signature
from Chain.mcp.messages.message_classes import (
    PromptDefinition,
    PromptRequest,
    PromptResponse,
)
import json


# Tool class
class Prompt:
    """
    Resources are parameterless functions that return a static resource (typically a string but could be anything that an LLM would interpret).

    Example usage:

    ```python
    @mcp.tool
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

    def get_input_schema(self):
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

    def to_dict(self):
        """
        Return a dictionary representation of this tool for MCP compatibility.
        Per MCP spec, the tool should be represented as:
        {
          "name": "analyze_data",
          "description": "Template for analyzing data files",
          "arguments": [
            {
              "name": "file_path",
              "description": "Path to the data file",
              "required": true
            },
            {
              "name": "analysis_type",
              "description": "Type of analysis to perform",
              "required": false
            }
          ]
        }
        """
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.input_schema,
            },
        }

    def to_json(self):
        """Return a JSON representation of this tool for MCP compatibility."""
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self):
        """Return a string representation of this tool."""
        params_str = json.dumps(self.input_schema)
        return f"<Tool: {self.name}, Description: {self.description}, Parameters: {params_str}>"

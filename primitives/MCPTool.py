from typing import Callable
from inspect import signature
import json
from MCPLite.messages.Definitions import ToolDefinition
from MCPLite.messages.Responses import TextContent
from pydantic import BaseModel, Field


# Tool class
class MCPTool(BaseModel):
    """
    Tools are parameterized functions that return a dynamic resource (typically a string but could be anything that an LLM would interpret).

    Note: the function must be named, have a docstring, and have type annotations for all parameters or this will throw an error.

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

    function: Callable
    description: str = Field(default="")
    name: str = Field(default="")
    input_schema: dict = Field(default_factory=dict)

    def model_post_init(self, __context) -> None:
        """
        This method is called after the model is created.
        It sets the name and description of the tool.
        """
        self.name = self._get_name()
        self.description = self._get_description()
        self.input_schema = self._get_input_schema()

    def _get_name(self) -> str:
        try:
            return self.function.__name__
        except AttributeError:
            raise ValueError("Function needs a name, did you just slip me a lambdas?")

    def _get_description(self) -> str:
        try:
            return self.function.__doc__.strip()  # type: ignore
        except AttributeError:
            raise ValueError("Function needs a docstring.")

    def _get_input_schema(self) -> dict:
        sig = signature(self.function)
        params = sig.parameters
        input_schema = {
            name: param.annotation.__name__ for name, param in params.items()
        }
        if "_empty" in input_schema.values():
            raise ValueError("Function parameters must have type annotations.")
        return input_schema

    def __call__(self, **kwargs) -> TextContent:
        """
        Here we need to return the result of the function call, such that it can be inserted into CallRoolResult.
        content: list[Union[TextContent, ImageContent, EmbeddedResource]]
        TBD: implementation of ImageContent, EmbeddedResource
        """
        # Assume everything is TextContent for now.
        result_content = str(self.function(**kwargs))
        # Convert the result to a TextContent object
        content = TextContent(
            type="text",
            text=result_content,
        )
        return content

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
        return tool_definition

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

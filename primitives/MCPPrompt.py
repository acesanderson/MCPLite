"""
Note: main class needs to be refactored for pydantic
"""

from typing import Callable
from inspect import signature
from MCPLite.messages import PromptDefinition, GetPromptResult, Argument
from MCPLite.messages.Responses import TextContent
from pydantic import BaseModel, Field
from typing import Literal


# Some basic types required for Prompts
class PromptMessage(BaseModel):
    """Base class for all prompt messages."""

    role: Literal["user", "assistant"]
    content: TextContent


# Tool class
class MCPPrompt(BaseModel):
    """
    TBD: allow user to set descriptions for the arguments through the doc string or by parameter within the decorator.
    For example this FastMCP implementation:
        @mcp.prompt(
        arguments=[
            {"name": "code", "description": "The source code to analyze", "required": True},
            {"name": "language", "description": "The programming language of the code", "required": False}
        ]
    )
    """

    function: Callable
    description: str = Field(default="")
    name: str = Field(default="")
    arguments: list[Argument] = Field(default=[])

    def model_post_init(self, __context) -> None:
        """
        This method is called after the model is created.
        It sets the name and description of the tool.
        """
        self.name = self._get_name()
        self.description = self._get_description()
        self.arguments = self._get_arguments()

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

    def _get_arguments(self):
        """
        Build a list of Argument objects.
        TBD: allow for parameter descriptions.
        """
        sig = signature(self.function)
        params = sig.parameters
        arguments = []
        for name, param in params.items():
            # A parameter is required if it doesn't have a default value
            # PARAMETER_EMPTY is used to indicate no default value
            required = param.default == param.empty
            # Create an Argument object
            arg = Argument(
                name=name,
                description="",  # Empty description as mentioned
                required=required,
            )
            arguments.append(arg)
        return arguments

    def __call__(self, **kwargs) -> GetPromptResult:
        """
        class PromptMessage(BaseModel):
            role: Role
            content: list[Union[TextContent, ImageContent, EmbeddedResource]]

        class GetPromptResult(MCPResult):
            messages: list[PromptMessage]  # Changed from Any for type safety
            description: Optional[str] = None  # Changed from PromptMessage
        """
        # Prompt functions either return a list of Message or a single string
        function_output: str | list[PromptMessage] = self.function(**kwargs)
        # Detect if single string
        if isinstance(function_output, str):
            function_output = [
                PromptMessage(
                    role="user", content=TextContent(type="text", text=function_output)
                )
            ]
            return GetPromptResult(
                _meta=None, description=self.description, messages=function_output  # type: ignore
            )
        elif isinstance(function_output, list):
            return GetPromptResult(
                _meta=None, description=self.description, messages=function_output  # type: ignore
            )
        else:
            raise ValueError(
                "Prompt function output is neither str nor list[PromptMessage]."
            )

    @property
    def definition(self) -> PromptDefinition:
        """
        class PromptDefinition(Definition):
            class Argument(BaseModel):
                name: str
                description: str
                required: bool

            name: str
            description: str
            arguments: list[Argument]
        """
        return PromptDefinition(
            name=self.name,
            description=self.description,
            arguments=self.arguments,  # type: ignore
        )

    def __repr__(self):
        """Return a string representation of this prompt."""
        if self.arguments:
            args_str = " ".join(
                [argument.model_dump_json() for argument in self.arguments]
            )
        else:
            args_str = ""
        return f"<Prompt: {self.name}, Description: {self.description}, Parameters: {args_str}>"

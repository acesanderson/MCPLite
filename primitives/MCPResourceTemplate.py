from typing import Callable, Any
from inspect import signature, Parameter
import json
import re
from MCPLite.messages.Definitions import ResourceTemplateDefinition
from pydantic import BaseModel, Field
from MCPLite.primitives.Primitive import Primitive

from MCPLite.logs.logging_config import get_logger

# Get logger with this module's name
logger = get_logger(__name__)


uri_template_regex = r"^[a-zA-Z][a-zA-Z\d+\-.]*://[^\s/$.?#].[^\s]*\{[^}]+\}$"


def get_string_size_in_bytes(content):
    """
    Convert object to bytes using UTF-8 encoding (or another encoding of your choice), return len().
    """
    try:
        str(content)
    except ValueError:
        raise ValueError("Cannot convert object to string.")
    byte_representation = str(content).encode("utf-8")
    return len(byte_representation)


# Tool class
class MCPResourceTemplate(Primitive):
    """
    ResourceTemplates are parameterized functions that return dynamic resources based on provided parameters.
    You need to pass the function, a URI pattern, and optionally a mimeType and size.
    The function must be named, have a docstring, and define parameters, or this will throw an error.

    Example usage:

    ```python
    resource_template_registry = ResourceTemplateRegistry()
    @resource_template_registry.register("http://example.com/resource/{param}", "text/plain", 1024)

    def my_resource_template(param: str):
        # This is a resource template that returns a string based on the param.
        return f"This is my resource with parameter: {param}"
    ```
    """

    function: Callable
    uriTemplate: str
    name: str = Field(default="")
    description: str = Field(default="")
    mimeType: str = Field(default="text/plain")
    size: int = Field(default=1024)
    parameters: list[dict[str, Any]] = Field(
        default_factory=list
    )  # New field for function parameters

    def model_post_init(self, __context) -> None:
        """
        This method is called after the model is created.
        It sets the name, description, and parameters of the resource.
        """
        self.uriTemplate = self._validate_uri_template(self.uriTemplate)
        self.name = self._get_name()
        self.description = self._get_description()

    def _validate_uri_template(self, uri_pattern: str):
        """
        Validate the URI template format.
        Per MCP spec, the URI template should contain parameter placeholders: [protocol]://[host]/[path]/{param}
        """
        if not re.match(uri_template_regex, uri_pattern):
            raise ValueError(
                "Invalid URI template format. URI pattern should start with a protocol (e.g., http://) and contain parameter placeholders in {}"
            )

        # Check that all parameters in URI pattern exist in function signature
        pattern_params = re.findall(r"{([^}]+)}", uri_pattern)
        sig_params = set(signature(self.function).parameters.keys())

        for param in pattern_params:
            if param not in sig_params:
                raise ValueError(
                    f"Parameter '{param}' in URI pattern not found in function signature."
                )

        return uri_pattern

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

    def _get_parameters(self) -> list[dict[str, Any]]:
        """
        Get the parameters of the function.
        """
        params = []

        sig = signature(self.function)
        for param_name, param in sig.parameters.items():
            param_info = {
                "name": param_name,
                "required": param.default == Parameter.empty,
            }

            # Try to get type annotation
            if param.annotation != Parameter.empty:
                if hasattr(param.annotation, "__name__"):
                    param_info["type"] = param.annotation.__name__
                else:
                    # Handle more complex type annotations (Optional, Union, etc.)
                    param_info["type"] = str(param.annotation)

            # Add default value if available
            if param.default != Parameter.empty:
                param_info["default"] = param.default

            params.append(param_info)

            if not params:
                raise ValueError(
                    "Resource template function must have at least one parameter."
                )

            return params

    @property
    def definition(self):
        """Return a dictionary representation of this resource template for MCP compatibility."""
        return ResourceTemplateDefinition(
            uriTemplate=self.uriTemplate,
            name=self.name,
            description=self.description,
            mimeType=self.mimeType,
        )

    def __call__(self, **kwargs):
        return self.function(**kwargs)

    def __repr__(self):
        """Return a string representation of this resource template."""
        param_str = ", ".join(
            [
                f"{p['name']}" + (": optional" if not p.get("required", True) else "")
                for p in self.parameters
            ]
        )
        return f"<ResourceTemplate: {self.name}, Parameters: [{param_str}], Description: {self.description}>"

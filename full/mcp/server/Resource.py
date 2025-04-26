from typing import Callable
from inspect import signature
import json
import re
from Chain.mcp.messages.message_classes import (
    ResourceDefinition,
    ResourceRequest,
    ResourceResponse,
    ResourceTemplateDefinition,
)

uri_regex = r"^[a-zA-Z][a-zA-Z\d+\-.]*://[^\s/$.?#].[^\s]*"


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
class Resource:
    """
    Resources are parameterless functions that return a static resource (typically a string but could be anything that an LLM would interpret).

    Example usage:

    ```python
    resource_registry = ResourceRegistry()

    @resource_registry.register("http://example.com/resource", "text/plain", 1024)
    def my_resource():
        # This is a resource that returns a string.
        return "This is my resource."
    ```
    name = my_resource (the function name)
    description = "This is a resource that returns a string." (the docstring)
    """

    def __init__(
        self,
        function: Callable,
        uri: str,
        mime_type: str = "text/plain",
        size: int = 1024,
    ):
        self.function = function
        self.uri = uri
        self.mime_type = mime_type
        self.size = size
        # self.description
        try:
            self.description = function.__doc__.strip()  # type: ignore
        except AttributeError:
            print("Function needs a docstring")
        self.name = function.__name__

    def validate_uri(self, uri: str):
        """
        Validate the URI format.
        Per MCP spec, the URI should be in the format: [protocol]://[host]/[path]
        """
        if not re.match(uri_regex, uri):
            raise ValueError(
                "Invalid URI format. URI should start with a protocol (e.g., http://)"
            )
        return uri

    def validate_parameters(self):
        sig = signature(self.function)
        params = sig.parameters
        param_types = {
            name: param.annotation.__name__ for name, param in params.items()
        }
        return str(param_types)

    def to_dict(self):
        """Return a dictionary representation of this resource for MCP compatibility."""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
            "size": self.size,
        }

    def to_json(self):
        """Return a JSON representation of this resource for MCP compatibility."""
        return json.dumps(self.to_dict(), indent=2)

    def __call__(self, **kwargs):
        return self.function(**kwargs)

    def __repr__(self):
        """Return a string representation of this resource."""
        return f"<Resource: {self.name}, Description: {self.description}>"

from typing import Callable
import json
import re
from MCPLite.messages.Definitions import ResourceDefinition
from pydantic import BaseModel, Field

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
class MCPResource(BaseModel):
    """
    Resources are parameterless functions that return a static resource (typically a string but could be anything that an LLM would interpret).
    You need to pass the function, a URI, and optionally a mimeType and size.
    The function must be named, and have a docstring, or this will throw an error.

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

    function: Callable
    uri: str
    name: str = Field(default="")
    description: str = Field(default="")
    mimeType: str = Field(default="text/plain")
    size: int = Field(default=1024)

    def model_post_init(self, __context) -> None:
        """
        This method is called after the model is created.
        It sets the name and description of the resource.
        """
        self.uri = self._validate_uri(self.uri)
        self.name = self._get_name()
        self.description = self._get_description()

    def _validate_uri(self, uri: str):
        """
        Validate the URI format.
        Per MCP spec, the URI should be in the format: [protocol]://[host]/[path]
        """
        if not re.match(uri_regex, uri):
            raise ValueError(
                "Invalid URI format. URI should start with a protocol (e.g., http://)"
            )
        return uri

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

    @property
    def definition(self):
        """Return a dictionary representation of this resource for MCP compatibility."""
        return ResourceDefinition(
            uri=self.uri,
            name=self.name,
            description=self.description,
            mimeType=self.mimeType,
            size=self.size,
        )

    def to_json(self):
        """Return a JSON representation of this resource for MCP compatibility."""
        return json.dumps(self.to_dict(), indent=2)

    def __call__(self, **kwargs):
        return self.function(**kwargs)

    def __repr__(self):
        """Return a string representation of this resource."""
        return f"<Resource: {self.name}, Description: {self.description}>"

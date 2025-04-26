from pydantic import BaseModel
from MCPMessage import (
    ResourceDefinition,
    ResourceTemplateDefinition,
    ToolDefinition,
    PromptDefinition,
)
from MCPTool import MCPTool
from MCPResource import MCPResource
from MCPPrompt import MCPPrompt


class ClientRegistry(BaseModel):
    """
    A registry that holds resources, tools, and prompts.
    Client side this means our MCPMessage objects, which map to MCP schema.
    """

    resources: list[ResourceDefinition | ResourceTemplateDefinition] = []
    tools: list[ToolDefinition] = []
    prompts: list[PromptDefinition] = []

    # We want to be able to add two registries together.
    def __add__(self, other: "ClientRegistry"):
        """
        Add two registries together.
        """
        try:
            self.resources.extend(other.resources)
            self.tools.extend(other.tools)
            self.prompts.extend(other.prompts)
            return self
        except AttributeError:
            raise TypeError(
                f"Cannot add {type(self)} and {type(other)}. Both must be of type ClientRegistry."
            )

    def __radd__(self, other: "ClientRegistry"):
        """
        Add two registries together.
        """
        try:
            self.resources.extend(other.resources)
            self.tools.extend(other.tools)
            self.prompts.extend(other.prompts)
            return self
        except AttributeError:
            raise TypeError(
                f"Cannot add {type(self)} and {type(other)}. Both must be of type ClientRegistry."
            )

    @property
    def definitions(self) -> dict[str, list[dict]]:
        """
        All definitions in the registry, as dicts for rendering system prompt.
        Returns a dictionary with keys "resources", "tools", and "prompts", each of these being a list of dicts (i.e. the definitions per MCP schema).
        """
        resources = (
            [resource.model_dump() for resource in self.resources]
            if self.resources
            else []
        )
        tools = [tool.model_dump() for tool in self.tools] if self.tools else []
        prompts = (
            [prompt.model_dump() for prompt in self.prompts] if self.prompts else []
        )
        return {
            "resources": resources,
            "tools": tools,
            "prompts": prompts,
        }


class ServerRegistry(BaseModel):
    """
    A registry that holds resources, tools, and prompts. SErver side this means our MCPResource, MCPTool, and MCPPrompt objects, which map to MCP schema but also have python function code attached.
    """

    resources: list[MCPResource] = []
    tools: list[MCPTool] = []
    prompts: list[MCPPrompt] = []

    # We want to be able to add two registries together.
    def __add__(self, other: "ServerRegistry"):
        """
        Add two registries together.
        """
        try:
            self.resources.extend(other.resources)
            self.tools.extend(other.tools)
            self.prompts.extend(other.prompts)
            return self
        except AttributeError:
            raise TypeError(
                f"Cannot add {type(self)} and {type(other)}. Both must be of type ServerRegistry."
            )

    def __radd__(self, other: "ServerRegistry"):
        """
        Add two registries together.
        """
        try:
            self.resources.extend(other.resources)
            self.tools.extend(other.tools)
            self.prompts.extend(other.prompts)
            return self
        except AttributeError:
            raise TypeError(
                f"Cannot add {type(self)} and {type(other)}. Both must be of type ServerRegistry."
            )

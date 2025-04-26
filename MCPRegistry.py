from pydantic import BaseModel
from MCPMessage import (
    ResourceDefinition,
    ResourceTemplateDefinition,
    ToolDefinition,
    PromptDefinition,
)


class Registry(BaseModel):
    """
    A registry that holds resources, tools, and prompts.
    """

    resources: list[ResourceDefinition | ResourceTemplateDefinition] = []
    tools: list[ToolDefinition] = []
    prompts: list[PromptDefinition] = []

    # We want to be able to add two registries together.
    def __add__(self, other: "Registry"):
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
                f"Cannot add {type(self)} and {type(other)}. Both must be of type Registry."
            )

    def __radd__(self, other: "Registry"):
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
                f"Cannot add {type(self)} and {type(other)}. Both must be of type Registry."
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

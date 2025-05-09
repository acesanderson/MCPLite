from pydantic import BaseModel
from MCPLite.messages.MCPMessage import MCPMessage

# ClientRegistry holds Definitions. These map to Resource, Tool, Prompt in the official MCP schema.
from MCPLite.messages import (
    ResourceDefinition,
    ResourceTemplateDefinition,
    ToolDefinition,
    PromptDefinition,
    ReadResourceRequest,
    GetPromptRequest,
    CallToolRequest,
)

# ServerRegistry holds MCPResource, MCPTool, and MCPPrompt. These are the actual implementations of the definitions.
from MCPLite.primitives import MCPTool, MCPResource, MCPPrompt, MCPResourceTemplate


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
            [
                resource.model_dump()
                for resource in self.resources
                if isinstance(resource, ResourceDefinition)
            ]
            if self.resources
            else []
        )
        resource_templates = (
            [
                resource.model_dump()
                for resource in self.resources
                if isinstance(resource, ResourceTemplateDefinition)
            ]
            if self.resources
            else []
        )
        tools = [tool.model_dump() for tool in self.tools] if self.tools else []
        prompts = (
            [prompt.model_dump() for prompt in self.prompts] if self.prompts else []
        )
        return {
            "resources": resources,
            "resource_templates": resource_templates,
            "tools": tools,
            "prompts": prompts,
        }


class ServerRegistry(BaseModel):
    """
    A registry that holds resources, tools, and prompts. SErver side this means our MCPResource, MCPTool, and MCPPrompt objects, which map to MCP schema but also have python function code attached.
    """

    resources: list[MCPResource | MCPResourceTemplate] = []
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

    def get(
        self, name: MCPMessage
    ) -> MCPTool | MCPResource | MCPPrompt | MCPResourceTemplate | None:
        """
        Get a tool, resource, or prompt being requested by an MCPMessage request.
        """
        if isinstance(
            name, ReadResourceRequest
        ):  # Need to double check schema if you are getting errors.
            return self._get_resource(name.params.name)
        elif isinstance(name, CallToolRequest):
            return self._get_tool(name.params.name)
        elif isinstance(name, GetPromptRequest):
            return self._get_prompt(name.params.name)
        else:
            raise TypeError(
                f"Cannot get {type(name)}. Must be of type ResourceRequest, ToolRequest, or PromptRequest."
            )

    def _get_tool(self, name: str) -> MCPTool | None:
        """
        Get a tool by name.
        """
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def _get_resource(self, name: str) -> MCPResource | None:
        """
        Get a resource by name.
        """
        for resource in self.resources:
            if resource.name == name:
                return resource
        return None

    def _get_prompt(self, name: str) -> MCPPrompt | None:
        """
        Get a prompt by name.
        """
        for prompt in self.prompts:
            if prompt.name == name:
                return prompt
        return None

from pydantic import BaseModel


class Definition(BaseModel):
    pass


class PromptDefinition(Definition):
    class Argument(BaseModel):
        name: str
        description: str
        required: bool

    name: str
    description: str
    arguments: list[Argument]


class ResourceDefinition(Definition):
    uri: str
    name: str
    description: str
    mimeType: str
    size: int


class ResourceTemplateDefinition(Definition):
    """
    This is for dynamically generated resources; schema tells LLM how to make the query.
    """

    uriTemplate: str
    name: str
    description: str
    mimeType: str


class ToolDefinition(Definition):
    class InputSchema(BaseModel):
        type: str
        properties: dict

    name: str
    description: str
    inputSchema: InputSchema

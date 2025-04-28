"""
TBD
This is the logic for routing the incoming JSONRPC ressponses to the appropriate MCPResponse object.
Inherits the registry so we have access to adding the listed resources, prompts, and tools to the registry.
"""

from MCPLite.messages import *
from MCPLite.primitives import ClientRegistry
from pydantic import ValidationError

MCPResponses = [
    CallToolResult,
    GetPromptResult,
    ReadResourceResult,
    ListResourcesResult,
    ListPromptsResult,
    ListToolsResult,
    InitializeResult,
]


def convert_jsonrpc_response(
    response: JSONRPCResponse,
) -> tuple[str, MCPResult] | None:
    """
    Convert the JSONRPC response to a tuple of (method, id, params).
    Mirrors the convert_jsonrpc function in Routes.py.

    Args:
        request: JSONRPCResponse: The JSONRPC request to convert.
        pydantic_model: BaseModel: The Pydantic model to validate the request against.
    """
    # Strip the request of the JSONRPC and ID fields, then validate the remainder.
    json_rpc_dict = response.model_dump()
    _ = str(json_rpc_dict.pop("jsonrpc"))
    id = str(json_rpc_dict.pop("id"))
    mcpresponse = None
    for mcpresponse_class in MCPResponses:
        try:
            mcpresponse = mcpresponse_class(**json_rpc_dict)
            return id, mcpresponse
        except ValidationError:
            pass
    if not mcpresponse:
        raise ValueError(
            f"Invalid JSON-RPC response, unable to convert to MCPResponse: {json_rpc_dict}"
        )


class ClientRoute:

    def __init__(self, registry: ClientRegistry):
        self.registry = registry

    def __call__(self, response: JSONRPCResponse) -> MCPResult:
        """
        Call the appropriate route based on the response type.
        Args:
            request (MCPResponse): The request to process.
        Returns:
            MCPMessage: The response to the request.
        """
        id, mcpresponse = convert_jsonrpc_response(response)
        if isinstance(mcpresponse, InitializeResult):
            # Handle the InitializeResult
            return mcpresponse
        elif isinstance(mcpresponse, ListResourcesResult):
            # Handle the ListResourcesResult
            self.registry.resources = mcpresponse.resources
            return mcpresponse
        elif isinstance(mcpresponse, ListPromptsResult):
            # Handle the ListPromptsResult
            self.registry.prompts = mcpresponse.prompts
            return mcpresponse
        elif isinstance(mcpresponse, ListToolsResult):
            # Handle the ListToolsResult
            self.registry.tools = mcpresponse.tools
            return mcpresponse
        else:
            raise ValueError(f"Unknown MCPResponse type: {type(mcpresponse)}")

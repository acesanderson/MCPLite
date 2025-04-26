from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from MCPLite.primitives.MCPTool import MCPTool
from MCPLite.primitives.MCPResource import MCPResource
from MCPLite.primitives.MCPPrompt import MCPPrompt


class ListPromptsResult(BaseModel):
    prompts: List[MCPPrompt]
    nextCursor: Optional[str] = Field(
        default=None,
        description="An opaque token representing the pagination position after the last returned result.",
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="This result property is reserved by the protocol to allow clients and servers to attach additional metadata to their responses.",
        alias="_meta",
    )

    class Config:
        json_schema_extra = {
            "description": "The server's response to a prompts/list request from the client."
        }


class ListResourcesResult(BaseModel):
    resources: List[MCPResource]
    nextCursor: Optional[str] = Field(
        default=None,
        description="An opaque token representing the pagination position after the last returned result.",
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="This result property is reserved by the protocol to allow clients and servers to attach additional metadata to their responses.",
        alias="_meta",
    )

    class Config:
        json_schema_extra = {
            "description": "The server's response to a resources/list request from the client."
        }


# LET'S NOT SWEAT THIS FOR NOW
# class ListResourceTemplatesResult(BaseModel):
#     resourceTemplates: List[MCPResourceTemplate]
#     nextCursor: Optional[str] = Field(
#         default=None,
#         description="An opaque token representing the pagination position after the last returned result.",
#     )
#     meta: Optional[Dict[str, Any]] = Field(
#         default=None,
#         description="This result property is reserved by the protocol to allow clients and servers to attach additional metadata to their responses.",
#         alias="_meta",
#     )
#
#     class Config:
#         json_schema_extra = {
#             "description": "The server's response to a resources/templates/list request from the client."
#         }
#
#
class ListToolsResult(BaseModel):
    tools: List[MCPTool]
    nextCursor: Optional[str] = Field(
        default=None,
        description="An opaque token representing the pagination position after the last returned result.",
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="This result property is reserved by the protocol to allow clients and servers to attach additional metadata to their responses.",
        alias="_meta",
    )

    class Config:
        json_schema_extra = {
            "description": "The server's response to a tools/list request from the client."
        }


# Adding JSONRPC wrapper classes for complete responses


class JSONRPCListPromptsResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: ListPromptsResult


class JSONRPCListResourcesResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: ListResourcesResult


# # DON'T CARE ABOUT RESOURCE TEMPLATES FOR NOW
# class JSONRPCListResourceTemplatesResponse(BaseModel):
#     jsonrpc: str = "2.0"
#     id: Union[str, int]
#     result: ListResourceTemplatesResult


class JSONRPCListToolsResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: ListToolsResult


# Helper function to create minimal examples
def create_minimal_list_response(response_type: str, id_value: Union[str, int] = "1"):
    if response_type == "prompts":
        result = ListPromptsResult(prompts=[Prompt(name="example-prompt")])
        return JSONRPCListPromptsResponse(id=id_value, result=result).json(
            by_alias=True, indent=2
        )

    elif response_type == "resources":
        result = ListResourcesResult(
            resources=[Resource(name="example-resource", uri="resource://example")]
        )
        return JSONRPCListResourcesResponse(id=id_value, result=result).json(
            by_alias=True, indent=2
        )

    # elif response_type == "resourceTemplates":
    #     result = ListResourceTemplatesResult(
    #         resourceTemplates=[
    #             ResourceTemplate(
    #                 name="example-template", uriTemplate="resource://example/{param}"
    #             )
    #         ]
    #     )
    #     return JSONRPCListResourceTemplatesResponse(id=id_value, result=result).json(
    #         by_alias=True, indent=2
    #     )
    #
    elif response_type == "tools":
        result = ListToolsResult(
            tools=[Tool(name="example-tool", inputSchema=Tool.InputSchema())]
        )
        return JSONRPCListToolsResponse(id=id_value, result=result).json(
            by_alias=True, indent=2
        )

    else:
        raise ValueError(f"Unknown response type: {response_type}")

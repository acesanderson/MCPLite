from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from Requests import MCPRequest


class ListResourcesRequest(MCPRequest):
    method: str = "resources/list"
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Optional parameters for the request"
    )

    class Config:
        json_schema_extra = {
            "description": "Sent from the client to request a list of resources the server has."
        }


# DON'T CARE ABOUT RESOURCE TEMPLATES FOR NOW
# class ListResourceTemplatesRequest(MCPRequest):
#     method: str = "resources/templates/list"
#     params: Optional[Dict[str, Any]] = Field(
#         default_factory=dict, description="Optional parameters for the request"
#     )
#
#     class Config:
#         json_schema_extra = {
#             "description": "Sent from the client to request a list of resource templates the server has."
#         }
#


class ListPromptsRequest(MCPRequest):
    method: str = "prompts/list"
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Optional parameters for the request"
    )

    class Config:
        json_schema_extra = {
            "description": "Sent from the client to request a list of prompts and prompt templates the server has."
        }


class ListToolsRequest(MCPRequest):
    method: str = "tools/list"
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Optional parameters for the request"
    )

    class Config:
        json_schema_extra = {
            "description": "Sent from the client to request a list of tools the server has."
        }


# REALLY DON'T CARE ABOUT PAGINATION FOR NOW
# All of these list requests can include a cursor parameter, so we can define a more specific params model:
class PaginationParams(BaseModel):
    cursor: Optional[str] = Field(
        default=None,
        description="An opaque token representing the current pagination position. "
        "If provided, the server should return results starting after this cursor.",
    )


# Now let's update our request models to use this more specific parameter type
class ListResourcesRequestWithPagination(BaseModel):
    method: str = "resources/list"
    params: Optional[PaginationParams] = Field(
        default_factory=PaginationParams, description="Parameters for pagination"
    )

    class Config:
        json_schema_extra = {
            "description": "Sent from the client to request a list of resources the server has."
        }


#
# class ListResourceTemplatesRequestWithPagination(BaseModel):
#     method: str = "resources/templates/list"
#     params: Optional[PaginationParams] = Field(
#         default_factory=PaginationParams, description="Parameters for pagination"
#     )
#
#     class Config:
#         json_schema_extra = {
#             "description": "Sent from the client to request a list of resource templates the server has."
#         }
#


class ListPromptsRequestWithPagination(BaseModel):
    method: str = "prompts/list"
    params: Optional[PaginationParams] = Field(
        default_factory=PaginationParams, description="Parameters for pagination"
    )

    class Config:
        json_schema_extra = {
            "description": "Sent from the client to request a list of prompts and prompt templates the server has."
        }


class ListToolsRequestWithPagination(BaseModel):
    method: str = "tools/list"
    params: Optional[PaginationParams] = Field(
        default_factory=PaginationParams, description="Parameters for pagination"
    )

    class Config:
        json_schema_extra = {
            "description": "Sent from the client to request a list of tools the server has."
        }

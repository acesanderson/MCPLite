from pydantic import BaseModel, Field
from typing import Any, Optional, Literal, Union
from enum import IntEnum


class JSONRPCError(BaseModel):
    """Error information for JSON-RPC."""

    code: int = Field(..., description="The error type that occurred")
    message: str = Field(..., description="A short description of the error")
    data: Optional[Any] = Field(
        None, description="Additional information about the error"
    )


class JSONRPCErrorResponse(BaseModel):
    """A response to a request that indicates an error occurred."""

    jsonrpc: Literal["2.0"] = "2.0"
    id: Union[str, int]
    error: JSONRPCError


class ErrorCode(IntEnum):
    """Standard JSON-RPC 2.0 error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # MCP-specific error codes can be defined in the range -32000 to -32099
    PROTOCOL_ERROR = -32000
    NOT_INITIALIZED = -32001
    ALREADY_INITIALIZED = -32002
    UNSUPPORTED_PROTOCOL_VERSION = -32003
    RESOURCE_NOT_FOUND = -32004
    RESOURCE_TEMPLATE_NOT_FOUND = -32005
    PROMPT_NOT_FOUND = -32006
    TOOL_NOT_FOUND = -32007
    CAPABILITY_NOT_SUPPORTED = -32008
    REQUEST_CANCELLED = -32009


class Error(BaseModel):
    """A response to a request that indicates an error occurred."""

    code: int = Field(..., description="The error type that occurred.")
    message: str = Field(
        ...,
        description="A short description of the error. The message should be limited to a concise single sentence.",
    )
    data: Optional[Any] = Field(
        None,
        description="Additional information about the error (e.g. detailed error information, nested errors etc.)",
    )

    class Config:
        allow_population_by_field_name = True

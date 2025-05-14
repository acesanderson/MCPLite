from pydantic import BaseModel, Field
from typing import Any, Optional, Literal, Union
from enum import IntEnum


class ErrorCode(IntEnum):
    """Standard JSON-RPC 2.0 error codes."""

    # Standard JSON-RPC 2.0 error codes
    PARSE_ERROR = -32700  # Invalid JSON
    INVALID_REQUEST = -32600  # The JSON is not a valid Request object
    METHOD_NOT_FOUND = -32601  # The requested method does not exist
    INVALID_PARAMS = -32602  # Invalid method parameters
    INTERNAL_ERROR = -32603  # Internal JSON-RPC error

    # MCP-specific error codes (from -32000 to -32099)
    PROTOCOL_ERROR = -32000  # Generic protocol error
    NOT_INITIALIZED = -32001  # Server not initialized yet
    ALREADY_INITIALIZED = -32002  # Server already initialized
    UNSUPPORTED_PROTOCOL_VERSION = -32003  # Protocol version not supported
    RESOURCE_NOT_FOUND = -32004  # Requested resource not found
    RESOURCE_TEMPLATE_NOT_FOUND = -32005  # Requested resource template not found
    PROMPT_NOT_FOUND = -32006  # Requested prompt not found
    TOOL_NOT_FOUND = -32007  # Requested tool not found
    CAPABILITY_NOT_SUPPORTED = -32008  # Requested capability not supported
    REQUEST_CANCELLED = -32009  # Request was cancelled


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
    id: Union[str, int, None]  # Can be None for parsing errors
    error: JSONRPCError


class MCPError(Exception):
    """
    Base exception class for MCP errors.

    This allows us to raise errors in a way that can be properly
    converted to JSON-RPC error responses.
    """

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

    def to_json_rpc(self, id: Union[str, int, None] = None) -> JSONRPCErrorResponse:
        """Convert the error to a JSON-RPC error response."""
        return JSONRPCErrorResponse(
            jsonrpc="2.0",
            id=id,
            error=JSONRPCError(code=self.code, message=self.message, data=self.data),
        )


# Pre-defined error classes for common error types
class ParseError(MCPError):
    """Invalid JSON was received by the server."""

    def __init__(self, message: str = "Parse error", data: Any = None):
        super().__init__(ErrorCode.PARSE_ERROR, message, data)


class InvalidRequestError(MCPError):
    """The JSON sent is not a valid Request object."""

    def __init__(self, message: str = "Invalid Request", data: Any = None):
        super().__init__(ErrorCode.INVALID_REQUEST, message, data)


class MethodNotFoundError(MCPError):
    """The method does not exist / is not available."""

    def __init__(self, message: str = "Method not found", data: Any = None):
        super().__init__(ErrorCode.METHOD_NOT_FOUND, message, data)


class InvalidParamsError(MCPError):
    """Invalid method parameter(s)."""

    def __init__(self, message: str = "Invalid params", data: Any = None):
        super().__init__(ErrorCode.INVALID_PARAMS, message, data)


class InternalError(MCPError):
    """Internal JSON-RPC error."""

    def __init__(self, message: str = "Internal error", data: Any = None):
        super().__init__(ErrorCode.INTERNAL_ERROR, message, data)


# MCP-specific error classes
class ProtocolError(MCPError):
    """Generic protocol error."""

    def __init__(self, message: str = "Protocol error", data: Any = None):
        super().__init__(ErrorCode.PROTOCOL_ERROR, message, data)


class NotInitializedError(MCPError):
    """Server not initialized yet."""

    def __init__(self, message: str = "Server not initialized", data: Any = None):
        super().__init__(ErrorCode.NOT_INITIALIZED, message, data)


class AlreadyInitializedError(MCPError):
    """Server already initialized."""

    def __init__(self, message: str = "Server already initialized", data: Any = None):
        super().__init__(ErrorCode.ALREADY_INITIALIZED, message, data)


class UnsupportedProtocolVersionError(MCPError):
    """Protocol version not supported."""

    def __init__(self, message: str = "Unsupported protocol version", data: Any = None):
        super().__init__(ErrorCode.UNSUPPORTED_PROTOCOL_VERSION, message, data)


class ResourceNotFoundError(MCPError):
    """Requested resource not found."""

    def __init__(self, message: str = "Resource not found", data: Any = None):
        super().__init__(ErrorCode.RESOURCE_NOT_FOUND, message, data)


class ResourceTemplateNotFoundError(MCPError):
    """Requested resource template not found."""

    def __init__(self, message: str = "Resource template not found", data: Any = None):
        super().__init__(ErrorCode.RESOURCE_TEMPLATE_NOT_FOUND, message, data)


class PromptNotFoundError(MCPError):
    """Requested prompt not found."""

    def __init__(self, message: str = "Prompt not found", data: Any = None):
        super().__init__(ErrorCode.PROMPT_NOT_FOUND, message, data)


class ToolNotFoundError(MCPError):
    """Requested tool not found."""

    def __init__(self, message: str = "Tool not found", data: Any = None):
        super().__init__(ErrorCode.TOOL_NOT_FOUND, message, data)


class CapabilityNotSupportedError(MCPError):
    """Requested capability not supported."""

    def __init__(self, message: str = "Capability not supported", data: Any = None):
        super().__init__(ErrorCode.CAPABILITY_NOT_SUPPORTED, message, data)


class RequestCancelledError(MCPError):
    """Request was cancelled."""

    def __init__(self, message: str = "Request cancelled", data: Any = None):
        super().__init__(ErrorCode.REQUEST_CANCELLED, message, data)

from typing import Optional, Any
from pydantic import BaseModel
from enum import Enum


# 1. Request
class Request(BaseModel):
    """
    Excepts a response from the other side.
    """

    method: str
    params: Optional[dict[str, Any]] = None


# 2. Result
class Result(dict[str, Any]):
    """
    Successful response to a request. (actually just a dict)
    """

    pass


# 3. Error
class Error(BaseModel):
    """
    Indicates a request has failed.
    """

    code: int
    message: str
    data: Optional[Any] = None


# 4. Notification
class Notification(BaseModel):
    """
    One-way messages that don't expect a response.
    """

    method: str
    params: Optional[dict[str, Any]] = None


# Error handling
class ErrorCode(Enum):
    """
    Standard JSON-RPC error codes.
    """

    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603

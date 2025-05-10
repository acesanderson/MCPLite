from pydantic import BaseModel, Field
from typing import Any, Optional, Literal, Union
from MCPLite.messages.MCPMessage import MCPMessage
from enum import Enum


class NotificationMethod(str, Enum):
    """
    Notification methods are constrained to this list.
    """

    # Client -> Server
    INITIALIZED = "notifications/initialized"
    ROOTS_LIST_CHANGED = "notifications/roots/list_changed"

    # Server -> Client
    PROGRESS = "notifications/progress"
    MESSAGE = "notifications/message"
    RESOURCES_UPDATED = "notifications/resources/updated"
    RESOURCES_LIST_CHANGED = "notifications/resources/list_changed"
    TOOLS_LIST_CHANGED = "notifications/tools/list_changed"
    PROMPTS_LIST_CHANGED = "notifications/prompts/list_changed"

    # Bidirectional
    CANCELLED = "notifications/cancelled"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return repr(self.value)


class LogLevel(str, Enum):
    """Log levels for message notifications."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class JSONRPCNotification(BaseModel):
    """A notification which does not expect a response."""

    jsonrpc: Literal["2.0"] = "2.0"
    method: NotificationMethod
    params: Optional[dict[str, Any]] = Field(None)

    def from_json_rpc(self) -> "MCPNotification":
        """Convert the JSON-RPC notification to an MCPNotification."""
        return MCPNotification(
            method=self.method,
            params=self.params or {},
        )


class MCPNotification(MCPMessage):
    """Base class for all notifications."""

    method: NotificationMethod
    params: dict[str, Any] = Field(default_factory=dict)

    def to_json_rpc(self) -> JSONRPCNotification:
        """Convert the notification to a JSON-RPC format."""
        return JSONRPCNotification(
            jsonrpc="2.0",
            method=self.method,
            params=self.params,
        )


# Client -> Server Notifications
class InitializedNotification(MCPNotification):
    """Sent from client to server after initialization is complete."""

    method: NotificationMethod = NotificationMethod.INITIALIZED
    params: dict[str, Any] = Field(default_factory=dict)


class RootsListChangedNotification(MCPNotification):
    """Sent when the client's root directories have changed."""

    method: NotificationMethod = NotificationMethod.ROOTS_LIST_CHANGED
    params: dict[str, Any] = Field(default_factory=dict)


# Server -> Client Notifications


class ProgressNotification(MCPNotification):
    """Sent to report progress on long-running operations."""

    method: NotificationMethod = NotificationMethod.PROGRESS

    def __init__(
        self,
        progressToken: Union[str, int],
        progress: float,
        total: Optional[float] = None,
        **kwargs
    ):
        params = {"progressToken": progressToken, "progress": progress}
        if total is not None:
            params["total"] = total
        super().__init__(params=params, **kwargs)


class LogMessageNotification(MCPNotification):
    """Sent to log messages to the client."""

    method: NotificationMethod = NotificationMethod.MESSAGE

    def __init__(
        self,
        level: LogLevel,
        message: str,
        logger: Optional[str] = None,
        data: Optional[Any] = None,
        **kwargs
    ):
        params = {"level": level.value, "message": message}
        if logger is not None:
            params["logger"] = logger
        if data is not None:
            params["data"] = data
        super().__init__(params=params, **kwargs)


class ResourceUpdatedNotification(MCPNotification):
    """Sent when a subscribed resource has been updated."""

    method: NotificationMethod = NotificationMethod.RESOURCES_UPDATED

    def __init__(self, uri: str, **kwargs):
        params = {"uri": uri}
        super().__init__(params=params, **kwargs)


class ResourceListChangedNotification(MCPNotification):
    """Sent when the list of available resources has changed."""

    method: NotificationMethod = NotificationMethod.RESOURCES_LIST_CHANGED
    params: dict[str, Any] = Field(default_factory=dict)


class ToolListChangedNotification(MCPNotification):
    """Sent when the list of available tools has changed."""

    method: NotificationMethod = NotificationMethod.TOOLS_LIST_CHANGED
    params: dict[str, Any] = Field(default_factory=dict)


class PromptListChangedNotification(MCPNotification):
    """Sent when the list of available prompts has changed."""

    method: NotificationMethod = NotificationMethod.PROMPTS_LIST_CHANGED
    params: dict[str, Any] = Field(default_factory=dict)


# Bidirectional Notifications


class CancelledNotification(MCPNotification):
    """Sent to indicate that an operation was cancelled."""

    method: NotificationMethod = NotificationMethod.CANCELLED

    def __init__(
        self, requestId: Union[str, int], reason: Optional[str] = None, **kwargs
    ):
        params = {"requestId": requestId}
        if reason is not None:
            params["reason"] = reason
        super().__init__(params=params, **kwargs)

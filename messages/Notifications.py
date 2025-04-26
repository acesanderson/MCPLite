from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal
from MCPLite.messages.MCPMessage import MCPMessage


class JSONRPCNotification(BaseModel):
    """A notification which does not expect a response."""

    jsonrpc: Literal["2.0"] = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = Field(None)


class MCPNotification(MCPMessage):
    """Base class for all notifications."""

    method: str
    params: Dict[str, Any] = Field(default_factory=dict)

    def to_json_rpc(self) -> JSONRPCNotification:
        """Convert the notification to a JSON-RPC format."""
        return JSONRPCNotification(
            jsonrpc="2.0",
            method=self.method,
            params=self.params,
        )

"""
This takes the registry from mcplite.py.
This is the server class that will handle incoming requests and route them to the appropriate primitives. It handles all of the application logic as well (since the primitives are in the registry). Dependency injection pattern.
"""

from pydantic import Json, ValidationError
from typing import Optional
from MCPLite.messages import (
    JSONRPCRequest,
    MCPResult,
    JSONRPCResponse,
    JSONRPCNotification,
    JSONRPCError,
    JSONRPCErrorResponse,
    MCPError,
    ParseError,
    InvalidRequestError,
    MethodNotFoundError,
    InvalidParamsError,
    InternalError,
    ProtocolError,
    NotInitializedError,
    AlreadyInitializedError,
    UnsupportedProtocolVersionError,
    ResourceNotFoundError,
    ResourceTemplateNotFoundError,
    PromptNotFoundError,
    ToolNotFoundError,
    CapabilityNotSupportedError,
    RequestCancelledError,
)
from MCPLite.primitives import ServerRegistry
from MCPLite.transport.Transport import Transport
from MCPLite.routes.ServerRoutes import ServerRoute
import json

from MCPLite.logs.logging_config import get_logger

# Get logger with this module's name
logger = get_logger(__name__)


class Server:
    # Map method names to their corresponding handling functions.
    def __init__(self, registry: ServerRegistry, transport: Optional[Transport] = None):
        self.registry = registry
        self.transport = transport
        self.route = ServerRoute(self)
        self.initialized: bool = False
        self.initialization_time: Optional[float] = None
        self.client_info: Optional[dict] = None

    def process_message(self, json_str: Json) -> Json:
        """
        Receive JSON from the client, parse it, and return a response.
        """
        logger.info(f"Server received JSON: {json_str}")

        request_id = None  # Default ID for error responses

        try:
            # First, parse the JSON
            try:
                json_obj = json.loads(json_str)
            except json.JSONDecodeError as e:
                # Handle JSON parsing errors
                logger.error(f"Failed to decode JSON: {e}")
                raise ParseError(f"Invalid JSON format: {str(e)}")

            # Extract ID for potential error responses
            request_id = json_obj.get("id")

            # Check if this is a method-based message (request or notification)
            if "method" not in json_obj:
                raise InvalidRequestError("Missing 'method' field in request")

            # Try to validate as a request first
            try:
                request = JSONRPCRequest.model_validate(json_obj)
                logger.info("Valid JSON-RPC request, processing...")
                return self._process_request(json_obj)
            except ValidationError:
                # Not a valid request, try as notification
                try:
                    notification = JSONRPCNotification.model_validate(json_obj)
                    logger.info("Valid JSON-RPC notification, processing...")
                    self._process_notification(json_obj)
                    return json.dumps(json_obj)  # Return the original for notifications
                except ValidationError:
                    # Neither a valid request nor notification
                    raise InvalidRequestError(
                        "Message is neither a valid request nor notification"
                    )

        except MCPError as e:
            # Handle MCP-specific errors
            logger.error(f"MCP error: {e}")
            error_response = e.to_json_rpc(id=request_id)
            return error_response.model_dump_json()

        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error: {e}", exc_info=True)
            internal_error = InternalError(f"Internal server error: {str(e)}")
            error_response = internal_error.to_json_rpc(id=request_id)
            return error_response.model_dump_json()

    def _process_request(self, json_obj: dict) -> Json:
        # Process the request.
        json_rpc_request = JSONRPCRequest(**json_obj)
        mcp_request = json_rpc_request.from_json_rpc()
        logger.info(f"Routing request: {mcp_request}")
        response: MCPResult = self.route(mcp_request)
        # Convert the response to JSON-RPC format.
        # TBD: Implement actual indexing.
        json_rpc_response = JSONRPCResponse(
            id="blah", jsonrpc="2.0", result=response.model_dump()
        )
        logger.info(f"Server sending JSON-RPC response: {json_rpc_response}")
        return json_rpc_response.model_dump_json()

    def _process_notification(self, json_obj: dict) -> None:
        # Process the notification.
        json_rpc_notification = JSONRPCNotification(**json_obj)
        mcp_notification = json_rpc_notification.from_json_rpc()
        logger.info(f"Routing notification: {mcp_notification}")
        self.route(mcp_notification)

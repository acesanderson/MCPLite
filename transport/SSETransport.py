# SSEServerTransport.py
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from typing import Dict, Callable, Optional
from pydantic import Json
import asyncio, json, uuid, aiohttp
from MCPLite.transport.Transport import Transport
from MCPLite.logs.logging_config import get_logger

logger = get_logger(__name__)


class SSEServerTransport(Transport):
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        """
        Initialize the SSE server transport.
        Note: Bind to localhost by default for security.
        """
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.clients: Dict[str, asyncio.Queue] = {}
        self.message_handler: Optional[Callable] = None

        # Add CORS middleware with restrictions
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],  # Restrict as needed
            allow_credentials=True,
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
        )

        # Set up routes
        self.app.post("/mcp")(self.handle_client_message)
        self.app.get("/mcp/events")(self.sse_endpoint)

    async def validate_origin(self, request: Request) -> bool:
        """Validate the origin header to prevent DNS rebinding attacks."""
        origin = request.headers.get("Origin")
        allowed_origins = ["http://localhost:3000"]  # Configure as needed

        if not origin or origin not in allowed_origins:
            raise HTTPException(status_code=403, detail="Origin not allowed")
        return True

    async def handle_client_message(self, request: Request):
        """Handle incoming client messages via HTTP POST."""
        await self.validate_origin(request)

        # Get client ID from headers or generate a new one
        client_id = request.headers.get("X-Client-ID")
        if not client_id:
            client_id = str(uuid.uuid4())

        # Ensure client has a message queue
        if client_id not in self.clients:
            self.clients[client_id] = asyncio.Queue()

        # Get JSON data from request
        json_data = await request.json()

        # Process message using the handler
        if self.message_handler:
            response_json = self.message_handler(json.dumps(json_data))

            # If there's a response, queue it for SSE delivery
            if response_json:
                await self.clients[client_id].put(response_json)

        return {"client_id": client_id}

    async def sse_endpoint(self, request: Request):
        """SSE endpoint for server-to-client communication."""
        await self.validate_origin(request)

        client_id = request.headers.get("X-Client-ID")
        if not client_id or client_id not in self.clients:
            raise HTTPException(status_code=400, detail="Invalid client ID")

        # Create event generator for this client
        async def event_generator():
            try:
                while True:
                    # Get message from queue or wait
                    message = await self.clients[client_id].get()

                    # Yield the message as an SSE event
                    yield {"data": message}
            except asyncio.CancelledError:
                # Clean up when client disconnects
                if client_id in self.clients:
                    del self.clients[client_id]

        return EventSourceResponse(event_generator())

    def start(self):
        """Start the SSE server."""
        import uvicorn

        uvicorn.run(self.app, host=self.host, port=self.port)

    def stop(self):
        """Stop the SSE server."""
        # Uvicorn handles this via signals
        pass

    def send_json_message(self, json_str: str) -> Optional[Json]:
        """
        Server-side method to send a message to a client.
        This queues the message for delivery via SSE.
        """
        # This method would be called by your Server class
        # The actual sending happens via the client's SSE connection
        # We'd need client_id to target specific client
        # For now, broadcast to all clients
        for client_queue in self.clients.values():
            asyncio.create_task(client_queue.put(json_str))
        return None


class SSEClientTransport(Transport):
    def __init__(self, server_url: str):
        """
        Initialize the SSE client transport.
        Args:
            server_url: URL of the MCP server (e.g. "http://localhost:8000")
        """
        self.server_url = server_url
        self.client_id = str(uuid.uuid4())
        self.session = None
        self.sse_response = None
        self.message_queue = asyncio.Queue()
        self.running = False
        self.sse_task = None

    async def _init_session(self):
        """Initialize the HTTP session."""
        self.session = aiohttp.ClientSession(
            headers={
                "X-Client-ID": self.client_id,
                "Origin": "http://localhost:3000",
            }
        )

    async def _listen_for_sse_events(self):
        """Listen for SSE events from the server."""
        url = f"{self.server_url}/mcp/events"
        try:
            async with self.session.get(url) as response:
                self.sse_response = response
                if response.status != 200:
                    logger.error(f"SSE connection failed with status {response.status}")
                    return

                # Process the SSE stream
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        # Put the message in the queue for processing
                        await self.message_queue.put(data)
        except Exception as e:
            logger.error(f"SSE connection error: {e}")
        finally:
            # Reconnect after a delay if still running
            if self.running:
                await asyncio.sleep(1)
                self.sse_task = asyncio.create_task(self._listen_for_sse_events())

    async def start_async(self):
        """Start the client transport asynchronously."""
        self.running = True
        await self._init_session()
        self.sse_task = asyncio.create_task(self._listen_for_sse_events())

    def start(self):
        """Start the client transport."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start_async())

    async def stop_async(self):
        """Stop the client transport asynchronously."""
        self.running = False
        if self.sse_task:
            self.sse_task.cancel()
            try:
                await self.sse_task
            except asyncio.CancelledError:
                pass

        if self.session:
            await self.session.close()

    def stop(self):
        """Stop the client transport."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.stop_async())

    async def send_json_message_async(self, json_str: str) -> Optional[Json]:
        """Send a JSON message to the server asynchronously."""
        url = f"{self.server_url}/mcp"
        if not self.session:
            await self._init_session()

        try:
            async with self.session.post(
                url, data=json_str, headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    logger.error(f"Error sending message: {response.status}")
                    return None

                # For requests that expect responses, we need to wait for the SSE event
                response_data = await response.json()

                # Check if this is a notification that doesn't expect a response
                try:
                    msg_dict = json.loads(json_str)
                    if "id" not in msg_dict:  # Notifications don't have IDs
                        return None
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON message")
                    return None

                # Wait for response via SSE
                try:
                    # Set a reasonable timeout
                    response_json = await asyncio.wait_for(
                        self.message_queue.get(), timeout=30
                    )
                    return response_json
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for response")
                    return None

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None

    def send_json_message(self, json_str: str) -> Optional[Json]:
        """Send a JSON message to the server."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.send_json_message_async(json_str))

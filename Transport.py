from abc import ABC, abstractmethod
from typing import Any, Dict, Callable


class BaseTransport(ABC):
    """Base class for all transports"""
    pass


class ClientTransport(BaseTransport):
    """Transport for sending requests from client to server"""
    
    @abstractmethod
    def send_request(self, method: str, params: Any) -> Any:
        """Send a request and return the response"""
        pass


class ServerTransport(BaseTransport):
    """Transport for receiving requests on the server side"""
    
    @abstractmethod
    def register_method(self, method: str, handler: Callable) -> None:
        """Register a method handler for incoming requests"""
        pass
    
    @abstractmethod
    def start(self) -> None:
        """Start listening for incoming requests"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop listening for incoming requests"""
        pass


class DirectClientTransport(ClientTransport):
    """Client transport that directly calls the server transport"""
    
    def __init__(self, server_transport: 'DirectServerTransport'):
        self.server_transport = server_transport
    
    def send_request(self, method: str, params: Any) -> Any:
        """
        'Send' a request by directly calling the server transport's
        handle_request method
        """
        return self.server_transport.handle_request(method, params)


class DirectServerTransport(ServerTransport):
    """Server transport that directly handles method calls"""
    
    def __init__(self):
        self._methods: Dict[str, Callable] = {}
        self._running = False
    
    def register_method(self, method: str, handler: Callable) -> None:
        """Register a method handler"""
        self._methods[method] = handler
    
    def handle_request(self, method: str, params: Any) -> Any:
        """Process a request and return the result"""
        if not self._running:
            raise RuntimeError("Server transport is not running")
            
        if method not in self._methods:
            raise ValueError(f"Method '{method}' not registered")
        
        return self._methods[method](params)
    
    def start(self) -> None:
        """Start the server transport"""
        self._running = True
    
    def stop(self) -> None:
        """Stop the server transport"""
        self._running = False
Then your client and server would be implemented like this:
pythonclass Server:
    def __init__(self, transport: ServerTransport):
        self.transport = transport
        
        # Register methods
        self.transport.register_method("add", self.add)
        self.transport.register_method("subtract", self.subtract)
    
    def start(self):
        self.transport.start()
    
    def stop(self):
        self.transport.stop()
    
    def add(self, params: Dict[str, Any]) -> Dict[str, Any]:
        a = params.get("a", 0)
        b = params.get("b", 0)
        return {"result": a + b}
    
    def subtract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        a = params.get("a", 0)
        b = params.get("b", 0)
        return {"result": a - b}




if __name__ == "__main__":
    # Create the transports
    server_transport = DirectServerTransport()
    client_transport = DirectClientTransport(server_transport)

    # Initialize server and client
    server = Server(server_transport)
    client = Client(client_transport)

    # Start the server
    server.start()

    # Make requests
    result = client.add(5, 3)  # Returns 8

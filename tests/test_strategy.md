## Test Structure & Organization

```
tests/
├── unit/
│   ├── messages/           # Test message serialization/validation
│   ├── primitives/         # Test individual components
│   ├── transport/          # Test transport layers in isolation
│   └── server/            # Test server routing logic
├── integration/
│   ├── client_server/      # End-to-end client-server interactions
│   ├── transport/          # Transport-specific integration tests
│   └── host/              # Host orchestration tests
├── regression/
│   ├── scenarios/          # Captured real-world scenarios
│   └── compatibility/      # MCP protocol compliance
├── fixtures/
│   ├── servers/           # Test server implementations
│   ├── data/              # Sample data files
│   └── configs/           # Test configurations
└── conftest.py            # pytest fixtures and setup
```

## Testing Strategy by Layer

**1. Unit Tests (Isolated Components)**
- Test each primitive (MCPTool, MCPResource, etc.) independently
- Mock external dependencies completely
- Focus on business logic, validation, error handling
- Use DirectTransport extensively here since you maintain observability

**2. Integration Tests (Component Interactions)**
- Test client-server handshakes across different transports
- Test message routing and response handling
- Test registry aggregation and capability discovery
- Use controlled test servers with known responses

**3. Regression Tests (Captured Scenarios)**
- Record real interaction sequences (request/response pairs)
- Create "golden master" tests for complex agent loops
- Test backward compatibility with protocol changes
- Capture edge cases and bug scenarios as they're discovered

## Key Testing Principles for Your Architecture

**Transport Abstraction Testing**
- Create a MockTransport that records all messages
- Test the same scenarios across DirectTransport, StdioTransport, etc.
- Verify message serialization is transport-agnostic

**Server Registry Testing**
- Test capability aggregation from multiple clients
- Verify routing decisions are deterministic
- Test error handling when servers are unavailable

**Agent Loop Testing**
- Mock the LLM responses with canned JSON
- Test tool call sequences and error recovery
- Verify conversation state management

## Debugging & Observability Tips

**Structured Logging for Tests**
- Create test-specific log configurations
- Log all MCP messages with structured data
- Use correlation IDs to trace requests across components

**Test Fixtures as Documentation**
- Your test servers become living documentation
- Create minimal, focused test servers for specific scenarios
- Use them to validate protocol compliance

**Snapshot Testing**
- Capture full conversation flows as snapshots
- Detect when changes break existing behavior
- Especially useful for testing system prompt generation

## Specific Recommendations

**Start with DirectTransport Tests**
Since you have good observability there, create comprehensive test coverage using DirectTransport first. Then use those same test scenarios with other transports to verify behavior consistency.

**Mock External Dependencies**
For things like file systems (Obsidian server) or web requests (fetch server), create mock implementations that return predictable data.

**Test Error Paths Thoroughly**
MCP has many error conditions - test malformed messages, network failures, server timeouts, etc. Your error handling is critical for robustness.

**Protocol Compliance Suite**
Create tests that verify your implementation matches the official MCP specification exactly. This becomes your regression safety net.

The key insight is that your DirectTransport gives you a "glass box" view that's perfect for comprehensive testing, while your other transports should behave identically but are "black box" from a testing perspective. Build your confidence with DirectTransport tests, then use those same scenarios to validate the other transports.

# Code examples
Here are concrete code examples for each testing layer:

## Unit Tests

**Test Individual Primitives:**
```python
# tests/unit/primitives/test_mcp_tool.py
import pytest
from MCPLite.primitives import MCPTool
from MCPLite.messages import TextContent

def test_mcp_tool_creation():
    def add_numbers(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b
    
    tool = MCPTool(function=add_numbers)
    
    assert tool.name == "add_numbers"
    assert tool.description == "Add two numbers together."
    assert tool.input_schema == {"a": "int", "b": "int"}

def test_mcp_tool_execution():
    def multiply(x: int, y: int) -> int:
        """Multiply two numbers."""
        return x * y
    
    tool = MCPTool(function=multiply)
    result = tool(x=5, y=3)
    
    assert isinstance(result, TextContent)
    assert result.text == "15"

def test_mcp_tool_validation_errors():
    def bad_function():
        pass  # No docstring, no type annotations
    
    with pytest.raises(ValueError, match="Function needs a docstring"):
        MCPTool(function=bad_function)
```

**Test Message Serialization:**
```python
# tests/unit/messages/test_requests.py
import json
from MCPLite.messages import CallToolRequest, CallToolRequestParams

def test_call_tool_request_serialization():
    params = CallToolRequestParams(name="test_tool", arguments={"arg1": "value1"})
    request = CallToolRequest(params=params)
    
    json_rpc = request.to_jsonrpc()
    
    assert json_rpc.method == "tools/call"
    assert json_rpc.params["name"] == "test_tool"
    assert json_rpc.params["arguments"]["arg1"] == "value1"

def test_request_deserialization():
    json_data = {
        "jsonrpc": "2.0",
        "id": "test-id",
        "method": "tools/call",
        "params": {
            "name": "test_tool",
            "arguments": {"x": 10, "y": 20}
        }
    }
    
    request = JSONRPCRequest.model_validate(json_data)
    mcp_request = request.from_json_rpc()
    
    assert isinstance(mcp_request, CallToolRequest)
    assert mcp_request.params.name == "test_tool"
```

## Integration Tests

**Client-Server Interaction:**
```python
# tests/integration/test_client_server.py
import pytest
from MCPLite.mcplite import MCPLite
from MCPLite.client import Client
from MCPLite.transport import DirectTransport

@pytest.fixture
def test_server():
    mcp = MCPLite(transport="DirectTransport")
    
    @mcp.tool
    def calculator(operation: str, a: int, b: int) -> int:
        """Perform basic math operations."""
        if operation == "add":
            return a + b
        elif operation == "multiply":
            return a * b
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    return mcp

@pytest.fixture
def test_client(test_server):
    client = Client(server_function=test_server.server.process_message)
    client.initialize()
    return client

def test_tool_discovery(test_client):
    """Test that client can discover server tools."""
    assert len(test_client.registry.tools) == 1
    tool = test_client.registry.tools[0]
    assert tool.name == "calculator"
    assert "math operations" in tool.description

def test_tool_execution(test_client):
    """Test end-to-end tool execution."""
    from MCPLite.messages import CallToolRequest, CallToolRequestParams
    
    params = CallToolRequestParams(
        name="calculator", 
        arguments={"operation": "add", "a": 5, "b": 3}
    )
    request = CallToolRequest(params=params)
    
    result = test_client.send_request(request)
    
    assert result.content[0].text == "8"
    assert not result.isError
```

**Transport Compatibility:**
```python
# tests/integration/transport/test_transport_compatibility.py
import pytest
from MCPLite.mcplite import MCPLite
from MCPLite.client import Client
from MCPLite.transport import DirectTransport, StdioClientTransport

# Shared test scenarios
TEST_SCENARIOS = [
    {
        "name": "simple_addition",
        "request": {"method": "tools/call", "params": {"name": "add", "arguments": {"a": 2, "b": 3}}},
        "expected_result": "5"
    },
    {
        "name": "resource_access",
        "request": {"method": "resources/read", "params": {"uri": "test://data"}},
        "expected_contains": "test data"
    }
]

@pytest.mark.parametrize("transport_type", ["direct", "stdio"])
@pytest.mark.parametrize("scenario", TEST_SCENARIOS)
def test_transport_behavior_consistency(transport_type, scenario, test_server_command):
    """Verify all transports produce identical results for the same inputs."""
    
    if transport_type == "direct":
        client = Client(server_function=test_server_command)
    elif transport_type == "stdio":
        client = Client(transport=StdioClientTransport(["python", "test_server.py"]))
    
    client.initialize()
    
    # Execute the scenario
    request = create_request_from_dict(scenario["request"])
    result = client.send_request(request)
    
    # Verify expected behavior
    if "expected_result" in scenario:
        assert result.content[0].text == scenario["expected_result"]
    if "expected_contains" in scenario:
        assert scenario["expected_contains"] in result.content[0].text
```

## Regression Tests

**Golden Master Testing:**
```python
# tests/regression/test_agent_conversations.py
import json
import pytest
from pathlib import Path
from MCPLite.host import Host

GOLDEN_CONVERSATIONS = Path(__file__).parent / "golden_conversations"

@pytest.mark.parametrize("conversation_file", GOLDEN_CONVERSATIONS.glob("*.json"))
def test_conversation_replay(conversation_file):
    """Replay recorded conversations and verify outputs match."""
    
    with open(conversation_file) as f:
        conversation = json.load(f)
    
    host = Host(
        model="mock",  # Use deterministic mock model
        servers=conversation["config"]["servers"]
    )
    
    # Replay each step
    for step in conversation["steps"]:
        if step["type"] == "user_query":
            result = host.agent_query(step["input"])
            
            # Compare against golden output
            expected = step["expected_output"]
            assert normalize_output(result) == normalize_output(expected)
        
        elif step["type"] == "tool_call":
            # Verify tool was called with expected parameters
            assert step["tool_name"] in [call["tool"] for call in host.last_tool_calls]

def normalize_output(text):
    """Normalize output for comparison (remove timestamps, IDs, etc.)"""
    import re
    # Remove UUIDs, timestamps, etc.
    text = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', 'UUID', text)
    text = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', 'TIMESTAMP', text)
    return text.strip()
```

**Protocol Compliance:**
```python
# tests/regression/test_mcp_compliance.py
import pytest
from MCPLite.messages import *

class TestMCPCompliance:
    """Test compliance with official MCP protocol specification."""
    
    def test_initialize_handshake_sequence(self):
        """Test the three-part initialization handshake."""
        
        # 1. Client sends initialize request
        init_request = minimal_client_initialization()
        assert init_request.method == "initialize"
        assert "protocolVersion" in init_request.params.model_dump()
        
        # 2. Server responds with capabilities
        init_response = minimal_server_initialization()
        assert "capabilities" in init_response.model_dump()
        assert "serverInfo" in init_response.model_dump()
        
        # 3. Client sends initialized notification
        initialized = InitializedNotification()
        assert initialized.method == "notifications/initialized"
    
    def test_error_response_format(self):
        """Verify error responses match MCP specification."""
        from MCPLite.messages import ToolNotFoundError
        
        error = ToolNotFoundError("Tool 'nonexistent' not found")
        error_response = error.to_json_rpc(id="test-123")
        
        assert error_response.jsonrpc == "2.0"
        assert error_response.id == "test-123"
        assert error_response.error.code == -32007  # MCP error code for tool not found
        assert "not found" in error_response.error.message
    
    @pytest.mark.parametrize("message_class", [
        CallToolRequest, GetPromptRequest, ReadResourceRequest,
        ListToolsRequest, ListPromptsRequest, ListResourcesRequest
    ])
    def test_request_message_validation(self, message_class):
        """Test all request messages validate according to JSON schema."""
        # This would validate against the official MCP JSON schemas
        sample_message = create_sample_message(message_class)
        
        # Serialize and validate against official schema
        json_data = sample_message.model_dump()
        assert validate_against_mcp_schema(json_data, message_class.__name__)
```

**Scenario Capture:**
```python
# tests/regression/test_captured_scenarios.py
class TestCapturedBugs:
    """Regression tests for previously discovered bugs."""
    
    def test_resource_template_parameter_extraction_bug_123(self):
        """
        Regression test for bug #123: Resource template parameters 
        weren't being extracted correctly from URI patterns.
        """
        from MCPLite.primitives import MCPResourceTemplate
        
        def get_todo(date: str) -> str:
            """Get todo for specific date."""
            return f"Todo for {date}"
        
        template = MCPResourceTemplate(
            function=get_todo,
            uriTemplate="todo://items/{date}"
        )
        
        # This used to fail - ensure it works now
        assert template.match_uri("todo://items/2025-01-15")
        result = template(param="todo://items/2025-01-15")
        assert "2025-01-15" in result
    
    def test_stdio_transport_deadlock_bug_456(self):
        """
        Regression test for bug #456: StdioTransport would deadlock
        when server process died unexpectedly.
        """
        from MCPLite.transport import StdioClientTransport
        
        # Create transport with command that will fail
        transport = StdioClientTransport(["nonexistent-command"])
        
        # This should raise a clear error, not deadlock
        with pytest.raises(RuntimeError, match="Could not start server"):
            transport.start()
```

**Test Fixtures:**
```python
# tests/conftest.py
import pytest
from MCPLite.mcplite import MCPLite

@pytest.fixture
def mock_model():
    """Mock model that returns predictable responses."""
    class MockModel:
        def __init__(self):
            self.responses = []
            self.call_count = 0
        
        def stream(self, messages, **kwargs):
            response = self.responses[self.call_count % len(self.responses)]
            self.call_count += 1
            
            class MockChunk:
                def __init__(self, content):
                    self.choices = [type('obj', (), {'delta': type('obj', (), {'content': content})()})]
            
            for char in response:
                yield MockChunk(char)
    
    return MockModel()

@pytest.fixture
def minimal_test_server():
    """Minimal server for testing basic functionality."""
    mcp = MCPLite(transport="DirectTransport")
    
    @mcp.tool
    def echo(message: str) -> str:
        """Echo the input message."""
        return message
    
    @mcp.resource(uri="test://data")
    def test_data() -> str:
        """Return test data."""
        return "This is test data"
    
    return mcp
```

This structure gives you:
- **Fast feedback** from unit tests
- **Confidence** from integration tests  
- **Protection** from regression tests
- **Debuggability** through DirectTransport in all layers

The key is starting with DirectTransport everywhere to build confidence, then expanding to other transports using the same test scenarios.

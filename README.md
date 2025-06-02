Model: claude-sonnet-4-20250514  Temperature: None  Query: # README.md Generation Prompt  You are an expert technical w...
# MCPLite

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A lightweight, developer-friendly Python implementation of the Model Context Protocol (MCP) that makes it easy to connect AI assistants to external tools and data sources.**

MCPLite provides a clean, FastAPI-inspired interface for creating MCP servers and an intelligent host system for orchestrating multiple servers in AI agent workflows.

## Quick Start

**Create an MCP server in 30 seconds:**

```python
from MCPLite import MCPLite

mcp = MCPLite()

@mcp.tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@mcp.resource(uri="data://example")
def get_data() -> str:
    """Get some example data."""
    return "Hello from MCPLite!"

if __name__ == "__main__":
    mcp.run()
```

**Use the intelligent chat interface:**

```python
from MCPLite import MCPChat

# Connect to multiple MCP servers with one line
chat = MCPChat(model="gpt", servers=["fetch", "obsidian"])
chat.chat()  # Start interactive session
```

## Core Value Demonstration

MCPLite shines in **multi-server agent workflows** where you need to combine capabilities from different sources:

```python
from MCPLite.host import Host

# Orchestrate multiple MCP servers
host = Host(model="gpt", servers=["fetch", "filesystem", "calculator"])

# Ask complex questions that require multiple tools
result = host.agent_query(
    "Fetch the latest Python release notes, save them to a file, "
    "and calculate how many days since the last release"
)
```

**What makes this powerful:**
- **Automatic capability discovery** - The host finds and aggregates all available tools/resources
- **Intelligent routing** - Requests automatically go to the right server
- **Agent loop handling** - Multi-step tool usage works seamlessly
- **Transport abstraction** - Same code works with stdio, direct, or HTTP transports

## Installation & Setup

**Install MCPLite:**
```bash
pip install mcplite  # When published
# Or for development:
git clone https://github.com/yourusername/MCPLite.git
cd MCPLite
pip install -e .
```

**Basic usage patterns:**

```python
# 1. Create servers with decorators (FastAPI-style)
from MCPLite import MCPLite

mcp = MCPLite()

@mcp.tool
def my_tool(param: str) -> str:
    """Tool description here."""
    return f"Processed: {param}"

# 2. Use the chat interface
from MCPLite import MCPChat
chat = MCPChat(servers=["my_server"])
chat.chat()

# 3. Orchestrate programmatically
from MCPLite.host import Host
host = Host(servers=["server1", "server2"])
result = host.agent_query("Your question here")
```

## Architecture Overview

MCPLite implements a clean separation between **servers** (capability providers) and **hosts** (orchestrators):

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Assistant  │────│   MCPLite Host   │────│   MCP Servers   │
│   (GPT, Claude) │    │   (Orchestrator) │    │   (Tools/Data)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Key Components:**
- **MCPLite**: FastAPI-inspired server creation with decorators
- **Host**: Intelligent orchestration engine for multi-server workflows  
- **Transport Layer**: Supports stdio, direct (in-process), and HTTP/SSE
- **MCPChat**: Ready-to-use chat interface with MCP capabilities

## Basic Usage

**Define tools, resources, and prompts:**

```python
from MCPLite import MCPLite

mcp = MCPLite()

@mcp.tool
def fetch_weather(city: str) -> str:
    """Get weather for a city."""
    # Your weather API logic here
    return f"Sunny and 72°F in {city}"

@mcp.resource(uri="config://settings")
def get_settings() -> str:
    """Application configuration."""
    return "debug=true, api_key=hidden"

@mcp.prompt
def analysis_prompt(data: str) -> str:
    """Generate analysis prompt."""
    return f"Please analyze this data: {data}"
```

**Resource templates with parameters:**

```python
@mcp.resource(uri="todos://items/{date}")
def get_todos(date: str) -> str:
    """Get todos for a specific date."""
    return f"Todos for {date}: Buy groceries, Walk dog"
```

## Contributing

We welcome contributions! MCPLite is designed to be:

- **Beginner-friendly**: Clear patterns, good documentation
- **Production-ready**: Robust error handling, comprehensive testing
- **Extensible**: Easy to add new transports and capabilities

**Development setup:**
```bash
git clone https://github.com/yourusername/MCPLite.git
cd MCPLite
pip install -e ".[dev]"
pytest  # Run tests
```

**Key areas for contribution:**
- Additional transport implementations (WebSocket, etc.)
- More built-in server examples
- Enhanced debugging and monitoring tools
- Documentation and tutorials

## Support & Maintenance

- **Status**: Active development, production-ready core
- **Python**: 3.9+ supported
- **Dependencies**: Pydantic, Chain framework, Rich (for UI)
- **License**: MIT

**Get help:**
- [Documentation](docs/) - Comprehensive guides and API reference
- [GitHub Issues](https://github.com/yourusername/MCPLite/issues) - Bug reports and feature requests
- [Discussions](https://github.com/yourusername/MCPLite/discussions) - Questions and community

---

MCPLite makes the Model Context Protocol accessible to Python developers without sacrificing power or flexibility. Start simple with decorators, scale up to multi-server orchestration.

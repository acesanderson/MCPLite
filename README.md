# MCPLite

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/yourusername/MCPLite)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue)](https://python.org)

**A lightweight, pythonic implementation of the Model Context Protocol (MCP) for seamless integration of external tools and data sources into LLM applications.**

MCPLite provides everything you need to build, connect, and orchestrate MCP servers with a clean, decorator-based API inspired by FastAPI. Turn any Python function into an MCP tool, resource, or prompt with just a decorator.

## Quick Start

```python
from MCPLite import MCPLite

# Create your MCP server
mcp = MCPLite(transport="stdio")

@mcp.tool
def calculator(operation: str, a: int, b: int) -> int:
    """Perform basic math operations."""
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b
    raise ValueError(f"Unknown operation: {operation}")

@mcp.resource(uri="data://current-time")
def current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().isoformat()

if __name__ == "__main__":
    mcp.run()
```

**Start using it immediately:**
```bash
# Install dependencies
pip install pydantic rich chain-of-thought beautifulsoup4 markdownify

# Run your server
python my_server.py

# Or use our pre-built servers
python -m MCPLite.servers.fetch
```

## Core Value Demonstration

MCPLite excels at bridging the gap between language models and external capabilities. Here's a complete example showing tool creation, client connection, and agent orchestration:

```python
from MCPLite.host import Host
from MCPLite.mcpchat import MCPChat

# 1. Quick server setup with multiple capabilities
mcp = MCPLite(transport="direct")

@mcp.tool
def web_search(query: str, limit: int = 3) -> str:
    """Search the web and return results."""
    # Your search implementation
    return f"Found {limit} results for: {query}"

@mcp.resource(uri="weather://current/{city}")
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: 72°F, sunny"

# 2. Instant client connection and capability discovery
host = Host(model="gpt-4", servers=["fetch", "filesystem"])

# 3. Natural language interaction with automatic tool routing
result = host.agent_query(
    "What's the weather in San Francisco and find recent news about AI?"
)

# 4. Or use the interactive chat interface
chat = MCPChat(model="claude", servers=["fetch", "obsidian"])
chat.chat()  # Starts interactive session with rich formatting
```

## Installation & Setup

```bash
# Core installation
pip install pydantic rich

# For web functionality
pip install requests beautifulsoup4 markdownify

# For stdio transport (recommended)
pip install chain-of-thought  # Our LLM integration layer
```

**Environment Setup:**
```bash
# For Obsidian integration
export OBSIDIAN_PATH="/path/to/your/obsidian/vault"

# For advanced logging
export MCPLITE_LOG_LEVEL="DEBUG"
```

## Architecture Overview

MCPLite follows a clean separation of concerns:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCPChat/Host  │    │   MCPLite Core   │    │  MCP Servers    │
│  (Orchestration)│◄──►│   (Framework)    │◄──►│  (Your Tools)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐              │
         │              │    Transport    │              │
         │              │ (stdio/direct)  │              │
         └──────────────┤                 ├──────────────┘
                        └─────────────────┘
```

**Key Components:**
- **MCPLite**: Server framework with decorators for tools/resources/prompts
- **Host**: Client orchestration engine for multi-server coordination  
- **MCPChat**: Interactive chat interface with rich formatting
- **Transport**: Pluggable communication layer (stdio, direct, SSE)

## Basic Usage

### Server Creation
```python
from MCPLite import MCPLite

mcp = MCPLite(transport="stdio")

@mcp.tool
def analyze_code(code: str, language: str) -> str:
    """Analyze code for potential issues."""
    return f"Analyzed {len(code)} chars of {language} code"

@mcp.prompt
def code_review_prompt(code: str) -> str:
    """Generate a code review prompt."""
    return f"Please review this code:\n\n{code}"
```

### Client Integration
```python
from MCPLite.host import Host

# Connect to multiple servers
host = Host(
    model="gpt-4",
    servers=["fetch", "filesystem", "my-custom-server"]
)

# Natural language queries automatically route to appropriate tools
response = host.agent_query(
    "Read the README.md file and summarize the project structure"
)
```

### Interactive Chat
```python
from MCPLite.mcpchat import MCPChat

chat = MCPChat(
    model="claude-3",
    servers=["fetch", "obsidian"],
    preferred_transport="stdio"
)

# Rich interactive interface with:
# - Syntax highlighting
# - MCP capability display  
# - Real-time tool execution
# - Conversation history
chat.chat()
```

## Built-in Servers

### Fetch Server
Web content retrieval with automatic markdown conversion:
```python
# Automatically converts HTML to clean markdown
# Respects robots.txt and rate limits
# Supports proxy configuration
python -m MCPLite.servers.fetch
```

### Obsidian Server  
Secure filesystem operations within your Obsidian vault:
```python
# Sandboxed file operations
# Search across notes with patterns
# Metadata extraction and analysis
export OBSIDIAN_PATH="/path/to/vault"
python -m MCPLite.servers.obsidian
```

## Contributing

MCPLite is designed for extensibility. Create custom servers by implementing the decorator pattern:

```python
from MCPLite import MCPLite

mcp = MCPLite(transport="stdio")

@mcp.tool
def your_custom_tool(param: str) -> str:
    """Your tool description here."""
    return f"Processed: {param}"
```

**Development Setup:**
```bash
git clone https://github.com/yourusername/MCPLite
cd MCPLite
pip install -e .
```

## Support & Documentation

- **Quick Help**: Use `/status` in MCPChat to see connected capabilities
- **Server Management**: Built-in server inventory and discovery
- **Transport Options**: stdio (production), direct (development), SSE (web)
- **Logging**: Comprehensive logging with configurable levels

**Example Commands:**
```bash
# View available servers
python -c "from MCPLite.inventory import ServerInventory; ServerInventory().view_servers()"

# Test server connection
python -m MCPLite.mcpchat --server fetch --model gpt-4
```

---

MCPLite brings the power of the Model Context Protocol to Python developers with zero configuration overhead. Build once, connect everywhere.

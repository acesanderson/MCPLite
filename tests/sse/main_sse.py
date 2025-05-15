"""
Vibe coded this.
"""

from MCPLite.logs.logging_config import configure_logging
import logging

# Set up logging with trace mode for detailed flow tracking
logger = configure_logging(
    level=logging.DEBUG,  # Show all log levels
    # level=logging.ERROR,  # Show only errors
    log_file="mcplite_trace.log",  # Also save to file
    trace_mode=True,  # Include line numbers and function names
)

# Rest of your application code
from MCPLite.host.Host import Host
from MCPLite.client.Client import Client
from MCPLite.transport import SSEClientTransport
from pathlib import Path

# Define the path to the example resource template
dir_path = Path(__file__).parent
todos_path = dir_path / "example_resource_template"
# Set up our Server
logger.info("Initializing MCPLite application")
server_command = ["python", "stdio_server.py"]


if __name__ == "__main__":
    # Create our client
    client = Client(transport=SSEClientTransport("http://localhost:8000"))
    client.initialize()
    # Set up our Host
    host = Host(model="gpt")
    host.add_client(client)
    # host.run_prompt(prompt_name="partner", topic="Business Intelligence")
    host.query("What were my todos for May 3 2025?")

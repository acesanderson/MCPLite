"""
New e2e script; take our dummy code from Host.py.
Next up: add initialization logic
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
from jinja2 import Template
from MCPLite.mcplite.mcplite import MCPLite
from MCPLite.host.Host import Host
from MCPLite.client.Client import Client
from MCPLite.main.example_prompt import partner_prompt
from MCPLite.transport import StdioClientTransport
from pathlib import Path

# Set up our Server
logger.info("Initializing MCPLite application")
# server_command = ["python", "stdio_server.py"]
server_command = ["python", "/home/bianders/Brian_Code/MCPLite/servers/obsidian.py"]

if __name__ == "__main__":
    # Create our client
    client = Client(
        transport=StdioClientTransport(server_command)
    )  # Default is DirectTransport
    client.initialize()
    # Set up our Host
    host = Host(model="gpt")
    host.add_client(client)
    # host.run_prompt(prompt_name="partner", topic="Business Intelligence")
    host.query(
        "Find the file titled 'Summary of my Job.md' in my fileserver and summarize it for me."
    )

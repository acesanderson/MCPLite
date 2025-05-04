"""
New e2e script; take our dummy code from Host.py.
Next up: add initialization logic
"""

from MCPLite.logs.logging_config import configure_logging
import logging

# Set up logging with trace mode for detailed flow tracking
logger = configure_logging(
    level=logging.DEBUG,  # Show all log levels
    log_file="mcplite_trace.log",  # Also save to file
    trace_mode=True,  # Include line numbers and function names
)

# Rest of your application code
from jinja2 import Template
from MCPLite.mcplite.mcplite import MCPLite
from MCPLite.transport.Transport import Transport, DirectTransport
from MCPLite.server.Server import Server
from MCPLite.host.Host import Host
from MCPLite.client.Client import Client
from MCPLite.main.example_prompt import partner_prompt

# Set up our Server
logger.info("Initializing MCPLite application")
mcp = MCPLite(transport="DirectTransport")


@mcp.resource(uri="names://sheepadoodle")
def name_of_sheepadoodle() -> str:
    """
    Returns the name of the sheepadoodle.
    """
    return "Otis"


@mcp.tool
def add(a: int, b: int) -> int:
    """
    Add two numbers.
    """
    return a + b


@mcp.prompt
def partner(topic: str):
    """
    Suggest some endorsing partners for a given topic.
    """
    prompt_template = Template(partner_prompt)
    prompt_string = prompt_template.render({"topic": topic})
    return prompt_string


# Create our client
client = Client(
    server_function=mcp.server.process_message
)  # Default is DirectTransport
client.initialize()
#
# Set up our Host
# host = Host(model="gpt")
# host.add_client(client)
# host.query("What's the name of my cute sheepadoodle?")

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
from pathlib import Path

# Define the path to the example resource template
dir_path = Path(__file__).parent
todos_path = dir_path / "example_resource_template"
# Set up our Server
logger.info("Initializing MCPLite application")
mcp = MCPLite(transport="DirectTransport")


@mcp.resource(uri="names://sheepadoodle")
def name_of_sheepadoodle() -> str:
    """
    Returns the name of the sheepadoodle.
    """
    return "Otis"


@mcp.resource(uri="file://todos/{date}")
def todos(date: str) -> str:
    """
    Returns a list of todos for a given date. Requires YYYY-MM-DD format.
    """
    todo = list(todos_path.glob(f"{date}*.md"))[0]
    return str(todo)


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


if __name__ == "__main__":
    # Create our client
    client = Client(
        server_function=mcp.server.process_message
    )  # Default is DirectTransport
    client.initialize()
    # Set up our Host
    host = Host(model="gpt")
    host.add_client(client)
    # host.run_prompt(prompt_name="partner", topic="Business Intelligence")
    host.query("What were my todos for May 3 2025?")

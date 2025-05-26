from MCPLite.logs.logging_config import configure_logging
import logging

# Set up logging with trace mode for detailed flow tracking
logger = configure_logging(
    # level=logging.DEBUG,  # Show all log levels
    level=logging.ERROR,  # Show only errors
    log_file="mcplite_trace.log",  # Also save to file
    trace_mode=True,  # Include line numbers and function names
)

# Rest of your application code
from MCPLite.host.Host import Host
from MCPLite.client.Client import Client
from MCPLite.transport import StdioClientTransport

# Set up our Server
logger.info("Initializing MCPLite application")
server_command = ["python", "fetch_stdio.py"]
# server_command = ["python", "/home/bianders/Brian_Code/MCPLite/servers/obsidian.py"]

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
        "Please read the docs at this link https://modelcontextprotocol.io/ and summarize the key points for me."
    )

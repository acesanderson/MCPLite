from MCPLite.mcplite.mcplite import MCPLite
from pathlib import Path
from MCPLite.logs.logging_config import get_logger
from MCPLite.transport import StdioServerTransport
from MCPLite.tests.direct.example_prompt import partner_prompt
from jinja2 import Template

# Get logger with this module's name
logger = get_logger(__name__)


# Define the path to the example resource template
dir_path = Path(__file__).parent
todos_path = dir_path / "example_resource_template"
# Set up our Server
logger.info("Initializing MCPLite application")
mcp = MCPLite(transport=StdioServerTransport())


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
    # Extract the date from the URI
    uri = date.split("/")[-1]
    # Read the file from the todos_path directory
    todo = list(todos_path.glob(f"{uri}*.md"))[0]
    content = todo.read_text()
    return content


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
    mcp.run()

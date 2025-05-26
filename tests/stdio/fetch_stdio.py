"""
MCPLite Fetch Server - Web content fetching and conversion for LLM usage.
Implements the same functionality as the official MCP fetch server.
"""

from MCPLite.mcplite.mcplite import MCPLite
from MCPLite.logs.logging_config import get_logger
from MCPLite.transport import StdioServerTransport
import requests
import re
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import markdownify
import argparse

# Get logger with this module's name
logger = get_logger(__name__)

# Configuration
DEFAULT_MAX_LENGTH = 5000
DEFAULT_USER_AGENT_AUTONOMOUS = "ModelContextProtocol/1.0 (Autonomous; +https://github.com/modelcontextprotocol/servers)"
DEFAULT_USER_AGENT_USER = "ModelContextProtocol/1.0 (User-Specified; +https://github.com/modelcontextprotocol/servers)"


class FetchConfig:
    def __init__(self):
        self.ignore_robots_txt = False
        self.custom_user_agent = None
        self.proxy_url = None


# Global config instance
config = FetchConfig()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MCPLite Fetch Server")
    parser.add_argument(
        "--ignore-robots-txt",
        action="store_true",
        help="Ignore robots.txt restrictions",
    )
    parser.add_argument("--user-agent", type=str, help="Custom user agent string")
    parser.add_argument("--proxy-url", type=str, help="Proxy URL for requests")

    args = parser.parse_args()

    # Update global config
    config.ignore_robots_txt = args.ignore_robots_txt
    config.custom_user_agent = args.user_agent
    config.proxy_url = args.proxy_url


def check_robots_txt(url: str, user_agent: str) -> bool:
    """Check if the URL is allowed by robots.txt."""
    if config.ignore_robots_txt:
        return True

    try:
        parsed_url = urlparse(url)
        robots_url = urljoin(
            f"{parsed_url.scheme}://{parsed_url.netloc}", "/robots.txt"
        )

        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logger.warning(f"Could not check robots.txt for {url}: {e}")
        return True  # Allow if we can't check


def clean_html_to_markdown(html_content: str, url: str) -> str:
    """Convert HTML content to clean markdown."""
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Remove comments
        from bs4 import Comment

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Convert to markdown
        markdown_content = markdownify.markdownify(
            str(soup), heading_style="ATX", strip=["script", "style"]
        )

        # Clean up extra whitespace
        markdown_content = re.sub(r"\n\s*\n\s*\n", "\n\n", markdown_content)
        markdown_content = re.sub(r"[ \t]+", " ", markdown_content)

        return markdown_content.strip()

    except Exception as e:
        logger.error(f"Error converting HTML to markdown: {e}")
        return html_content  # Return original if conversion fails


def fetch_url_content(url: str, is_user_initiated: bool = False) -> tuple[str, str]:
    """
    Fetch content from URL and return (content, mime_type).

    Args:
        url: The URL to fetch
        is_user_initiated: Whether the request was user-initiated (affects user-agent and robots.txt)

    Returns:
        Tuple of (content, mime_type)
    """
    # Validate URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError("Invalid URL format")

    # Determine user agent
    if config.custom_user_agent:
        user_agent = config.custom_user_agent
    elif is_user_initiated:
        user_agent = DEFAULT_USER_AGENT_USER
    else:
        user_agent = DEFAULT_USER_AGENT_AUTONOMOUS

    # Check robots.txt for autonomous requests
    if not is_user_initiated and not check_robots_txt(url, user_agent):
        raise ValueError(f"Access to {url} is disallowed by robots.txt")

    # Prepare request
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    proxies = {}
    if config.proxy_url:
        proxies = {"http": config.proxy_url, "https": config.proxy_url}

    try:
        response = requests.get(
            url, headers=headers, proxies=proxies, timeout=30, allow_redirects=True
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()

        return response.text, content_type

    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch {url}: {str(e)}")


# Set up our Server
logger.info("Initializing MCPLite Fetch Server")
mcp = MCPLite(transport=StdioServerTransport())


@mcp.tool
def fetch(
    url: str,
    max_length: int = DEFAULT_MAX_LENGTH,
    start_index: int = 0,
    raw: bool = False,
) -> str:
    """
    Fetch a URL from the internet and extract its contents as markdown.

    Args:
        url: URL to fetch (required)
        max_length: Maximum number of characters to return (default: 5000)
        start_index: Start content from this character index (default: 0)
        raw: Get raw content without markdown conversion (default: false)

    Returns:
        The fetched content, optionally converted to markdown
    """
    logger.info(f"Fetching URL: {url}")

    try:
        # Fetch the content (this is a tool call, so autonomous)
        content, content_type = fetch_url_content(url, is_user_initiated=False)

        # Convert to markdown unless raw is requested or it's not HTML
        if not raw and "html" in content_type:
            content = clean_html_to_markdown(content, url)

        # Apply start_index and max_length
        if start_index > 0:
            content = content[start_index:]

        if len(content) > max_length:
            content = content[:max_length]
            logger.info(f"Content truncated to {max_length} characters")

        logger.info(f"Successfully fetched {len(content)} characters from {url}")
        return content

    except Exception as e:
        error_msg = f"Error fetching {url}: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


@mcp.prompt
def fetch_prompt(url: str) -> str:
    """
    Fetch a URL and extract its contents as markdown.

    Args:
        url: URL to fetch (required)

    Returns:
        A prompt asking to fetch the URL content
    """
    return f"""Please fetch the content from the following URL and convert it to markdown format:

URL: {url}

The content should be clean, readable markdown that preserves the main structure and information from the original page while removing navigation, advertisements, and other non-essential elements."""


@mcp.resource(uri="fetch://status")
def fetch_status() -> str:
    """
    Returns the current status and configuration of the fetch server.
    """
    status_info = {
        "server": "MCPLite Fetch Server",
        "version": "1.0.0",
        "configuration": {
            "ignore_robots_txt": config.ignore_robots_txt,
            "custom_user_agent": config.custom_user_agent or "Default",
            "proxy_url": config.proxy_url or "None",
            "default_max_length": DEFAULT_MAX_LENGTH,
        },
        "supported_features": [
            "HTML to Markdown conversion",
            "Robots.txt compliance",
            "Custom User-Agent support",
            "Proxy support",
            "Content truncation and chunking",
            "Raw content fetching",
        ],
    }

    import json

    return json.dumps(status_info, indent=2)


@mcp.resource(uri="fetch://help")
def fetch_help() -> str:
    """
    Returns help information about using the fetch server.
    """
    return """# MCPLite Fetch Server Help

## Tools

### fetch
Fetches a URL from the internet and extracts its contents as markdown.

**Parameters:**
- `url` (string, required): URL to fetch
- `max_length` (integer, optional): Maximum number of characters to return (default: 5000)
- `start_index` (integer, optional): Start content from this character index (default: 0)
- `raw` (boolean, optional): Get raw content without markdown conversion (default: false)

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://example.com",
      "max_length": 10000
    }
  }
}
```

## Prompts

### fetch_prompt
Provides a template for fetching URL content.

**Parameters:**
- `url` (string, required): URL to fetch

## Resources

### fetch://status
Returns current server status and configuration.

### fetch://help
Returns this help information.

## Configuration

The server supports the following command-line options:
- `--ignore-robots-txt`: Ignore robots.txt restrictions
- `--user-agent`: Custom user agent string
- `--proxy-url`: Proxy URL for requests

## Security Features

- Robots.txt compliance (can be disabled)
- Different user agents for autonomous vs user-initiated requests
- Proxy support for network restrictions
- Content length limits to prevent excessive resource usage
"""


if __name__ == "__main__":
    # Parse command line arguments
    parse_arguments()

    logger.info("Starting MCPLite Fetch Server...")
    logger.info(
        f"Configuration: ignore_robots_txt={config.ignore_robots_txt}, "
        f"custom_user_agent={'Set' if config.custom_user_agent else 'Default'}, "
        f"proxy_url={'Set' if config.proxy_url else 'None'}"
    )

    mcp.run()

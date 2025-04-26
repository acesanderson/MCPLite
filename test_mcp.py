"""
Minimal MCP sever mock for development purposes.
"""

import mcplite


@mcplite.tool
def add(a: int, b: int) -> int:
    """
    Add two numbers.
    """
    return a + b


@mcplite.resource("http://example.com/resource", "text/plain", 1024)
def my_resource():
    """
    This is a resource that returns a string.
    """
    return "This is my resource."


list_capabilities = mcplite.list_capabilities()
print(list_capabilities)

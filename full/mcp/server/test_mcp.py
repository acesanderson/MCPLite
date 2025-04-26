import mcp


@mcp.tool
def add(a: int, b: int) -> int:
    """
    Add two numbers.
    """
    return a + b


@mcp.resource("http://example.com/resource", "text/plain", 1024)
def my_resource():
    """
    This is a resource that returns a string.
    """
    return "This is my resource."


print(mcp.registry)

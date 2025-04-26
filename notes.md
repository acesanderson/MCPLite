# Roadmap for implementation
## Server
- rework the primitives (Tool, Resource, Prompt) as decorators that convert functions to mcp objects
- these mcp objects have the following input/output/variables per the official MCP schema:
    - definition (currently 'to_dict' -- should return json)
    - request (this is json)
    - response (this is the return type -- json)
- pydantic classes for all of the above

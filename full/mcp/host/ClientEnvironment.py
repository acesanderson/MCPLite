"""
ClientEnvironment is a module attached to a host.
It has a registry of clients/mcp servers.
It handles crafting of Request objects that get sent to the specific Client (who then handles json transport for a specific MCP server).
It also handles rendering of Responses as prompts.
"""

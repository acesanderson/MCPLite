NOTE: THIS IS ABANDONED IN FAVOR OF MCP LITE WHICH IS MORE IN MY ZONE OF PROXIMAL DEVELOPMENT

### Directories
- host: handles ClientEnvironment and whatever the integration with Chat class looks like.
- messages: these are our Pydantic classes mapped to MCP schema
- server: the base logic for creating a server, including Transport classes (test, http, stdio, sse), the base classes for primitives (tools, resources, prompts, samplings), the Server class itself, and the decorators (in MCP.py for now) for composing a server.
- client: the base class of Client, which is tied to a specific MCP server by a specific transport mechanism. This converts pydantic classes to json and handled communications with the server. Actual rendering / application logic is handled in the host, in ClientEnvironment
- protocol: this may be temporary; this is where I'm building protocol from bottom up (right now it's transport / session logic)

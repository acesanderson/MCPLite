from MCPLite.mcplite.mcplite import MCPLite

mcp = MCPLite()    

# Dummy resource function
    def name_of_sheepadoodle() -> str:
        """
        Returns the name of the sheepadoodle.
        """
        return "Otis"

    # Dummy tool function
    def add(a: int, b: int) -> int:
        """
        Add two numbers.
        """
        return a + b

    # The objects that will be working together
    resource = MCPResource(
        function=name_of_sheepadoodle,
        uri="names://sheepadoodle",
    )
    resource_definition = resource.definition
    tool = MCPTool(function=add)
    tool_definition = tool.definition
    host = Host(model=Model("gpt"))
    host.registry.tools.append(tool_definition)
    host.registry.resources.append(resource_definition)
    host.system_prompt = host.generate_system_prompt()
    print(host.system_prompt)
    server = Server()
    client = Client(transport=DirectTransport(server.process_message))
    host.add_client(client)
    stuff = host.query("What is 2333 + 1266? Use the add function.")
    # stuff = host.query("What is the name of my cute sheepadoodle?")
    # print(type(stuff))
    # print(stuff)

from Chain import Model, Prompt, Chain, create_system_message

system_prompt = """
You have access to one or more of following capabilities through the MCP framework:

TOOLS - Functions you can call to perform actions
   - Use tools when you need to execute operations or compute something
   - Each tool has a name, description, and defined parameters
   - Tools require explicit human approval before execution
   - To call a tool, use the format:
     ```
     {
       "method": "tools/call",
       "name": "tool_name",
       "arguments": {
         "param1": "value1",
         "param2": "value2"
       }
     }
     ```

RESOURCES - Sources of information you can access
   - Use resources when you need to retrieve information
   - Resources are accessed via URI patterns that may be static or templated
   - To read a resource, use the format:
     ```
     {
       "method": "resources/read",
       "uri": "resource://example"
     }
     ```

PROMPTS - Pre-defined templates for specific interactions
   - Use prompts when you need to follow a standardized format for a particular task
   - Prompts require user selection and cannot be automatically invoked
   - To use a prompt, use the format:
     ```
     {
       "method": "prompts/get",
       "name": "prompt_name",
       "arguments": {
         "arg1": "value1",
         "arg2": "value2"
       }
     }
     ```

When you need to use any capability:
1. First determine whether you need a Tool, Resource, or Prompt
2. Format your request using the correct structure as shown above
3. For tools, acknowledge that human approval may be required
4. If an error occurs, try different parameters or an alternative approach
5. Report on whether the capability was successfully used

The system will handle formatting your request into a proper JSON-RPC message, execute it, and return the results, which you should incorporate into your response appropriately.


You have access to the following tools:

{
  "name": "add",
  "description": "Add two numbers.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "a": "int",
      "b": "int"
    }
  }
}

{
  "name": "open_garage_door",
  "description": "Open the user's garage door.",
  "inputSchema": {
    "type": "object",
    "properties": {
    }
  }
}

You have access to the following resources:

{
  "uri": "http://example.com/resource",
  "name": "my_resource",
  "description": "This is a resource that returns a string.",
  "mimeType": "text/plain",
  "size": 1024
}
"""


if __name__ == "__main__":
    messages = create_system_message(system_prompt)
    prompt = Prompt("Please add 9801 and 1444")
    model = Model("claude")
    chain = Chain(prompt=prompt, model=model)
    response = chain.run(messages=messages)
    print(response)

"""
Some higher level classes --
- Primitive: base class for Resource, Tool, and Prompt, and handles basic json input and output
- Transport: our transport layer, with subclasses for http, sse, stdio
"""

from pydantic import BaseModel


class Primitive(BaseModel):
    """
    Base class for Tool, Resource, and Prompt.
    Handles basic json input and output.
    """

    pass

"""
This module defines a Pydantic model for handling JSON strings.
TBD: use this instead of pydantic.Json if I want even stricter validation!
"""

from pydantic import BaseModel, model_validator
import json
from typing import Any


class JsonData(BaseModel):
    raw: str
    parsed: Any = None

    @model_validator(mode="after")
    def parse_json(self):
        try:
            self.parsed = json.loads(self.raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        return self

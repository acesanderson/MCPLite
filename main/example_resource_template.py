"""
Create some example resource files for development + testing of the MCPResourceTemplate.
"""

from pathlib import Path

dir_path = Path(__file__).parent

resource_paths = []
for i in range(1, 4):
    resource_path = dir_path / "example_resource_template" / f"2025-05-0{i}.md"
    resource_path.touch()
    resource_paths.append(resource_path)

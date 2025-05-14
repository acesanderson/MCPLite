"""
This is just my implementation of Claude's filesystem MCP.
"""

from MCPLite.mcplite.mcplite import MCPLite
from MCPLite.transport import StdioServerTransport
from pathlib import Path
import os, fnmatch  # fnmatch is Unix-like globbing (wildcards)

# --- Global Setup ---
_obsidian_path_env = os.getenv("OBSIDIAN_PATH")
if not _obsidian_path_env:
    raise EnvironmentError("OBSIDIAN_PATH environment variable is not set.")

OBSIDIAN_ROOT = Path(_obsidian_path_env).resolve()
if not OBSIDIAN_ROOT.is_dir():
    raise NotADirectoryError(
        f"OBSIDIAN_PATH '{OBSIDIAN_ROOT}' is not a valid directory."
    )

# Pre-calculate allowed directories (as resolved strings for easier checking if needed)
# For a strict "is within OBSIDIAN_ROOT" check, this list might be less critical
# if every path operation is checked against OBSIDIAN_ROOT.
# However, it's useful for `list_allowed_directories`.
ALLOWED_DIRS_SET = set()
for root, _, _ in os.walk(OBSIDIAN_ROOT):
    ALLOWED_DIRS_SET.add(str(Path(root).resolve()))


def is_path_within_obsidian_root(path_to_check: str | Path) -> bool:
    """Checks if the given path is within the OBSIDIAN_ROOT sandbox."""
    try:
        resolved_path = Path(path_to_check).resolve()
        # Python 3.9+
        # return resolved_path.is_relative_to(OBSIDIAN_ROOT)
        # Older Python:
        return str(resolved_path).startswith(str(OBSIDIAN_ROOT)) and (
            OBSIDIAN_ROOT == resolved_path or OBSIDIAN_ROOT in resolved_path.parents
        )
    except (
        Exception
    ):  # Catches FileNotFoundError from resolve if path doesn't exist, or other errors
        return False


# --- MCP Instance ---
mcp = MCPLite(transport=StdioServerTransport())


# -- Tools --
@mcp.tool
def search_files(path: str, pattern: str, excludePatterns: list[str] = []):
    """
    Recursively search for files/directories from a starting directory
    within the OBSIDIAN_PATH.
    """
    # Security: Ensure the starting search path is allowed
    if not is_path_within_obsidian_root(path):
        raise ValueError(f"Search path '{path}' is outside the allowed sandbox.")

    # Convert to Path object for consistency
    search_root = Path(path).resolve()  # Resolve again to be absolutely sure

    if not search_root.is_dir():  # Check after resolving and security check
        raise ValueError(f"Path '{path}' is not a directory.")
    # ... (rest of your validation and search logic)
    # The os.walk will be rooted at search_root, which is already validated.
    matches = []
    for root_str, dirs, files in os.walk(search_root):
        current_root = Path(root_str)  # For easier joining
        for name in files + dirs:
            # full_path = os.path.join(root, name) # old
            full_path_obj = current_root / name
            if fnmatch.fnmatch(name, pattern) and not any(
                fnmatch.fnmatch(name, ex) for ex in excludePatterns
            ):
                matches.append(str(full_path_obj))  # Return strings as per original
    return matches


@mcp.tool
def read_file(path: str):
    """Read complete contents of a file within OBSIDIAN_PATH."""
    if not is_path_within_obsidian_root(path):
        raise ValueError(f"Path '{path}' is outside the allowed sandbox.")

    file_path = Path(
        path
    ).resolve()  # Resolve for safety, though is_path_within_obsidian_root does it
    if not file_path.is_file():
        raise ValueError(f"Path '{path}' is not a file.")
    # Read the file
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.tool
def read_multiple_files(paths: list[str]):
    """
    Read multiple files simultaneously within OBSIDIAN_PATH.
    """
    # Security: Check if each path is within the allowed sandbox
    for path in paths:
        if not is_path_within_obsidian_root(path):
            raise ValueError(f"Path '{path}' is outside the allowed sandbox.")

    # Check if the paths are valid files
    contents = {}
    for path in paths:
        file_path = Path(path).resolve()
        if not file_path.is_file():
            raise ValueError(f"Path '{path}' is not a file.")

        # Read the file
        try:
            contents[str(file_path)] = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Handle binary files or non-UTF-8 text files
            raise ValueError(f"File '{path}' is not a valid UTF-8 text file.")
        except Exception as e:
            raise ValueError(f"Error reading file '{path}': {str(e)}")

    return contents


@mcp.tool
def list_directory(path: str):
    """
    List directory contents with [FILE] or [DIR] prefixes.
    The directory must be within the OBSIDIAN_PATH sandbox.
    """
    # Security: Ensure the path is within the allowed sandbox
    if not is_path_within_obsidian_root(path):
        # This check in is_path_within_obsidian_root inherently handles
        # if the path resolves correctly and is under OBSIDIAN_ROOT.
        # If path doesn't exist, resolve() in the helper would raise FileNotFoundError,
        # and is_path_within_obsidian_root would return False.
        raise ValueError(
            f"Path '{path}' is outside the allowed sandbox or does not resolve to a valid location within it."
        )

    # Convert to Path object and ensure it's the resolved, canonical path
    # is_path_within_obsidian_root has already effectively done this,
    # but doing it again here ensures dir_path is a resolved Path object.
    dir_path = Path(path).resolve()

    # Check if the resolved path is actually a directory
    if not dir_path.is_dir():
        # This is important because is_path_within_obsidian_root might be true
        # for a *file* within the sandbox, but this function requires a directory.
        raise ValueError(f"Resolved path '{dir_path}' is not a directory.")

    # List the directory contents
    contents = []
    try:
        for item in dir_path.iterdir():  # item is a Path object
            # Determine prefix
            # No need to re-check security of 'item' as it's directly under 'dir_path'
            # which has already been validated.
            if item.is_file():
                prefix = "[FILE]"
            elif item.is_dir():
                prefix = "[DIR]"
            else:
                # Could be a symlink to something else, or a special file type.
                # For simplicity, we can skip or mark as [OTHER].
                # If you need to handle symlinks specifically, you can use item.is_symlink().
                prefix = "[OTHER]"  # Or you could choose to skip these

            contents.append(f"{prefix} {item.name}")

    except PermissionError:
        raise ValueError(
            f"Permission denied to access directory contents of '{dir_path}'."
        )
    except FileNotFoundError:
        # This might happen in a race condition if the directory is deleted
        # between the is_dir() check and iterdir(), though unlikely.
        raise ValueError(f"Directory '{dir_path}' not found during listing.")
    except Exception as e:
        # Catch-all for other OS-level errors during iteration
        raise ValueError(f"Error listing directory '{dir_path}': {str(e)}")

    return sorted(contents)  # Sort for consistent output


@mcp.tool
def get_file_info(path: str):
    """
    Get detailed file/directory metadata for items within OBSIDIAN_PATH.
    """
    # Security: Check if the path is within the allowed sandbox
    if not is_path_within_obsidian_root(path):
        raise ValueError(f"Path '{path}' is outside the allowed sandbox.")

    # Convert to Path object and resolve
    item_path = Path(path).resolve()

    # Check if the path exists
    if not item_path.exists():
        raise ValueError(f"Path '{path}' does not exist.")

    # Get the file info
    try:
        stat_info = item_path.stat()
        info = {
            "name": item_path.name,
            "full_path": str(item_path),
            "size_bytes": stat_info.st_size,
            "size_human": (
                f"{stat_info.st_size / 1024:.1f} KB"
                if stat_info.st_size < 1024 * 1024
                else f"{stat_info.st_size / (1024 * 1024):.1f} MB"
            ),
            "creation_time": stat_info.st_ctime,
            "modified_time": stat_info.st_mtime,
            "access_time": stat_info.st_atime,
            "type": "file" if item_path.is_file() else "directory",
            "permissions": oct(stat_info.st_mode)[-3:],
            "is_hidden": item_path.name.startswith("."),
        }

        # Add file-specific info if it's a file
        if item_path.is_file():
            info["extension"] = (
                item_path.suffix.lower() if item_path.suffix else "(no extension)"
            )
            try:
                # Try to get the first few lines as a preview (for text files only)
                if item_path.suffix.lower() in [
                    ".txt",
                    ".md",
                    ".py",
                    ".js",
                    ".html",
                    ".css",
                    ".json",
                    ".csv",
                    ".yml",
                    ".yaml",
                    ".xml",
                ]:
                    with open(item_path, "r", encoding="utf-8") as f:
                        preview_lines = [line.strip() for line in f.readlines()[:5]]
                        info["preview"] = "\n".join(preview_lines)
            except:
                # If we can't read the file as text, skip the preview
                pass

    except Exception as e:
        raise ValueError(f"Error getting info for '{path}': {str(e)}")

    return info


@mcp.tool
def list_allowed_directories():
    """List all directories the server is allowed to access (subdirectories of OBSIDIAN_PATH)."""
    # OBSIDIAN_ROOT is already validated at startup
    return sorted(list(ALLOWED_DIRS_SET))  # Return the pre-calculated and resolved list

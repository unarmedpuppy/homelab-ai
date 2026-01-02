"""File operation tools for the agent.

Tools:
- read_file: Read file contents
- write_file: Create or overwrite files
- edit_file: Make precise edits using string replacement
- search_files: Find files by pattern or content
- list_directory: List directory contents
"""

import os
import subprocess
from glob import glob

from .security import validate_path
from .registry import register_tool

# =============================================================================
# Read File Tool
# =============================================================================

def _read_file(arguments: dict, working_dir: str) -> str:
    """Read file contents with optional line range."""
    valid, path = validate_path(arguments["path"], working_dir)
    if not valid:
        return f"Error: {path}"
    
    if not os.path.exists(path):
        return f"Error: File not found: {path}"
    
    try:
        with open(path, "r") as f:
            lines = f.readlines()
    except Exception as e:
        return f"Error reading file: {e}"
    
    start = arguments.get("start_line", 1) - 1
    end = arguments.get("end_line", len(lines))
    
    # Add line numbers
    result_lines = []
    for i, line in enumerate(lines[start:end], start=start+1):
        result_lines.append(f"{i:4d}| {line.rstrip()}")
    
    return "\n".join(result_lines) if result_lines else "(empty file)"


register_tool(
    name="read_file",
    description="Read the contents of a file. Use this to examine files before making changes.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute or relative path to the file to read"
            },
            "start_line": {
                "type": "integer",
                "description": "Optional starting line number (1-indexed)"
            },
            "end_line": {
                "type": "integer",
                "description": "Optional ending line number (inclusive)"
            }
        },
        "required": ["path"]
    },
    handler=_read_file
)

# =============================================================================
# Write File Tool
# =============================================================================

def _write_file(arguments: dict, working_dir: str) -> str:
    """Write content to a file, creating it if needed."""
    valid, path = validate_path(arguments["path"], working_dir)
    if not valid:
        return f"Error: {path}"
    
    try:
        # Create parent directories if needed
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w") as f:
            f.write(arguments["content"])
        
        return f"Successfully wrote {len(arguments['content'])} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


register_tool(
    name="write_file",
    description="Write content to a file, creating it if it doesn't exist or overwriting if it does.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute or relative path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["path", "content"]
    },
    handler=_write_file
)

# =============================================================================
# Edit File Tool
# =============================================================================

def _edit_file(arguments: dict, working_dir: str) -> str:
    """Edit a file by replacing a specific string."""
    valid, path = validate_path(arguments["path"], working_dir)
    if not valid:
        return f"Error: {path}"
    
    if not os.path.exists(path):
        return f"Error: File not found: {path}"
    
    try:
        with open(path, "r") as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {e}"
    
    old_string = arguments["old_string"]
    new_string = arguments["new_string"]
    
    if old_string not in content:
        return f"Error: old_string not found in file. Make sure it matches exactly."
    
    if content.count(old_string) > 1:
        return f"Error: old_string found {content.count(old_string)} times. Provide more context for a unique match."
    
    new_content = content.replace(old_string, new_string, 1)
    
    try:
        with open(path, "w") as f:
            f.write(new_content)
        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error writing file: {e}"


register_tool(
    name="edit_file",
    description="Edit a file by replacing a specific string with new content. The old_string must match exactly and be unique.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute or relative path to the file to edit"
            },
            "old_string": {
                "type": "string",
                "description": "Exact string to find and replace (must be unique in file)"
            },
            "new_string": {
                "type": "string",
                "description": "String to replace old_string with"
            }
        },
        "required": ["path", "old_string", "new_string"]
    },
    handler=_edit_file
)

# =============================================================================
# Search Files Tool
# =============================================================================

def _search_files(arguments: dict, working_dir: str) -> str:
    """Search for files by pattern or content."""
    valid, path = validate_path(arguments["path"], working_dir)
    if not valid:
        return f"Error: {path}"
    
    pattern = arguments["pattern"]
    content_search = arguments.get("content_search", False)
    
    if content_search:
        # Grep for content
        try:
            result = subprocess.run(
                ["grep", "-rn", "--include=*", pattern, path],
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout
            if len(output) > 5000:
                output = output[:5000] + "\n... (truncated)"
            return output if output.strip() else "No matches found"
        except subprocess.TimeoutExpired:
            return "Error: Search timed out"
        except Exception as e:
            return f"Error: {e}"
    else:
        # Glob for file patterns
        matches = glob(os.path.join(path, pattern), recursive=True)
        if not matches:
            return "No files found matching pattern"
        return "\n".join(matches[:100])


register_tool(
    name="search_files",
    description="Search for files matching a pattern or content. Uses glob for file patterns, grep for content.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern (e.g., '**/*.py') or text to search for"
            },
            "path": {
                "type": "string",
                "description": "Directory to search in"
            },
            "content_search": {
                "type": "boolean",
                "description": "If true, search file contents. If false (default), search file names.",
                "default": False
            }
        },
        "required": ["pattern", "path"]
    },
    handler=_search_files
)

# =============================================================================
# List Directory Tool
# =============================================================================

def _list_directory(arguments: dict, working_dir: str) -> str:
    """List contents of a directory."""
    valid, path = validate_path(arguments["path"], working_dir)
    if not valid:
        return f"Error: {path}"
    
    if not os.path.isdir(path):
        return f"Error: Not a directory: {path}"
    
    try:
        entries = []
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                entries.append(f"[DIR]  {entry}/")
            else:
                try:
                    size = os.path.getsize(full_path)
                    entries.append(f"[FILE] {entry} ({size} bytes)")
                except:
                    entries.append(f"[FILE] {entry}")
        
        return "\n".join(entries) if entries else "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {e}"


register_tool(
    name="list_directory",
    description="List contents of a directory with file types and sizes.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute or relative path to the directory"
            }
        },
        "required": ["path"]
    },
    handler=_list_directory
)

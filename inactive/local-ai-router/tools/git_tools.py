"""Git operation tools for the agent.

Tools:
- git_status: Get repository status
- git_diff: Show changes (staged, unstaged, or between refs)
- git_log: Show commit history
- git_add: Stage files for commit
- git_commit: Commit staged changes
- git_push: Push commits to remote
- git_pull: Pull changes from remote
- git_branch: List or switch branches
- git_checkout: Checkout a branch or file
"""

import os
import subprocess
from typing import Optional

from .security import validate_path, validate_git_repo, validate_command
from .registry import register_tool

# =============================================================================
# Helpers
# =============================================================================

def _run_git_command(
    command: list[str], 
    repo_path: str, 
    timeout: int = 30
) -> tuple[bool, str]:
    """
    Run a git command in a repository.
    
    Returns:
        (success, output_or_error)
    """
    try:
        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout
        if result.stderr:
            # Git often writes to stderr even on success (progress, etc.)
            if result.returncode != 0:
                output += f"\n[stderr]: {result.stderr}"
            else:
                # Include stderr only if it's not just progress info
                if "error" in result.stderr.lower() or "fatal" in result.stderr.lower():
                    output += f"\n[stderr]: {result.stderr}"
        
        if result.returncode != 0:
            return False, output or result.stderr or f"Exit code: {result.returncode}"
        
        return True, output if output.strip() else "(no output)"
        
    except subprocess.TimeoutExpired:
        return False, f"Error: Git command timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Error: {e}"


def _validate_repo(repo_path: str, working_dir: str) -> tuple[bool, str]:
    """Validate repository path and return resolved path."""
    # If no repo_path specified, use working_dir
    if not repo_path:
        repo_path = working_dir
    
    return validate_git_repo(repo_path, working_dir)


# =============================================================================
# Git Status Tool
# =============================================================================

def _git_status(arguments: dict, working_dir: str) -> str:
    """Get repository status."""
    valid, repo_path = _validate_repo(arguments.get("repo_path", ""), working_dir)
    if not valid:
        return f"Error: {repo_path}"
    
    success, output = _run_git_command(
        ["git", "status", "--short", "--branch"],
        repo_path
    )
    
    return output


register_tool(
    name="git_status",
    description="Get the status of a git repository. Shows current branch, staged/unstaged changes, and untracked files.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository (optional, defaults to working directory)"
            }
        },
        "required": []
    },
    handler=_git_status
)

# =============================================================================
# Git Diff Tool
# =============================================================================

def _git_diff(arguments: dict, working_dir: str) -> str:
    """Show changes in the repository."""
    valid, repo_path = _validate_repo(arguments.get("repo_path", ""), working_dir)
    if not valid:
        return f"Error: {repo_path}"
    
    cmd = ["git", "diff"]
    
    # Staged changes only
    if arguments.get("staged", False):
        cmd.append("--staged")
    
    # Specific file
    if arguments.get("file_path"):
        cmd.append("--")
        cmd.append(arguments["file_path"])
    
    # Between refs
    if arguments.get("ref1") and arguments.get("ref2"):
        cmd.extend([arguments["ref1"], arguments["ref2"]])
    elif arguments.get("ref1"):
        cmd.append(arguments["ref1"])
    
    success, output = _run_git_command(cmd, repo_path, timeout=60)
    
    # Truncate long diffs
    if len(output) > 8000:
        output = output[:8000] + "\n... (diff truncated, showing first 8000 chars)"
    
    return output


register_tool(
    name="git_diff",
    description="Show changes in a git repository. Can show staged changes, unstaged changes, or diff between refs.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository (optional)"
            },
            "staged": {
                "type": "boolean",
                "description": "Show only staged changes (default: false, shows unstaged)"
            },
            "file_path": {
                "type": "string",
                "description": "Show diff for specific file only"
            },
            "ref1": {
                "type": "string",
                "description": "First reference (commit, branch, tag)"
            },
            "ref2": {
                "type": "string",
                "description": "Second reference to compare against ref1"
            }
        },
        "required": []
    },
    handler=_git_diff
)

# =============================================================================
# Git Log Tool
# =============================================================================

def _git_log(arguments: dict, working_dir: str) -> str:
    """Show commit history."""
    valid, repo_path = _validate_repo(arguments.get("repo_path", ""), working_dir)
    if not valid:
        return f"Error: {repo_path}"
    
    limit = arguments.get("limit", 10)
    format_str = arguments.get("format", "%h %s (%an, %ar)")
    
    cmd = [
        "git", "log",
        f"--max-count={limit}",
        f"--format={format_str}"
    ]
    
    # Specific file history
    if arguments.get("file_path"):
        cmd.append("--")
        cmd.append(arguments["file_path"])
    
    success, output = _run_git_command(cmd, repo_path)
    
    return output


register_tool(
    name="git_log",
    description="Show git commit history. Returns recent commits with hash, message, author, and time.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository (optional)"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of commits to show (default: 10)"
            },
            "file_path": {
                "type": "string",
                "description": "Show history for specific file only"
            },
            "format": {
                "type": "string",
                "description": "Git log format string (default: '%h %s (%an, %ar)')"
            }
        },
        "required": []
    },
    handler=_git_log
)

# =============================================================================
# Git Add Tool
# =============================================================================

def _git_add(arguments: dict, working_dir: str) -> str:
    """Stage files for commit."""
    valid, repo_path = _validate_repo(arguments.get("repo_path", ""), working_dir)
    if not valid:
        return f"Error: {repo_path}"
    
    files = arguments.get("files", ["."])
    if isinstance(files, str):
        files = [files]
    
    cmd = ["git", "add"] + files
    
    success, output = _run_git_command(cmd, repo_path)
    
    if success:
        # Show what was staged
        _, status = _run_git_command(["git", "status", "--short"], repo_path)
        return f"Staged files. Current status:\n{status}"
    
    return output


register_tool(
    name="git_add",
    description="Stage files for the next commit. Use '.' to stage all changes.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository (optional)"
            },
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Files to stage (default: '.' for all)"
            }
        },
        "required": []
    },
    handler=_git_add
)

# =============================================================================
# Git Commit Tool
# =============================================================================

def _git_commit(arguments: dict, working_dir: str) -> str:
    """Commit staged changes."""
    valid, repo_path = _validate_repo(arguments.get("repo_path", ""), working_dir)
    if not valid:
        return f"Error: {repo_path}"
    
    message = arguments.get("message", "")
    if not message:
        return "Error: Commit message is required"
    
    cmd = ["git", "commit", "-m", message]
    
    success, output = _run_git_command(cmd, repo_path)
    
    return output


register_tool(
    name="git_commit",
    description="Commit staged changes with a message. Requires files to be staged first with git_add.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository (optional)"
            },
            "message": {
                "type": "string",
                "description": "Commit message (required)"
            }
        },
        "required": ["message"]
    },
    handler=_git_commit
)

# =============================================================================
# Git Push Tool
# =============================================================================

def _git_push(arguments: dict, working_dir: str) -> str:
    """Push commits to remote."""
    valid, repo_path = _validate_repo(arguments.get("repo_path", ""), working_dir)
    if not valid:
        return f"Error: {repo_path}"
    
    remote = arguments.get("remote", "origin")
    branch = arguments.get("branch", "")
    
    cmd = ["git", "push", remote]
    if branch:
        cmd.append(branch)
    
    # Set upstream if requested
    if arguments.get("set_upstream", False):
        cmd.insert(2, "-u")
    
    # NOTE: Force push is intentionally NOT supported for safety
    # The command blocklist in security.py blocks --force patterns
    
    success, output = _run_git_command(cmd, repo_path, timeout=60)
    
    return output


register_tool(
    name="git_push",
    description="Push commits to remote repository. Force push is blocked for safety.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository (optional)"
            },
            "remote": {
                "type": "string",
                "description": "Remote name (default: 'origin')"
            },
            "branch": {
                "type": "string",
                "description": "Branch to push (optional, uses current branch)"
            },
            "set_upstream": {
                "type": "boolean",
                "description": "Set upstream tracking reference (-u flag)"
            }
        },
        "required": []
    },
    handler=_git_push
)

# =============================================================================
# Git Pull Tool
# =============================================================================

def _git_pull(arguments: dict, working_dir: str) -> str:
    """Pull changes from remote."""
    valid, repo_path = _validate_repo(arguments.get("repo_path", ""), working_dir)
    if not valid:
        return f"Error: {repo_path}"
    
    remote = arguments.get("remote", "origin")
    branch = arguments.get("branch", "")
    
    cmd = ["git", "pull", remote]
    if branch:
        cmd.append(branch)
    
    if arguments.get("rebase", False):
        cmd.insert(2, "--rebase")
    
    success, output = _run_git_command(cmd, repo_path, timeout=120)
    
    return output


register_tool(
    name="git_pull",
    description="Pull changes from remote repository.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository (optional)"
            },
            "remote": {
                "type": "string",
                "description": "Remote name (default: 'origin')"
            },
            "branch": {
                "type": "string",
                "description": "Branch to pull (optional)"
            },
            "rebase": {
                "type": "boolean",
                "description": "Use rebase instead of merge"
            }
        },
        "required": []
    },
    handler=_git_pull
)

# =============================================================================
# Git Branch Tool
# =============================================================================

def _git_branch(arguments: dict, working_dir: str) -> str:
    """List or create branches."""
    valid, repo_path = _validate_repo(arguments.get("repo_path", ""), working_dir)
    if not valid:
        return f"Error: {repo_path}"
    
    # List branches
    if not arguments.get("name"):
        cmd = ["git", "branch", "-a", "-v"]
        success, output = _run_git_command(cmd, repo_path)
        return output
    
    # Create new branch
    name = arguments["name"]
    cmd = ["git", "branch", name]
    
    if arguments.get("start_point"):
        cmd.append(arguments["start_point"])
    
    success, output = _run_git_command(cmd, repo_path)
    
    if success:
        return f"Created branch: {name}"
    return output


register_tool(
    name="git_branch",
    description="List all branches or create a new branch. To switch branches, use git_checkout.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository (optional)"
            },
            "name": {
                "type": "string",
                "description": "Name for new branch (if omitted, lists all branches)"
            },
            "start_point": {
                "type": "string",
                "description": "Starting point for new branch (commit, branch, tag)"
            }
        },
        "required": []
    },
    handler=_git_branch
)

# =============================================================================
# Git Checkout Tool
# =============================================================================

def _git_checkout(arguments: dict, working_dir: str) -> str:
    """Checkout a branch or restore files."""
    valid, repo_path = _validate_repo(arguments.get("repo_path", ""), working_dir)
    if not valid:
        return f"Error: {repo_path}"
    
    target = arguments.get("target", "")
    if not target:
        return "Error: target (branch name or file path) is required"
    
    cmd = ["git", "checkout"]
    
    # Create new branch with -b
    if arguments.get("create_branch", False):
        cmd.append("-b")
    
    cmd.append(target)
    
    success, output = _run_git_command(cmd, repo_path)
    
    if success:
        return f"Checked out: {target}"
    return output


register_tool(
    name="git_checkout",
    description="Checkout a branch, tag, or restore files. Use create_branch=true to create and checkout a new branch.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository (optional)"
            },
            "target": {
                "type": "string",
                "description": "Branch name, tag, commit, or file path to checkout"
            },
            "create_branch": {
                "type": "boolean",
                "description": "Create a new branch (-b flag)"
            }
        },
        "required": ["target"]
    },
    handler=_git_checkout
)

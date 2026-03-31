"""
Rolling conversation compaction for context window management.

When a conversation approaches the model's context limit, older messages
are summarized into a compact form while preserving recent context.
Full uncompacted history is always preserved in the router's SQLite DB.
"""
import logging
import tiktoken
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-loaded tokenizer
_tokenizer = None

def get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = tiktoken.get_encoding("cl100k_base")
    return _tokenizer


def estimate_message_tokens(messages: list[dict]) -> int:
    """Estimate token count for a list of messages."""
    enc = get_tokenizer()
    total = 0
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content", "") or ""
            if isinstance(content, str):
                total += len(enc.encode(content))
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        total += len(enc.encode(part.get("text", "")))
            # Overhead per message (role, formatting)
            total += 4
    return total


def needs_compaction(messages: list[dict], context_limit: int, threshold_ratio: float = 0.85) -> bool:
    """Check if messages need compaction based on token count vs context limit."""
    token_count = estimate_message_tokens(messages)
    threshold = int(context_limit * threshold_ratio)
    return token_count > threshold


def build_compaction_prompt(messages_to_compact: list[dict], previous_summary: Optional[str] = None) -> str:
    """Build the prompt that asks the model to summarize older messages."""
    parts = []
    if previous_summary:
        parts.append(f"Previous conversation summary:\n{previous_summary}\n")

    parts.append("Summarize the following conversation messages into a concise summary (2-3 paragraphs). "
                  "Preserve key facts, decisions, code snippets, and context that would be needed to continue "
                  "the conversation. Do not include pleasantries or meta-commentary about summarizing.\n\n")

    for msg in messages_to_compact:
        role = msg.get("role", "unknown")
        content = msg.get("content", "") or ""
        if isinstance(content, list):
            content = " ".join(
                part.get("text", "") for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        parts.append(f"[{role}]: {content}\n")

    return "".join(parts)


def compact_messages(
    messages: list[dict],
    context_limit: int,
    previous_summary: Optional[str] = None,
    keep_recent: int = 6,
    target_ratio: float = 0.4,
) -> tuple[list[dict], list[dict], str]:
    """
    Split messages into those to compact and those to keep.

    Returns:
        (messages_to_compact, messages_to_keep, compaction_prompt)

    The caller should:
    1. Send compaction_prompt to the model to get a summary
    2. Replace messages_to_compact with the summary as a system message
    3. Prepend the summary to messages_to_keep
    """
    if len(messages) <= keep_recent:
        return [], messages, ""

    # Always keep system messages at the front
    system_messages = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]

    # Keep the most recent messages
    to_keep = non_system[-keep_recent:]
    to_compact = non_system[:-keep_recent]

    if not to_compact:
        return [], messages, ""

    prompt = build_compaction_prompt(to_compact, previous_summary)

    return to_compact, system_messages + to_keep, prompt


def rebuild_messages_with_summary(
    summary: str,
    kept_messages: list[dict],
    original_system_prompt: Optional[str] = None,
) -> list[dict]:
    """
    Rebuild the message list with the compaction summary injected.

    The summary becomes a system message prepended to the kept messages.
    """
    result = []

    # Preserve original system message if present
    system_msgs = [m for m in kept_messages if m.get("role") == "system"]
    non_system = [m for m in kept_messages if m.get("role") != "system"]

    # Add original system messages first
    result.extend(system_msgs)

    # Add compaction summary as a system message
    result.append({
        "role": "system",
        "content": f"[Conversation Summary]\n{summary}",
    })

    # Add kept messages
    result.extend(non_system)

    return result

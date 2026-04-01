"""anthropic-openai-bridge — Anthropic Messages API ↔ OpenAI chat completions translation.

Standalone module with zero router/auth/provider dependencies.
Can be extracted and used in any project that needs this translation layer.

Public API:
  translate_request(body)              Anthropic Messages request → OpenAI chat completions body
  translate_response(oai, model)       OpenAI response dict → Anthropic Messages response dict
  translate_stream(url, headers, ...)  Async generator: OpenAI SSE → Anthropic SSE events
  count_message_tokens(body)           Token estimate for an Anthropic Messages request body
"""
from .translate import translate_request, translate_response, count_message_tokens
from .stream import translate_stream

__all__ = [
    "translate_request",
    "translate_response",
    "translate_stream",
    "count_message_tokens",
]

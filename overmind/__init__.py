"""
Overmind Python Client

A Python client for the Overmind API that provides automatic observability for
LLM applications.
"""

from opentelemetry.overmind.prompt import PromptString

from .exceptions import OvermindAPIError, OvermindAuthenticationError, OvermindError
from .tracing import (
    SpanType,
    capture_exception,
    entry_point,
    function,
    get_tracer,
    init,
    observe,
    set_tag,
    set_user,
    start_span,
    tool,
    workflow,
)

__version__ = "0.1.39"
__all__ = [
    "OvermindAPIError",
    "OvermindAuthenticationError",
    "OvermindError",
    "PromptString",
    "SpanType",
    "capture_exception",
    "entry_point",
    "function",
    "get_tracer",
    "init",
    "observe",
    "set_tag",
    "set_user",
    "start_span",
    "tool",
    "workflow",
]

"""
Overmind Python Client

A Python client for the Overmind API that provides easy access to AI provider endpoints
with policy enforcement and automatic observability.
"""

from .client import OvermindClient
from .exceptions import OvermindAPIError, OvermindAuthenticationError, OvermindError

from .tracing import (
    init,
    get_tracer,
    set_user,
    set_tag,
    capture_exception,
    observe,
    SpanType,
    start_span,
    function,
    entry_point,
    workflow,
    tool,
)
from opentelemetry.overmind.prompt import PromptString


__version__ = "0.1.33"
__all__ = [
    "OvermindClient",
    "OvermindError",
    "OvermindAPIError",
    "OvermindAuthenticationError",
    "init",
    "get_tracer",
    "set_user",
    "set_tag",
    "capture_exception",
    "PromptString",
    "observe",
    "start_span",
    "SpanType",
    "function",
    "entry_point",
    "workflow",
    "tool",
]

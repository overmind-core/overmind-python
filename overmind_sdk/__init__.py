"""
Overmind Python Client

A Python client for the Overmind API that provides easy access to AI provider endpoints
with policy enforcement and automatic observability.
"""

from opentelemetry.overmind.prompt import PromptString

from .client import OvermindClient
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
    "OvermindClient",
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

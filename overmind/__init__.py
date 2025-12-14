"""
Overmind Python Client

A Python client for the Overmind API that provides easy access to AI provider endpoints
with policy enforcement and automatic observability.
"""

from .client import OvermindClient
from .exceptions import OvermindAPIError, OvermindAuthenticationError, OvermindError
from .overmind_sdk import init, get_tracer, set_user, set_tag, capture_exception

__version__ = "0.1.0"
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
]

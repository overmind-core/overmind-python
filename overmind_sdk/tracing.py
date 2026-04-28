"""
Overmind SDK tracing.

Provides SDK initialization, provider auto-instrumentation, and helpers
(decorators and a context manager) for creating custom OpenTelemetry spans.
"""

import importlib.metadata
import importlib.util
import inspect
import logging
import os
from collections.abc import Callable
from contextlib import contextmanager
from enum import Enum
from functools import wraps
from typing import Any

from opentelemetry import trace
from opentelemetry.context import attach, get_value, set_value
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv_ai import SpanAttributes
from opentelemetry.trace import Status, StatusCode

from overmind_sdk.utils.api_settings import get_api_settings
from overmind_sdk.utils.serializers import serialize

logger = logging.getLogger(__name__)

try:
    _SDK_VERSION = importlib.metadata.version("overmind_sdk")
except importlib.metadata.PackageNotFoundError:
    _SDK_VERSION = "unknown"

_strict_mode = os.environ.get("OVERMIND_STRICT_MODE", "false").lower() == "true"

# Global state to track initialization
_initialized = False
_tracer: trace.Tracer | None = None
_providers: set[str] = set()


# ---------------------------------------------------------------------------
# Provider auto-instrumentation
# ---------------------------------------------------------------------------


def enable_agno():
    name, module = "agno", "agno"
    global _providers
    if name in _providers:
        logger.debug("%s already enabled", name)
        return

    if importlib.util.find_spec(module) is None:
        if _strict_mode:
            raise ImportError(f"{module} is not installed. Please install it with `pip install {module}`.")
        logger.warning("%s is not installed. Please install it with `pip install %s`.", module, module)
        return

    from opentelemetry.instrumentation.agno import AgnoInstrumentor

    AgnoInstrumentor().instrument()
    _providers.add(name)
    logger.info("%s instrumentation enabled", name)


def enable_openai():
    name, module = "openai", "openai"
    global _providers
    if name in _providers:
        logger.debug("%s already enabled", name)
        return

    if importlib.util.find_spec(module) is None:
        if _strict_mode:
            raise ImportError(f"{module} is not installed. Please install it with `pip install {module}`.")
        logger.warning("%s is not installed. Please install it with `pip install %s`.", module, module)
        return

    from opentelemetry.instrumentation.openai import OpenAIInstrumentor

    OpenAIInstrumentor().instrument()

    _providers.add(name)
    logger.info("%s instrumentation enabled", name)


def enable_anthropic():
    name, module = "anthropic", "anthropic"
    global _providers
    if name in _providers:
        logger.debug("%s already enabled", name)
        return

    if importlib.util.find_spec(module) is None:
        if _strict_mode:
            raise ImportError(f"{module} is not installed. Please install it with `pip install {module}`.")
        logger.warning("%s is not installed. Please install it with `pip install %s`.", module, module)
        return

    from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

    AnthropicInstrumentor().instrument()

    _providers.add(name)
    logger.info("%s instrumentation enabled", name)


def enable_google_genai():
    name, module = "google", "google.genai"

    global _providers
    if name in _providers:
        logger.debug("%s already enabled", name)
        return

    if importlib.util.find_spec(module) is None:
        module = module.replace(".", "-")
        if _strict_mode:
            raise ImportError(f"{module} is not installed. Please install it with `pip install {module}`.")
        logger.warning("%s is not installed. Please install it with `pip install %s`.", module, module)
        return

    from opentelemetry.instrumentation.google_generativeai import GoogleGenerativeAiInstrumentor

    GoogleGenerativeAiInstrumentor().instrument()

    _providers.add(name)
    logger.info("%s instrumentation enabled", name)


def enable_tracing(providers: list[str]):
    if providers == []:
        # if no providers are provided, enable all supported providers
        providers = ["openai", "anthropic", "google", "agno"]

    logger.info("Enabling tracing for providers: %s", providers)
    if "agno" in providers:
        enable_agno()
    if "openai" in providers:
        enable_openai()
    if "anthropic" in providers:
        enable_anthropic()
    if "google" in providers:
        enable_google_genai()


def _span_processor_on_start(span: trace.Span, parent_context: trace.Context | None = None):
    if value := get_value("workflow_name"):
        span.set_attribute(SpanAttributes.TRACELOOP_WORKFLOW_NAME, str(value))


# ---------------------------------------------------------------------------
# SDK initialization
# ---------------------------------------------------------------------------


def init(
    overmind_api_key: str | None = None,
    *,
    service_name: str | None = None,
    environment: str | None = None,
    providers: list[str] | None = None,
    overmind_base_url: str | None = None,
):
    """
    Initialize the Overmind SDK for automatic monitoring.

    Example:
        import overmind
        overmind.init(service_name="my-backend", environment="production", providers=["openai", "anthropic", "google", "agno"])

    Args:
        overmind_api_key: Your Overmind API key. If not provided, uses OVERMIND_API_KEY env var.
        service_name: Name of your service (appears in traces). Defaults to OVERMIND_SERVICE_NAME
                      env var or "unknown-service".
        environment: Environment name (e.g., "production", "staging"). Defaults to
                     OVERMIND_ENVIRONMENT env var or "development".
        providers: List of providers to trace. Supported values: "openai", "anthropic", "google", "agno".
        overmind_base_url: Base URL for traces. If not provided, uses OVERMIND_API_URL env var.
    """
    global _initialized, _tracer

    if providers is None:
        providers = []

    if _initialized:
        # user can call init again with different providers, so we should not skip
        # there is no such thing as remove initialization
        logger.debug("Overmind SDK already initialized, reinitializing with providers: %s", providers)
        enable_tracing(providers)
        return

    # Resolve service name and environment
    service_name = (
        service_name or os.environ.get("OVERMIND_SERVICE_NAME") or os.environ.get("SERVICE_NAME") or "unknown-service"
    )
    environment = (
        environment or os.environ.get("OVERMIND_ENVIRONMENT") or os.environ.get("ENVIRONMENT") or "development"
    )

    overmind_api_key, overmind_base_url = get_api_settings(overmind_api_key, overmind_base_url)

    endpoint = f"{overmind_base_url}/api/v1/traces"

    # Configure OpenTelemetry Provider with rich resource attributes
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.environ.get("SERVICE_VERSION", "unknown"),
        "deployment.environment": environment,
        "overmind.sdk.name": "overmind-python",
        "overmind.sdk.version": _SDK_VERSION,
    })

    provider = TracerProvider(resource=resource)

    # Configure OTLP Exporter
    headers = {"X-API-Token": overmind_api_key}

    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)

    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    span_processor.on_start = _span_processor_on_start

    # Set global Trace Provider
    trace.set_tracer_provider(provider)

    # Store tracer for custom spans
    _tracer = trace.get_tracer("overmind", _SDK_VERSION)
    enable_tracing(providers)

    _initialized = True
    logger.info("Overmind SDK initialized: service=%s, environment=%s", service_name, environment)


def get_tracer() -> trace.Tracer:
    """
    Get the Overmind tracer for creating custom spans.

    Example:
        tracer = overmind.get_tracer()
        with tracer.start_as_current_span("my-operation") as span:
            span.set_attribute("user.id", user_id)
            # ... your code ...

    Returns:
        OpenTelemetry Tracer instance.

    Raises:
        RuntimeError: If SDK not initialized.
    """
    if not _initialized or _tracer is None:
        raise RuntimeError("Overmind SDK not initialized. Call overmind.init() first.")
    return _tracer


# ---------------------------------------------------------------------------
# Span attribute helpers
# ---------------------------------------------------------------------------


def set_user(user_id: str, email: str | None = None, username: str | None = None) -> None:
    """
    Associate current trace with a user (like Sentry's set_user).

    Call this in your request handler to tag traces with user info.

    Example:
        @app.middleware("http")
        async def add_user_context(request: Request, call_next):
            if request.state.user:
                overmind.set_user(user_id=request.state.user.id)
            return await call_next(request)

    Args:
        user_id: Unique user identifier.
        email: Optional user email.
        username: Optional username.
    """
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute("user.id", user_id)
        if email:
            span.set_attribute("user.email", email)
        if username:
            span.set_attribute("user.username", username)


def set_tag(key: str, value) -> None:
    """
    Add a custom tag to the current span.

    Accepts str, int, float, bool, or list[str] values.  Other types are
    coerced to str automatically.

    Example:
        overmind.set_tag("feature.flag", "new-checkout-flow")
        overmind.set_tag("iteration", 3)
        overmind.set_tag("score", 85.2)
    """
    span = trace.get_current_span()
    if not span.is_recording():
        return
    if isinstance(value, (str, int, float, bool)):
        span.set_attribute(key, value)
    elif value is None:
        span.set_attribute(key, "")
    elif isinstance(value, (list, tuple)) and all(isinstance(v, str) for v in value):
        span.set_attribute(key, list(value))
    else:
        span.set_attribute(key, str(value))


def capture_exception(exception: Exception) -> None:
    """
    Record an exception on the current span.

    Example:
        try:
            risky_operation()
        except Exception as e:
            overmind.capture_exception(e)
            raise

    Args:
        exception: The exception to record.
    """
    span = trace.get_current_span()
    if span.is_recording():
        span.record_exception(exception)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))


def set_workflow_name(workflow_name: str) -> None:
    attach(set_value("workflow_name", workflow_name))


def set_agent_name(agent_name: str) -> None:
    attach(set_value("agent_name", agent_name))


def set_conversation_id(conversation_id: str):
    attach(set_value("conversation_id", conversation_id))


# ---------------------------------------------------------------------------
# Span types and decorators
# ---------------------------------------------------------------------------


class SpanType(str, Enum):
    FUNCTION = "function"
    ENTRY_POINT = "entry_point"
    WORKFLOW = "workflow"
    TOOL = "tool"


_SKIP_INPUT_TYPES = (
    "Console", "Progress", "Live", "Table", "Panel",
    "TracerProvider", "Tracer", "Span",
)


def _should_skip_value(value: Any) -> bool:
    type_name = type(value).__name__
    return type_name in _SKIP_INPUT_TYPES


def _prepare_for_otel(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool, type(None))):
        return value

    if _should_skip_value(value):
        return f"<{type(value).__name__}>"

    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            return str(value)

    if isinstance(value, (dict, list, tuple)):
        return value

    if isinstance(value, (set, frozenset)):
        return list(value)

    from pathlib import PurePath
    if isinstance(value, PurePath):
        return str(value)

    return str(value)


def _safe_set_attribute(otel_span, key: str, value: Any) -> None:
    """Set a span attribute, coercing the value to an OTel-compatible type."""
    if isinstance(value, (str, int, float, bool)):
        otel_span.set_attribute(key, value)
    elif value is None:
        otel_span.set_attribute(key, "")
    elif isinstance(value, (list, tuple)):
        if all(isinstance(v, str) for v in value):
            otel_span.set_attribute(key, list(value))
        else:
            otel_span.set_attribute(key, serialize(value))
    else:
        otel_span.set_attribute(key, str(value))


def observe(span_name: str | None = None, type: SpanType = SpanType.FUNCTION):
    """
    Decorator that automatically traces function execution with OpenTelemetry.

    Captures function inputs and outputs as span attributes in OTEL style.
    Works with both synchronous and asynchronous functions.
    """

    def decorator(func: Callable) -> Callable:
        name = span_name or func.__name__

        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                tracer = get_tracer()

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                is_method = len(param_names) > 0 and param_names[0] in ("self", "cls")
                start_idx = 1 if is_method else 0

                with tracer.start_as_current_span(name) as otel_span:
                    try:
                        otel_span.set_attribute("name", name)
                        otel_span.set_attribute("type", type.value)

                        inputs = {}
                        for i, arg in enumerate(args[start_idx:], start=start_idx):
                            if _should_skip_value(arg):
                                continue
                            param_name = param_names[i] if i < len(param_names) else f"arg_{i}"
                            inputs[param_name] = _prepare_for_otel(arg)

                        for key, value in kwargs.items():
                            if _should_skip_value(value):
                                continue
                            inputs[key] = _prepare_for_otel(value)

                        otel_span.set_attribute("inputs", serialize(inputs))

                        result = await func(*args, **kwargs)

                        output = _prepare_for_otel(result)
                        otel_span.set_attribute("outputs", serialize(output))

                        otel_span.set_status(Status(StatusCode.OK))

                        return result

                    except Exception as e:
                        otel_span.record_exception(e)
                        otel_span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                tracer = get_tracer()

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                is_method = len(param_names) > 0 and param_names[0] in ("self", "cls")
                start_idx = 1 if is_method else 0

                with tracer.start_as_current_span(name) as otel_span:
                    try:
                        otel_span.set_attribute("name", name)
                        otel_span.set_attribute("type", type.value)

                        inputs = {}
                        for i, arg in enumerate(args[start_idx:], start=start_idx):
                            if _should_skip_value(arg):
                                continue
                            param_name = param_names[i] if i < len(param_names) else f"arg_{i}"
                            inputs[param_name] = _prepare_for_otel(arg)

                        for key, value in kwargs.items():
                            if _should_skip_value(value):
                                continue
                            inputs[key] = _prepare_for_otel(value)

                        otel_span.set_attribute("inputs", serialize(inputs))

                        result = func(*args, **kwargs)

                        output = _prepare_for_otel(result)
                        otel_span.set_attribute("outputs", serialize(output))

                        otel_span.set_status(Status(StatusCode.OK))

                        return result

                    except Exception as e:
                        otel_span.record_exception(e)
                        otel_span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise

            return sync_wrapper

    return decorator


@contextmanager
def start_span(name: str, span_type: SpanType = SpanType.FUNCTION, attributes: dict[str, Any] | None = None):
    """Context manager that creates a child span under the current trace.

    Use this for explicit span creation in loops or conditional blocks
    where a decorator isn't practical.

    Example::

        for i in range(iterations):
            with start_span("iteration", attributes={"iteration": i, "score": score}):
                # ... iteration work ...
                set_tag("decision", "keep")
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as otel_span:
        otel_span.set_attribute("name", name)
        otel_span.set_attribute("type", span_type.value)
        if attributes:
            for key, value in attributes.items():
                _safe_set_attribute(otel_span, key, value)
        try:
            yield otel_span
        except Exception as e:
            otel_span.record_exception(e)
            otel_span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        else:
            otel_span.set_status(Status(StatusCode.OK))


def conversation(conversation_id: str):
    """Decorator that sets a conversation ID in the current context."""

    def decorator(fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                set_conversation_id(conversation_id)
                return await fn(*args, **kwargs)

            return async_wrapper
        else:

            @wraps(fn)
            def sync_wrapper(*args, **kwargs):
                set_conversation_id(conversation_id)
                return fn(*args, **kwargs)

            return sync_wrapper

    return decorator


def function(name: str | None = None):
    """Decorator that traces a function span."""
    return observe(span_name=name, type=SpanType.FUNCTION)


def entry_point(name: str | None = None):
    """Decorator that traces an entry point span."""
    return observe(span_name=name, type=SpanType.ENTRY_POINT)


def workflow(name: str | None = None):
    """Decorator that traces a workflow span."""
    return observe(span_name=name, type=SpanType.WORKFLOW)


def tool(name: str | None = None):
    """Decorator that traces a tool span."""
    return observe(span_name=name, type=SpanType.TOOL)

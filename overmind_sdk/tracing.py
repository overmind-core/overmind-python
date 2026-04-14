import logging
import os
from opentelemetry import trace
from opentelemetry.context import get_value
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv_ai import SpanAttributes
import importlib.metadata
import importlib.util

from overmind_sdk.utils.api_settings import get_api_settings

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

    if overmind_base_url:
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
    else:
        # No URL provided: fallback to writing spans to disk for local debugging
        from overmind_sdk.filexporter import FileSpanExporter
        otlp_exporter = FileSpanExporter(
            file_name=os.environ.get("OVERMIND_TRACE_FILE", "overmind-traces.jsonl"),
            write_mode="a"  # Append by default
        )

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


def set_tag(key: str, value: str) -> None:
    """
    Add a custom tag to the current span.

    Example:
        overmind.set_tag("feature.flag", "new-checkout-flow")
        overmind.set_tag("tenant.id", tenant_id)

    Args:
        key: Tag name.
        value: Tag value.
    """
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute(key, value)


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

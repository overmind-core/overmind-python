import logging
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from overmind.utils.api_settings import get_api_settings

logger = logging.getLogger(__name__)


def enable_agno():
    try:
        from opentelemetry.instrumentation.agno import AgnoInstrumentor

        AgnoInstrumentor().instrument()
        import agno  # noqa: F401

    except ImportError:
        raise ImportError("agno is not installed. Please install it with `pip install agno`.")


def enable_openai():
    try:
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor

        OpenAIInstrumentor().instrument()
        from openai import OpenAI  # noqa: F401

    except ImportError:
        raise ImportError("openai is not installed. Please install it with `pip install openai`.")


def enable_anthropic():
    try:
        from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

        AnthropicInstrumentor().instrument()
        from anthropic import Anthropic  # noqa: F401

    except ImportError:
        raise ImportError("anthropic is not installed. Please install it with `pip install anthropic`.")


def enable_google_genai():
    try:
        from opentelemetry.instrumentation.google_generativeai import GoogleGenerativeAiInstrumentor

        GoogleGenerativeAiInstrumentor().instrument()
        from google import genai  # noqa: F401

    except ImportError:
        raise ImportError("google-genai is not installed. Please install it with `pip install google-genai`.")


def enable_tracing(providers: list[str]):
    if "agno" in providers:
        enable_agno()
    elif "openai" in providers:
        enable_openai()
    elif "anthropic" in providers:
        enable_anthropic()
    elif "google" in providers:
        enable_google_genai()
    else:
        raise ValueError(f"Tracing for {providers} is not supported")


# Global state to track initialization
_initialized = False
_tracer: trace.Tracer | None = None


def init(
    overmind_api_key: str | None = None,
    *,
    service_name: str = "unknown-service",
    environment: str = "development",
    providers: list[str] = [],
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

    if _initialized:
        logger.debug("Overmind SDK already initialized, skipping.")
        return

    service_name = service_name or os.environ.get("OVERMIND_SERVICE_NAME") or os.environ.get("SERVICE_NAME")
    environment = environment or os.environ.get("OVERMIND_ENVIRONMENT") or os.environ.get("ENVIRONMENT")

    overmind_api_key, overmind_base_url = get_api_settings(overmind_api_key, overmind_base_url)

    endpoint = f"{overmind_base_url}/api/v1/traces"

    # Configure OpenTelemetry Provider with rich resource attributes
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": os.environ.get("SERVICE_VERSION", "unknown"),
            "deployment.environment": environment,
            "overmind.sdk.name": "overmind-python",
            "overmind.sdk.version": "0.1.15",
        }
    )

    provider = TracerProvider(resource=resource)

    # Configure OTLP Exporter
    headers = {"X-API-Token": overmind_api_key}

    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    # Set global Trace Provider
    trace.set_tracer_provider(provider)

    # Store tracer for custom spans
    _tracer = trace.get_tracer("overmind", "0.1.15")
    enable_tracing(providers)

    _initialized = True
    logger.info(
        "Overmind SDK initialized: service=%s, environment=%s",
        service_name,
        environment,
    )


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

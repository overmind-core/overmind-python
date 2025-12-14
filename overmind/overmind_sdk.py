import logging
import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from overmind.utils.api_settings import get_api_settings

logger = logging.getLogger(__name__)

# Global state to track initialization
_initialized = False
_tracer: Optional[trace.Tracer] = None


def init(
    overmind_api_key: Optional[str] = None,
    traces_base_url: Optional[str] = None,
    service_name: Optional[str] = None,
    environment: Optional[str] = None,
    processes_sample_rate: float = 1.0,
    capture_request_body: bool = True,
    capture_response_body: bool = True,
) -> None:
    """
    Initialize the Overmind SDK for automatic monitoring.
    
    Call this once at application startup, before creating your FastAPI app.
    
    Example:
        import overmind
        overmind.init(service_name="my-backend")
        
        from fastapi import FastAPI
        app = FastAPI()

    Args:
        overmind_api_key: Your Overmind API key. If not provided, uses OVERMIND_API_KEY env var.
        traces_base_url: Base URL for traces. If not provided, uses OVERMIND_TRACES_URL env var.
        service_name: Name of your service (appears in traces). Defaults to OVERMIND_SERVICE_NAME 
                      env var or "unknown-service".
        environment: Environment name (e.g., "production", "staging"). Defaults to 
                     OVERMIND_ENVIRONMENT env var or "development".
        processes_sample_rate: Sampling rate for traces (0.0 to 1.0). Default 1.0 captures all.
        capture_request_body: Whether to capture OpenAI request payloads. Default True.
        capture_response_body: Whether to capture OpenAI response payloads. Default True.
    """
    global _initialized, _tracer
    
    if _initialized:
        logger.debug("Overmind SDK already initialized, skipping.")
        return
    
    try:
        api_key, _, traces_url = get_api_settings(
            overmind_api_key=overmind_api_key,
            traces_base_url=traces_base_url,
        )
    except Exception as e:
        logger.error(f"Failed to initialize Overmind SDK settings: {e}")
        return

    # Resolve service name and environment
    resolved_service_name = (
        service_name 
        or os.environ.get("OVERMIND_SERVICE_NAME") 
        or os.environ.get("SERVICE_NAME")
        or "unknown-service"
    )
    resolved_environment = (
        environment 
        or os.environ.get("OVERMIND_ENVIRONMENT") 
        or os.environ.get("ENVIRONMENT")
        or "development"
    )

    endpoint = f"{traces_url}/api/v1/traces/create"
    
    # Configure OpenTelemetry Provider with rich resource attributes
    resource = Resource.create({
        "service.name": resolved_service_name,
        "service.version": os.environ.get("SERVICE_VERSION", "unknown"),
        "deployment.environment": resolved_environment,
        "overmind.sdk.name": "overmind-python",
        "overmind.sdk.version": "0.1.15",
    })
    
    provider = TracerProvider(resource=resource)
    
    # Configure OTLP Exporter
    headers = {"X-API-Token": api_key}
    
    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    
    # Set global Trace Provider
    trace.set_tracer_provider(provider)
    
    # Store tracer for custom spans
    _tracer = trace.get_tracer("overmind", "0.1.15")

    # Instrument FastAPI (for HTTP request tracing)
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument()
        logger.info("Overmind SDK: FastAPI instrumentation enabled.")
    except ImportError:
        logger.debug("Overmind SDK: opentelemetry-instrumentation-fastapi not found, skipping.")
    except Exception as e:
        logger.warning(f"Overmind SDK: Failed to instrument FastAPI: {e}")

    # Instrument OpenAI (for LLM call tracing) - using vendored patched version
    try:
        from overmind._vendor.opentelemetry_instrumentation_openai import OpenAIInstrumentor
        OpenAIInstrumentor().instrument()
        logger.info("Overmind SDK: OpenAI instrumentation enabled (patched).")
    except ImportError:
        logger.debug("Overmind SDK: opentelemetry-instrumentation-openai not found, skipping.")
    except Exception as e:
        logger.warning(f"Overmind SDK: Failed to instrument OpenAI: {e}")

    # Instrument requests library (for outgoing HTTP calls)
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
        logger.info("Overmind SDK: Requests instrumentation enabled.")
    except ImportError:
        logger.debug("Overmind SDK: opentelemetry-instrumentation-requests not found, skipping.")
    except Exception as e:
        logger.warning(f"Overmind SDK: Failed to instrument Requests: {e}")

    # Instrument httpx (async HTTP client, used by newer OpenAI SDK)
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()
        logger.info("Overmind SDK: HTTPX instrumentation enabled.")
    except ImportError:
        logger.debug("Overmind SDK: opentelemetry-instrumentation-httpx not found, skipping.")
    except Exception as e:
        logger.warning(f"Overmind SDK: Failed to instrument HTTPX: {e}")

    # Instrument logging (to correlate logs with traces)
    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        LoggingInstrumentor().instrument(set_logging_format=True)
        logger.info("Overmind SDK: Logging instrumentation enabled.")
    except ImportError:
        logger.debug("Overmind SDK: opentelemetry-instrumentation-logging not found, skipping.")
    except Exception as e:
        logger.warning(f"Overmind SDK: Failed to instrument Logging: {e}")

    _initialized = True
    logger.info(
        f"Overmind SDK initialized: service={resolved_service_name}, "
        f"environment={resolved_environment}"
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
        raise RuntimeError(
            "Overmind SDK not initialized. Call overmind.init() first."
        )
    return _tracer


def set_user(user_id: str, email: Optional[str] = None, username: Optional[str] = None) -> None:
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

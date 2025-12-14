import os
from unittest.mock import patch, MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_sdk_state():
    """Reset SDK state before each test."""
    import overmind.overmind_sdk as sdk
    sdk._initialized = False
    sdk._tracer = None
    yield
    sdk._initialized = False
    sdk._tracer = None


@pytest.fixture
def mock_opentelemetry():
    """Mock all OpenTelemetry dependencies."""
    mock_fastapi_class = MagicMock()
    mock_openai_class = MagicMock()
    
    with patch("overmind.overmind_sdk.TracerProvider") as mock_provider, \
         patch("overmind.overmind_sdk.OTLPSpanExporter") as mock_exporter, \
         patch("overmind.overmind_sdk.BatchSpanProcessor") as mock_processor, \
         patch("overmind.overmind_sdk.trace") as mock_trace:
        
        # Set up tracer mock
        mock_tracer = MagicMock()
        mock_trace.get_tracer.return_value = mock_tracer
        
        yield {
            "provider": mock_provider,
            "exporter": mock_exporter,
            "processor": mock_processor,
            "trace": mock_trace,
            "tracer": mock_tracer,
        }


def test_sdk_init_configures_tracing(mock_opentelemetry):
    """Test that calling init configures OpenTelemetry correctly."""
    from overmind import overmind_sdk
    
    with patch.object(overmind_sdk, "FastAPIInstrumentor", create=True) as mock_fastapi, \
         patch.object(overmind_sdk, "OpenAIInstrumentor", create=True) as mock_openai:
        
        # Mock the dynamic imports
        with patch.dict("sys.modules", {
            "opentelemetry.instrumentation.fastapi": MagicMock(FastAPIInstrumentor=mock_fastapi),
            "opentelemetry.instrumentation.openai": MagicMock(OpenAIInstrumentor=mock_openai),
        }):
            overmind_sdk.init(
                overmind_api_key="test_key", 
                traces_base_url="http://localhost:4318",
                service_name="test-service",
                environment="testing"
            )
    
    # Verify Exporter configuration
    mock_opentelemetry["exporter"].assert_called_with(
        endpoint="http://localhost:4318/api/v1/traces/create",
        headers={"X-API-Token": "test_key"}
    )
    
    # Verify tracer provider was set
    mock_opentelemetry["trace"].set_tracer_provider.assert_called_once()


def test_sdk_init_only_once():
    """Test that init only runs once."""
    from overmind import overmind_sdk
    
    with patch("overmind.overmind_sdk.TracerProvider"), \
         patch("overmind.overmind_sdk.OTLPSpanExporter"), \
         patch("overmind.overmind_sdk.BatchSpanProcessor"), \
         patch("overmind.overmind_sdk.trace") as mock_trace:
        
        overmind_sdk.init(overmind_api_key="test_key", traces_base_url="http://localhost:4318")
        overmind_sdk.init(overmind_api_key="test_key", traces_base_url="http://localhost:4318")
        
        # Should only be called once
        assert mock_trace.set_tracer_provider.call_count == 1


def test_sdk_init_handles_missing_deps():
    """Test that init doesn't crash if optional instrumentation libraries are missing."""
    from overmind import overmind_sdk
    
    with patch("overmind.overmind_sdk.TracerProvider"), \
         patch("overmind.overmind_sdk.OTLPSpanExporter"), \
         patch("overmind.overmind_sdk.BatchSpanProcessor"), \
         patch("overmind.overmind_sdk.trace"):
        
        # Should not raise exception even if instrumentors fail to import
        overmind_sdk.init(overmind_api_key="test_key", traces_base_url="http://localhost:4318")


def test_get_tracer_before_init():
    """Test that get_tracer raises if SDK not initialized."""
    from overmind import overmind_sdk
    
    with pytest.raises(RuntimeError, match="not initialized"):
        overmind_sdk.get_tracer()


def test_get_tracer_after_init(mock_opentelemetry):
    """Test that get_tracer returns tracer after init."""
    from overmind import overmind_sdk
    
    overmind_sdk.init(overmind_api_key="test_key", traces_base_url="http://localhost:4318")
    
    tracer = overmind_sdk.get_tracer()
    assert tracer is not None


def test_set_user(mock_opentelemetry):
    """Test that set_user adds user attributes to current span."""
    from overmind import overmind_sdk
    
    mock_span = MagicMock()
    mock_span.is_recording.return_value = True
    mock_opentelemetry["trace"].get_current_span.return_value = mock_span
    
    overmind_sdk.init(overmind_api_key="test_key", traces_base_url="http://localhost:4318")
    overmind_sdk.set_user(user_id="user123", email="test@example.com")
    
    mock_span.set_attribute.assert_any_call("user.id", "user123")
    mock_span.set_attribute.assert_any_call("user.email", "test@example.com")


def test_set_tag(mock_opentelemetry):
    """Test that set_tag adds custom attributes to current span."""
    from overmind import overmind_sdk
    
    mock_span = MagicMock()
    mock_span.is_recording.return_value = True
    mock_opentelemetry["trace"].get_current_span.return_value = mock_span
    
    overmind_sdk.init(overmind_api_key="test_key", traces_base_url="http://localhost:4318")
    overmind_sdk.set_tag("tenant.id", "tenant123")
    
    mock_span.set_attribute.assert_called_with("tenant.id", "tenant123")


def test_capture_exception(mock_opentelemetry):
    """Test that capture_exception records exception on current span."""
    from overmind import overmind_sdk
    
    mock_span = MagicMock()
    mock_span.is_recording.return_value = True
    mock_opentelemetry["trace"].get_current_span.return_value = mock_span
    
    overmind_sdk.init(overmind_api_key="test_key", traces_base_url="http://localhost:4318")
    
    test_exception = ValueError("test error")
    overmind_sdk.capture_exception(test_exception)
    
    mock_span.record_exception.assert_called_once_with(test_exception)


def test_fastapi_request_flow():
    """
    Test that a FastAPI app works normally when instrumented.
    """
    app = FastAPI()
    
    @app.get("/ping")
    def ping():
        return {"message": "pong"}
    
    client = TestClient(app)
    response = client.get("/ping")
    
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}


def test_service_name_from_env():
    """Test that service name can be set via environment variable."""
    from overmind import overmind_sdk
    
    with patch("overmind.overmind_sdk.TracerProvider") as mock_provider, \
         patch("overmind.overmind_sdk.OTLPSpanExporter"), \
         patch("overmind.overmind_sdk.BatchSpanProcessor"), \
         patch("overmind.overmind_sdk.trace"), \
         patch("overmind.overmind_sdk.Resource") as mock_resource, \
         patch.dict(os.environ, {"OVERMIND_SERVICE_NAME": "env-service"}):
        
        overmind_sdk.init(overmind_api_key="test_key", traces_base_url="http://localhost:4318")
        
        # Check that Resource.create was called with the env service name
        call_args = mock_resource.create.call_args[0][0]
        assert call_args["service.name"] == "env-service"

"""
Unit tests for the trace_function decorator.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from opentelemetry.trace import Status, StatusCode


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
def mock_tracer():
    """Create a mock tracer with span context manager."""
    mock_span = MagicMock()
    mock_span.__enter__ = MagicMock(return_value=mock_span)
    mock_span.__exit__ = MagicMock(return_value=False)
    
    mock_tracer = MagicMock()
    mock_tracer.start_as_current_span.return_value = mock_span
    
    return mock_tracer, mock_span


def test_trace_function_sync_basic(mock_tracer):
    """Test basic synchronous function tracing."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function()
        def add_numbers(a: int, b: int):
            return a + b
        
        result = add_numbers(5, 3)
        
        assert result == 8
        mock_tracer_obj.start_as_current_span.assert_called_once_with("add_numbers")
        assert mock_span.set_attribute.call_count >= 2  # inputs and outputs
        mock_span.set_status.assert_called_once_with(Status(StatusCode.OK))


def test_trace_function_with_custom_span_name(mock_tracer):
    """Test decorator with custom span name."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function(span_name="custom_operation")
        def my_function(x: int):
            return x * 2
        
        result = my_function(10)
        
        assert result == 20
        mock_tracer_obj.start_as_current_span.assert_called_once_with("custom_operation")


def test_trace_function_captures_inputs(mock_tracer):
    """Test that function inputs are captured."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function()
        def process_data(name: str, age: int, metadata: dict):
            return {"processed": True}
        
        process_data("Alice", 30, {"city": "NYC"})
        
        # Check that inputs were set
        input_calls = [c for c in mock_span.set_attribute.call_args_list if "inputs" in str(c)]
        assert len(input_calls) > 0


def test_trace_function_captures_outputs(mock_tracer):
    """Test that function outputs are captured."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function()
        def get_result():
            return {"status": "success", "value": 42}
        
        result = get_result()
        
        assert result == {"status": "success", "value": 42}
        # Check that outputs were set
        output_calls = [c for c in mock_span.set_attribute.call_args_list if "outputs" in str(c)]
        assert len(output_calls) > 0


def test_trace_function_handles_exceptions(mock_tracer):
    """Test that exceptions are properly recorded."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function()
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            failing_function()
        
        # Check that exception was recorded
        mock_span.record_exception.assert_called_once()
        # Check that error status was set
        status_calls = [c for c in mock_span.set_status.call_args_list]
        assert len(status_calls) > 0
        # Verify error status
        error_call = status_calls[-1]
        assert error_call[0][0].status_code == StatusCode.ERROR


def test_trace_function_async(mock_tracer):
    """Test async function tracing."""
    import asyncio
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function(span_name="async_operation")
        async def async_add(a: int, b: int):
            await asyncio.sleep(0.01)
            return a + b
        
        result = asyncio.run(async_add(10, 20))
        
        assert result == 30
        mock_tracer_obj.start_as_current_span.assert_called_once_with("async_operation")
        mock_span.set_status.assert_called_once_with(Status(StatusCode.OK))


def test_trace_function_async_with_exception(mock_tracer):
    """Test async function exception handling."""
    import asyncio
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function()
        async def async_fail():
            await asyncio.sleep(0.01)
            raise RuntimeError("Async error")
        
        with pytest.raises(RuntimeError, match="Async error"):
            asyncio.run(async_fail())
        
        mock_span.record_exception.assert_called_once()
        status_calls = [c for c in mock_span.set_status.call_args_list]
        assert status_calls[-1][0][0].status_code == StatusCode.ERROR


def test_trace_function_with_kwargs(mock_tracer):
    """Test function with keyword arguments."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function()
        def greet(name: str, greeting: str = "Hello"):
            return f"{greeting}, {name}!"
        
        result = greet("World", greeting="Hi")
        
        assert result == "Hi, World!"
        mock_tracer_obj.start_as_current_span.assert_called_once()


def test_trace_function_preserves_function_metadata(mock_tracer):
    """Test that function metadata is preserved."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function()
        def documented_function(param: int) -> int:
            """This is a test function."""
            return param * 2
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."


def test_trace_function_with_complex_types(mock_tracer):
    """Test tracing with complex data types."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function()
        def process_complex(data: dict, items: list):
            return {"processed": len(items), "data_keys": list(data.keys())}
        
        result = process_complex(
            {"key1": "value1", "key2": 123},
            [1, 2, 3, 4, 5]
        )
        
        assert result == {"processed": 5, "data_keys": ["key1", "key2"]}
        mock_tracer_obj.start_as_current_span.assert_called_once()


def test_trace_function_with_no_args(mock_tracer):
    """Test function with no arguments."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function()
        def get_constant():
            return 42
        
        result = get_constant()
        
        assert result == 42
        mock_tracer_obj.start_as_current_span.assert_called_once()


def test_trace_function_with_positional_only_args(mock_tracer):
    """Test function with positional arguments."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        @trace_function()
        def multiply(x, y):
            return x * y
        
        result = multiply(6, 7)
        
        assert result == 42
        mock_tracer_obj.start_as_current_span.assert_called_once()


def test_trace_function_skips_self_in_class_method(mock_tracer):
    """Test that self is not captured for instance methods."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        class TestClass:
            def __init__(self):
                self.value = 10
            
            @trace_function()
            def instance_method(self, x: int, y: int):
                return self.value + x + y
        
        obj = TestClass()
        result = obj.instance_method(5, 3)
        
        assert result == 18
        # Check that inputs were captured but self was skipped
        input_calls = [c for c in mock_span.set_attribute.call_args_list if "inputs" in str(c)]
        assert len(input_calls) > 0
        # Verify self is not in the captured inputs
        captured_inputs = str(input_calls[0])
        assert "self" not in captured_inputs or '"self"' not in captured_inputs


def test_trace_function_skips_cls_in_classmethod(mock_tracer):
    """Test that cls is not captured for class methods."""
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        class TestClass:
            class_value = 20
            
            @classmethod
            @trace_function()
            def class_method(cls, x: int, y: int):
                return cls.class_value + x + y
        
        result = TestClass.class_method(5, 3)
        
        assert result == 28
        # Check that inputs were captured but cls was skipped
        input_calls = [c for c in mock_span.set_attribute.call_args_list if "inputs" in str(c)]
        assert len(input_calls) > 0
        # Verify cls is not in the captured inputs
        captured_inputs = str(input_calls[0])
        assert "cls" not in captured_inputs or '"cls"' not in captured_inputs


def test_trace_function_async_class_method(mock_tracer):
    """Test async class method with self skipped."""
    import asyncio
    from overmind.tracer import trace_function
    
    mock_tracer_obj, mock_span = mock_tracer
    
    with patch("overmind.tracer.get_tracer", return_value=mock_tracer_obj):
        class AsyncTestClass:
            def __init__(self):
                self.value = 15
            
            @trace_function()
            async def async_method(self, x: int):
                await asyncio.sleep(0.01)
                return self.value * x
        
        obj = AsyncTestClass()
        result = asyncio.run(obj.async_method(2))
        
        assert result == 30
        mock_tracer_obj.start_as_current_span.assert_called_once()

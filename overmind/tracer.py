"""
OpenTelemetry tracing decorator for automatic function instrumentation.

This module provides a decorator that automatically traces function calls,
capturing inputs and outputs in OpenTelemetry style.
"""
import functools
import inspect
from typing import Any, Callable, Optional
from opentelemetry.trace import Status, StatusCode

from overmind.overmind_sdk import get_tracer
from overmind.utils.serializers import serialize


def _prepare_for_otel(value: Any) -> Any:
    """
    Prepare a value for inclusion in OpenTelemetry span attributes.

    Converts complex types to serializable formats while preserving simple types.
    """
    # Simple types can be used directly
    if isinstance(value, (str, int, float, bool, type(None))):
        return value

    # For Pydantic models, convert to dict
    if hasattr(value, 'model_dump'):
        try:
            return value.model_dump()
        except Exception:
            return str(value)

    # For dicts, lists, tuples - return as-is (will be serialized later)
    if isinstance(value, (dict, list, tuple)):
        return value

    # For other types, convert to string
    return str(value)


def trace_function(span_name: Optional[str] = None):
    """
    Decorator that automatically traces function execution with OpenTelemetry.

    Captures function inputs and outputs as span attributes in OTEL style.
    Works with both synchronous and asynchronous functions.

    Args:
        span_name: Optional name for the span. If not provided, uses the function name.

    Example:
        ```python
        @trace_function(span_name="process_data")
        def process_data(user_id: int, data: dict):
            return {"result": "success"}

        @trace_function()  # Uses function name as span name
        async def async_operation(param: str):
            return await some_async_call(param)
        ```

    The decorator will:
    - Create a span with the specified name (or function name)
    - Capture all function arguments as span attributes (skips self/cls for class methods)
    - Capture the return value as a span attribute
    - Record exceptions if they occur
    - Set appropriate span status codes
    """
    def decorator(func: Callable) -> Callable:
        # Determine span name
        name = span_name or func.__name__

        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                tracer = get_tracer()

                # Get function signature for better argument names
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # Check if this is a method (has self or cls as first parameter)
                param_names = list(sig.parameters.keys())
                is_method = len(param_names) > 0 and param_names[0] in ('self', 'cls')
                start_idx = 1 if is_method else 0

                # Start span
                with tracer.start_as_current_span(name) as span:
                    try:
                        # Capture inputs
                        inputs = {}

                        # Add positional arguments (skip self/cls if it's a method)
                        for i, arg in enumerate(args[start_idx:], start=start_idx):
                            if i < len(param_names):
                                param_name = param_names[i]
                                inputs[param_name] = _prepare_for_otel(arg)
                            else:
                                inputs[f"arg_{i}"] = _prepare_for_otel(arg)

                        # Add keyword arguments
                        for key, value in kwargs.items():
                            inputs[key] = _prepare_for_otel(value)

                        # Set input attributes on span (serialize the entire inputs dict)
                        span.set_attribute("inputs", serialize(inputs))

                        # Execute function
                        result = await func(*args, **kwargs)

                        # Capture output
                        output = _prepare_for_otel(result)
                        span.set_attribute("outputs", serialize(output))

                        # Set success status
                        span.set_status(Status(StatusCode.OK))

                        return result

                    except Exception as e:
                        # Record exception
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                tracer = get_tracer()

                # Get function signature for better argument names
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # Check if this is a method (has self or cls as first parameter)
                param_names = list(sig.parameters.keys())
                is_method = len(param_names) > 0 and param_names[0] in ('self', 'cls')
                start_idx = 1 if is_method else 0

                # Start span
                with tracer.start_as_current_span(name) as span:
                    try:
                        # Capture inputs
                        inputs = {}

                        # Add positional arguments (skip self/cls if it's a method)
                        for i, arg in enumerate(args[start_idx:], start=start_idx):
                            if i < len(param_names):
                                param_name = param_names[i]
                                inputs[param_name] = _prepare_for_otel(arg)
                            else:
                                inputs[f"arg_{i}"] = _prepare_for_otel(arg)

                        # Add keyword arguments
                        for key, value in kwargs.items():
                            inputs[key] = _prepare_for_otel(value)

                        # Set input attributes on span (serialize the entire inputs dict)
                        span.set_attribute("inputs", serialize(inputs))

                        # Execute function
                        result = func(*args, **kwargs)

                        # Capture output
                        output = _prepare_for_otel(result)
                        span.set_attribute("outputs", serialize(output))

                        # Set success status
                        span.set_status(Status(StatusCode.OK))

                        return result

                    except Exception as e:
                        # Record exception
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise

            return sync_wrapper

    return decorator

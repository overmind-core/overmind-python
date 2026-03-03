import logging

from overmind.clients.overmind_client import OvermindClient

try:
    import opentelemetry.instrumentation.anthropic as __anthropic_instrumentation

    __anthropic_instrumentation.AnthropicInstrumentor().instrument()
    import anthropic as __anthropic
except ImportError:
    raise ImportError("anthropic is not installed. Please install it with `pip install anthropic`.")

logger = logging.getLogger(__name__)


class Anthropic(__anthropic.Anthropic):
    def __init__(
        self,
        *,
        overmind_api_key: str | None = None,
        overmind_base_url: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.overmind_client = OvermindClient(overmind_api_key, overmind_base_url)

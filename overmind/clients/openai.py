import logging

from overmind.clients.overmind_client import OvermindClient

try:
    import openai as __openai
except ImportError:
    raise ImportError("openai is not installed. Please install it with `pip install openai`.")

logger = logging.getLogger(__name__)


class OpenAI(__openai.OpenAI):
    # init_overmind
    def __init__(
        self,
        *,
        overmind_api_key: str | None = None,
        overmind_base_url: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.overmind_client = OvermindClient(overmind_api_key, overmind_base_url)


class AsyncOpenAI(__openai.AsyncOpenAI):
    """
    Async Overmind-wrapped OpenAI client.

    Telemetry (OpenTelemetry traces) is fully captured via the OvermindClient
    initialisation which instruments the openai library.

    Policy support (input_policies / output_policies) is not yet wired for
    async - the parameters are accepted and stored so the interface is
    forward-compatible with the sync OpenAI client.
    """

    def __init__(
        self,
        *,
        overmind_api_key: str | None = None,
        overmind_base_url: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        # This triggers overmind.init() which sets up OTel tracing +
        # instruments the openai module (both sync and async paths).
        self.overmind_client = OvermindClient(overmind_api_key, overmind_base_url)

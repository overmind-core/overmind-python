
from typing import Optional
import logging
from overmind.clients.overmind_client import OvermindClient

try:
    import opentelemetry.instrumentation.google_generativeai as __google_instrumentation
    __google_instrumentation.GoogleGenerativeAiInstrumentor().instrument()
    from google import genai
except ImportError:
    raise ImportError(
        "google-genai is not installed. Please install it with `pip install google-genai`."
    )

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Client(genai.Client):
    def __init__(
        self,
        *,
        overmind_api_key: str,
        overmind_base_url: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.overmind_client = OvermindClient(overmind_api_key, overmind_base_url)

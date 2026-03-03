import logging
import os
from overmind.overmind_sdk import init

logger = logging.getLogger(__name__)


def enable_logging():
    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor

        LoggingInstrumentor().instrument(set_logging_format=True)
    except ImportError:
        raise ImportError(
            "opentelemetry-instrumentation-logging is not installed. Please install it with `pip install opentelemetry-instrumentation-logging`."
        )


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


class OvermindClient:
    def __init__(
        self,
        overmind_api_key: str | None = None,
        overmind_base_url: str | None = None,
    ):
        self.overmind_api_key = overmind_api_key or os.getenv(
            "OVERMIND_API_KEY",
        )
        if not self.overmind_api_key:
            raise ValueError("OVERMIND_API_KEY is not set")

        self.overmind_base_url = overmind_base_url or os.getenv(
            "OVERMIND_API_URL",
        )

        init(overmind_api_key, traces_base_url=self.overmind_base_url)

    def enable_tracing(self, names: list[str]):
        if "agno" in names:
            enable_agno()
        elif "openai" in names:
            enable_openai()
        elif "anthropic" in names:
            enable_anthropic()
        elif "google" in names:
            enable_google_genai()
        if "logging" in names:
            enable_logging()
        else:
            raise ValueError(f"Tracing for {names} is not supported")

from typing import Optional, List, Any
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


class Client(genai.Client):
    def __init__(
        self,
        *,
        overmind_api_key: Optional[str] = None,
        overmind_base_url: Optional[str] = None,
        input_policies: List[str] = [],
        output_policies: List[str] = [],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.overmind_client = OvermindClient(overmind_api_key, overmind_base_url)
        self.global_input_policies = input_policies
        self.global_output_policies = output_policies
        # Wrap generate_content for policy interception
        self._original_generate_content = self.models.generate_content
        self.models.generate_content = self._wrapped_generate_content

    def _run_input_policies(self, contents):
        """Run input policies on the contents, modifying text in place."""
        if isinstance(contents, str):
            for policy in self.global_input_policies:
                res = self.overmind_client.run_layer(
                    policy=policy, input_data=contents
                )
                contents = res.processed_data or contents
            return contents

        if isinstance(contents, list) and contents:
            last = contents[-1]
            if isinstance(last, dict):
                parts = last.get("parts", [])
                for part in parts:
                    if isinstance(part, dict) and "text" in part:
                        text = part["text"]
                        for policy in self.global_input_policies:
                            res = self.overmind_client.run_layer(
                                policy=policy, input_data=text
                            )
                            part["text"] = res.processed_data or text

        return contents

    def _extract_question(self, contents) -> str:
        """Extract the question text from contents for output policy context."""
        if isinstance(contents, str):
            return contents
        if isinstance(contents, list) and contents:
            last = contents[-1]
            if isinstance(last, str):
                return last
            if isinstance(last, dict):
                parts = last.get("parts", [])
                texts = [
                    p.get("text", "")
                    for p in parts
                    if isinstance(p, dict) and "text" in p
                ]
                return " ".join(texts)
        return str(contents)

    def _wrapped_generate_content(self, **kwargs):
        contents = kwargs.get("contents")

        # Run input policies
        if self.global_input_policies and contents:
            kwargs["contents"] = self._run_input_policies(contents)

        question = self._extract_question(kwargs.get("contents", contents))

        # Call original generate_content
        response = self._original_generate_content(**kwargs)

        # Run output policies
        if self.global_output_policies:
            try:
                response_text = response.text
            except Exception:
                response_text = None

            if response_text:
                for policy in self.global_output_policies:
                    self.overmind_client.run_layer(
                        policy=policy,
                        input_data=response_text,
                        question=question,
                    )

        return response

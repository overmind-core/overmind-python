from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Any
import logging

from httpx import Request, Response, URL

from overmind.clients.overmind_client import OvermindClient

try:
    import opentelemetry.instrumentation.anthropic as __anthropic_instrumentation

    __anthropic_instrumentation.AnthropicInstrumentor().instrument()
    import anthropic as __anthropic
except ImportError:
    raise ImportError(
        "anthropic is not installed. Please install it with `pip install anthropic`."
    )

logger = logging.getLogger(__name__)


class Anthropic(__anthropic.Anthropic):
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
        self._client.build_request = self.build_request_decorator(
            self._client.build_request
        )
        self.global_input_policies = input_policies
        self.global_output_policies = output_policies
        self._client.event_hooks = {
            "response": [self.run_output_policies],
        }

    def _get_handler(self, path: str) -> Optional["BaseHandler"]:
        if path == messagesHandler.path:
            logger.debug(f"using messagesHandler for path: {path}")
            return messagesHandler(self.overmind_client)
        return None

    def build_request_decorator(self, func):
        def wrapper(*args, **kwargs) -> Request:
            json_content = kwargs.get("json")
            if not json_content:
                return func(*args, **kwargs)

            input_policies = (
                json_content.pop("input_policies", None) or self.global_input_policies
            )
            output_policies = (
                json_content.pop("output_policies", None)
                or self.global_output_policies
            )

            url: URL = kwargs.get("url")
            handler = self._get_handler(url.path)

            if handler and not json_content.get("stream", False):
                kwargs = handler.pre_request(
                    kwargs=kwargs,
                    json_content=json_content,
                    input_policies=input_policies,
                )
            else:
                kwargs.update(json=json_content)

            request: Request = func(*args, **kwargs)
            setattr(request, "input_policies", input_policies)
            setattr(request, "output_policies", output_policies)
            if handler:
                handler.post_request(request=request, kwargs=kwargs)

            return request

        return wrapper

    def run_output_policies(self, response: Response):
        if response.status_code != 200:
            return

        if response.headers.get("Content-Type") != "application/json":
            return

        output_policies = getattr(response._request, "output_policies", [])
        logger.info(f"output_policies={output_policies} in response")

        response.read()
        json_output = response.json()
        handler = self._get_handler(response._request.url.path)

        if handler:
            handler.post_response(
                response=response,
                json_output=json_output,
                output_policies=output_policies,
            )


@dataclass
class BaseHandler(ABC):
    overmind_client: OvermindClient
    path: str = None

    def _run_input_policies_messages(
        self, inputs: list[str], input_policies: list[Any]
    ):
        for policy in input_policies:
            res = self.overmind_client.run_layer(policy=policy, input_data=inputs[-1])
            inputs[-1] = res.processed_data or inputs[-1]
        return inputs

    @abstractmethod
    def pre_request(
        self, kwargs: dict, json_content: dict, input_policies: list[Any]
    ): ...

    @abstractmethod
    def post_request(self, request: Request, kwargs: dict): ...

    @abstractmethod
    def post_response(
        self, response: Response, json_output: dict, output_policies: list[Any]
    ): ...


class messagesHandler(BaseHandler):
    path = "/v1/messages"

    def pre_request(self, kwargs: dict, json_content: dict, input_policies: list[Any]):
        messages = json_content.get("messages", [])
        if messages and input_policies:
            last_message = messages[-1]
            content = last_message.get("content", "")
            # Anthropic supports string content or list of content blocks
            if isinstance(content, str):
                modified = self._run_input_policies_messages(
                    inputs=[content], input_policies=input_policies
                )[-1]
                messages[-1] = {**last_message, "content": modified}
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        modified = self._run_input_policies_messages(
                            inputs=[block["text"]], input_policies=input_policies
                        )[-1]
                        block["text"] = modified
            json_content["messages"] = messages
        kwargs.update(json=json_content)
        return kwargs

    def post_request(self, request: Request, kwargs: dict):
        messages = kwargs.get("json", {}).get("messages", [])
        question = ""
        if messages:
            content = messages[-1].get("content", "")
            if isinstance(content, str):
                question = content
            elif isinstance(content, list):
                question = " ".join(
                    b.get("text", "")
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
        setattr(request, "kwargs", {"question": question})

    def post_response(
        self, response: Response, json_output: dict, output_policies: list[Any]
    ):
        # Anthropic response format: {"content": [{"type": "text", "text": "..."}]}
        content_blocks = json_output.get("content", [])
        text_content = " ".join(
            block.get("text", "")
            for block in content_blocks
            if isinstance(block, dict) and block.get("type") == "text"
        )

        if not text_content:
            return

        for policy in output_policies:
            self.overmind_client.run_layer(
                policy=policy,
                input_data=text_content,
                **getattr(response._request, "kwargs", {}),
            )

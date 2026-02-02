from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Any, List
import logging

from httpx import Request, Response, URL

from overmind.clients.overmind_client import OvermindClient

try:
    import openai as __openai
except ImportError:
    raise ImportError(
        "openai is not installed. Please install it with `pip install openai`."
    )

logger = logging.getLogger(__name__)


class OpenAI(__openai.OpenAI):
    # init_overmind
    def __init__(
        self,
        *,
        overmind_api_key: Optional[str] = None,
        # internal client will use OVERMIND_API_KEY env var
        overmind_base_url: Optional[str] = None,
        # internal client will use OVERMIND_API_URL env var
        # a set of global policies that will be applied to all requests
        input_policies: List[str] = [],
        # a set of global policies that will be applied to all responses
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
        if path == responsesHandler.path:
            logger.debug(f"using responsesHandler for path: {path}")
            return responsesHandler(self.overmind_client)
        if path == chatCompletionHandler.path:
            logger.debug(f"using chatCompletionHandler for path: {path}")
            return chatCompletionHandler(self.overmind_client)
        if path == audioSpeechHandler.path:
            logger.debug(f"using audioSpeechHandler for path: {path}")
            return audioSpeechHandler(self.overmind_client)
        if path == responsesCompactHandler.path:
            logger.debug(f"using responsesCompactHandler for path: {path}")
            return responsesCompactHandler(self.overmind_client)

    def build_request_decorator(
        self, func: Callable[[Any], Request]
    ) -> Callable[[Any], Request]:
        # TODO: not the best idea to add to extra_body
        def wrapper(*args, **kwargs) -> Request:
            # TODO: need to handle all, content, body, and data, and files
            json_content = kwargs.get("json")
            # role = input policy will change the user input
            # output policy will  not change the response but just flags it to the user
            input_policies = (
                json_content.pop("input_policies", None) or self.global_input_policies
            )
            output_policies = (
                json_content.pop("output_policies", None) or self.global_output_policies
            )

            url: URL = kwargs.get("url")
            handler = self._get_handler(url.path)
            # TODO: add stram handler here
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

            # run input policies here, modify the request content as needed
            return request

        return wrapper

    def run_output_policies(self, response: Response):
        def summary():
            raise NotImplementedError("method not implemented yet")

        setattr(response, "summary", summary)
        # return
        if response.status_code != 200:
            return

        # allow audio responses/ non text responses
        if response.headers.get("Content-Type") != "application/json":
            return

        output_policies = getattr(response._request, "output_policies", [])
        logger.info(f"output_policies={output_policies} in response")

        response.read()  # read the response content to get the actual content
        # TODO: need a few checks here for all kinds of payloads
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

    def run_input_policies(self, messages: list[dict], input_policies: List[Any]):
        # ideally should run it for all items in the array of messages messages
        content_modified = self._run_input_policies_messages(
            [messages[-1]["content"]], input_policies
        )[-1]

        messages[-1]["content"] = content_modified
        return messages

    def _run_input_policies_messages(
        self, inputs: list[str], input_policies: list[Any]
    ):
        for policy in input_policies:
            res = self.overmind_client.run_layer(policy=policy, input_data=inputs[-1])
            inputs[-1] = (
                res.processed_data or inputs[-1]
            )  # if the policy returns None, keep the original input
        return inputs

    @abstractmethod
    def pre_request(
        self,
        kwargs: dict,
        json_content: dict,
        input_policies: list[Any],
    ): ...

    @abstractmethod
    def post_request(self, request: Request, kwargs: dict): ...

    @abstractmethod
    def post_response(
        self, response: Response, json_output: dict, output_policies: list[Any]
    ): ...


class chatCompletionHandler(BaseHandler):
    path = "/v1/chat/completions"

    def pre_request(self, kwargs: dict, json_content: dict, input_policies: list[Any]):
        kwargs.update(json=self._pre_json(json_content, input_policies))
        return kwargs

    def _pre_json(self, json_content: dict, input_policies: list[Any]):
        messages = json_content.pop("messages", None)
        original_message = messages[-1]["content"]
        messages[-1] = {
            "role": messages[-1]["role"],
            "content": self._run_input_policies_messages(
                inputs=[original_message], input_policies=input_policies
            )[-1],
        }
        json_content["messages"] = messages
        return json_content

    def _pre_file(self, file: dict, input_policies: list[Any]): ...

    def post_request(self, request: Request, kwargs: dict):
        setattr(
            request,
            "kwargs",
            {"question": kwargs["json"]["messages"][-1]["content"]},
        )

    def post_response(
        self, response: Response, json_output: dict, output_policies: list[Any]
    ):
        content = json_output["choices"][0]["message"].get("content", "")
        tool_calls = json_output["choices"][0]["message"].get("tool_calls", [])

        if not content:
            return
        for policy in output_policies:
            self.overmind_client.run_layer(
                policy=policy,
                input_data=content,
                **getattr(response._request, "kwargs", {}),
            )


class responsesHandler(BaseHandler):
    path = "/v1/responses"

    def pre_request(self, kwargs: dict, json_content: dict, input_policies: list[Any]):
        modified_input = self._run_input_policies_messages(
            inputs=[json_content.pop("input", None)],
            input_policies=input_policies,
        )[-1]
        json_content.update({"input": modified_input})
        kwargs.update(json=json_content)
        return kwargs

    def post_request(self, request: Request, kwargs: dict):
        setattr(
            request,
            "kwargs",
            {"question": kwargs["json"]["input"]},
        )

    def post_response(
        self, response: Response, json_output: dict, output_policies: list[Any]
    ):
        pass


class doNothingHandler(BaseHandler):
    path = None

    def pre_request(self, kwargs: dict, json_content: dict, input_policies: list[Any]):
        return kwargs

    def post_request(self, request: Request, kwargs: dict):
        return

    def post_response(
        self, response: Response, json_output: dict, output_policies: list[Any]
    ):
        return


class audioSpeechHandler(doNothingHandler):
    path = "/v1/audio/speech"


class responsesCompactHandler(doNothingHandler):
    path = "/v1/responses/compact"


class AsyncOpenAI(__openai.AsyncOpenAI):
    def __init__(
        self,
        *,
        overmind_api_key: str,
        overmind_base_url: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.overmind_client = OvermindClient(overmind_api_key, overmind_base_url)
        logger.warning("overmind AsyncOpenAI is not ready with tracing and layers yet")

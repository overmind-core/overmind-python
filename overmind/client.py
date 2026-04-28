"""
Overmind layers client.
"""

from collections.abc import Sequence
from functools import lru_cache

import requests

from .exceptions import OvermindAPIError
from .models import LayerResponse
from .utils.api_settings import get_api_settings


class OvermindLayersClient:
    def __init__(
        self,
        overmind_api_key: str | None = None,
        base_url: str | None = None,
        traces_base_url: str | None = None,
    ):
        self.overmind_api_key, self.base_url = get_api_settings(overmind_api_key, base_url)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-API-Token": self.overmind_api_key,
                "Content-Type": "application/json",
            }
        )

    def run_layer(
        self, input_data: str, policies: Sequence[str | dict], layer_position: str, **kwargs
    ) -> LayerResponse:
        """
        Run a layer of the Overmind API.
        """
        payload = {
            "input_data": input_data,
            "policies": policies,
            "layer_position": layer_position,
            "kwargs": kwargs,
        }

        response_data = self.session.request("POST", f"{self.base_url}/api/v1/layers/run", json=payload)

        if response_data.status_code != 200:
            raise OvermindAPIError(
                message=response_data.text,
                status_code=response_data.status_code,
                response_data=response_data.json(),
            )

        return LayerResponse(**response_data.json())


@lru_cache
def get_layers_client(
    overmind_api_key: str | None = None,
    base_url: str | None = None,
    traces_base_url: str | None = None,
):
    return OvermindLayersClient(overmind_api_key, base_url, traces_base_url)

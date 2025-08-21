import os
from overmind.client import OvermindError
from typing import Optional


def get_api_settings(
    overmind_api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    traces_base_url: Optional[str] = None,
) -> tuple[str, str, str]:
    if overmind_api_key is None:
        overmind_api_key = os.getenv("OVERMIND_API_KEY")
        if overmind_api_key is None:
            raise OvermindError(
                "No Overmind API key provided. Either pass 'overmind_api_key' parameter "
                "or set OVERMIND_API_KEY environment variable."
            )

    if base_url is None:
        base_url = os.getenv("OVERMIND_API_URL")
        if base_url is None:
            base_url = "https://api.overmindlab.ai"

    if traces_base_url is None:
        traces_base_url = os.getenv("OVERMIND_TRACES_URL")
        if traces_base_url is None:
            traces_base_url = "https://traces.overmindlab.ai"

    base_url = base_url.rstrip("/")

    return overmind_api_key, base_url, traces_base_url

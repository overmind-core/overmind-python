import os
from overmind.client import OvermindError
from typing import Optional

LOCAL_API_KEY_PREFIX = "ovr_core_"
LOCAL_BASE_URL = "http://localhost:8000"
DEFAULT_BASE_URL = "https://api.overmindlab.ai"


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

    is_local = overmind_api_key.startswith(LOCAL_API_KEY_PREFIX)
    default_url = LOCAL_BASE_URL if is_local else DEFAULT_BASE_URL

    if base_url is None:
        base_url = os.getenv("OVERMIND_API_URL") or default_url

    if traces_base_url is None:
        traces_base_url = os.getenv("OVERMIND_TRACES_URL") or default_url

    base_url = base_url.rstrip("/")

    return overmind_api_key, base_url, traces_base_url

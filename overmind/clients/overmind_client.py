import logging
import os
from typing import Optional


from overmind.overmind_sdk import init

logger = logging.getLogger(__name__)


class OvermindClient:
    def __init__(
        self,
        overmind_api_key: Optional[str] = None,
        overmind_base_url: Optional[str] = None,
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

        logger.debug("OVERMIND_API_URL is set to: %s", self.overmind_base_url)

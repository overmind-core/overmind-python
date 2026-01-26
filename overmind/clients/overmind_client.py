import os
import logging
from overmind import layers

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class OvermindClient:
    def __init__(self, overmind_api_key: str, overmind_base_url: str = None):
        self.overmind_api_key = overmind_api_key or os.getenv(
            "OVERMIND_API_KEY",
        )
        if not self.overmind_api_key:
            raise ValueError("OVERMIND_API_KEY is not set")

        self.overmind_base_url = overmind_base_url or os.getenv(
            "OVERMIND_API_URL",
        )

        logger.debug("OVERMIND_API_URL is set to: %s", self.overmind_base_url)

    def summary(self, *args, **kwargs): ...

    def _make_request(self, *args, **kwargs): ...

    def create_agent(self, *args, **kwargs): ...

    def create_policy(self, *args, **kwargs): ...

    def run_layer(self, *, policy, input_data, **kwargs):
        layer = get_layer(policy, **kwargs)
        return layer.run(input_data=input_data, **kwargs)


def get_layer(name: str, **kwargs) -> layers.GenericOvermindLayer:
    # layer factory
    if name == "anonymize_pii":
        return layers.AnonymizePIILayer(**kwargs)
    if name == "reject_irrelevant_answer":
        return layers.RejectIrrelevantAnswersLayer(**kwargs)
    if name == "reject_prompt_injection":
        return layers.RejectPromptInjectionLayer(**kwargs)
    if name == "reject_llm_judge_with_criteria":
        return layers.LLMJudgeScorerLayer(**kwargs)
    else:
        raise ValueError(f"Invalid layer name: {name}")

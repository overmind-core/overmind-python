import os
import logging
from typing import Optional
from overmind import layers
from overmind.overmind_sdk import init, get_tracer

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

    def run_layer(self, *, policy, input_data, **kwargs):
        layer = get_layer(policy, **kwargs)
        with get_tracer().start_as_current_span(f"execute_policy_{policy}") as span:
            response = layer.run(input_data=input_data, **kwargs)
            span.set_attribute("inputs", str(input_data))
            span.set_attribute("outputs", str(response.processed_data))
            span.set_attribute("policy_outcome", response.overall_policy_outcome)
            span.set_attribute("policy_results", str(response.policy_results))

        return response


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

from overmind.client import get_layers_client, OvermindLayersClient
from overmind.models import LayerResponse
from typing import Sequence


class GenericOvermindLayer:
    def __init__(
        self,
        policies: Sequence[str | dict],
        layer_position: str,
        layers_client: OvermindLayersClient | None = None,
        **kwargs,
    ):
        self.layers_client = layers_client or get_layers_client()
        self.policies = policies
        self.layer_position = layer_position

    def run(self, input_data: str, **kwargs) -> LayerResponse:
        return self.layers_client.run_layer(input_data, self.policies, self.layer_position, **kwargs)


class AnonymizePIILayer(GenericOvermindLayer):
    """
    Anonymize PII data in the state.
    """

    def __init__(
        self,
        pii_types: dict[str, str] | None = None,
        layer_position: str = "input",
        layers_client: OvermindLayersClient | None = None,
        **kwargs,
    ):
        policies = [
            {
                "policy_template": "anonymize_pii",
                "parameters": {"pii_types": pii_types},
            }
        ]

        super().__init__(policies, layer_position, layers_client)


class RejectPromptInjectionLayer(GenericOvermindLayer):
    """
    Inject a reject prompt into the state.
    """

    def __init__(
        self,
        layer_position: str = "input",
        layers_client: OvermindLayersClient | None = None,
        **kwargs,
    ):
        super().__init__(["reject_prompt_injection"], layer_position, layers_client)


class RejectIrrelevantAnswersLayer(GenericOvermindLayer):
    """
    Reject answers that are irrelevant to the question.
    """

    def __init__(
        self,
        layer_position: str = "output",
        layers_client: OvermindLayersClient | None = None,
        **kwargs,
    ):
        super().__init__(["reject_irrelevant_answer"], layer_position, layers_client)


class LLMJudgeScorerLayer(GenericOvermindLayer):
    """
    Judge the LLM's response according to a list of criteria. Each criterion should evaluate to true or false.
    """

    def __init__(
        self,
        criteria: list[str],
        layer_position: str = "output",
        layers_client: OvermindLayersClient | None = None,
        **kwargs,
    ):
        policies = [
            {
                "policy_template": "reject_llm_judge_with_criteria",
                "parameters": {"criteria": criteria},
            }
        ]
        super().__init__(policies, layer_position, layers_client)


class LLMJudgeScorerLayerQA(GenericOvermindLayer):
    """
    Judge the LLM's response according to a list of criteria. Each criterion should evaluate to true or false.
    """

    def __init__(
        self,
        criteria: list[str],
        layer_position: str = "output",
        layers_client: OvermindLayersClient | None = None,
    ):
        policies = [
            {
                "policy_template": "reject_llm_judge_with_criteria_and_question",
                "parameters": {"criteria": criteria},
            }
        ]
        super().__init__(policies, layer_position, layers_client)

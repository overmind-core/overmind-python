from overmind.client import get_layers_client, OvermindLayersClient
from overmind.models import LayerResponse
from typing import Any, Callable, Sequence, TypedDict


def last_message_extractor(state: TypedDict) -> str:
    return state["messages"][-1].content


class GenericOvermindLayer:
    def __init__(
        self,
        # target_extractor: Callable,
        policies: Sequence[str | dict],
        layers_client: OvermindLayersClient | None = None,
    ):
        self.layers_client = layers_client or get_layers_client()
        # self.target_extractor = target_extractor
        self.policies = policies

    # def __call__(self, state: TypedDict) -> TypedDict:
    #     return self.layers_client.run_layer(
    #         self.target_extractor(state), self.policies
    #     )

    def run(self, input_data: str) -> LayerResponse:
        return self.layers_client.run_layer(input_data, self.policies)


class AnonymizePIILayer(GenericOvermindLayer):
    """
    Anonymize PII data in the state.
    """

    def __init__(
        self,
        # target_extractor: Callable,
        pii_types: list[str] | None = None,
        layers_client: OvermindLayersClient | None = None,
    ):
        if pii_types is None:
            pii_types = [
                "DEMOGRAPHIC_DATA",
                "FINANCIAL_ID",
                "GEOGRAPHIC_DATA",
                "GOVERNMENT_ID",
                "MEDICAL_DATA",
                "SECURITY_DATA",
                "TECHNICAL_ID",
                "PERSON_NAME",
            ]

        policies = [
            {
                "policy_template": "anonymize_pii",
                "parameters": {"pii_types": pii_types},
            }
        ]

        super().__init__(policies, layers_client)


class RejectPromptInjectionLayer(GenericOvermindLayer):
    """
    Inject a reject prompt into the state.
    """

    def __init__(
        self,
        # target_extractor: Callable,
        layers_client: OvermindLayersClient | None = None,
    ):
        super().__init__(["reject_prompt_injection"], layers_client)


class RejectIrrelevantAnswersLayer(GenericOvermindLayer):
    """
    Reject answers that are irrelevant to the question.
    """

    def __init__(
        self,
        # target_extractor: Callable,
        layers_client: OvermindLayersClient | None = None,
    ):
        super().__init__(["reject_irrelevant_answer"], layers_client)


class LLMJudgeScorerLayer(GenericOvermindLayer):
    """
    Judge the LLM's response according to a list of criteria. Each criterion should evaluate to true or false.
    """

    def __init__(
        self,
        # target_extractor: Callable,
        criteria: list[str],
        layers_client: OvermindLayersClient | None = None,
    ):
        policies = [
            {
                "policy_template": "reject_llm_judge_with_criteria",
                "parameters": {"criteria": criteria},
            }
        ]
        super().__init__(policies, layers_client)

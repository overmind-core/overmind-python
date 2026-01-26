"""
Integration tests for the Overmind Python client.
"""

from unittest.mock import Mock, patch

import pytest

from overmind import OvermindClient
from overmind.exceptions import (
    OvermindAPIError,
    OvermindAuthenticationError,
    OvermindError,
)
from overmind.models import AgentCreateRequest, PolicyCreateRequest


class TestClientIntegration:
    """Integration tests to verify all client components work together."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = OvermindClient(
            overmind_api_key="test_token",
            base_url="http://test.com",
            openai_api_key="test_openai_key",
        )

    def test_client_has_all_subclients(self):
        """Test that the client has all expected subclients."""
        assert hasattr(self.client, "policies")

    def test_client_has_dynamic_provider_access(self):
        """Test that the client supports dynamic provider access."""
        assert hasattr(self.client, "openai")
        assert self.client.openai is not None

    @patch("requests.Session.request")
    def test_end_to_end_workflow(self, mock_request):
        """Test a complete workflow using all client components."""
        # Mock responses for different operations
        mock_request.side_effect = [
            # Create policy response
            Mock(
                status_code=200,
                json=lambda: {
                    "policy_id": "test_policy",
                    "policy_description": "Test policy",
                    "parameters": {"param1": "value1"},
                    "policy_template": "test_template",
                    "stats": {},
                    "is_input_policy": True,
                    "is_output_policy": False,
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z",
                },
                content=b'{"policy_id": "test_policy"}',
            ),
            # Invoke response
            Mock(
                status_code=200,
                json=lambda: {
                    "llm_client_response": {
                        "choices": [{"message": {"content": "Hello"}}]
                    },
                    "input_layer_results": {},
                    "output_layer_results": {},
                    "processed_input": "test input",
                    "processed_output": "test output",
                    "span_context": {},
                },
                content=b'{"llm_client_response": {"choices": [{"message": {"content": "Hello"}}]}}',
            ),
        ]

        # Create a policy
        policy = self.client.policies.create(
            policy_id="test_policy",
            policy_template="test_template",
            policy_description="Test policy",
            parameters={"param1": "value1"},
            is_input_policy=True,
            is_output_policy=False,
        )
        # Create methods return success response, not the created object
        assert policy is not None

        # Make an invocation
        result = self.client.invoke(
            client_path="openai.chat.completions.create",
            client_call_params={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert result.llm_client_response["choices"][0]["message"]["content"] == "Hello"
        assert result.processed_input == "test input"

        # Verify all expected requests were made
        assert mock_request.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])

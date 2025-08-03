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
        assert hasattr(self.client, "agents")
        assert hasattr(self.client, "policies")
        assert hasattr(self.client, "invocations")

    def test_client_has_dynamic_provider_access(self):
        """Test that the client supports dynamic provider access."""
        assert hasattr(self.client, "openai")
        assert self.client.openai is not None

    @patch("requests.Session.request")
    def test_end_to_end_workflow(self, mock_request):
        """Test a complete workflow using all client components."""
        # Mock responses for different operations
        mock_request.side_effect = [
            # Create agent response
            Mock(
                status_code=200,
                json=lambda: {
                    "agent_id": "test_agent",
                    "agent_model": "gpt-4o",
                    "agent_description": "Test agent",
                    "input_policies": [],
                    "output_policies": [],
                    "stats": {},
                    "parameters": {},
                    "business_id": "test_business",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z",
                },
                content=b'{"agent_id": "test_agent"}',
            ),
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
                    "invocation_id": "test_inv",
                    "agent_id": "test_agent",
                    "raw_input": "test input",
                    "raw_output": "test output",
                    "processed_input": "test input",
                    "processed_output": "test output",
                    "invocation_results": {},
                    "policy_results": {},
                    "llm_client_response": {
                        "choices": [{"message": {"content": "Hello"}}]
                    },
                    "business_id": "test_business",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z",
                },
                content=b'{"invocation_id": "test_inv"}',
            ),
        ]

        # Create an agent
        agent = self.client.agents.create(
            agent_id="test_agent",
            agent_model="gpt-4o",
            agent_description="Test agent",
        )
        # Create methods return success response, not the created object
        assert agent is not None

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
            agent_id="test_agent",
        )
        assert result.invocation_id == "test_inv"
        assert result.agent_id == "test_agent"

        # Verify all expected requests were made
        assert mock_request.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__])

"""
Tests for the InvocationsClient subclient.
"""

from unittest.mock import Mock, patch

import pytest

from overmind_client import OvermindClient


class TestInvocationsClient:
    """Test cases for the InvocationsClient sub-client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = OvermindClient(
            overmind_api_key="test_token",
            base_url="http://test.com",
            openai_api_key="test_openai_key",
        )

    @patch("requests.Session.request")
    def test_list_invocations(self, mock_request):
        """Test listing invocations."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "invocation_id": "inv1",
                "agent_id": "agent1",
                "raw_input": "test input 1",
                "raw_output": "test output 1",
            },
            {
                "invocation_id": "inv2",
                "agent_id": "agent2",
                "raw_input": "test input 2",
                "raw_output": "test output 2",
            },
        ]
        mock_response.content = b'[{"invocation_id": "inv1"}]'
        mock_request.return_value = mock_response

        result = self.client.invocations.list()
        assert len(result) == 2
        assert result[0].invocation_id == "inv1"
        assert result[1].invocation_id == "inv2"

    @patch("requests.Session.request")
    def test_get_invocation(self, mock_request):
        """Test getting a specific invocation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "invocation_id": "test_inv",
            "agent_id": "test_agent",
            "raw_input": "test input",
            "raw_output": "test output",
        }
        mock_response.content = b'{"invocation_id": "test_inv"}'
        mock_request.return_value = mock_response

        result = self.client.invocations.get("test_inv")
        assert result.invocation_id == "test_inv"
        assert result.agent_id == "test_agent"

    @patch("requests.Session.request")
    def test_list_invocations_by_agent(self, mock_request):
        """Test listing invocations filtered by agent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "invocation_id": "inv1",
                "agent_id": "test_agent",
                "raw_input": "test input 1",
                "raw_output": "test output 1",
            },
        ]
        mock_response.content = b'[{"invocation_id": "inv1"}]'
        mock_request.return_value = mock_response

        result = self.client.invocations.list(agent_id="test_agent")
        assert len(result) == 1
        assert result[0].invocation_id == "inv1"
        assert result[0].agent_id == "test_agent"


if __name__ == "__main__":
    pytest.main([__file__])

"""
Tests for the AgentsClient subclient.
"""

from unittest.mock import Mock, patch

import pytest

from overmind_client import OvermindClient


class TestAgentsClient:
    """Test cases for the AgentsClient sub-client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = OvermindClient(
            overmind_api_key="test_token",
            base_url="http://test.com",
            openai_api_key="test_openai_key",
        )

    @patch("requests.Session.request")
    def test_create_agent(self, mock_request):
        """Test creating an agent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "agent_id": "test_agent",
            "agent_model": "gpt-4o",
            "agent_description": "Test agent",
        }
        mock_response.content = b'{"agent_id": "test_agent"}'
        mock_request.return_value = mock_response

        agent_data = {
            "agent_id": "test_agent",
            "agent_model": "gpt-4o",
            "agent_description": "Test agent",
        }

        result = self.client.agents.create(agent_data)
        assert result.agent_id == "test_agent"

    @patch("requests.Session.request")
    def test_list_agents(self, mock_request):
        """Test listing agents."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "agent_id": "agent1",
                "agent_model": "gpt-4o",
                "agent_description": "Agent 1",
            },
            {
                "agent_id": "agent2",
                "agent_model": "gpt-4o",
                "agent_description": "Agent 2",
            },
        ]
        mock_response.content = b'[{"agent_id": "agent1"}]'
        mock_request.return_value = mock_response

        result = self.client.agents.list()
        assert len(result) == 2
        assert result[0].agent_id == "agent1"
        assert result[1].agent_id == "agent2"

    @patch("requests.Session.request")
    def test_get_agent(self, mock_request):
        """Test getting a specific agent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "agent_id": "test_agent",
            "agent_model": "gpt-4o",
            "agent_description": "Test agent",
        }
        mock_response.content = b'{"agent_id": "test_agent"}'
        mock_request.return_value = mock_response

        result = self.client.agents.get("test_agent")
        assert result.agent_id == "test_agent"
        assert result.agent_model == "gpt-4o"

    @patch("requests.Session.request")
    def test_delete_agent(self, mock_request):
        """Test deleting an agent."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_request.return_value = mock_response

        # Should not raise an exception
        self.client.agents.delete("test_agent")


if __name__ == "__main__":
    pytest.main([__file__])

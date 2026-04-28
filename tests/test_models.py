"""
Tests for Pydantic models.
"""

import pytest

from overmind.models import AgentCreateRequest


class TestModels:
    """Test cases for Pydantic models."""

    def test_agent_create_request(self):
        """Test AgentCreateRequest model."""
        agent_data = {
            "agent_id": "test_agent",
            "agent_model": "gpt-5-mini",
            "agent_description": "Test agent",
        }

        agent = AgentCreateRequest(**agent_data)
        assert agent.agent_id == "test_agent"
        assert agent.agent_model == "gpt-5-mini"
        assert agent.agent_description == "Test agent"


if __name__ == "__main__":
    pytest.main([__file__])

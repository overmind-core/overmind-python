"""
Tests for Pydantic models.
"""

import pytest

from overmind.models import AgentCreateRequest, PolicyCreateRequest


class TestModels:
    """Test cases for Pydantic models."""

    def test_agent_create_request(self):
        """Test AgentCreateRequest model."""
        agent_data = {
            "agent_id": "test_agent",
            "agent_model": "gpt-4o",
            "agent_description": "Test agent",
        }

        agent = AgentCreateRequest(**agent_data)
        assert agent.agent_id == "test_agent"
        assert agent.agent_model == "gpt-4o"
        assert agent.agent_description == "Test agent"
        assert agent.input_policies == []
        assert agent.output_policies == []

    def test_agent_create_request_with_policies(self):
        """Test AgentCreateRequest model with policies."""
        agent_data = {
            "agent_id": "test_agent",
            "agent_model": "gpt-4o",
            "agent_description": "Test agent",
            "input_policies": ["policy1", "policy2"],
            "output_policies": ["policy3"],
        }

        agent = AgentCreateRequest(**agent_data)
        assert agent.agent_id == "test_agent"
        assert agent.input_policies == ["policy1", "policy2"]
        assert agent.output_policies == ["policy3"]

    def test_policy_create_request(self):
        """Test PolicyCreateRequest model."""
        policy_data = {
            "policy_id": "test_policy",
            "policy_description": "Test policy",
            "parameters": {"param1": "value1"},
            "policy_template": "test_template",
            "is_input_policy": True,
            "is_output_policy": False,
        }

        policy = PolicyCreateRequest(**policy_data)
        assert policy.policy_id == "test_policy"
        assert policy.policy_description == "Test policy"
        assert policy.parameters == {"param1": "value1"}
        assert policy.policy_template == "test_template"
        assert policy.is_input_policy is True
        assert policy.is_output_policy is False

    def test_policy_create_request_validation(self):
        """Test PolicyCreateRequest validation."""
        # Test that at least one of is_input_policy or is_output_policy must be True
        with pytest.raises(ValueError):
            PolicyCreateRequest(
                policy_id="test_policy",
                policy_description="Test policy",
                parameters={},
                policy_template="test_template",
                is_input_policy=False,
                is_output_policy=False,
            )

        # Test that both can be True
        policy = PolicyCreateRequest(
            policy_id="test_policy",
            policy_description="Test policy",
            parameters={},
            policy_template="test_template",
            is_input_policy=True,
            is_output_policy=True,
        )
        assert policy.is_input_policy is True
        assert policy.is_output_policy is True


if __name__ == "__main__":
    pytest.main([__file__])

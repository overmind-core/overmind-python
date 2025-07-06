"""
Shared pytest fixtures and configuration.
"""

import pytest
from unittest.mock import Mock

from overmind_client import OvermindClient


@pytest.fixture
def overmind_client():
    """Create a test OvermindClient instance."""
    return OvermindClient(
        overmind_api_key="test_token",
        base_url="http://test.com",
        openai_api_key="test_openai_key",
    )


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.status_code = 200
    response.content = b'{"status": "success"}'
    response.json.return_value = {"status": "success"}
    return response


@pytest.fixture
def mock_agent_response():
    """Create a mock response for agent operations."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "agent_id": "test_agent",
        "agent_model": "gpt-4o",
        "agent_description": "Test agent",
    }
    response.content = b'{"agent_id": "test_agent"}'
    return response


@pytest.fixture
def mock_policy_response():
    """Create a mock response for policy operations."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "policy_id": "test_policy",
        "policy_description": "Test policy",
        "parameters": {"param1": "value1"},
        "engine": "test_engine",
        "is_input_policy": True,
        "is_output_policy": False,
    }
    response.content = b'{"policy_id": "test_policy"}'
    return response


@pytest.fixture
def mock_invocation_response():
    """Create a mock response for invocation operations."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "invocation_id": "test_inv",
        "agent_id": "test_agent",
        "raw_input": "test input",
        "raw_output": "test output",
    }
    response.content = b'{"invocation_id": "test_inv"}'
    return response

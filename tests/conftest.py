"""
Shared pytest fixtures and configuration.
"""

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.status_code = 200
    response.content = b'{"status": "success"}'
    response.json.return_value = {"status": "success"}
    return response

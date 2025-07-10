"""
Tests for the PoliciesClient subclient.
"""

from unittest.mock import Mock, patch

import pytest

from overmind import OvermindClient


class TestPoliciesClient:
    """Test cases for the PoliciesClient sub-client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = OvermindClient(
            overmind_api_key="test_token",
            base_url="http://test.com",
            openai_api_key="test_openai_key",
        )

    @patch("requests.Session.request")
    def test_create_policy(self, mock_request):
        """Test creating a policy."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "policy_id": "test_policy",
            "policy_description": "Test policy",
            "parameters": {"param1": "value1"},
            "policy_template": "test_template",
            "stats": {},
            "is_input_policy": True,
            "is_output_policy": False,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        mock_response.content = b'{"policy_id": "test_policy"}'
        mock_request.return_value = mock_response

        # Create policy using the correct API signature
        result = self.client.policies.create(
            policy_id="test_policy",
            policy_template="test_template",
            policy_description="Test policy",
            parameters={"param1": "value1"},
            is_input_policy=True,
            is_output_policy=False,
        )
        # Create methods return success response, not the created object
        assert result is not None

    @patch("requests.Session.request")
    def test_list_policies(self, mock_request):
        """Test listing policies."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "policy_id": "policy1",
                "policy_description": "Policy 1",
                "parameters": {},
                "policy_template": "test_template",
                "stats": {},
                "is_input_policy": True,
                "is_output_policy": False,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            },
            {
                "policy_id": "policy2",
                "policy_description": "Policy 2",
                "parameters": {},
                "policy_template": "test_template",
                "stats": {},
                "is_input_policy": False,
                "is_output_policy": True,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            },
        ]
        mock_response.content = b'[{"policy_id": "policy1"}]'
        mock_request.return_value = mock_response

        result = self.client.policies.list()
        assert len(result) == 2
        assert result[0].policy_id == "policy1"
        assert result[1].policy_id == "policy2"

    @patch("requests.Session.request")
    def test_get_policy(self, mock_request):
        """Test getting a specific policy."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "policy_id": "test_policy",
            "policy_description": "Test policy",
            "parameters": {"param1": "value1"},
            "policy_template": "test_template",
            "stats": {},
            "is_input_policy": True,
            "is_output_policy": False,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        mock_response.content = b'{"policy_id": "test_policy"}'
        mock_request.return_value = mock_response

        result = self.client.policies.get("test_policy")
        assert result.policy_id == "test_policy"
        assert result.policy_description == "Test policy"

    @patch("requests.Session.request")
    def test_delete_policy(self, mock_request):
        """Test deleting a policy."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_request.return_value = mock_response

        # Should not raise an exception
        self.client.policies.delete("test_policy")


if __name__ == "__main__":
    pytest.main([__file__])

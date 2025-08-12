"""
Tests for the main OvermindClient class.
"""

import os
from unittest.mock import Mock, patch

import pytest

from overmind import OvermindClient
from overmind.exceptions import (
    OvermindAPIError,
    OvermindAuthenticationError,
    OvermindError,
)


class TestOvermindClient:
    """Test cases for the OvermindClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = OvermindClient(
            overmind_api_key="test_token",
            base_url="http://test.com",
            openai_api_key="test_openai_key",
        )

    def test_client_initialization(self):
        """Test client initialization."""
        assert self.client.overmind_api_key == "test_token"
        assert self.client.base_url == "http://test.com"
        assert self.client.provider_parameters == {"openai_api_key": "test_openai_key"}
        assert "Authorization" in self.client.session.headers
        assert "Content-Type" in self.client.session.headers

        # Test sub-clients are initialized
        assert hasattr(self.client, "agents")
        assert hasattr(self.client, "policies")

    def test_dynamic_provider_access(self):
        """Test dynamic provider access."""
        # Test that we can access a provider
        openai_proxy = self.client.openai
        assert openai_proxy is not None
        assert openai_proxy.path_parts == ["openai"]

    def test_provider_method_chaining(self):
        """Test provider method chaining."""
        # Test that we can chain method calls
        proxy = self.client.openai.chat.completions
        assert proxy.path_parts == ["openai", "chat", "completions"]

    @patch("requests.Session.request")
    def test_provider_invocation(self, mock_request):
        """Test provider invocation through dynamic access."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "llm_client_response": {"choices": [{"message": {"content": "Hello"}}]},
            "input_layer_results": {},
            "output_layer_results": {},
            "processed_input": "test input",
            "processed_output": "test output",
        }
        mock_response.content = (
            b'{"llm_client_response": {"choices": [{"message": {"content": "Hello"}}]}}'
        )
        mock_request.return_value = mock_response

        # Call the provider through dynamic access
        result = self.client.openai.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": "Hello"}]
        )

        # Verify the request was made with correct parameters
        call_args = mock_request.call_args
        request_data = call_args[1]["json"]
        assert request_data["agent_id"] == "default_agent"
        # client_call_params is serialized to JSON string
        import json

        client_call_params = json.loads(request_data["client_call_params"])
        assert client_call_params["model"] == "gpt-4o"
        assert request_data["client_init_params"]["openai_api_key"] == "test_openai_key"

    @patch("requests.Session.request")
    def test_successful_api_request(self, mock_request):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.content = b'{"status": "success"}'
        mock_request.return_value = mock_response

        result = self.client._make_request("GET", "test/endpoint")
        assert result == {"status": "success"}

    @patch("requests.Session.request")
    def test_authentication_error(self, mock_request):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.content = b'{"detail": "Invalid token"}'
        mock_request.return_value = mock_response

        with pytest.raises(OvermindAuthenticationError):
            self.client._make_request("GET", "test/endpoint")

    @patch("requests.Session.request")
    def test_api_error(self, mock_request):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Bad request"}
        mock_response.content = b'{"detail": "Bad request"}'
        mock_request.return_value = mock_response

        with pytest.raises(OvermindAPIError) as exc_info:
            self.client._make_request("GET", "test/endpoint")

        assert exc_info.value.status_code == 400
        assert "Bad request" in str(exc_info.value)

    @patch("requests.Session.request")
    def test_invoke_method(self, mock_request):
        """Test invoke method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "llm_client_response": {"choices": [{"message": {"content": "Hello"}}]},
            "input_layer_results": {},
            "output_layer_results": {},
            "processed_input": "test input",
            "processed_output": "test output",
        }
        mock_response.content = (
            b'{"llm_client_response": {"choices": [{"message": {"content": "Hello"}}]}}'
        )
        mock_request.return_value = mock_response

        result = self.client.invoke(
            client_path="openai.chat.completions.create",
            client_call_params={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Hello"}],
            },
            agent_id="test_agent",
        )

        assert result.llm_client_response["choices"][0]["message"]["content"] == "Hello"
        assert result.processed_input == "test input"

    @patch("requests.Session.request")
    def test_invoke_method_with_custom_init_params(self, mock_request):
        """Test invoke method with custom client_init_params."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "llm_client_response": {"choices": [{"message": {"content": "Hello"}}]},
            "input_layer_results": {},
            "output_layer_results": {},
            "processed_input": "test input",
            "processed_output": "test output",
        }
        mock_response.content = (
            b'{"llm_client_response": {"choices": [{"message": {"content": "Hello"}}]}}'
        )
        mock_request.return_value = mock_response

        custom_init_params = {"api_key": "custom_key"}
        result = self.client.invoke(
            client_path="openai.chat.completions.create",
            client_call_params={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Hello"}],
            },
            agent_id="test_agent",
            client_init_params=custom_init_params,
        )

        # Verify the request was made with custom init params
        call_args = mock_request.call_args
        request_data = call_args[1]["json"]
        assert request_data["client_init_params"] == custom_init_params

    @patch.dict(os.environ, {"OVERMIND_API_KEY": "env_test_token"})
    def test_client_initialization_with_env_var(self):
        """Test client initialization using environment variable."""
        client = OvermindClient(
            base_url="http://test.com",
            openai_api_key="test_openai_key",
        )
        assert client.overmind_api_key == "env_test_token"

    def test_client_initialization_no_api_key(self):
        """Test client initialization without API key raises error."""
        with pytest.raises(OvermindError) as exc_info:
            OvermindClient(
                base_url="http://test.com",
                openai_api_key="test_openai_key",
            )
        assert "No Overmind API key provided" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])

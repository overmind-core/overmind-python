"""
Main Overmind client implementation.
"""

import os
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests

from .exceptions import OvermindAPIError, OvermindAuthenticationError, OvermindError
from .models import InvocationResponse
from .agents import AgentsClient
from .policies import PoliciesClient
from .invocations import InvocationsClient


# Mapping of common environment variables to provider parameter names
COMMON_ENV_VARS = {
    "OPENAI_API_KEY": "api_key",
}


class ClientPathProxy:
    """
    Proxy object that enables dynamic method chaining for client paths.

    This allows for syntax like: client.openai.chat.completions.create(...)
    """

    def __init__(self, client, path_parts: List[str]):
        self.client = client
        self.path_parts = path_parts

    def __getattr__(self, name: str):
        """Add the attribute name to the path and return self for chaining."""
        return ClientPathProxy(self.client, self.path_parts + [name])

    def __call__(self, *args, **kwargs):
        """
        When called, construct the full path and invoke the provider.

        Args:
            *args: Positional arguments (not used in this implementation)
            **kwargs: Keyword arguments for the provider call

        Returns:
            The result from the provider invocation
        """
        if not self.path_parts:
            raise OvermindError("No method path specified")

        # Construct the full client path
        client_path = ".".join(self.path_parts)

        input_policies = kwargs.pop("input_policies", None)
        output_policies = kwargs.pop("output_policies", None)
        agent_id = kwargs.pop("agent_id", "default_agent")

        # Invoke the provider through the Overmind API
        return self.client.invoke(
            client_path=client_path,
            client_call_params=kwargs,
            input_policies=input_policies,
            output_policies=output_policies,
            agent_id=agent_id,
        )


class OvermindClient:
    """
    Main client for interacting with the Overmind API.

    This client provides:
    - Dynamic provider access (e.g., client.openai.chat.completions.create)
    - Agent management via client.agents.{methods}
    - Policy management via client.policies.{methods}
    - Invocation management via client.invocations.{methods}
    """

    def __init__(
        self,
        overmind_api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **provider_parameters: Dict[str, Any],
    ):
        """
        Initialize the Overmind client.

        Args:
            overmind_api_key: Your Overmind API key for authentication. If not provided,
                             will try to use OVERMIND_API_KEY environment variable.
            base_url: Base URL of the Overmind API server
            **provider_parameters: Provider-specific credentials (e.g., openai_api_key)

        Raises:
            OvermindError: If no API key is provided and OVERMIND_API_KEY environment variable is not set
        """
        # Get API key from parameter or environment variable
        if overmind_api_key is None:
            overmind_api_key = os.getenv("OVERMIND_API_KEY")
            if overmind_api_key is None:
                raise OvermindError(
                    "No Overmind API key provided. Either pass 'overmind_api_key' parameter "
                    "or set OVERMIND_API_KEY environment variable."
                )

        if base_url is None:
            base_url = os.getenv("OVERMIND_API_URL")
            if base_url is None:
                base_url = (
                    "https://api.evallab.dev"
                )

        self.overmind_api_key = overmind_api_key
        self.base_url = base_url.rstrip("/")

        # Start with provided provider parameters
        self.provider_parameters = (
            provider_parameters.copy() if provider_parameters else {}
        )

        # Add common environment variables if they exist and aren't already in provider_parameters
        for env_var, param_name in COMMON_ENV_VARS.items():
            env_value = os.getenv(env_var)
            if env_value and param_name not in self.provider_parameters:
                self.provider_parameters[param_name] = env_value

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {overmind_api_key}",
                "Content-Type": "application/json",
            }
        )

        # Initialize sub-clients
        self.agents = AgentsClient(self)
        self.policies = PoliciesClient(self)
        self.invocations = InvocationsClient(self)

        # Cache for provider proxies
        self._provider_proxies = {}

    def __getattr__(self, name: str):
        """Enable dynamic provider access (e.g., client.openai)."""
        if name in self._provider_proxies:
            return self._provider_proxies[name]

        # Create a new proxy for this provider
        proxy = ClientPathProxy(self, [name])
        self._provider_proxies[name] = proxy
        return proxy

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Overmind API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            OvermindAuthenticationError: If authentication fails
            OvermindAPIError: If the API returns an error
        """
        url = urljoin(f"{self.base_url}/api/v1/", endpoint)

        try:
            response = self.session.request(
                method=method, url=url, json=data, params=params
            )

            if response.status_code == 401:
                raise OvermindAuthenticationError("Invalid Overmind API key")

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise OvermindAPIError(
                    message=error_data.get("detail", f"HTTP {response.status_code}"),
                    status_code=response.status_code,
                    response_data=error_data,
                )

            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            raise OvermindError(f"Request failed: {str(e)}")

    def invoke(
        self,
        client_path: str,
        client_call_params: Dict[str, Any],
        agent_id: str = "default_agent",
        client_init_params: Optional[Dict[str, Any]] = None,
        input_policies: Optional[List[str]] = None,
        output_policies: Optional[List[str]] = None,
    ) -> InvocationResponse:
        """
        Invoke an AI provider through the Overmind API.

        Args:
            client_path: Provider path (e.g., "openai.chat.completions.create")
            client_call_params: Parameters for the provider call
            agent_id: Agent ID to use for the invocation
            client_init_params: Parameters for provider client initialization (overrides stored parameters)
            input_policies: Input policies to apply
            output_policies: Output policies to apply

        Returns:
            InvocationResponse object
        """
        # Use provided client_init_params or fall back to stored provider_parameters
        init_params = client_init_params or self.provider_parameters

        payload = {
            "agent_id": agent_id,
            "client_call_params": client_call_params,
            "client_init_params": init_params,
            "input_policies": input_policies,
            "output_policies": output_policies,
        }

        response_data = self._make_request(
            "POST", f"invocations/invoke/{client_path}", data=payload
        )

        return InvocationResponse(**response_data)

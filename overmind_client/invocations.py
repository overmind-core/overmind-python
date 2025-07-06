"""
Invocations sub-client for Overmind API.
"""

from typing import Dict, List

from .models import InvocationResponse


class InvocationsClient:
    """
    Sub-client for managing invocations in the Overmind API.
    """

    def __init__(self, parent_client):
        self._client = parent_client

    def list(self, agent_id: str) -> List[InvocationResponse]:
        """List all invocations for a specific agent."""
        response_data = self._client._make_request(
            "GET", f"invocations/list/{agent_id}"
        )
        return [InvocationResponse(**invocation) for invocation in response_data]

    def get(self, invocation_id: str) -> InvocationResponse:
        """Get a specific invocation by ID."""
        response_data = self._client._make_request(
            "GET", f"invocations/view/{invocation_id}"
        )
        return InvocationResponse(**response_data)

    def delete(self, invocation_id: str) -> Dict[str, str]:
        """Delete an invocation by ID."""
        return self._client._make_request("GET", f"invocations/delete/{invocation_id}")

"""
Policies sub-client for Overmind API.
"""

from typing import Any, Dict, List, Optional, Union

from .models import PolicyCreateRequest, PolicyResponse, PolicyUpdateRequest


class PoliciesClient:
    """
    Sub-client for managing policies in the Overmind API.
    """

    def __init__(self, parent_client):
        self._client = parent_client

    def create(
        self, policy_data: Union[PolicyCreateRequest, Dict[str, Any]]
    ) -> PolicyResponse:
        """Create a new policy."""
        if isinstance(policy_data, dict):
            policy_data = PolicyCreateRequest(**policy_data)

        response_data = self._client._make_request(
            "PUT", "policies/add_policy", data=policy_data.model_dump()
        )
        return PolicyResponse(**response_data)

    def list(self, policy_type: Optional[str] = None) -> List[PolicyResponse]:
        """List all policies with optional filtering by type."""
        params = {"policy_type": policy_type} if policy_type else None
        response_data = self._client._make_request(
            "GET", "policies/list_policies", params=params
        )
        return [PolicyResponse(**policy) for policy in response_data]

    def get(self, policy_id: str) -> PolicyResponse:
        """Get a specific policy by ID."""
        response_data = self._client._make_request("GET", f"policies/view/{policy_id}")
        return PolicyResponse(**response_data)

    def update(
        self, policy_data: Union[PolicyUpdateRequest, Dict[str, Any]]
    ) -> Dict[str, str]:
        """Update an existing policy."""
        if isinstance(policy_data, dict):
            policy_data = PolicyUpdateRequest(**policy_data)

        return self._client._make_request(
            "POST", "policies/edit_policy", data=policy_data.model_dump()
        )

    def delete(self, policy_id: str) -> Dict[str, str]:
        """Delete a policy by ID."""
        return self._client._make_request("GET", f"policies/delete/{policy_id}")

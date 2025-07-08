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
        self,
        policy_id: str,
        policy_template: str,
        policy_description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        is_input_policy: Optional[bool] = True,
        is_output_policy: Optional[bool] = True,
        stats: Optional[Dict[str, Any]] = None,
        *,
        policy_data: Optional[Union[PolicyCreateRequest, Dict[str, Any]]] = None,
    ) -> PolicyResponse:
        """
        Create a new policy.
        
        Args:
            policy_id: Unique identifier for the policy
            policy_description: Description of the policy
            parameters: Policy parameters
            policy_template: Policy template to use
            is_input_policy: Whether this is an input policy
            is_output_policy: Whether this is an output policy
            stats: Policy statistics
            policy_data: Alternative: pass a complete PolicyCreateRequest or dict (for backward compatibility)
        """
        if policy_data is not None:
            if isinstance(policy_data, dict):
                policy_data = PolicyCreateRequest(**policy_data)
            elif isinstance(policy_data, PolicyCreateRequest):
                pass
            else:
                raise TypeError("policy_data must be a dict or PolicyCreateRequest")
        else:
            policy_data = PolicyCreateRequest(
                policy_id=policy_id,
                policy_description=policy_description,
                parameters=parameters,
                policy_template=policy_template,
                is_input_policy=is_input_policy,
                is_output_policy=is_output_policy,
                stats=stats or {},
            )

        response_data = self._client._make_request(
            "PUT", "policies/add_policy", data=policy_data.model_dump()
        )
        return response_data

    def list(self, policy_type: Optional[str] = None) -> List[PolicyResponse]:
        """
        List all policies with optional filtering by type.
        
        Args:
            policy_type: Optional filter to show only input or output policies
        """
        params = {"policy_type": policy_type} if policy_type else None
        response_data = self._client._make_request(
            "GET", "policies/list_policies", params=params
        )
        return [PolicyResponse(**policy) for policy in response_data]

    def get(self, policy_id: str) -> PolicyResponse:
        """
        Get a specific policy by ID.
        
        Args:
            policy_id: The unique identifier of the policy to retrieve
        """
        response_data = self._client._make_request("GET", f"policies/view/{policy_id}")
        return PolicyResponse(**response_data)

    def update(
        self,
        policy_id: str,
        policy_template: str,
        policy_description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        is_input_policy: Optional[bool] = None,
        is_output_policy: Optional[bool] = None,
        stats: Optional[Dict[str, Any]] = None,
        *,
        policy_data: Optional[Union[PolicyUpdateRequest, Dict[str, Any]]] = None,
    ) -> Dict[str, str]:
        """
        Update an existing policy.
        
        Args:
            policy_id: Unique identifier for the policy
            policy_description: Description of the policy
            parameters: Policy parameters
            engine: Policy engine
            is_input_policy: Whether this is an input policy
            is_output_policy: Whether this is an output policy
            stats: Policy statistics
            policy_data: Alternative: pass a complete PolicyUpdateRequest or dict (for backward compatibility)
        """
        if policy_data is not None:
            if isinstance(policy_data, dict):
                policy_data = PolicyUpdateRequest(**policy_data)
            elif isinstance(policy_data, PolicyUpdateRequest):
                pass
            else:
                raise TypeError("policy_data must be a dict or PolicyUpdateRequest")
        else:
            policy_data = PolicyUpdateRequest(
                policy_id=policy_id,
                policy_description=policy_description,
                parameters=parameters,
                policy_template=policy_template,
                is_input_policy=is_input_policy,
                is_output_policy=is_output_policy,
                stats=stats,
            )

        return self._client._make_request(
            "POST", "policies/edit_policy", data=policy_data.model_dump()
        )

    def delete(self, policy_id: str) -> Dict[str, str]:
        """
        Delete a policy by ID.
        
        Args:
            policy_id: The unique identifier of the policy to delete
        """
        return self._client._make_request("GET", f"policies/delete/{policy_id}")

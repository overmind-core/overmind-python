"""
Agents sub-client for Overmind API.
"""

from typing import Any, Dict, List, Union

from .models import AgentCreateRequest, AgentResponse, AgentUpdateRequest


class AgentsClient:
    """
    Sub-client for managing agents in the Overmind API.
    """

    def __init__(self, parent_client):
        self._client = parent_client

    def create(
        self, agent_data: Union[AgentCreateRequest, Dict[str, Any]]
    ) -> AgentResponse:
        """Create a new agent."""
        if isinstance(agent_data, dict):
            agent_data = AgentCreateRequest(**agent_data)

        response_data = self._client._make_request(
            "POST", "agents/create", data=agent_data.model_dump()
        )
        return AgentResponse(**response_data)

    def list(self) -> List[AgentResponse]:
        """List all agents for the current business."""
        response_data = self._client._make_request("GET", "agents/list_agents")
        return [AgentResponse(**agent) for agent in response_data]

    def get(self, agent_id: str) -> AgentResponse:
        """Get a specific agent by ID."""
        response_data = self._client._make_request("GET", f"agents/view/{agent_id}")
        return AgentResponse(**response_data)

    def update(
        self, agent_data: Union[AgentUpdateRequest, Dict[str, Any]]
    ) -> Dict[str, str]:
        """Update an existing agent."""
        if isinstance(agent_data, dict):
            agent_data = AgentUpdateRequest(**agent_data)

        return self._client._make_request(
            "POST", "agents/edit_agent", data=agent_data.model_dump()
        )

    def delete(self, agent_id: str) -> Dict[str, str]:
        """Delete an agent by ID."""
        return self._client._make_request("GET", f"agents/delete/{agent_id}")

"""
Agents sub-client for Overmind API.
"""

from typing import Any, Dict, List, Optional, Union

from .models import AgentCreateRequest, AgentResponse, AgentUpdateRequest


class AgentsClient:
    """
    Sub-client for managing agents in the Overmind API.
    """

    def __init__(self, parent_client):
        self._client = parent_client

    def create(
        self,
        agent_id: str,
        agent_model: Optional[str] = None,
        agent_description: Optional[str] = None,
        input_policies: Optional[List[str]] = None,
        output_policies: Optional[List[str]] = None,
        stats: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        *,
        agent_data: Optional[Union[AgentCreateRequest, Dict[str, Any]]] = None,
    ) -> Dict[str, str]:
        """
        Create a new agent.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_model: The AI model to use (e.g., 'gpt-4o')
            agent_description: Description of the agent
            input_policies: List of input policy IDs
            output_policies: List of output policy IDs
            stats: Agent statistics
            parameters: Agent parameters
            agent_data: Alternative: pass a complete AgentCreateRequest or dict (for backward compatibility)
        """
        if agent_data is not None:
            if isinstance(agent_data, dict):
                agent_data = AgentCreateRequest(**agent_data)
            elif isinstance(agent_data, AgentCreateRequest):
                pass
            else:
                raise TypeError("agent_data must be a dict or AgentCreateRequest")
        else:
            agent_data = AgentCreateRequest(
                agent_id=agent_id,
                agent_model=agent_model,
                agent_description=agent_description,
                input_policies=input_policies or [],
                output_policies=output_policies or [],
                stats=stats or {},
                parameters=parameters or {},
            )

        response_data = self._client._make_request(
            "POST", "agents/create", data=agent_data.model_dump()
        )
        return response_data

    def list(self) -> List[AgentResponse]:
        """List all agents for the current business."""
        response_data = self._client._make_request("GET", "agents/list_agents")
        return [AgentResponse(**agent) for agent in response_data]

    def get(self, agent_id: str) -> AgentResponse:
        """
        Get a specific agent by ID.
        
        Args:
            agent_id: The unique identifier of the agent to retrieve
        """
        response_data = self._client._make_request("GET", f"agents/view/{agent_id}")
        return AgentResponse(**response_data)

    def update(
        self,
        agent_id: str,
        agent_model: Optional[str] = None,
        agent_description: Optional[str] = None,
        input_policies: Optional[List[str]] = None,
        output_policies: Optional[List[str]] = None,
        stats: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        *,
        agent_data: Optional[Union[AgentUpdateRequest, Dict[str, Any]]] = None,
    ) -> Dict[str, str]:
        """
        Update an existing agent.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_model: The AI model to use (e.g., 'gpt-4o')
            agent_description: Description of the agent
            input_policies: List of input policy IDs
            output_policies: List of output policy IDs
            stats: Agent statistics
            parameters: Agent parameters
            agent_data: Alternative: pass a complete AgentUpdateRequest or dict (for backward compatibility)
        """
        if agent_data is not None:
            if isinstance(agent_data, dict):
                agent_data = AgentUpdateRequest(**agent_data)
            elif isinstance(agent_data, AgentUpdateRequest):
                pass
            else:
                raise TypeError("agent_data must be a dict or AgentUpdateRequest")
        else:
            agent_data = AgentUpdateRequest(
                agent_id=agent_id,
                agent_model=agent_model,
                agent_description=agent_description,
                input_policies=input_policies,
                output_policies=output_policies,
                stats=stats,
                parameters=parameters,
            )

        return self._client._make_request(
            "POST", "agents/edit_agent", data=agent_data.model_dump()
        )

    def delete(self, agent_id: str) -> Dict[str, str]:
        """
        Delete an agent by ID.
        
        Args:
            agent_id: The unique identifier of the agent to delete
        """
        return self._client._make_request("GET", f"agents/delete/{agent_id}")

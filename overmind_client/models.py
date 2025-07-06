"""
Pydantic models for the Overmind client.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentCreateRequest(BaseModel):
    """Model for creating a new agent."""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_model: str = Field(..., description="The AI model to use (e.g., 'gpt-4o')")
    agent_description: str = Field(..., description="Description of the agent")
    input_policies: Optional[List[str]] = Field(
        default=[], description="List of input policy IDs"
    )
    output_policies: Optional[List[str]] = Field(
        default=[], description="List of output policy IDs"
    )
    stats: Optional[Dict[str, Any]] = Field(default={}, description="Agent statistics")
    parameters: Optional[Dict[str, Any]] = Field(
        default={}, description="Agent parameters"
    )


class AgentUpdateRequest(BaseModel):
    """Model for updating an existing agent."""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_model: Optional[str] = Field(None, description="The AI model to use")
    agent_description: Optional[str] = Field(
        None, description="Description of the agent"
    )
    input_policies: Optional[List[str]] = Field(
        None, description="List of input policy IDs"
    )
    output_policies: Optional[List[str]] = Field(
        None, description="List of output policy IDs"
    )
    stats: Optional[Dict[str, Any]] = Field(None, description="Agent statistics")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Agent parameters")


class AgentResponse(BaseModel):
    """Model for agent response data."""

    agent_id: str
    agent_model: str
    agent_description: str
    input_policies: List[str]
    output_policies: List[str]
    stats: Dict[str, Any]
    parameters: Dict[str, Any]
    business_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class PolicyCreateRequest(BaseModel):
    """Model for creating a new policy."""

    policy_id: str = Field(..., description="Unique identifier for the policy")
    policy_description: str = Field(..., description="Description of the policy")
    parameters: Dict[str, Any] = Field(..., description="Policy parameters")
    engine: str = Field(..., description="Policy engine")
    is_input_policy: bool = Field(..., description="Whether this is an input policy")
    is_output_policy: bool = Field(..., description="Whether this is an output policy")
    stats: Optional[Dict[str, Any]] = Field(default={}, description="Policy statistics")


class PolicyUpdateRequest(BaseModel):
    """Model for updating an existing policy."""

    policy_id: str = Field(..., description="Unique identifier for the policy")
    policy_description: Optional[str] = Field(
        None, description="Description of the policy"
    )
    parameters: Optional[Dict[str, Any]] = Field(None, description="Policy parameters")
    engine: Optional[str] = Field(None, description="Policy engine")
    is_input_policy: Optional[bool] = Field(
        None, description="Whether this is an input policy"
    )
    is_output_policy: Optional[bool] = Field(
        None, description="Whether this is an output policy"
    )
    stats: Optional[Dict[str, Any]] = Field(None, description="Policy statistics")


class PolicyResponse(BaseModel):
    """Model for policy response data."""

    policy_id: str
    policy_description: str
    parameters: Dict[str, Any]
    engine: str
    stats: Dict[str, Any]
    is_input_policy: bool
    is_output_policy: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_built_in: Optional[bool] = False


class InvocationResponse(BaseModel):
    """Model for invocation response data."""

    invocation_id: str
    agent_id: str
    raw_input: str
    processed_input: Optional[str]
    raw_output: Optional[str]
    processed_output: Optional[str]
    invocation_results: Dict[str, Any]
    policy_results: Dict[str, Any]
    business_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class InvokeRequest(BaseModel):
    """Model for invoke request payload."""

    agent_id: str = Field(default="default_agent", description="Agent ID to use")
    client_call_params: Dict[str, Any] = Field(
        ..., description="Parameters for the client call"
    )
    client_init_params: Optional[Dict[str, Any]] = Field(
        default={}, description="Parameters for client initialization"
    )
    input_policies: Optional[List[str]] = Field(
        default=None, description="Input policies to apply"
    )
    output_policies: Optional[List[str]] = Field(
        default=None, description="Output policies to apply"
    )

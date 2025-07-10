"""
Pydantic models for the Overmind client.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import pprint
from pydantic import BaseModel, Field, field_validator, model_validator
from .formatters import summarise_invocation
from rich.console import Console
from rich.pretty import Pretty
import io


class ReadableBaseModel(BaseModel):
    """Base model with a readable __repr__ method for better display in Jupyter notebooks."""

    def __repr__(self) -> str:
        """
        Generate a rich-formatted string representation for the terminal.

        This is called by the Python REPL when you inspect an object.
        """
        # Create a Rich Console that captures output to a string
        string_buffer = io.StringIO()
        console = Console(file=string_buffer, force_terminal=True)
        console.print(self)
        return string_buffer.getvalue()


class AgentCreateRequest(ReadableBaseModel):
    """Model for creating a new agent."""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_model: Optional[str] = Field(None, description="The AI model to use (e.g., 'gpt-4o')")
    agent_description: Optional[str] = Field(None, description="Description of the agent")
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


class AgentUpdateRequest(ReadableBaseModel):
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


class AgentResponse(ReadableBaseModel):
    """Model for agent response data."""

    agent_id: str
    agent_model: Optional[str]
    agent_description: Optional[str]
    input_policies: Optional[List[str]]
    output_policies: Optional[List[str]]
    stats: Optional[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]]
    business_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class PolicyCreateRequest(ReadableBaseModel):
    """Model for creating a new policy."""

    policy_id: str = Field(..., description="Unique identifier for the policy")
    policy_description: str = Field(..., description="Description of the policy")
    parameters: Dict[str, Any] = Field(..., description="Policy parameters")
    policy_template: str = Field(..., description="Policy template")
    is_input_policy: bool = Field(..., description="Whether this is an input policy")
    is_output_policy: bool = Field(..., description="Whether this is an output policy")
    stats: Optional[Dict[str, Any]] = Field(default={}, description="Policy statistics")

    @model_validator(mode="after")
    def validate_policy_type(self):
        """Ensure at least one of is_input_policy or is_output_policy is True."""
        if not self.is_input_policy and not self.is_output_policy:
            raise ValueError(
                "At least one of is_input_policy or is_output_policy must be True"
            )
        return self


class PolicyUpdateRequest(ReadableBaseModel):
    """Model for updating an existing policy."""

    policy_id: str = Field(..., description="Unique identifier for the policy")
    policy_description: Optional[str] = Field(
        None, description="Description of the policy"
    )
    parameters: Optional[Dict[str, Any]] = Field(None, description="Policy parameters")
    policy_template: Optional[str] = Field(None, description="Policy template")
    is_input_policy: Optional[bool] = Field(
        None, description="Whether this is an input policy"
    )
    is_output_policy: Optional[bool] = Field(
        None, description="Whether this is an output policy"
    )
    stats: Optional[Dict[str, Any]] = Field(None, description="Policy statistics")


class PolicyResponse(ReadableBaseModel):
    """Model for policy response data."""

    policy_id: str
    policy_description: str
    parameters: Dict[str, Any]
    policy_template: str
    stats: Dict[str, Any]
    is_input_policy: bool
    is_output_policy: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_built_in: Optional[bool] = False


class InvocationResponse(ReadableBaseModel):
    """Model for invocation response data."""

    invocation_id: str
    agent_id: str
    raw_input: str
    processed_input: Optional[str]
    raw_output: Optional[str]
    processed_output: Optional[str]
    invocation_results: Dict[str, Any]
    policy_results: Dict[str, Any]
    llm_client_response: Optional[Dict[str, Any]]
    business_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    def summary(self) -> None:
        summarise_invocation(self)


class InvokeRequest(ReadableBaseModel):
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

"""
Pydantic models for the Overmind client.
"""

import io
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from rich.console import Console


class ReadableBaseModel(BaseModel):
    """Base model with a readable __repr__ method for better display in Jupyter notebooks."""

    def __repr__(self) -> str:
        """
        Generate a rich-formatted string representation for the terminal.

        This is called by the Python REPL when you inspect an object.
        """
        string_buffer = io.StringIO()
        console = Console(file=string_buffer, force_terminal=True)
        console.print(self)
        return string_buffer.getvalue()


class AgentCreateRequest(ReadableBaseModel):
    """Model for creating a new agent."""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_model: str | None = Field(None, description="The AI model to use (e.g., 'gpt-5-mini')")
    agent_description: str | None = Field(None, description="Description of the agent")
    stats: dict[str, Any] | None = Field(default={}, description="Agent statistics")
    parameters: dict[str, Any] | None = Field(default={}, description="Agent parameters")


class AgentUpdateRequest(ReadableBaseModel):
    """Model for updating an existing agent."""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_model: str | None = Field(None, description="The AI model to use")
    agent_description: str | None = Field(None, description="Description of the agent")
    stats: dict[str, Any] | None = Field(None, description="Agent statistics")
    parameters: dict[str, Any] | None = Field(None, description="Agent parameters")


class AgentResponse(ReadableBaseModel):
    """Model for agent response data."""

    agent_id: str
    agent_model: str | None
    agent_description: str | None
    stats: dict[str, Any] | None
    parameters: dict[str, Any] | None
    business_id: str
    created_at: datetime | None
    updated_at: datetime | None


class LayerResponse(BaseModel):
    """Model for invocation response data."""

    policy_results: dict[str, Any]
    overall_policy_outcome: str
    processed_data: str | None
    span_context: dict[str, Any]

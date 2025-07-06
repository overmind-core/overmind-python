# Overmind Python Client

A Python client for the Overmind API that provides easy access to AI provider endpoints with policy enforcement.

## Features

- **Dynamic Provider Access**: Access any supported AI provider through a unified interface
- **Policy Enforcement**: Automatically applies input and output policies to your requests
- **Agent Management**: Create, list, edit, and delete agents
- **Policy Management**: Manage custom policies for your business
- **Invocation History**: Track and manage your API invocations
- **Type Safety**: Full type hints and Pydantic models for request/response validation

## Installation

### From Source

```bash
cd client
poetry install
```

### Development Installation

```bash
cd client
poetry install --with dev
```

## Quick Start

```python
from overmind_client import OvermindClient

# Initialize the client with your Overmind API token and provider credentials
client = OvermindClient(
    overmind_token="your_overmind_token",
    openai_api_key="your_openai_api_key",
    base_url="http://localhost:8000"  # Your Overmind server URL
)

# Use OpenAI chat completions with policy enforcement
response = client.openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello, world!"}],
    agent_id="default_agent"
)

print(response.processed_output)
print(f"Invocation ID: {response.invocation_id}")
```

## Usage Examples

### Dynamic Provider Access

The client supports dynamic method chaining for provider access:

```python
# OpenAI chat completions
response = client.openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Tell me a joke"}],
    agent_id="my_agent"
)

# OpenAI embeddings (if supported)
response = client.openai.embeddings.create(
    model="text-embedding-ada-002",
    input="Hello world",
    agent_id="my_agent"
)
```

### Agent Management

```python
# Create a new agent
agent = client.create_agent({
    "agent_id": "my_agent",
    "agent_model": "gpt-4o",
    "agent_description": "My custom agent",
    "input_policies": ["reject_prompt_injection"],
    "output_policies": ["reject_irrelevant_answer"]
})

# List all agents
agents = client.list_agents()
for agent in agents:
    print(f"{agent.agent_id}: {agent.agent_description}")

# Get a specific agent
agent = client.get_agent("my_agent")

# Update an agent
client.update_agent({
    "agent_id": "my_agent",
    "agent_description": "Updated description"
})

# Delete an agent
client.delete_agent("my_agent")
```

### Policy Management

```python
# Create a new policy
policy = client.create_policy({
    "policy_id": "my_policy",
    "policy_description": "My custom policy",
    "parameters": {"threshold": 0.8},
    "engine": "custom_engine",
    "is_input_policy": True,
    "is_output_policy": False
})

# List all policies
policies = client.list_policies()

# List input policies only
input_policies = client.list_policies(policy_type="input")

# List output policies only
output_policies = client.list_policies(policy_type="output")

# Get a specific policy
policy = client.get_policy("my_policy")

# Update a policy
client.update_policy({
    "policy_id": "my_policy",
    "parameters": {"threshold": 0.9}
})

# Delete a policy
client.delete_policy("my_policy")
```

### Invocation Management

```python
# List invocations for an agent
invocations = client.list_invocations("my_agent")

# Get a specific invocation
invocation = client.get_invocation("invocation_id")

# Delete an invocation
client.delete_invocation("invocation_id")
```

## Configuration

### Authentication

The client requires:
- **Overmind API Token**: Your authentication token for the Overmind API
- **Provider Credentials**: API keys for the AI providers you want to use

```python
client = OvermindClient(
    overmind_token="your_overmind_token",
    openai_api_key="your_openai_api_key",
    # Add other provider credentials as needed
    # anthropic_api_key="your_anthropic_key",
    # google_api_key="your_google_key",
)
```

### Base URL

By default, the client connects to `http://localhost:8000`. You can specify a different base URL:

```python
client = OvermindClient(
    overmind_token="your_token",
    openai_api_key="your_key",
    base_url="https://your-overmind-server.com"
)
```

## Error Handling

The client provides specific exception types for different error scenarios:

```python
from overmind_client import OvermindError, OvermindAPIError, OvermindAuthenticationError

try:
    response = client.openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}],
        agent_id="my_agent"
    )
except OvermindAuthenticationError:
    print("Invalid API token")
except OvermindAPIError as e:
    print(f"API error: {e.message} (Status: {e.status_code})")
except OvermindError as e:
    print(f"Client error: {e}")
```

## Supported Providers

Currently supported AI providers:
- **OpenAI**: GPT-4, GPT-3.5, embeddings, etc.

The client is designed to be easily extensible for additional providers.

## Development

### Running Tests

```bash
cd client
poetry run pytest
```

### Code Formatting

```bash
cd client
poetry run black .
poetry run isort .
```

### Linting

```bash
cd client
poetry run flake8 .
```

## API Reference

For detailed API documentation, see the docstrings in the source code or run:

```python
help(OvermindClient)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License. 
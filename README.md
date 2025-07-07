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



```bash
pip install -i https://test.pypi.org/simple/ overmind-client
```


## Quick Start

### Use default Overmind agent
Below we initialise the Overmind client and call GPT-4o-mini using `default_agent`. This will run our `reject_prompt_injection` and `reject_irrelevant_answer` policies.
```python
import os
from overmind_client.client import OvermindClient

# Set env variables (or pass directly to the client)
os.environ["OVERMIND_API_KEY"] = "your_overmind_api_key"
os.environ["OPENAI_API_KEY"] = "youtr_openai_api_key"

overmind = OvermindClient()


# Use existing OpenAI client methods
response = client.openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Tell me a joke"}],
    agent_id="default_agent"
)
```

We get the following response - we passed both policies as stated in `policy_results`!
```python
InvocationResponse(
    invocation_id='0ae903b0-e855-4282-abb0-7acfbda2f8cb',
    agent_id='default_agent',
    raw_input="[{'role': 'user', 'content': 'Tell me a joke'}]",
    processed_input="[{'role': 'user', 'content': 'Tell me a joke'}]",
    raw_output="Why don't scientists trust atoms? \n\nBecause they make up everything!",
    processed_output="Why don't scientists trust atoms? \n\nBecause they make up everything!",
    invocation_results={'input': 'passed', 'output': 'passed'},
    policy_results={'prompt_injection_attempt': False, 'relevant_answer': True},
    business_id='AgenticCo Ltd',
    created_at=datetime.datetime(2025, 7, 7, 18, 57, 49, 104204, tzinfo=TzInfo(UTC)),
    updated_at=None
)
```

### Defining your own ad-hoc policies
There are different policy templates that can be set up at invocation time. For example PII removal policy:
```python
input_pii_policy = {
    'policy_template': 'anonymize_pii',
    'parameters': {
        'pii_types': ['DEMOGRAPHIC_DATA', 'GOVERNMENT_ID']
    }
}

messages = [
    {"role": "user", "content": "Hi my name is Jon, born in 1990, passport number 20194812, how old am I?"}
]

result = overmind.openai.chat.completions.create(
    model='gpt-4o-mini',
    messages=messages,
    input_policies=[input_pii_policy]
)
```

This will generate the response below. The `processed_input` is what was actually passed to the LLM, with the sensitive data obfuscated
```python
InvocationResponse(
    invocation_id='cad3c430-357d-4da9-826f-d7b7d4bd76a6',
    agent_id='default_agent',
    raw_input="[{'role': 'user', 'content': 'Hi my name is Jon, born in 1990, passport number 20194812, how old am 
I?'}]",
    processed_input="[{'role': 'user', 'content': 'Hi my name is [PERSON_NAME], born in [DEMOGRAPHIC_DATA], 
passport number [GOVERNMENT_ID], how old am I?'}]",
    raw_output='Hi Jon! If you were born in 1990 and it is now 2023, you would be either 32 or 33 years old, 
depending on whether your birthday has occurred yet this year.',
    processed_output=None,
    invocation_results={'input': 'altered', 'output': 'rejected'},
    policy_results={
        'PII_detected': True,
        'relevant_answer': False,
        'reason': "The answer assumes specific values for [PERSON_NAME], [DEMOGRAPHIC_DATA], and the current year, 
which are not provided in the original question, and directly answers a question that wasn't directly answerable 
from the given information."
    },
    business_id='AgenticCo Ltd',
    created_at=datetime.datetime(2025, 7, 7, 19, 44, 41, 213627, tzinfo=TzInfo(UTC)),
    updated_at=None
)
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
- **Overmind API Key**: Your authentication key for the Overmind API (can be provided directly or via OVERMIND_API_KEY environment variable)
- **Provider Credentials**: API keys for the AI providers you want to use

```python
client = OvermindClient(
    overmind_api_key="your_overmind_api_key",
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
    overmind_api_key="your_api_key",
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
    print("Invalid API key")
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
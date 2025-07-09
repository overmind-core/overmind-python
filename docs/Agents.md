# Agents

Agents are the core entities in Overmind that define how AI models are configured and which policies are applied to requests. Each agent represents a specific configuration for interacting with AI providers.

## Agent Model

The `AgentResponse` model contains the following fields:

### Core Fields
- **`agent_id`** (str): Unique identifier for the agent
- **`agent_model`** (Optional[str]): The AI model to use. Only relevant for UI, in code will depend on client method used (see [Invocations](Invocations.md))
- **`agent_description`** (Optional[str]): Human-readable description of the agent's purpose

### Policy Configuration
- **`input_policies`** (Optional[List[str]]): List of policy IDs to apply to input before sending to the AI model
- **`output_policies`** (Optional[List[str]]): List of policy IDs to apply to output after receiving from the AI model

### Metadata
- **`stats`** (Optional[Dict[str, Any]]): Agent usage statistics and metrics
- **`parameters`** (Optional[Dict[str, Any]]): Additional configuration parameters for the agent
- **`business_id`** (str): The business identifier this agent belongs to
- **`created_at`** (Optional[datetime]): When the agent was created
- **`updated_at`** (Optional[datetime]): When the agent was last modified

## API Methods

### Create Agent
```python
overmind.agents.create(
    agent_id='my_agent',
    agent_model='gpt-4o-mini',
    agent_description='Agent for customer support',
    input_policies=['pii_anonymizer'],
    output_policies=['relevance_checker']
)
```

**Parameters:**
- `agent_id` (str): Unique identifier for the agent
- `agent_model` (Optional[str]): AI model to use
- `agent_description` (Optional[str]): Description of the agent
- `input_policies` (Optional[List[str]]): List of input policy IDs
- `output_policies` (Optional[List[str]]): List of output policy IDs
- `stats` (Optional[Dict[str, Any]]): Agent statistics
- `parameters` (Optional[Dict[str, Any]]): Agent parameters

### List Agents
```python
agents = overmind.agents.list()
```

Returns a list of all agents for the current business.

### Get Agent
```python
agent = overmind.agents.get('my_agent')
```

**Parameters:**
- `agent_id` (str): The unique identifier of the agent to retrieve

### Update Agent
```python
overmind.agents.update(
    agent_id='my_agent',
    agent_description='Updated description',
    input_policies=['pii_anonymizer', 'new_policy']
)
```

**Parameters:**
- `agent_id` (str): Unique identifier for the agent
- `agent_model` (Optional[str]): The AI model to use
- `agent_description` (Optional[str]): Description of the agent
- `input_policies` (Optional[List[str]]): List of input policy IDs
- `output_policies` (Optional[List[str]]): List of output policy IDs
- `stats` (Optional[Dict[str, Any]]): Agent statistics
- `parameters` (Optional[Dict[str, Any]]): Agent parameters

### Delete Agent
```python
overmind.agents.delete('my_agent')
```

**Parameters:**
- `agent_id` (str): The unique identifier of the agent to delete

## Usage Examples

### Creating an Agent for PII-Safe Embeddings
```python
overmind.agents.create(
    agent_id='embedding_agent',
    agent_description='Create document embedding without PII',
    agent_model='openai.text-embedding-3-small',
    input_policies=['redact_our_pii'],
)
```

### Using an Agent with OpenAI Methods
```python
# Use the agent with OpenAI chat completions
result = overmind.openai.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{"role": "user", "content": "Hello"}],
    agent_id='my_agent'
)

# Use the agent with OpenAI embeddings
result = overmind.openai.embeddings.create(
    model="text-embedding-3-small", 
    input="Some text to embed", 
    agent_id='embedding_agent'
)
```

### Default Agent
When no `agent_id` is specified, Overmind uses the `default_agent` which includes:
- `reject_prompt_injection` policy
- `reject_irrelevant_answer` policy

# Invocations

Invocations represent individual API calls made through Overmind. Each invocation contains the complete request and response data, along with policy execution results and metadata.

## InvocationResponse Model

The `InvocationResponse` model contains the following fields:

### Core Identification
- **`invocation_id`** (str): UUID for identifying individual calls
- **`agent_id`** (str): Unique ID of the agent that processed this invocation
- **`business_id`** (str): Your business identifier

### Input/Output Data
- **`raw_input`** (str): The original input received from the client
- **`processed_input`** (Optional[str]): The input after being processed by input policies (may differ from raw_input)
- **`raw_output`** (Optional[str]): The original output produced by the LLM
- **`processed_output`** (Optional[str]): The output after being processed by output policies (may differ from raw_output)

### Policy and Execution Results
- **`invocation_results`** (Dict[str, Any]): Results from the invocation execution
- **`policy_results`** (Dict[str, Any]): Results produced by the specified policies
- **`llm_client_response`** (Optional[Dict[str, Any]]): Full response from the underlying LLM client (varies by provider)

### Metadata
- **`created_at`** (Optional[datetime]): When the invocation was created
- **`updated_at`** (Optional[datetime]): When the invocation was last modified (always None as invocations aren't modifiable)

## API Methods

### List Invocations
```python
invocations = overmind.invocations.list('my_agent')
```

**Parameters:**
- `agent_id` (str): The agent ID to list invocations for

Returns a list of all invocations for the specified agent.

### Get Invocation
```python
invocation = overmind.invocations.get('invocation_uuid_here')
```

**Parameters:**
- `invocation_id` (str): The unique identifier of the invocation to retrieve

### Delete Invocation
```python
overmind.invocations.delete('invocation_uuid_here')
```

**Parameters:**
- `invocation_id` (str): The unique identifier of the invocation to delete

## Usage Examples

### Accessing Invocation Data
```python
# Make a call through an agent
result = overmind.openai.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{"role": "user", "content": "Tell me a joke"}],
    agent_id='my_agent'
)

# The result is an InvocationResponse object
print(f"Invocation ID: {result.invocation_id}")
print(f"Agent ID: {result.agent_id}")
print(f"Raw input: {result.raw_input}")
print(f"Processed input: {result.processed_input}")
print(f"Raw output: {result.raw_output}")
print(f"Processed output: {result.processed_output}")
print(f"Policy results: {result.policy_results}")
```

### Using the Summary Method
```python
# Get a quick overview of the invocation
result.summary()
```

The `summary()` method provides a formatted overview of the invocation, including:
- Invocation ID
- Agent ID
- Input/output comparison
- Policy results summary

### Listing Invocations for an Agent
```python
# Get all invocations for a specific agent
invocations = overmind.invocations.list('my_agent')

for invocation in invocations:
    print(f"Invocation {invocation.invocation_id} at {invocation.created_at}")
    invocation.summary()
```

### Retrieving Specific Invocation
```python
# Get a specific invocation by ID
invocation = overmind.invocations.get('invocation_uuid_here')
invocation.summary()
```

## Supported LLM Clients

Currently, Overmind supports:
- **OpenAI**: Chat completions and text embedding methods
- More providers will be added soon

## Invocation Lifecycle

1. **Request Received**: Raw input is received from the client
2. **Input Processing**: Input policies are applied (if any)
3. **LLM Call**: Processed input is sent to the underlying LLM
4. **Output Processing**: Output policies are applied (if any)
5. **Response**: Complete invocation data is returned

## Policy Results

The `policy_results` field contains detailed information about how each policy affected the invocation:

- **Input Policies**: Results from policies applied to the input
- **Output Policies**: Results from policies applied to the output
- **Rejection Information**: If any policies caused the request to be rejected
- **Modification Details**: How the input/output was modified by policies

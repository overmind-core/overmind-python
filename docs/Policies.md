# Policies

Policies in Overmind are rules that can be applied to input (before sending to AI models) or output (after receiving from AI models) to ensure compliance, security, and quality standards.

## Policy Model

The `PolicyResponse` model contains the following fields:

### Core Fields
- **`policy_id`** (str): Unique identifier for the policy
- **`policy_description`** (str): Human-readable description of the policy's purpose
- **`policy_template`** (str): The template/type of policy (e.g., 'anonymize_pii', 'reject_prompt_injection')
- **`parameters`** (Dict[str, Any]): Configuration parameters specific to the policy template

### Policy Type Configuration
- **`is_input_policy`** (bool): Whether this policy can be applied to input
- **`is_output_policy`** (bool): Whether this policy can be applied to output
- **`is_built_in`** (Optional[bool]): Whether this is a built-in policy (default: False)

### Metadata
- **`stats`** (Dict[str, Any]): Policy usage statistics and metrics
- **`created_at`** (Optional[datetime]): When the policy was created
- **`updated_at`** (Optional[datetime]): When the policy was last modified

## Available Policy Templates

Currently, Overmind supports 5 basic policy templates:

- **`anonymize_pii`**: Anonymizes PII (Personally Identifiable Information)
- **`reject_pii`**: Rejects requests containing PII
- **`reject_prompt_injection`**: Rejects responses that appear to be prompt injection attempts
- **`reject_irrelevant_answer`**: Rejects responses that don't answer the original question
- **`reject_llm_judge_with_criteria`**: Rejects responses that don't meet specified criteria

### Policy Template Details

#### AnonymizePii & RejectPii
Both policies accept an optional `pii_types` parameter, which must be one or more from:
- `"DEMOGRAPHIC_DATA"`
- `"FINANCIAL_ID"`
- `"GEOGRAPHIC_DATA"`
- `"GOVERNMENT_ID"`
- `"MEDICAL_DATA"`
- `"SECURITY_DATA"`
- `"TECHNICAL_ID"`
- `"PERSON_NAME"`

#### RejectLlmJudgeWithCriteria
Requires a `criteria` parameter which is a list of statements. Each statement should evaluate to true or false. The policy will reject if at least one of these statements evaluates to false.

## API Methods

### Create Policy
```python
overmind.policies.create(
    policy_id='redact_our_pii',
    policy_template='anonymize_pii',
    policy_description='Remove PII relevant to our use case, keep the rest',
    parameters={
        'pii_types': ['DEMOGRAPHIC_DATA', 'GOVERNMENT_ID', "PERSON_NAME"]
    },
    is_input_policy=True,
    is_output_policy=False
)
```

**Parameters:**
- `policy_id` (str): Unique identifier for the policy
- `policy_template` (str): Policy template to use
- `policy_description` (Optional[str]): Description of the policy
- `parameters` (Optional[Dict[str, Any]]): Policy parameters
- `is_input_policy` (Optional[bool]): Whether this is an input policy (default: True)
- `is_output_policy` (Optional[bool]): Whether this is an output policy (default: True)
- `stats` (Optional[Dict[str, Any]]): Policy statistics

### List Policies
```python
# List all policies
policies = overmind.policies.list()

# List only input policies
input_policies = overmind.policies.list(policy_type='input')

# List only output policies
output_policies = overmind.policies.list(policy_type='output')
```

**Parameters:**
- `policy_type` (Optional[str]): Filter to show only 'input' or 'output' policies

### Get Policy
```python
policy = overmind.policies.get('redact_our_pii')
```

**Parameters:**
- `policy_id` (str): The unique identifier of the policy to retrieve

### Update Policy
```python
overmind.policies.update(
    policy_id='redact_our_pii',
    policy_description='Updated PII removal policy',
    parameters={
        'pii_types': ['DEMOGRAPHIC_DATA', 'FINANCIAL_ID', 'PERSON_NAME']
    }
)
```

**Parameters:**
- `policy_id` (str): Unique identifier for the policy
- `policy_description` (Optional[str]): Description of the policy
- `parameters` (Optional[Dict[str, Any]]): Policy parameters
- `policy_template` (Optional[str]): Policy template
- `is_input_policy` (Optional[bool]): Whether this is an input policy
- `is_output_policy` (Optional[bool]): Whether this is an output policy
- `stats` (Optional[Dict[str, Any]]): Policy statistics

### Delete Policy
```python
overmind.policies.delete('redact_our_pii')
```

**Parameters:**
- `policy_id` (str): The unique identifier of the policy to delete

## Usage Examples

### Creating a PII Anonymization Policy
```python
overmind.policies.create(
    policy_id='redact_our_pii',
    policy_template='anonymize_pii',
    policy_description='Remove PII relevant to our use case, keep the rest',
    parameters={
        'pii_types': ['DEMOGRAPHIC_DATA', 'GOVERNMENT_ID', "PERSON_NAME"]
    },
    is_input_policy=True,
    is_output_policy=False
)
```

### Creating an LLM Judge Policy
```python
overmind.policies.create(
    policy_id='financial_safety',
    policy_template='reject_llm_judge_with_criteria',
    policy_description='Ensure responses don\'t provide financial advice',
    parameters={
        'criteria': [
            "Must not be a financial advice",
            "Must answer the question fully",
        ]
    },
    is_input_policy=False,
    is_output_policy=True
)
```

### Using Policies at Invocation Time
```python
# Define input policy to filter out PII
input_pii_policy = {
    'policy_template': 'anonymize_pii',
    'parameters': {
        'pii_types': ['DEMOGRAPHIC_DATA', 'FINANCIAL_ID']
    }
}

# Define output policy to check response against criteria
output_llm_judge_criteria = {
    'policy_template': 'reject_llm_judge_with_criteria',
    'parameters': {
        'criteria': [
            "Must not be a financial advice",
            "Must answer the question fully",
        ]
    }
}

# Use policies with OpenAI methods
result = overmind.openai.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{"role": "user", "content": "Hi my name is Jon, account number 20194812. Should I switch my mortgage now?"}],
    input_policies=[input_pii_policy],
    output_policies=[output_llm_judge_criteria]
)
```
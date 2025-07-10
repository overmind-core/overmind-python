# Overmind Client

[![CI Checks](https://github.com/overmind-core/overmind-python/actions/workflows/publish.yml/badge.svg)](https://github.com/overmind-core/overmind-python/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/overmind.svg)](https://pypi.org/project/overmind/)

A client for the Overmind API that provides easy access to AI provider endpoints with policy enforcement.

## Features

- **Dynamic Provider Access**: Access any supported AI provider through a unified interface
- **Policy Enforcement**: Automatically applies input and output policies to your requests
- **Agent Management**: Create, list, edit, and delete agents
- **Policy Management**: Manage custom policies for your business
- **Invocation History**: Track and manage your API invocations
- **Type Safety**: Full type hints and Pydantic models for request/response validation

## Installation



```bash
pip install overmind
```


## Quick Start

### Use default Overmind agent

Get your free Overmind API key at [overmind.evallab.dev](https://overmind.evallab.dev)

Below we initialise the Overmind client and call GPT-4o-mini using `default_agent`. This will run our `reject_prompt_injection` and `reject_irrelevant_answer` policies.
```python
import os
from overmind.client import OvermindClient

# Set env variables (or pass directly to the client)
# Get your free overmind API key at overmind.evallab.dev
os.environ["OVERMIND_API_KEY"] = "your_overmind_api_key"
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"

overmind = OvermindClient()


# Use existing OpenAI client methods
response = overmind.openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Tell me a joke about LLMs"}],
    agent_id="default_agent"
)

response.summary()
```



### Define your own policies
There are different policy templates that can be set up at invocation time.
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

messages = [
    {
        "role": "user", 
        "content": "Hi my name is Jon, account number 20194812. Should I switch my mortgage now or wait for a year to have a lower interest rate?"
    }
]

# Use existing OpenAI client methods but now you can pass your policies
response = overmind.openai.chat.completions.create(
    model='gpt-4o-mini',
    messages=messages,
    input_policies=[input_pii_policy],
    output_policies=[output_llm_judge_criteria]
)

response.summary()
```
## Further usage

There is a more detailed [tutorial notebook](docs/overmind_tutorial.ipynb) available.

We are not storing your API keys and you are solely responsible for managing them and the associated costs.

On ours side we run policy executions for free as this is an alpha stage product. We may impose usage limits and scale our services up and down from time to time.

We appreciate any feedback, collaboration or other suggestions. You can reach out at [support@evallab.dev](mailto:support@evallab.dev)
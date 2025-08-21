# Overmind Client

[![CI Checks](https://github.com/overmind-core/overmind-python/actions/workflows/publish.yml/badge.svg)](https://github.com/overmind-core/overmind-python/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/overmind.svg)](https://pypi.org/project/overmind/)

A client for the Overmind API that provides easy access to AI provider endpoints with policy enforcement.

## Features

- **Easy Integration**: Use major providers like OpenAI with the same call signatures
- **Policy Enforcement**: Apply customizable policies to your LLM inputs and outputs
- **Observability**: Log and explore all LLM calls and policy results

## Installation



```bash
pip install overmind
```


## Quick Start

### Use Overmind Proxy

Get your free Overmind API key at [console.overmindlab.ai](https://console.overmindlab.ai)

Below we initialise the Overmind client and call GPT-5-mini with `anonymize_pii` and `reject_irrelevant_answer` policies. This will prevent PII data leakage and ensure only relevant answers are produced.
```python
import os
from overmind.client import OvermindClient

# Set env variables (or pass directly to the client)
# Get your free overmind API key at console.overmindlab.ai
os.environ["OVERMIND_API_KEY"] = "your_overmind_api_key"
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"

overmind = OvermindClient()


# Use existing OpenAI client methods
response = overmind.openai.responses.create(
    model='gpt-5-mini',
    input="Should I switch my mortgage now or wait for a year to have a lower interest rate?",
    # Overmind built-in policies
    input_policies=['anonymize_pii'],
    output_policies=['reject_irrelevant_answer'],
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

input_messages = [
    {
        "role": "user", 
        "content": "Hi my name is Jon, account number 20194812. Should I switch my mortgage now or wait for a year to have a lower interest rate?"
    }
]

result = overmind.openai.responses.create(
    model='gpt-5-mini',
    input=input_messages,
    input_policies=[input_pii_policy],
    output_policies=[output_llm_judge_criteria]
)

result.summary()
```
### Use Overmind Layers

For more complex use cases you can choose Overmind Layers - an API to call standalone policies without relying on us to call LLMs. 

This use case is best demonstrated in our [LangGraph integration tutorial](https://github.com/overmind-core/overmind-python/blob/main/docs/Overmind%20Layers%20%26%20LangGraph%20tutorial.ipynb), although the Layers can be used with any framework.

## Further usage

There are a more detailed tutorials available for [Overmind Proxy](https://github.com/overmind-core/overmind-python/blob/main/docs/Overmind%20Proxy%20tutorial.ipynb) and [Overmind Layers & LangGraph integration](https://github.com/overmind-core/overmind-python/blob/main/docs/Overmind%20Layers%20%26%20LangGraph%20tutorial.ipynb).

We are not storing your API keys and you are solely responsible for managing them and the associated costs.

On our side we run policy executions for free as this is an alpha stage product. We may impose usage limits and scale our services up and down from time to time.

We appreciate any feedback, collaboration or other suggestions. You can reach out at [support@evallab.dev](mailto:support@evallab.dev)
# Overmind SDK

[![CI Checks](https://github.com/overmind-core/overmind-python/actions/workflows/publish.yml/badge.svg)](https://github.com/overmind-core/overmind-python/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/overmind-sdk.svg)](https://pypi.org/project/overmind-sdk/)

Automatic observability for LLM applications. One call to `init()` instruments your existing OpenAI, Anthropic, Google Gemini, or Agno code — no proxy, no key sharing, no import changes.

## Features

- **Zero-change instrumentation**: Keep using your existing LLM clients as-is
- **Auto-detection**: Detects installed providers automatically, or specify them explicitly
- **Custom spans**: Add your own tracing spans alongside LLM calls
- **User & tag context**: Tag traces with user IDs, custom attributes, and exceptions
- **OpenTelemetry native**: Built on standard OTLP — works with any OTel-compatible backend

## Installation

```bash
pip install overmind-sdk
```

Install alongside your LLM provider package:

```bash
pip install overmind-sdk openai          # OpenAI
pip install overmind-sdk anthropic       # Anthropic
pip install overmind-sdk google-genai    # Google Gemini
pip install overmind-sdk agno            # Agno
```

---

## Quick Start

### 1. Get your API key

Sign up at [console.overmindlab.ai](https://console.overmindlab.ai) — your API key is shown immediately after signup.

### 2. Initialize the SDK

Call `init()` once at application startup, before any LLM calls:

```python
from overmind_sdk import init

init(
    overmind_api_key="ovr_...",    # or set OVERMIND_API_KEY env var
    service_name="my-service",
    environment="production",
)
```

That's it. Your existing LLM code works unchanged and every call is automatically traced.

### 3. Use your LLM client as normal

```python
from openai import OpenAI

client = OpenAI()  # your existing client, unchanged

response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[{"role": "user", "content": "Explain quantum computing"}],
)
print(response.choices[0].message.content)
```

Traces appear in your [Overmind dashboard](https://console.overmindlab.ai) in real time.

---

## Provider Examples

### OpenAI

```python
from overmind_sdk import init
from openai import OpenAI

init(service_name="my-service", providers=["openai"])

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Anthropic

```python
from overmind_sdk import init
import anthropic

init(service_name="my-service", providers=["anthropic"])

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Google Gemini

```python
from overmind_sdk import init
from google import genai

init(service_name="my-service", providers=["google"])

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Explain quantum computing",
)
```

### Agno

```python
from overmind_sdk import init
from agno.agent import Agent
from agno.models.openai import OpenAIChat

init(service_name="my-service", providers=["agno"])

agent = Agent(model=OpenAIChat(id="gpt-5"), markdown=True)
agent.print_response("Write a short poem about the sea.")
```

### Auto-detect all installed providers

Pass an empty `providers` list (or omit it) to automatically instrument every supported provider that is installed:

```python
from overmind_sdk import init

init(service_name="my-service")  # auto-detects openai, anthropic, google, agno
```

---

## Configuration

### `init()` parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `overmind_api_key` | `str \| None` | `None` | Your Overmind API key. Falls back to `OVERMIND_API_KEY` env var. |
| `service_name` | `str \| None` | `None` | Name of your service (shown in traces). Also reads `OVERMIND_SERVICE_NAME`. Defaults to `"unknown-service"`. |
| `environment` | `str \| None` | `None` | Deployment environment (`"production"`, `"staging"`, etc.). Also reads `OVERMIND_ENVIRONMENT`. Defaults to `"development"`. |
| `providers` | `list[str] \| None` | `None` | Providers to instrument. Supported: `"openai"`, `"anthropic"`, `"google"`, `"agno"`. `None` or empty = auto-detect. |
| `overmind_base_url` | `str \| None` | `None` | Override the Overmind API URL. Falls back to `OVERMIND_API_URL` env var, then `https://api.overmindlab.ai`. |

### Environment variables

| Variable | Description |
|----------|-------------|
| `OVERMIND_API_KEY` | Your Overmind API key |
| `OVERMIND_SERVICE_NAME` | Service name (overridden by `service_name` param) |
| `OVERMIND_ENVIRONMENT` | Environment name (overridden by `environment` param) |
| `OVERMIND_API_URL` | Custom API endpoint URL |

---

## Additional SDK Functions

### `get_tracer()`

Get the OpenTelemetry tracer to create custom spans around any block of code:

```python
from overmind_sdk import init, get_tracer

init(service_name="my-service")

tracer = get_tracer()

with tracer.start_as_current_span("process-document") as span:
    span.set_attribute("document.id", doc_id)
    result = process(doc)
```

### `set_user()`

Tag the current trace with user identity. Call this in your request handler or middleware:

```python
from overmind_sdk import set_user

# In a FastAPI middleware:
@app.middleware("http")
async def add_user_context(request: Request, call_next):
    if request.state.user:
        set_user(
            user_id=request.state.user.id,
            email=request.state.user.email,
        )
    return await call_next(request)
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `user_id` | Yes | Unique identifier for the user |
| `email` | No | User's email address |
| `username` | No | User's display name |

### `set_tag()`

Add a custom attribute to the current span:

```python
from overmind_sdk import set_tag

set_tag("feature.flag", "new-checkout-flow")
set_tag("tenant.id", tenant_id)
```

### `capture_exception()`

Record an exception on the current span and mark it as an error:

```python
from overmind_sdk import capture_exception

try:
    result = risky_llm_call()
except Exception as e:
    capture_exception(e)
    raise
```

---

## Full Example

```python
import os
from overmind_sdk import init, get_tracer, set_user, set_tag, capture_exception
from openai import OpenAI

os.environ["OVERMIND_API_KEY"] = "ovr_your_key_here"

init(
    service_name="customer-support",
    environment="production",
    providers=["openai"],
)

client = OpenAI()

def handle_query(user_id: str, question: str) -> str:
    set_user(user_id=user_id)
    set_tag("workflow", "support")

    tracer = get_tracer()
    with tracer.start_as_current_span("handle-support-query"):
        try:
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful customer support agent."},
                    {"role": "user", "content": question},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            capture_exception(e)
            raise

answer = handle_query("user-123", "How do I reset my password?")
print(answer)
```

---

## What Happens After Your First Traces

Once Overmind has collected 10+ traces for a given prompt pattern, the optimization engine starts automatically:

1. **Agent detection** — extracts prompt templates from your traces
2. **LLM judge scoring** — evaluates each trace against auto-generated quality criteria
3. **Prompt experimentation** — generates and tests candidate prompt variations
4. **Model backtesting** — replays traces through alternative models to find cost/quality tradeoffs
5. **Suggestions** — surfaces the best alternatives in your dashboard

See [How Optimization Works](https://docs.overmindlab.ai/guides/how-it-works) for details.

---

We appreciate any feedback or suggestions. Reach out at [support@overmindlab.ai](mailto:support@overmindlab.ai)

# Overmind Python SDK

[![CI Checks](https://github.com/overmind-core/overmind-python/actions/workflows/publish.yml/badge.svg)](https://github.com/overmind-core/overmind-python/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/overmind.svg)](https://pypi.org/project/overmind/)

Automatic observability for LLM applications. One call to `overmind.init()` instruments your existing OpenAI, Anthropic, Google Gemini, or Agno code — no proxy, no key sharing, no import changes.

## What is Overmind?

Overmind automatically optimizes your AI agents — better prompts, better models, lower cost. It collects execution traces, evaluates them with LLM judges, and recommends better prompts and models to reduce cost, improve quality, and lower latency.

- **Zero-change instrumentation**: Keep using your existing LLM clients as-is
- **Auto-detection**: Detects installed providers automatically, or specify them explicitly
- **Custom spans**: Add your own tracing spans alongside LLM calls
- **User & tag context**: Tag traces with user IDs, custom attributes, and exceptions
- **OpenTelemetry native**: Built on standard OTLP — works with any OTel-compatible backend
- **Managed service**: [console.overmindlab.ai](https://console.overmindlab.ai)
- **Self-hosted (open-source)**: [github.com/overmind-core/overmind](https://github.com/overmind-core/overmind)
- **Docs**: [docs.overmindlab.ai](https://docs.overmindlab.ai)

## Installation

```bash
pip install overmind
```

Install alongside your LLM provider package:

```bash
pip install overmind openai          # OpenAI
pip install overmind anthropic       # Anthropic
pip install overmind google-genai    # Google Gemini
pip install overmind agno            # Agno
```

---

## Quick Start

### 1. Get your API key

Sign up at [console.overmindlab.ai](https://console.overmindlab.ai) — your API key is shown immediately after signup.

### 2. Initialize the SDK

Call `overmind.init()` once at application startup, before any LLM calls:

```python
import overmind

overmind.init(
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
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain quantum computing"}],
)
print(response.choices[0].message.content)
```

Traces appear in your [Overmind dashboard](https://console.overmindlab.ai) in real time.

---

## Provider Examples

### OpenAI

```python
import overmind
from openai import OpenAI

overmind.init(service_name="my-service", providers=["openai"])

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Anthropic

```python
import overmind
import anthropic

overmind.init(service_name="my-service", providers=["anthropic"])

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Google Gemini

```python
import overmind
from google import genai

overmind.init(service_name="my-service", providers=["google"])

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Explain quantum computing",
)
```

### Agno

```python
import overmind
from agno.agent import Agent
from agno.models.openai import OpenAIChat

overmind.init(service_name="my-service", providers=["agno"])

agent = Agent(model=OpenAIChat(id="gpt-4o-mini"), markdown=True, name="Storyteller")
agent.print_response("Write a short poem about the sea.")
```

### Auto-detect all installed providers

Omit `providers` (or pass an empty list) to automatically instrument every supported provider that is installed:

```python
import overmind

overmind.init(service_name="my-service")  # auto-detects openai, anthropic, google, agno
```

---

## Configuration

### `overmind.init()` parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `overmind_api_key` | `str \| None` | `None` | Your Overmind API key. Falls back to `OVERMIND_API_KEY` env var. |
| `service_name` | `str` | `"unknown-service"` | Name of your service (shown in traces). Also reads `OVERMIND_SERVICE_NAME`. |
| `environment` | `str` | `"development"` | Deployment environment (`"production"`, `"staging"`, etc.). Also reads `OVERMIND_ENVIRONMENT`. |
| `providers` | `list[str] \| None` | `None` | Providers to instrument. Supported: `"openai"`, `"anthropic"`, `"google"`, `"agno"`. `None` or `[]` = auto-detect all installed. |
| `overmind_base_url` | `str \| None` | `None` | Override the Overmind API URL. Falls back to `OVERMIND_API_URL` or `https://api.overmindlab.ai`. |

### Environment variables

| Variable | Description |
|----------|-------------|
| `OVERMIND_API_KEY` | Your Overmind API key |
| `OVERMIND_SERVICE_NAME` | Service name (overridden by `service_name` param) |
| `OVERMIND_ENVIRONMENT` | Environment name (overridden by `environment` param) |
| `OVERMIND_API_URL` | Custom API endpoint URL |

### Self-Hosted

The SDK works with both the managed service and the [self-hosted open-source edition](https://github.com/overmind-core/overmind). API keys prefixed with `ovr_core_` are automatically routed to `http://localhost:8000`. You can also set `OVERMIND_API_URL` to point to your own deployment.

---

## Additional SDK Functions

### `overmind.get_tracer()`

Get the OpenTelemetry tracer to create custom spans around any block of code:

```python
import overmind

overmind.init(service_name="my-service")

tracer = overmind.get_tracer()

with tracer.start_as_current_span("process-document") as span:
    span.set_attribute("document.id", doc_id)
    result = process(doc)
```

### `overmind.set_user()`

Tag the current trace with user identity. Call this in your request handler or middleware:

```python
import overmind

# In a FastAPI middleware:
@app.middleware("http")
async def add_user_context(request: Request, call_next):
    if request.state.user:
        overmind.set_user(
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

### `overmind.set_tag()`

Add a custom attribute to the current span:

```python
overmind.set_tag("feature.flag", "new-checkout-flow")
overmind.set_tag("tenant.id", tenant_id)
```

### `overmind.capture_exception()`

Record an exception on the current span and mark it as an error:

```python
try:
    result = risky_llm_call()
except Exception as e:
    overmind.capture_exception(e)
    raise
```

---

## Full Example

```python
import os
import overmind
from openai import OpenAI

os.environ["OVERMIND_API_KEY"] = "ovr_your_key_here"

overmind.init(
    service_name="customer-support",
    environment="production",
    providers=["openai"],
)

client = OpenAI()

def handle_query(user_id: str, question: str) -> str:
    overmind.set_user(user_id=user_id)

    tracer = overmind.get_tracer()
    with tracer.start_as_current_span("handle-support-query"):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful customer support agent."},
                    {"role": "user", "content": question},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            overmind.capture_exception(e)
            raise

answer = handle_query("user-123", "How do I reset my password?")
print(answer)
```

---

## What Happens After Your First Traces

Once Overmind has collected 30+ traces for a given prompt pattern, the optimization engine starts automatically:

1. **Agent detection** — extracts prompt templates from your traces
2. **LLM judge scoring** — evaluates each trace against auto-generated quality criteria
3. **Prompt experimentation** — generates and tests candidate prompt variations
4. **Model backtesting** — replays traces through alternative models to find cost/quality tradeoffs
5. **Suggestions** — surfaces the best alternatives in your dashboard

See [How Optimization Works](https://docs.overmindlab.ai/guides/how-it-works) for details.

---

## Documentation

- [Full documentation](https://docs.overmindlab.ai)
- [Python SDK reference](https://docs.overmindlab.ai/guides/sdk-reference)
- [JavaScript/TypeScript SDK](https://docs.overmindlab.ai/guides/sdk-js)
- [Self-hosted platform (OSS)](https://github.com/overmind-core/overmind)

## License

MIT

---

We appreciate any feedback or suggestions. Reach out at [support@overmindlab.ai](mailto:support@overmindlab.ai)

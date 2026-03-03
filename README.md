# Overmind Python SDK

[![CI Checks](https://github.com/overmind-core/overmind-python/actions/workflows/publish.yml/badge.svg)](https://github.com/overmind-core/overmind-python/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/overmind.svg)](https://pypi.org/project/overmind/)

Drop-in replacement for OpenAI, Anthropic, and Google Gemini clients that automatically traces every LLM call to the [Overmind](https://docs.overmindlab.ai) platform for optimization.

## What is Overmind?

Overmind automatically optimizes your AI agents — better prompts, better models, lower cost. It collects execution traces, evaluates them with LLM judges, and recommends better prompts and models to reduce cost, improve quality, and lower latency.

- **Managed service**: [console.overmindlab.ai](https://console.overmindlab.ai)
- **Self-hosted (open-source)**: [github.com/overmind-core/overmind](https://github.com/overmind-core/overmind)
- **Docs**: [docs.overmindlab.ai](https://docs.overmindlab.ai)

## Installation

```bash
pip install overmind
```

## Quick Start

Swap one import line. Everything else stays the same.

**Before:**
```python
from openai import OpenAI
```

**After:**
```python
from overmind.clients import OpenAI
```

Full example:

```python
import os
from overmind.clients import OpenAI

os.environ["OVERMIND_API_KEY"] = "<your-api-token>"
os.environ["OPENAI_API_KEY"] = "sk-..."

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

All your LLM calls are now traced automatically. After 10+ traces, Overmind starts detecting agents, scoring quality, and generating optimization suggestions.

## Supported Providers

### OpenAI

```python
from overmind.clients import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

Supports `chat.completions.create()`, `responses.create()`, and `embeddings.create()`.

### Anthropic

```python
from overmind.clients import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-5-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Google Gemini

```python
from overmind.clients.google import Client as GoogleClient

client = GoogleClient()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Hello!",
)
```

## Configuration

### Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `OVERMIND_API_KEY` | Yes | Your Overmind API token |
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `ANTHROPIC_API_KEY` | If using Anthropic | Anthropic API key |
| `GEMINI_API_KEY` | If using Google Gemini | Google Gemini API key |
| `OVERMIND_API_URL` | No | Override the Overmind API base URL |
| `OVERMIND_TRACES_URL` | No | Override the traces endpoint URL |

### Constructor Options

Keys can also be passed directly:

```python
client = OpenAI(
    overmind_api_key="ovr_...",
    api_key="sk-...",
)
```

### Self-Hosted

The SDK works with both the managed service and the [self-hosted open-source edition](https://github.com/overmind-core/overmind). API keys prefixed with `ovr_core_` are automatically routed to `localhost:8000`. You can also set `OVERMIND_API_URL` to point to your own deployment.

## Tips

- **One client per use case** — if your app has different prompt patterns (e.g., support agent vs. summarizer), create separate clients so Overmind can extract cleaner prompt templates.
- **Let it run** — more traces means better recommendations. Check the dashboard after a day or two.

## Documentation

- [Full documentation](https://docs.overmindlab.ai)
- [Python SDK reference](https://docs.overmindlab.ai/guides/sdk-reference)
- [JavaScript/TypeScript SDK](https://docs.overmindlab.ai/guides/sdk-js)
- [Self-hosted platform (OSS)](https://github.com/overmind-core/overmind)

## License

MIT

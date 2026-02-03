import hashlib
from overmind.overmind_sdk import get_tracer


def build_prompt(*, id: str, prompt: str, **kwargs) -> str:
    hash = hashlib.md5(prompt.encode()).hexdigest()
    with get_tracer().start_as_current_span(f"build_prompt_{id}") as span:
        span.set_attribute("id", id)
        span.set_attribute("prompt", prompt)
        span.set_attribute("hash", hash)

    return prompt.format(**kwargs)

from datetime import datetime
import json
import os
import requests
from time import sleep
from overmind.clients import OpenAI

project_id = os.environ.get("OVERMIND_PROJECT_ID", "e5445c2d-0e4b-4cb1-8a0c-26c18d0ba19f")

base_url = "https://api.overmindlab.ai"
openai_client = OpenAI(
    overmind_base_url=base_url,
    overmind_api_key=os.getenv("OVERMIND_API_KEY"),
)


today = str(datetime.now().timestamp())
system_prompt = f"""You are a fashion taxonomy assistant.
Classify the product into exactly one category from the allowed list.
Return strict JSON only in this format:
{{"category": "<one allowed category>", "confidence": <0 to 1>, "reason": "<short reason>"}}
Today's date: {today}"""

user_message = """Allowed categories: Dresses, Tops, Shirts, T-Shirts, Knitwear, Coats, Jackets, Blazers, Jeans, Trousers, Skirts, Shorts, Shoes, Bags, Accessories, Other

Product description:
Triple S Sneaker in light grey microfiber and rhinestones.
Leather free sneaker microfiber and rhinestones complex 3-layered outsole embroidered size at the edge of the toe embroidered logo on the side embossed logo in the back triple s rubber branding on the tongue 2 laces loops including 1 functional lacing system featuring 12 fabric eyelets laces recalling hiking boots' laces back and tongue pull-on tab made in china.
Upper: nylon, polyurethane - Sole: tpu - Insole: foam."""


def test_spans():
    openai_client.chat.completions.create(
        model="gpt-5-mini",
        reasoning_effort="minimal",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": system_prompt.strip(),
            },
            {
                "role": "user",
                "content": user_message.strip(),
            },
        ],
    )
    sleep(8)

    traces_response = requests.get(
        f"{base_url}/api/v1/traces/list",
        params=dict(
            project_id=project_id,
            limit=5,
            offset=0,
            root_only=True,
        ),
        headers={
            "X-API-Token": os.getenv("OVERMIND_API_KEY"),
        },
    )
    assert traces_response.status_code == 200
    traces = traces_response.json()["traces"]
    input_has_today = []
    for trace in traces:
        has_sign = today in trace["Inputs"]
        input_has_today.append(has_sign)
        if not has_sign:
            continue

        span_attributes = trace["SpanAttributes"]
        assert span_attributes["gen_ai.request.model"] == "gpt-5-mini"
        assert span_attributes["gen_ai.completion.0.finish_reason"] == "stop"
        assert span_attributes["gen_ai.request.structured_output_schema"] == json.dumps({"type": "json_object"})

    assert any(input_has_today), "unable to find trace pushed to prod"

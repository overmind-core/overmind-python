from collections.abc import Iterator
import json
from pathlib import Path
from overmind.overmind_sdk import init, get_tracer
from tqdm import tqdm
from opentelemetry import trace
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
import csv
from opentelemetry.trace import SpanKind


def get_log_item_model(mapping: Dict[str, str] = None):
    if mapping is None:
        mapping = {}

    def get_field(name: str):
        return mapping.get(name, name)

    class LogItem(BaseModel):
        input: object = Field(..., alias=get_field("input"))
        output: object = Field(..., alias=get_field("output"))

        start_time: int = Field(..., alias=get_field("start_time"))
        end_time: int = Field(..., alias=get_field("end_time"))

        # custom IDs (must be valid 32/16 hex chars)
        trace_state: Optional[str] = Field(
            default=None, alias=get_field("trace_state"), max_length=32, min_length=16
        )
        trace_id: Optional[str] = Field(
            default=None, alias=get_field("trace_id"), max_length=32, min_length=16
        )
        span_id: Optional[str] = Field(
            default=None, alias=get_field("span_id"), max_length=32, min_length=16
        )
        parent_span_id: Optional[str] = Field(
            default=None,
            alias=get_field("parent_span_id"),
            max_length=32,
            min_length=16,
        )

        name: Optional[str] = Field(
            default="log-ingestion-service", alias=get_field("name")
        )
        kind: int = Field(default=2, alias=get_field("kind"))

        status_code: int = Field(default=0, alias=get_field("status_code"))
        status_message: str = Field(default="", alias=get_field("status_message"))
        extra_attributes: Dict[str, str] = Field(
            ..., default_factory=dict, alias=get_field("extra_attributes")
        )

        model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    return LogItem


def process_log_item(item: dict, mapping: Dict[str, str]):
    log_model = get_log_item_model(mapping)
    log_item = log_model.model_validate(item, by_alias=True)

    ctx = {}
    if log_item.trace_id:
        ctx["trace_id"] = log_item.trace_id
    if log_item.span_id:
        ctx["span_id"] = log_item.span_id
    if log_item.trace_state:
        ctx["trace_state"] = log_item.trace_state

    context = None
    if ctx:
        context = trace.set_span_in_context(
            trace.NonRecordingSpan(
                trace.SpanContext(
                    **ctx,
                    is_remote=True,
                )
            )
        )

    tracer = get_tracer()
    span = tracer.start_span(
        name=log_item.name or "log-ingestion-service",
        start_time=log_item.start_time,
        kind=SpanKind(log_item.kind),
        attributes=log_item.extra_attributes,
        context=context,
    )
    span.set_status(log_item.status_code, log_item.status_message)
    span.set_attribute("inputs", str(log_item.input))
    span.set_attribute("outputs", str(log_item.output))
    span.end(end_time=log_item.end_time)


def load_from_jsonl(filepath: str) -> Iterator[dict]:
    with open(filepath, "r") as f:
        for line in f:
            yield json.loads(line)


def load_from_json(filepath: str) -> Iterator[dict]:
    with open(filepath, "r") as f:
        data = json.load(f)
        for item in data:
            yield item


def load_from_csv(filepath: str) -> Iterator[dict]:
    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def ingest_logs(filepath: str, mapping: Dict[str, str], **kwargs):
    if kwargs.get("overmind_api_key"):
        init(overmind_api_key=kwargs.get("overmind_api_key"))
    else:
        init()

    suffix = Path(filepath).suffix
    items: list[dict] = []
    if suffix == ".jsonl":
        items = load_from_jsonl(filepath)
    elif suffix == ".json":
        items = load_from_json(filepath)
    elif suffix == ".csv":
        items = load_from_csv(filepath)
    else:
        raise ValueError(f"Unsupported file extension: {suffix}")

    for i, dict_item in tqdm(enumerate(items)):
        try:
            process_log_item(dict_item, mapping)
        except Exception as trace_ex:
            print(f"Failed to record span for line {i}: {trace_ex}")
            continue


if __name__ == "__main__":
    data = "tests/data/logs_mapped.csv"  # Fixed path if running from project root

    mapping = {
        "input": "llm_input",
        "output": "llm_output",
        "start_time": "start_time_nano",
        "end_time": "end_time_nano",
    }
    ingest_logs(data, mapping)

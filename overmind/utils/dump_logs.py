from collections.abc import Iterator
import json
from pathlib import Path
from overmind.overmind_sdk import init, get_tracer
from tqdm import tqdm
from opentelemetry import trace
from typing import Dict, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field


def get_log_item_model(item: dict, mapping: Dict[str, str] = {}):
    class LogItem(BaseModel):
        input: any = Field(..., alias=mapping.get("input", "input"))
        output: any = Field(..., alias=mapping.get("output", "output"))

        start_time: int = Field(
            ..., alias=mapping.get("start_time", "start_time")
        )  # nanoseconds since epoch
        end_time: int = Field(
            ..., alias=mapping.get("end_time", "end_time")
        )  # nanoseconds since epoch

        # custom IDs (must be valid 32/16 hex chars)
        trace_state: Optional[str] = Field(
            default=None, alias=mapping.get("trace_state", "trace_state")
        )
        trace_id: Optional[str] = Field(
            default=None, alias=mapping.get("trace_id", "trace_id")
        )
        span_id: Optional[str] = Field(
            default=None, alias=mapping.get("span_id", "span_id")
        )
        parent_span_id: Optional[str] = Field(
            default=None, alias=mapping.get("parent_span_id", "parent_span_id")
        )

        name: str = Field(
            default="log-ingestion-service", alias=mapping.get("name", "name")
        )
        kind: int = Field(default=2, alias=mapping.get("kind", "kind"))

        status_code: int = Field(
            default=0, alias=mapping.get("status_code", "status_code")
        )
        status_message: str = Field(
            default="", alias=mapping.get("status_message", "status_message")
        )
        extra_attributes: Dict[str, str] = Field(
            default_factory=dict,
            alias=mapping.get("extra_attributes", "extra_attributes"),
        )
        model_config: ConfigDict = ConfigDict(
            arbitrary_types_allowed=True, extra="allow"
        )

    return LogItem


LogItem = TypeVar("LogItem", bound=BaseModel)


def process_log_item(log_item: "LogItem"):
    context = trace.set_span_in_context(
        trace.NonRecordingSpan(
            trace.SpanContext(
                trace_id=log_item.trace_id,
                span_id=log_item.span_id,
                is_remote=True,
                trace_flags=trace.TraceFlags(0x01),
            )
        )
    )
    tracer = get_tracer()
    with tracer.start_span(
        "process_log_item",
        start_time=log_item.start_time,
        kind=log_item.kind,
        attributes=log_item.extra_attributes,
        context=context,
    ) as span:
        span.set_status(log_item.status_code, log_item.status_message)
        span.set_attribute("inputs", log_item.input)
        span.set_attribute("outputs", log_item.output)
        span.end(end_time=log_item.end_time)


def load_from_jsonl(filepath: str) -> Iterator[LogItem]:
    with open(filepath, "r") as f:
        for line in f:
            item = json.loads(line)
            yield LogItem(**item)


def load_from_json(filepath: str) -> Iterator[LogItem]:
    with open(filepath, "r") as f:
        data = json.load(f)
        for item in data:
            yield LogItem(**item)


def load_from_csv(filepath: str) -> Iterator[LogItem]:
    import csv

    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming LogItem can be instantiated from a dict
            yield LogItem(**row)


def ingest_logs(filepath: str, mapping: Dict[str, str], **kwargs):
    LogItem = get_log_item_model(mapping)

    if kwargs.get("overmind_api_key"):
        init(overmind_api_key=kwargs.get("overmind_api_key"))
    else:
        init()

    suffix = Path(filepath).suffix
    items = []
    if suffix == ".jsonl":
        items = load_from_jsonl(filepath)
    elif suffix == ".json":
        items = load_from_json(filepath)
    elif suffix == ".csv":
        items = load_from_csv(filepath)
    else:
        raise ValueError(f"Unsupported file extension: {suffix}")

    for i, log_item in tqdm(enumerate(items)):
        try:
            process_log_item(log_item)
        except Exception as trace_ex:
            print(f"Failed to record span for line {i}: {trace_ex}")
            continue


if __name__ == "__main__":
    ingest_logs("logs.json", {})

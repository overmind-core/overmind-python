import json
from tqdm import tqdm
from opentelemetry import trace
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2
from typing import Dict, Optional
from typing import List
from pydantic import BaseModel, ConfigDict, Field, RootModel


class LogItem(BaseModel):
    input: any = Field(...)
    output: any = Field(...)

    start_time: int = Field(...) # nanoseconds since epoch
    end_time: int = Field(...) # nanoseconds since epoch

    trace_state: Optional[str]=Field( default=None)
    trace_id: Optional[str]=Field( default=None)
    span_id: Optional[str]=Field( default=None)
    parent_span_id: Optional[str]=Field( default=None)

    name: str = Field(default="log-ingestion-service")
    kind: int = Field(default=0)

    status_code: int = Field(default=0)
    status_message: str = Field(default="")
    extra_attributes: Dict[str, str] = Field(...,default_factory=dict)
    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True, extra="allow")





LogItems = RootModel[list[LogItem]]

def ingest_logs(filepath: str, mapping: Dict[str, str]):
    tracer = trace.get_tracer(__name__)
    with open(filepath, "r") as f:
        for i, line in tqdm(enumerate(json.load(f))):
            print(line)
            try:
                log_item = LogItem(**line)
            except Exception as e:
                print(f"Failed to parse JSON for line {i}: {e}")
                continue

            try:
                with tracer.start_as_current_span(
                    "process_log_item",
                    start_time=log_item.start_time,
                ) as span:
                    span.set_attribute("inputs", log_item.input)
                    span.set_attribute("outputs", log_item.output)
                    span.end(end_time=log_item.end_time)
                    # Additional actions can be performed here (send to API, validate, etc.)
                    print(span.to_json())
            except Exception as trace_ex:
                print(f"Failed to record span for line {i}: {trace_ex}")
                continue
        print("Done")

if __name__ == "__main__":
    ingest_logs("logs.json", {})

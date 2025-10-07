# Your library's code
from langchain_core.callbacks import BaseCallbackHandler
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from langgraph.graph import StateGraph
from typing import Optional
import hashlib
import json
from overmind.utils.api_settings import get_api_settings
from overmind.utils.serializers import serialize


class OvermindObservabilityCallback(BaseCallbackHandler):
    def __init__(
        self,
        graph: Optional[StateGraph] = None,
        name: Optional[str] = '',
        tags: Optional[dict] = {},
        overmind_api_key: Optional[str] = None,
        traces_base_url: Optional[str] = None,
        debug: bool = False,
    ):
        super().__init__()
        self.debug = debug
        self.overmind_api_key, _, self.traces_base_url = get_api_settings(
            overmind_api_key, None, traces_base_url
        )
        # This is where the magic happens!
        current_provider = trace.get_tracer_provider()
        if not hasattr(current_provider, "add_span_processor"):
            self._setup_opentelemetry()
        self.tracer = trace.get_tracer("overmind.langchain.instrumentation")

        self.run_spans = {}
        self.graph = graph.get_graph() if graph else None
        self.name = name
        self.tags = tags

    def parse_graph(self, graph: StateGraph):
        return {
            "nodes": list(graph.nodes.keys()),
            "edges": [(edge.source, edge.target) for edge in graph.edges],
        }

    def _setup_opentelemetry(self):
        provider = TracerProvider()

        exporter = OTLPSpanExporter(
            endpoint=f"{self.traces_base_url}/api/v1/traces/create",
            headers={"X-API-Token": self.overmind_api_key},
        )

        provider.add_span_processor(BatchSpanProcessor(exporter))

        if self.debug:
            console_exporter = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter)
            provider.add_span_processor(console_processor)

        trace.set_tracer_provider(provider)

    def on_chain_start(self, serialized, inputs, *, run_id, **kwargs):
        name = (
            kwargs.get("name")
            or (
                serialized
                and (str(serialized.get("name") or str(serialized.get("id", [""])[-1])))
            )
            or "<unknown>"
        )

        metadata = kwargs.get("metadata", {})
        parent_run_id = kwargs.get("parent_run_id")
        run_id = str(run_id)

        if parent_run_id is None:
            self.run_spans[run_id] = self.tracer.start_span(
                name=name,
            )

            if self.graph:
                metadata["graph"] = self.parse_graph(self.graph)
                self.graph_hash = hashlib.sha256(
                    json.dumps(metadata["graph"], sort_keys=True).encode('utf-8')
                ).hexdigest()

        else:
            parent_context = trace.set_span_in_context(
                self.run_spans[str(parent_run_id)]
            )
            self.run_spans[run_id] = self.tracer.start_span(
                name=name,
                context=parent_context,
            )

        if self.graph:
            self.run_spans[run_id].set_attribute("workflow_name", self.name)
            self.run_spans[run_id].set_attribute("workflow_hash", self.graph_hash)
            self.run_spans[run_id].set_attribute("workflow_tags", serialize(self.tags) if isinstance(self.tags, dict) else '{}')

        self.run_spans[run_id].set_attribute("metadata", serialize(metadata))
        self.run_spans[run_id].set_attribute("inputs", serialize(inputs))

    def on_chain_end(self, outputs, *, run_id, **kwargs):
        run_id = str(run_id)

        if "policy_results" in outputs:
            self.run_spans[run_id].set_attribute(
                "policy_outcome", outputs["overall_policy_outcome"]
            )
            self.run_spans[run_id].set_attribute(
                "policy_results", serialize(outputs.pop("policy_results"))
            )

        if "span_context" in outputs:
            # can't add links to the span that has been started and there is no clean way to pass
            # this span to the backend at the layer run time (since it happening in a downstream node)
            self.run_spans[run_id].set_attribute(
                "span_context", serialize(outputs.pop("span_context"))
            )

        self.run_spans[run_id].set_attribute("outputs", serialize(outputs))
        self.run_spans[run_id].set_status(trace.Status(trace.StatusCode.OK))
        self.run_spans[run_id].end()

    def on_chain_error(self, error, *, run_id, **kwargs):
        run_id = str(run_id)
        self.run_spans[run_id].set_attribute("error", str(error))
        self.run_spans[run_id].set_status(trace.Status(trace.StatusCode.ERROR))
        self.run_spans[run_id].record_exception(error)
        self.run_spans[run_id].end()

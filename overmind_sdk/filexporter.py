from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import IO, Sequence

from google.protobuf.json_format import MessageToDict
from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


class FileSpanExporter(SpanExporter):
    def __init__(
        self,
        file_path: str | Path | IO[str],
    ) -> None:
        self.file_path = Path(file_path) if isinstance(file_path, str) else file_path
        self._lock = threading.Lock()
        self._file: IO[str] | None = None

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        with self._lock:
            if not self._file:
                if isinstance(self.file_path, Path):
                    self._file = self.file_path.open('a', encoding='utf-8')
                else:
                    self._file = self.file_path
            encoded = encode_spans(spans)
            data = MessageToDict(encoded, preserving_proto_field_name=True)
            self._file.write(json.dumps(data) + '\n')
            self._file.flush()
        return SpanExportResult.SUCCESS

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def shutdown(self) -> None:
        with self._lock:
            if self._file:
                self._file.flush()
                if self._file is not self.file_path:
                    self._file.close()

from __future__ import annotations

import threading
from pathlib import Path
from typing import IO, Sequence

from opentelemetry.exporter.otlp.proto.common.trace_encoder import (
    encode_spans,
)
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

HEADER = b'OTEL BACKUP FILE\n'
VERSION = b'VERSION 1\n'

class FileSpanExporter(SpanExporter):
    def __init__(
        self,
        file_path: str | Path | IO[bytes],
    ) -> None:
        self.file_path = Path(file_path) if isinstance(file_path, str) else file_path
        self._lock = threading.Lock()
        self._file: IO[bytes] | None = None
        self._wrote_header = False

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        with self._lock:
            if not self._file:
                if isinstance(self.file_path, Path):
                    self._file = self.file_path.open('ab')
                else:
                    self._file = self.file_path
                if self._file.tell() == 0:
                    self._file.write(HEADER)
                    self._file.write(VERSION)
            encoded_spans = encode_spans(spans)
            size = encoded_spans.ByteSize()
            # we can represent up to a 4GB message
            self._file.write(size.to_bytes(4, 'big'))
            self._file.write(encoded_spans.SerializeToString())
            self._file.flush()
        return SpanExportResult.SUCCESS

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def shutdown(self) -> None:
        with self._lock:
            if self._file:
                self._file.flush()
                if self._file is not self.file_path:
                    # don't close the file if it was passed in
                    self._file.close()

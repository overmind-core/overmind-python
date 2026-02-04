import pytest
import os
import unittest
from unittest.mock import MagicMock
from overmind.utils.dump_logs import ingest_logs


current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@unittest.mock.patch("overmind.utils.dump_logs.get_tracer")
@unittest.mock.patch("overmind.utils.dump_logs.init")
@pytest.mark.parametrize("filepath", ["logs.jsonl", "logs.json", "logs.csv"])
def test_dump_logs(init_mock: MagicMock, mock_get_tracer: MagicMock, filepath):
    init_mock.return_value = None
    ingest_logs(os.path.join(current_dir, filepath), {})
    init_mock.assert_called()
    mock_get_tracer.assert_called()


@unittest.mock.patch("overmind.utils.dump_logs.get_tracer")
@unittest.mock.patch("overmind.utils.dump_logs.init")
@pytest.mark.parametrize(
    "filepath", ["logs_mapped.jsonl", "logs_mapped.json", "logs_mapped.csv"]
)
def test_dump_logs_with_mapping(
    init_mock: MagicMock, mock_get_tracer: MagicMock, filepath
):
    init_mock.return_value = None
    ingest_logs(
        os.path.join(current_dir, filepath),
        {
            "input": "llm_input",
            "output": "llm_output",
            "start_time": "start_time_nano",
            "end_time": "end_time_nano",
        },
    )
    assert init_mock.call_count == 1
    mock_get_tracer.assert_called()

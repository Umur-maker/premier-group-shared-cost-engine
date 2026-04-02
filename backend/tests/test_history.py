import os
import tempfile
import json
import pytest
from unittest.mock import patch
import backend.core.history as history


@pytest.fixture
def tmp_history_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        hist_dir = os.path.join(tmpdir, "history")
        os.makedirs(hist_dir)
        index_file = os.path.join(hist_dir, "index.json")
        with open(index_file, "w") as f:
            json.dump([], f)
        with patch.object(history, "HISTORY_DIR", hist_dir), \
             patch.object(history, "HISTORY_INDEX", index_file):
            yield hist_dir


@pytest.fixture
def sample_excel(tmp_history_dir):
    path = os.path.join(tmp_history_dir, "test_source.xlsx")
    with open(path, "wb") as f:
        f.write(b"FAKE_EXCEL_DATA")
    return path


def test_save_and_list_run(tmp_history_dir, sample_excel):
    entry = history.save_run(
        month=2, year=2026, language="en",
        monthly_input={"electricity_total": 100.0},
        ratios={"electricity": {"sqm_weight": 50, "headcount_weight": 50}},
        companies=[{"id": "a", "name": "A", "active": True}],
        results=[{"company_id": "a", "total": 100.0}],
        excel_path=sample_excel,
    )
    assert entry["month"] == 2
    assert entry["year"] == 2026

    runs = history.list_runs()
    assert len(runs) == 1
    assert runs[0]["id"] == entry["id"]


def test_delete_run(tmp_history_dir, sample_excel):
    entry = history.save_run(2, 2026, "en", {}, {}, [], [], sample_excel)
    assert len(history.list_runs()) == 1

    history.delete_run(entry["id"])
    assert len(history.list_runs()) == 0


def test_get_excel_path(tmp_history_dir, sample_excel):
    entry = history.save_run(3, 2026, "en", {}, {}, [], [], sample_excel)
    path = history.get_excel_path(entry)
    assert os.path.exists(path)


def test_multiple_runs_newest_first(tmp_history_dir, sample_excel):
    history.save_run(1, 2026, "en", {}, {}, [], [], sample_excel)
    history.save_run(2, 2026, "en", {}, {}, [], [], sample_excel)
    runs = history.list_runs()
    assert len(runs) == 2
    assert runs[0]["month"] == 2  # newest first

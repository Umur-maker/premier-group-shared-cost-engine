"""Simple file-based run history. Stores completed runs as JSON + Excel files."""

import json
import os
import shutil
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
HISTORY_INDEX = os.path.join(HISTORY_DIR, "index.json")


def _ensure_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _load_index():
    _ensure_dir()
    if os.path.exists(HISTORY_INDEX):
        with open(HISTORY_INDEX, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_index(entries):
    _ensure_dir()
    tmp = HISTORY_INDEX + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    os.replace(tmp, HISTORY_INDEX)


def save_run(month, year, language, monthly_input, ratios, companies, results, excel_path):
    """Save a completed run to history. Copies the Excel file into history dir."""
    _ensure_dir()
    run_id = f"{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    excel_filename = f"{run_id}.xlsx"
    dest_path = os.path.join(HISTORY_DIR, excel_filename)
    shutil.copy2(excel_path, dest_path)

    entry = {
        "id": run_id,
        "month": month,
        "year": year,
        "language": language,
        "generated_at": datetime.now().isoformat(),
        "excel_file": excel_filename,
        "monthly_input": monthly_input,
        "ratios": ratios,
        "company_count": len([c for c in companies if c["active"]]),
    }

    entries = _load_index()
    entries.insert(0, entry)
    _save_index(entries)
    return entry


def list_runs():
    """Return all history entries, newest first."""
    return _load_index()


def get_excel_path(entry):
    """Return full path to the stored Excel file."""
    return os.path.join(HISTORY_DIR, entry["excel_file"])


def delete_run(run_id):
    """Delete a history entry and its Excel file."""
    entries = _load_index()
    entry = next((e for e in entries if e["id"] == run_id), None)
    if entry:
        excel_path = os.path.join(HISTORY_DIR, entry["excel_file"])
        if os.path.exists(excel_path):
            os.remove(excel_path)
        entries = [e for e in entries if e["id"] != run_id]
        _save_index(entries)

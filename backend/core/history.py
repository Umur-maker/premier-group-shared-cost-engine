"""Simple file-based run history. Stores completed runs as JSON + Excel files."""

import json
import os
import shutil
import threading
from datetime import datetime

from backend.core.config import DATA_DIR
HISTORY_DIR = os.path.join(DATA_DIR, "history")
HISTORY_INDEX = os.path.join(HISTORY_DIR, "index.json")

_lock = threading.Lock()


def _ensure_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _load_index():
    _ensure_dir()
    if not os.path.exists(HISTORY_INDEX):
        return []
    try:
        with open(HISTORY_INDEX, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return data
    except (json.JSONDecodeError, OSError) as e:
        # Corrupted index — back it up and start fresh to avoid data loss
        try:
            backup = HISTORY_INDEX + ".corrupted_" + str(int(__import__("time").time()))
            os.rename(HISTORY_INDEX, backup)
            print(f"[history] Corrupted index backed up to {backup}: {e}")
        except OSError:
            pass
        return []


def _save_index(entries):
    _ensure_dir()
    tmp = HISTORY_INDEX + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    os.replace(tmp, HISTORY_INDEX)


def save_run(month, year, language, monthly_input, ratios, companies, results, excel_path):
    """Save a completed run to history. Copies the Excel file into history dir."""
    with _lock:
        _ensure_dir()
        run_id = f"{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        excel_filename = f"{run_id}.xlsx"
        dest_path = os.path.join(HISTORY_DIR, excel_filename)
        shutil.copy2(excel_path, dest_path)

        active_companies = [c for c in companies if c.get("active", True)]

        entry = {
            "id": run_id,
            "month": month,
            "year": year,
            "language": language,
            "generated_at": datetime.now().isoformat(),
            "excel_file": excel_filename,
            "monthly_input": monthly_input,
            "ratios": ratios,
            "company_count": len(active_companies),
            "results": results,
            "companies": active_companies,
        }

        entries = _load_index()
        entries.insert(0, entry)
        _save_index(entries)
        return entry


def find_run_for_month(year, month):
    """Find the official run for a specific month. Returns entry or None."""
    entries = _load_index()
    return next((e for e in entries if e["year"] == year and e["month"] == month), None)


def save_or_replace_run(month, year, language, monthly_input, ratios, companies, results, excel_path):
    """Save a run, replacing any existing run for the same month.

    Returns (entry, replaced_run_id_or_none).
    """
    with _lock:
        _ensure_dir()
        entries = _load_index()

        old_entry = next((e for e in entries if e["year"] == year and e["month"] == month), None)
        old_run_id = None

        if old_entry:
            old_run_id = old_entry["id"]
            old_excel = os.path.join(HISTORY_DIR, old_entry["excel_file"])
            if os.path.exists(old_excel):
                try:
                    os.remove(old_excel)
                except OSError as e:
                    # File may be locked by Excel.exe/OneDrive — orphan it rather than blocking save
                    print(f"[history] Could not remove old excel {old_excel}: {e}")
            entries = [e for e in entries if e["id"] != old_run_id]

        run_id = f"{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        excel_filename = f"{run_id}.xlsx"
        dest_path = os.path.join(HISTORY_DIR, excel_filename)
        shutil.copy2(excel_path, dest_path)

        active_companies = [c for c in companies if c.get("active", True)]

        entry = {
            "id": run_id,
            "month": month,
            "year": year,
            "language": language,
            "generated_at": datetime.now().isoformat(),
            "excel_file": excel_filename,
            "monthly_input": monthly_input,
            "ratios": ratios,
            "company_count": len(active_companies),
            "results": results,
            "companies": active_companies,
        }

        entries.insert(0, entry)
        _save_index(entries)
        return entry, old_run_id


def list_runs():
    """Return all history entries, newest first."""
    return _load_index()


def get_excel_path(entry):
    """Return full path to the stored Excel file."""
    return os.path.join(HISTORY_DIR, entry["excel_file"])


def delete_run(run_id):
    """Delete a history entry and its Excel file."""
    with _lock:
        entries = _load_index()
        entry = next((e for e in entries if e["id"] == run_id), None)
        if entry:
            excel_path = os.path.join(HISTORY_DIR, entry["excel_file"])
            if os.path.exists(excel_path):
                os.remove(excel_path)
            entries = [e for e in entries if e["id"] != run_id]
            _save_index(entries)

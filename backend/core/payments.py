"""Payment ledger system — multiple entries per company per run."""

import json
import os
import threading
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
LEDGER_FILE = os.path.join(DATA_DIR, "payment_ledger.json")

_lock = threading.Lock()


def _load():
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"entries": []}


def _save(data):
    tmp = LEDGER_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LEDGER_FILE)


def add_payment(run_id, company_id, amount, date, note=""):
    """Add a payment entry to the ledger."""
    with _lock:
        data = _load()
        entry = {
            "id": f"pay_{uuid.uuid4().hex[:8]}",
            "run_id": run_id,
            "company_id": company_id,
            "amount": round(amount, 2),
            "date": date,
            "note": note,
            "created_at": datetime.now().isoformat(),
        }
        data["entries"].append(entry)
        _save(data)
        return entry


def delete_payment(payment_id):
    """Delete a single payment entry."""
    with _lock:
        data = _load()
        data["entries"] = [e for e in data["entries"] if e["id"] != payment_id]
        _save(data)


def get_payments_for_run(run_id):
    """Get all payment entries for a specific run."""
    data = _load()
    return [e for e in data["entries"] if e["run_id"] == run_id]


def get_payments_for_company_run(run_id, company_id):
    """Get payment entries for a specific company in a specific run."""
    data = _load()
    return [e for e in data["entries"]
            if e["run_id"] == run_id and e["company_id"] == company_id]


def get_total_paid(run_id, company_id):
    """Sum of all payments for a company in a run."""
    entries = get_payments_for_company_run(run_id, company_id)
    return round(sum(e["amount"] for e in entries), 2)


def get_running_balance(company_id, history_runs):
    """Calculate running balance across all official runs.

    Walks runs oldest-to-newest. For each run:
      balance += (amount_due - total_paid)

    Positive = outstanding debt, Negative = credit available.
    """
    data = _load()
    balance = 0.0

    sorted_runs = sorted(history_runs, key=lambda r: (r["year"], r["month"]))

    for run in sorted_runs:
        results = run.get("results", [])
        company_result = next((r for r in results if r["company_id"] == company_id), None)
        if not company_result:
            continue

        due = company_result.get("total", 0)
        if due <= 0:
            continue

        paid = sum(e["amount"] for e in data["entries"]
                   if e["run_id"] == run["id"] and e["company_id"] == company_id)
        balance += (due - paid)

    return round(balance, 2)


def get_all_running_balances(history_runs, company_ids):
    """Get running balances for all companies."""
    return {cid: get_running_balance(cid, history_runs) for cid in company_ids}


def migrate_old_payments(history_runs):
    """Migrate old payments.json format to new ledger format."""
    old_file = os.path.join(DATA_DIR, "payments.json")
    if not os.path.exists(old_file):
        return 0

    with open(old_file, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    if not old_data:
        return 0

    count = 0
    with _lock:
        data = _load()
        for month_key, companies in old_data.items():
            parts = month_key.split("_")
            if len(parts) != 2:
                continue
            year, month = int(parts[0]), int(parts[1])

            matching_run = next(
                (r for r in history_runs if r["year"] == year and r["month"] == month),
                None
            )
            if not matching_run:
                continue

            for company_id, payment in companies.items():
                if not payment.get("paid"):
                    continue
                existing = [e for e in data["entries"]
                           if e["run_id"] == matching_run["id"]
                           and e["company_id"] == company_id]
                if existing:
                    continue

                entry = {
                    "id": f"pay_mig_{uuid.uuid4().hex[:6]}",
                    "run_id": matching_run["id"],
                    "company_id": company_id,
                    "amount": payment.get("paid_amount", 0),
                    "date": payment.get("paid_date", ""),
                    "note": "migrated from old system",
                    "created_at": datetime.now().isoformat(),
                }
                data["entries"].append(entry)
                count += 1

        _save(data)

    os.rename(old_file, old_file + ".bak")
    return count

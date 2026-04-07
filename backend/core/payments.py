"""Payment tracking and carry-forward system."""

import json
import os
import threading

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PAYMENTS_FILE = os.path.join(DATA_DIR, "payments.json")

_lock = threading.Lock()


def _load():
    if os.path.exists(PAYMENTS_FILE):
        with open(PAYMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(data):
    tmp = PAYMENTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PAYMENTS_FILE)


def get_payment_status(year, month):
    """Get payment status for a specific month.
    Returns dict of {company_id: {"paid": bool, "paid_amount": float, "paid_date": str}}
    """
    data = _load()
    key = f"{year}_{month:02d}"
    return data.get(key, {})


def set_payment(year, month, company_id, paid, paid_amount=0, paid_date=""):
    """Mark a company as paid/unpaid for a specific month."""
    with _lock:
        data = _load()
        key = f"{year}_{month:02d}"
        if key not in data:
            data[key] = {}
        data[key][company_id] = {
            "paid": paid,
            "paid_amount": paid_amount,
            "paid_date": paid_date,
        }
        _save(data)
    return data[key][company_id]


def get_outstanding_balance(company_id, up_to_year, up_to_month, history_runs):
    """Calculate total outstanding balance for a company up to a given month.

    Looks through history runs and payment records to find unpaid amounts.
    Returns {"total_outstanding": float, "unpaid_months": [...]}
    """
    data = _load()
    unpaid_months = []
    total = 0.0

    for run in history_runs:
        ry, rm = run["year"], run["month"]
        # Only look at months up to the specified month
        if (ry, rm) > (up_to_year, up_to_month):
            continue

        # Find this company's total in the run results
        results = run.get("results", [])
        company_result = next((r for r in results if r["company_id"] == company_id), None)
        if not company_result:
            continue

        billed = company_result.get("total", 0)
        if billed <= 0:
            continue

        # Check payment
        key = f"{ry}_{rm:02d}"
        payment = data.get(key, {}).get(company_id, {})
        if payment.get("paid"):
            paid_amount = payment.get("paid_amount", billed)
            remaining = round(billed - paid_amount, 2)
            if remaining > 0:
                total += remaining
                unpaid_months.append({"year": ry, "month": rm, "amount": remaining, "partial": True})
        else:
            total += billed
            unpaid_months.append({"year": ry, "month": rm, "amount": billed, "partial": False})

    return {"total_outstanding": round(total, 2), "unpaid_months": unpaid_months}


def get_all_balances(up_to_year, up_to_month, history_runs, company_ids):
    """Get outstanding balances for all companies."""
    return {
        cid: get_outstanding_balance(cid, up_to_year, up_to_month, history_runs)
        for cid in company_ids
    }

"""Payment ledger API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.core.payments import (
    add_payment, delete_payment, get_payments_for_run,
    get_running_balance, get_all_running_balances,
)
from backend.core.history import list_runs

router = APIRouter(prefix="/api/payments", tags=["payments"])


class PaymentCreate(BaseModel):
    company_id: str
    amount: float
    date: str
    note: Optional[str] = ""


@router.get("/run/{run_id}")
def get_run_payments(run_id: str):
    """Get all payment entries for a specific run."""
    return get_payments_for_run(run_id)


@router.post("/run/{run_id}")
def create_payment(run_id: str, body: PaymentCreate):
    """Add a payment entry."""
    if body.amount <= 0:
        raise HTTPException(400, "Payment amount must be positive.")
    runs = list_runs()
    if not any(r["id"] == run_id for r in runs):
        raise HTTPException(404, f"Run '{run_id}' not found.")
    entry = add_payment(run_id, body.company_id, body.amount, body.date, body.note or "")
    return entry


@router.delete("/entry/{payment_id}")
def remove_payment(payment_id: str):
    """Delete a payment entry."""
    delete_payment(payment_id)
    return {"status": "deleted", "id": payment_id}


@router.get("/balance/{company_id}")
def company_balance(company_id: str):
    """Get running balance for a company across all months."""
    runs = list_runs()
    balance = get_running_balance(company_id, runs)
    return {"company_id": company_id, "running_balance": balance}


@router.get("/balances")
def all_balances():
    """Get running balances for all companies."""
    runs = list_runs()
    company_ids = set()
    for run in runs:
        for r in run.get("results", []):
            company_ids.add(r["company_id"])
    return get_all_running_balances(runs, company_ids)


@router.post("/migrate")
def migrate():
    """Migrate old payments.json to new ledger format."""
    from backend.core.payments import migrate_old_payments
    runs = list_runs()
    count = migrate_old_payments(runs)
    return {"migrated": count}

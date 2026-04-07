# Workflow Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the monthly workflow into Calculate Preview → Save Official → Payment Ledger, with one report per month, multiple payments per company, and overpayment credit carry-forward.

**Architecture:** Backend splits `POST /api/calculate` into preview-only + save. Payment system rewrites from single-record to ledger model with individual entries linked to run_id. History enforces one official entry per month. Frontend adds two-step calculation flow and payment entry UI with confirmation.

**Tech Stack:** Python/FastAPI (backend), Next.js/TypeScript (frontend), JSON file storage

---

### Task 1: Rewrite Payment Ledger Backend

**Files:**
- Rewrite: `backend/core/payments.py`
- Test: `backend/tests/test_payments.py`

- [ ] **Step 1: Write new payments.py with ledger model**

Replace the entire file with a ledger-based system:

```python
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

    # Sort runs oldest first
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
            # Find matching run
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
                # Check if already migrated
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

    # Rename old file
    os.rename(old_file, old_file + ".bak")
    return count
```

- [ ] **Step 2: Write tests**

Create `backend/tests/test_payments_ledger.py`:

```python
import json
import os
import tempfile
import pytest
from unittest.mock import patch
import backend.core.payments as payments


@pytest.fixture
def tmp_ledger():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_file = os.path.join(tmpdir, "payment_ledger.json")
        with open(ledger_file, "w") as f:
            json.dump({"entries": []}, f)
        with patch.object(payments, "LEDGER_FILE", ledger_file), \
             patch.object(payments, "DATA_DIR", tmpdir):
            yield tmpdir


def test_add_payment(tmp_ledger):
    entry = payments.add_payment("run_1", "balkan", 500, "2026-04-10", "bank")
    assert entry["amount"] == 500
    assert entry["company_id"] == "balkan"
    assert entry["run_id"] == "run_1"
    assert entry["note"] == "bank"


def test_multiple_payments(tmp_ledger):
    payments.add_payment("run_1", "balkan", 500, "2026-04-10")
    payments.add_payment("run_1", "balkan", 300, "2026-04-15")
    entries = payments.get_payments_for_company_run("run_1", "balkan")
    assert len(entries) == 2
    assert payments.get_total_paid("run_1", "balkan") == 800


def test_delete_payment(tmp_ledger):
    entry = payments.add_payment("run_1", "balkan", 500, "2026-04-10")
    payments.delete_payment(entry["id"])
    assert len(payments.get_payments_for_run("run_1")) == 0


def test_running_balance_simple(tmp_ledger):
    runs = [{"id": "run_1", "year": 2026, "month": 3,
             "results": [{"company_id": "balkan", "total": 1000}]}]
    payments.add_payment("run_1", "balkan", 600, "2026-03-15")
    balance = payments.get_running_balance("balkan", runs)
    assert balance == 400  # owes 400


def test_running_balance_overpayment(tmp_ledger):
    runs = [
        {"id": "run_1", "year": 2026, "month": 3,
         "results": [{"company_id": "balkan", "total": 1000}]},
        {"id": "run_2", "year": 2026, "month": 4,
         "results": [{"company_id": "balkan", "total": 900}]},
    ]
    payments.add_payment("run_1", "balkan", 1200, "2026-03-15")  # overpay 200
    # No payment for April yet
    balance = payments.get_running_balance("balkan", runs)
    assert balance == 700  # -200 credit + 900 due = 700


def test_running_balance_credit_carryforward(tmp_ledger):
    runs = [
        {"id": "run_1", "year": 2026, "month": 3,
         "results": [{"company_id": "balkan", "total": 500}]},
    ]
    payments.add_payment("run_1", "balkan", 700, "2026-03-15")  # overpay 200
    balance = payments.get_running_balance("balkan", runs)
    assert balance == -200  # has 200 credit


def test_get_payments_for_run(tmp_ledger):
    payments.add_payment("run_1", "balkan", 500, "2026-04-10")
    payments.add_payment("run_1", "gbcs", 300, "2026-04-10")
    payments.add_payment("run_2", "balkan", 100, "2026-05-10")
    run1_payments = payments.get_payments_for_run("run_1")
    assert len(run1_payments) == 2
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest backend/tests/test_payments_ledger.py -v`
Expected: All 8 tests PASS

- [ ] **Step 4: Commit**

```bash
git add backend/core/payments.py backend/tests/test_payments_ledger.py
git commit -m "feat: rewrite payment system as ledger with multiple entries + credit carry-forward"
```

---

### Task 2: Add One-Per-Month Enforcement to History

**Files:**
- Modify: `backend/core/history.py`

- [ ] **Step 1: Add find_run_for_month and save_or_replace_run**

Add these functions to `backend/core/history.py`:

```python
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

        # Check for existing run for this month
        old_entry = next((e for e in entries if e["year"] == year and e["month"] == month), None)
        old_run_id = None

        if old_entry:
            old_run_id = old_entry["id"]
            # Remove old Excel
            old_excel = os.path.join(HISTORY_DIR, old_entry["excel_file"])
            if os.path.exists(old_excel):
                os.remove(old_excel)
            entries = [e for e in entries if e["id"] != old_run_id]

        # Create new entry
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/history.py
git commit -m "feat: add one-per-month enforcement to history with save_or_replace_run"
```

---

### Task 3: Split Calculate API into Preview + Save

**Files:**
- Modify: `backend/api/calculate.py`

- [ ] **Step 1: Modify POST /api/calculate to preview-only**

Change the `calculate` function to NOT save to history:

Remove these lines from the calculate function:
```python
    entry = save_run(...)
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
```

And change the return to:
```python
    return {
        "results": results,
        "filename": filename,
        "monthly_input": mi,
        "settings_snapshot": {
            "ratios": settings["ratios"],
            "eur_ron_rate": settings.get("eur_ron_rate", 5.1),
        },
    }
```

- [ ] **Step 2: Add POST /api/calculate/save endpoint**

```python
class SaveRequest(BaseModel):
    month: int
    year: int
    language: str = "en"
    monthly_input: MonthlyInput


@router.post("/save")
def save_official(body: SaveRequest):
    """Save calculation as official report for the month. Replaces existing if any."""
    _validate_period(body.month, body.year)

    companies = load_companies()
    settings = load_settings()
    mi = body.monthly_input.model_dump()

    try:
        results = allocate_costs(companies, settings["ratios"], mi, settings=settings)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not results:
        raise HTTPException(400, "No active companies found.")

    active = [c for c in companies if c["active"]]
    mn = month_name(body.month, body.language)
    filename = f"Premier_BC_{body.year}_{body.month:02d}_{mn}.xlsx"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    generate_excel(tmp_path, results, mi, settings["ratios"], active, body.language)

    from backend.core.history import save_or_replace_run, find_run_for_month
    existing = find_run_for_month(body.year, body.month)

    entry, old_run_id = save_or_replace_run(
        body.month, body.year, body.language, mi,
        settings["ratios"], companies, results, tmp_path
    )

    try:
        os.unlink(tmp_path)
    except OSError:
        pass

    return {
        "run_id": entry["id"],
        "filename": filename,
        "replaced": old_run_id,
        "results": results,
    }
```

- [ ] **Step 3: Add GET /api/calculate/check/{year}/{month}**

```python
@router.get("/check/{year}/{month}")
def check_month(year: int, month: int):
    """Check if an official report exists for this month."""
    from backend.core.history import find_run_for_month
    existing = find_run_for_month(year, month)
    if existing:
        return {
            "exists": True,
            "run_id": existing["id"],
            "generated_at": existing["generated_at"],
        }
    return {"exists": False}
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/calculate.py
git commit -m "feat: split calculate into preview-only + save-official endpoints"
```

---

### Task 4: Rewrite Payment API Endpoints

**Files:**
- Rewrite: `backend/api/payments.py`

- [ ] **Step 1: Replace with ledger-based endpoints**

```python
"""Payment ledger API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.core.payments import (
    add_payment, delete_payment, get_payments_for_run,
    get_running_balance, get_all_running_balances,
)
from backend.core.history import list_runs, find_run_for_month

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
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/payments.py
git commit -m "feat: rewrite payment API with ledger endpoints"
```

---

### Task 5: Update Frontend Types and API Client

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add/update types**

Add to `frontend/src/types/index.ts`:

```typescript
export interface PaymentEntry {
  id: string;
  run_id: string;
  company_id: string;
  amount: number;
  date: string;
  note: string;
  created_at: string;
}

export interface MonthCheck {
  exists: boolean;
  run_id?: string;
  generated_at?: string;
}
```

Remove old `PaymentStatus` and `OutstandingBalance` interfaces.

- [ ] **Step 2: Update API client**

Replace old payment functions in `frontend/src/lib/api.ts`:

```typescript
// Calculate
export const calculatePreview = (data: {
  month: number; year: number; language: string; monthly_input: MonthlyInput;
}) => request<{ results: AllocationResult[]; filename: string }>(
  "/api/calculate", { method: "POST", body: JSON.stringify(data) });

export const saveOfficial = (data: {
  month: number; year: number; language: string; monthly_input: MonthlyInput;
}) => request<{ run_id: string; filename: string; replaced: string | null; results: AllocationResult[] }>(
  "/api/calculate/save", { method: "POST", body: JSON.stringify(data) });

export const checkMonth = (year: number, month: number) =>
  request<MonthCheck>(`/api/calculate/check/${year}/${month}`);

// Payments (ledger)
export const getRunPayments = (runId: string) =>
  request<PaymentEntry[]>(`/api/payments/run/${runId}`);

export const addPayment = (runId: string, data: {
  company_id: string; amount: number; date: string; note?: string;
}) => request<PaymentEntry>(`/api/payments/run/${runId}`, {
  method: "POST", body: JSON.stringify(data) });

export const deletePaymentEntry = (paymentId: string) =>
  request<{ status: string }>(`/api/payments/entry/${paymentId}`, { method: "DELETE" });

export const getCompanyBalance = (companyId: string) =>
  request<{ company_id: string; running_balance: number }>(`/api/payments/balance/${companyId}`);

export const getAllBalances = () =>
  request<Record<string, number>>("/api/payments/balances");
```

Remove old `getPayments`, `updatePayment`, `getBalances` functions.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/lib/api.ts
git commit -m "feat: update frontend types and API client for ledger system"
```

---

### Task 6: Rewrite Monthly Input Page (Two-Step Flow)

**Files:**
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Implement preview → save flow**

Key changes to `page.tsx`:
- "Generate Report" button becomes "Calculate Preview" — calls `calculatePreview()`, shows results, does NOT save
- New "Save as Official Report" button appears after preview — calls `saveOfficial()`
- Before saving, call `checkMonth()` to warn if month already has a report
- After saving, show payment entry section linked to run_id
- Payment section uses `addPayment()` per entry, not batch save
- Show existing payments via `getRunPayments(run_id)`
- Show running balance via `getAllBalances()`
- Confirmation dialog before saving payments (summary of what's being recorded)

The page states become:
```
idle → previewing → saved (with run_id) → entering payments
```

- [ ] **Step 2: Build and verify**

Run: `cd frontend && npm run build`
Expected: 0 errors, all routes compile

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat: two-step calculate flow with payment ledger UI"
```

---

### Task 7: Update Manager View (Read-Only with Ledger)

**Files:**
- Modify: `frontend/src/app/manager/page.tsx`

- [ ] **Step 1: Switch to ledger-based data**

Key changes:
- Load payments via `getRunPayments(run_id)` instead of old `getPayments`
- Load balances via `getAllBalances()` instead of old endpoint
- Remove "Mark Paid / Mark Unpaid" toggle buttons (manager is read-only)
- Show payment entries list per company (date, amount, note)
- Show running balance per company
- Highlight credits in green, debts in red

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/manager/page.tsx
git commit -m "feat: manager view uses ledger data, read-only"
```

---

### Task 8: Update Reports Page with Payment Summary

**Files:**
- Modify: `frontend/src/app/reports/page.tsx`

- [ ] **Step 1: Add payment summary to period reports**

After the allocation table, add a section showing:
- Total billed across selected period
- Total paid (sum of all ledger entries for runs in period)
- Total outstanding (sum of running balances)

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/reports/page.tsx
git commit -m "feat: reports page includes payment summary for period"
```

---

### Task 9: Data Migration + Cleanup

**Files:**
- Modify: `backend/core/history.py` (optional: deduplicate old month entries)

- [ ] **Step 1: Run migration endpoint**

Call `POST /api/payments/migrate` to convert old payments.json to ledger format.

- [ ] **Step 2: Verify migration**

Check that `backend/data/payment_ledger.json` contains migrated entries.
Check that `backend/data/payments.json` was renamed to `.bak`.

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest backend/tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Build frontend**

Run: `cd frontend && npm run build`
Expected: 0 errors

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: workflow redesign complete - preview/save/ledger"
```

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
    assert balance == 400


def test_running_balance_overpayment(tmp_ledger):
    runs = [
        {"id": "run_1", "year": 2026, "month": 3,
         "results": [{"company_id": "balkan", "total": 1000}]},
        {"id": "run_2", "year": 2026, "month": 4,
         "results": [{"company_id": "balkan", "total": 900}]},
    ]
    payments.add_payment("run_1", "balkan", 1200, "2026-03-15")
    balance = payments.get_running_balance("balkan", runs)
    assert balance == 700


def test_running_balance_credit_carryforward(tmp_ledger):
    runs = [
        {"id": "run_1", "year": 2026, "month": 3,
         "results": [{"company_id": "balkan", "total": 500}]},
    ]
    payments.add_payment("run_1", "balkan", 700, "2026-03-15")
    balance = payments.get_running_balance("balkan", runs)
    assert balance == -200


def test_get_payments_for_run(tmp_ledger):
    payments.add_payment("run_1", "balkan", 500, "2026-04-10")
    payments.add_payment("run_1", "gbcs", 300, "2026-04-10")
    payments.add_payment("run_2", "balkan", 100, "2026-05-10")
    run1_payments = payments.get_payments_for_run("run_1")
    assert len(run1_payments) == 2

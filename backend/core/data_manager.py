import json
import os
import threading

from backend.core.config import DATA_DIR
COMPANIES_FILE = os.path.join(DATA_DIR, "companies.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

_lock = threading.Lock()


def load_companies():
    with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
        companies = json.load(f)
    # Migrate: ensure ALL eligibility fields exist with sensible defaults.
    # Utility eligibility defaults to True (matches historical engine behavior),
    # service eligibility defaults to False (these are opt-in per company).
    for c in companies:
        c.setdefault("electricity_eligible", True)
        c.setdefault("water_eligible", True)
        c.setdefault("garbage_eligible", True)
        c.setdefault("has_heating", False)
        c.setdefault("consumables_eligible", False)
        c.setdefault("printer_eligible", False)
        c.setdefault("internet_eligible", False)
        c.setdefault("monthly_rent_eur", 0)
        c.setdefault("maintenance_rate_eur", 0)
    return companies


def _atomic_write(filepath, data):
    tmp = filepath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, filepath)


def save_companies(companies):
    with _lock:
        _atomic_write(COMPANIES_FILE, companies)


def load_settings():
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(settings):
    with _lock:
        _atomic_write(SETTINGS_FILE, settings)


def add_company(company):
    with _lock:
        companies = load_companies()
        # Re-validate uniqueness inside lock to prevent race condition
        cid = company["id"]
        cname = company["name"].strip().lower()
        if any(c["id"] == cid for c in companies):
            raise ValueError(f"Company ID '{cid}' already exists.")
        if any(c["name"].strip().lower() == cname for c in companies):
            raise ValueError(f"Company name '{company['name']}' already exists.")
        companies.append(company)
        _atomic_write(COMPANIES_FILE, companies)
        return companies


def update_company(company_id, updated_fields):
    with _lock:
        companies = load_companies()
        for c in companies:
            if c["id"] == company_id:
                c.update(updated_fields)
                break
        _atomic_write(COMPANIES_FILE, companies)
        return companies


def deactivate_company(company_id):
    return update_company(company_id, {"active": False})


def get_active_companies():
    return [c for c in load_companies() if c["active"]]

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
        c.setdefault("meeting_room_user", False)
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


_SETTINGS_DEFAULTS = {
    "ratios": {
        "electricity": {"sqm_weight": 50, "headcount_weight": 50},
        "gas": {"sqm_weight": 80, "headcount_weight": 20},
        "water": {"sqm_weight": 30, "headcount_weight": 70},
        "garbage": {"sqm_weight": 25, "headcount_weight": 75},
        "consumables": {"sqm_weight": 50, "headcount_weight": 50},
    },
    "eur_ron_rate": 5.1,
    "cost_categories": {},
    "hotel_sublet": {"active": False, "name": "", "percentage": 0, "applies_to": []},
    "meeting_room": {"active": False, "area_m2": 0, "floor": "first_floor"},
}


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        if not isinstance(settings, dict):
            return _SETTINGS_DEFAULTS.copy()
        # Fill in missing keys with defaults
        for key, default_val in _SETTINGS_DEFAULTS.items():
            settings.setdefault(key, default_val)
        # Ensure all required ratio types exist
        for ratio_key, ratio_default in _SETTINGS_DEFAULTS["ratios"].items():
            settings["ratios"].setdefault(ratio_key, ratio_default)
        return settings
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        return _SETTINGS_DEFAULTS.copy()


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

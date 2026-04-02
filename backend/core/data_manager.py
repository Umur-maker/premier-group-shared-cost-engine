import json
import os
import threading

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
COMPANIES_FILE = os.path.join(DATA_DIR, "companies.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

_lock = threading.Lock()


def load_companies():
    with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


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

"""Centralized data directory configuration.

Resolution order:
1. PREMIER_DATA_DIR environment variable (set by Electron)
2. %APPDATA%/PremierCostEngine/data (Windows desktop mode)
3. backend/data/ (development fallback)

On first run, seed files are copied from the bundled defaults.
"""

import os
import sys
import shutil

# Bundled default data (shipped with the app / in the repo)
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BUNDLED_DATA = os.path.join(_BACKEND_ROOT, "data")


def _resolve_data_dir() -> str:
    """Determine which data directory to use."""
    # 1. Explicit env var (Electron sets this)
    env = os.environ.get("PREMIER_DATA_DIR")
    if env:
        return env

    # 2. If bundled data dir exists and is writable (dev mode), use it directly
    if os.path.isdir(_BUNDLED_DATA):
        return _BUNDLED_DATA

    # 3. AppData fallback (should not normally reach here)
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    return os.path.join(appdata, "PremierCostEngine", "data")


DATA_DIR = _resolve_data_dir()


def ensure_data_dir():
    """Create data directory and seed default files if needed."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "history"), exist_ok=True)

    # Seed default files on first run
    for filename in ["companies.json", "settings.json"]:
        target = os.path.join(DATA_DIR, filename)
        source = os.path.join(_BUNDLED_DATA, filename)
        if not os.path.exists(target) and os.path.exists(source):
            shutil.copy2(source, target)

    # Seed empty history index
    history_index = os.path.join(DATA_DIR, "history", "index.json")
    if not os.path.exists(history_index):
        with open(history_index, "w", encoding="utf-8") as f:
            f.write("[]")

    # Seed empty payment ledger
    ledger = os.path.join(DATA_DIR, "payment_ledger.json")
    if not os.path.exists(ledger):
        with open(ledger, "w", encoding="utf-8") as f:
            f.write("[]")

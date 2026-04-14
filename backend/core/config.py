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
from datetime import datetime

# Bundled default data (shipped with the app / in the repo)
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED_DATA = os.path.join(_BACKEND_ROOT, "data-seed")
_DEV_DATA = os.path.join(_BACKEND_ROOT, "data")


def _resolve_data_dir() -> str:
    """Determine which data directory to use."""
    # 1. Explicit env var (Electron sets this)
    env = os.environ.get("PREMIER_DATA_DIR")
    if env:
        return env

    # 2. If running as PyInstaller bundle, always use platform-specific app data
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "PremierCostEngine", "data")
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(appdata, "PremierCostEngine", "data")

    # 3. Development mode — use local data dir if it exists
    if os.path.isdir(_DEV_DATA):
        return _DEV_DATA

    # 4. Platform-specific fallback
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "PremierCostEngine", "data")
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    return os.path.join(appdata, "PremierCostEngine", "data")


DATA_DIR = _resolve_data_dir()


BACKUP_DIR = os.path.join(os.path.dirname(DATA_DIR), "backups")
MAX_BACKUPS = 20


def _create_backup():
    """Snapshot current data to a timestamped backup folder. Keeps MAX_BACKUPS most recent."""
    if not os.path.isdir(DATA_DIR):
        return
    # Only backup if we have actual data
    companies_file = os.path.join(DATA_DIR, "companies.json")
    if not os.path.exists(companies_file):
        return
    try:
        with open(companies_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content in ("", "[]"):
            return  # don't backup empty data
    except Exception:
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    try:
        shutil.copytree(DATA_DIR, backup_path, dirs_exist_ok=True)
    except Exception as e:
        print(f"[config] Backup failed: {e}")
        return

    # Rotate: keep only the MAX_BACKUPS most recent
    try:
        entries = sorted([d for d in os.listdir(BACKUP_DIR) if d.startswith("backup_")])
        while len(entries) > MAX_BACKUPS:
            old = entries.pop(0)
            shutil.rmtree(os.path.join(BACKUP_DIR, old), ignore_errors=True)
    except Exception:
        pass


def _try_restore_from_backup():
    """If DATA_DIR is missing/empty but a backup exists, restore the most recent."""
    companies_file = os.path.join(DATA_DIR, "companies.json")
    # Check if we have actual usable data
    has_data = False
    if os.path.exists(companies_file):
        try:
            with open(companies_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content and content != "[]":
                has_data = True
        except Exception:
            pass

    if has_data:
        return  # data is fine

    # Look for backups
    if not os.path.isdir(BACKUP_DIR):
        return
    try:
        entries = sorted([d for d in os.listdir(BACKUP_DIR) if d.startswith("backup_")], reverse=True)
    except Exception:
        return

    for entry in entries:
        backup_path = os.path.join(BACKUP_DIR, entry)
        backup_companies = os.path.join(backup_path, "companies.json")
        if not os.path.exists(backup_companies):
            continue
        try:
            with open(backup_companies, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content or content == "[]":
                continue
        except Exception:
            continue

        # Restore this backup
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            for name in os.listdir(backup_path):
                src = os.path.join(backup_path, name)
                dst = os.path.join(DATA_DIR, name)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            print(f"[config] Restored data from backup: {entry}")
            return
        except Exception as e:
            print(f"[config] Restore failed: {e}")
            continue


def ensure_data_dir():
    """Create data directory, try recovery, seed defaults, create backup."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "history"), exist_ok=True)

    # Step 1: If data dir appears empty, try to restore from a recent backup
    _try_restore_from_backup()

    # Step 2: Seed default files only if still missing after restore attempt
    for filename in ["companies.json", "settings.json"]:
        target = os.path.join(DATA_DIR, filename)
        for source_dir in [_SEED_DATA, _DEV_DATA]:
            source = os.path.join(source_dir, filename)
            if not os.path.exists(target) and os.path.exists(source):
                shutil.copy2(source, target)
                break

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

    # Step 3: Create a backup of current data (post-restore, post-seed)
    _create_backup()

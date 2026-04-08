"""Entry point for PyInstaller-bundled backend server."""

import os
import sys

# When running as a PyInstaller bundle, fix the module path
if getattr(sys, "frozen", False):
    # Running as compiled executable
    bundle_dir = os.path.dirname(sys.executable)
    # Add the bundle directory to sys.path so imports work
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

import uvicorn


def main():
    port = int(os.environ.get("PREMIER_PORT", "8000"))
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()

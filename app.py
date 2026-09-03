"""Compatibility shim to allow running `uvicorn app.main:app` directly from repository root."""

import sys
from pathlib import Path

# Allow Python to treat 'app' as a package located at the repository root
__path__ = [str(Path(__file__).resolve().parent)]

# Pre-bind app.main to main.py so uvicorn app.main:app resolves cleanly
import main

sys.modules["app.main"] = main

# Re-export app instance for uvicorn app:app compatibility
app = main.app

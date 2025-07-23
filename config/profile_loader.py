# ── config/profile_loader.py ────────────────────────────────────────
"""
Tiny utility to load the user-specific JSON profile exactly once
"""

import json, pathlib

_PROFILE_FILE   = pathlib.Path("config/profile.json")
_PROFILE_CACHE  = None      # lazy-loaded singleton


def load_profile(path: pathlib.Path = _PROFILE_FILE) -> dict:
    """Return the cached profile dict, loading it on first call."""
    global _PROFILE_CACHE
    if _PROFILE_CACHE is None:
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as fh:
            _PROFILE_CACHE = json.load(fh)
    return _PROFILE_CACHE


def profile_field(key: str, default=None):
    prof = load_profile()          # None until the user creates a profile
    if prof is None:
        return default
    return prof.get(key, default)
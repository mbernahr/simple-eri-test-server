from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Dict, Optional

USERS_FILE = Path(__file__).resolve().parent / "users.json"

_lock = RLock()
_users_cache: Optional[Dict[str, str]] = None


def _load_users() -> Dict[str, str]:
    """Internal loader with simple cache."""
    global _users_cache
    if _users_cache is not None:
        return _users_cache

    if USERS_FILE.exists():
        try:
            data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _users_cache = {str(k): str(v) for k, v in data.items()}
            else:
                _users_cache = {}
        except Exception:
            _users_cache = {}
    else:
        _users_cache = {}

    return _users_cache


def _save_users(users: Dict[str, str]) -> None:
    """Write users to users.json."""
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def upsert_user(username: str, password: str) -> None:
    """Create user or update password."""
    with _lock:
        users = _load_users()
        users[username] = password
        _save_users(users)


def get_password(username: str) -> Optional[str]:
    """Return password for a user (or None)."""
    with _lock:
        users = _load_users()
        return users.get(username)


def list_users() -> Dict[str, str]:
    """All users (for debugging purposes only)."""
    with _lock:
        return dict(_load_users())

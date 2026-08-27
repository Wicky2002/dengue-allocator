"""One place to read config that must never be committed.

Shared by every module that talks to an external service (Supabase, an email
API, ...) so each one doesn't reinvent "Streamlit secrets, falling back to
the environment" -- and so a future secret-backed integration has an obvious
place to plug into rather than growing its own copy.
"""

from __future__ import annotations

import os


def get_secret(name: str) -> str | None:
    """Read a config value from Streamlit secrets first, then the environment.

    Importing streamlit lazily (not at module level) keeps this importable
    from a plain script -- a scheduled job, a one-off seeding script -- with
    no Streamlit runtime present. GitHub Actions and any other non-Streamlit
    caller reaches this exclusively through the environment-variable path.
    """
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name)

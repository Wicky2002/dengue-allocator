"""Real authentication, backed by Supabase.

Phase 2's role switcher was a labelled demo: "No authentication is
connected... not a login and is not a security control." This module is
what makes that sentence untrue. It authenticates a real Supabase account
and loads its role/district scope from a ``profiles`` table, then hands
back the exact same :class:`~dengue.platform.rbac.Principal` every portal
already enforces permissions and scope against. Nothing about
``Permission``/``filter_to_scope`` changes -- only where a ``Principal``
comes from.

Setup this depends on (see ``supabase/schema.sql``, not run automatically):

- A Supabase project, with a ``profiles`` table (schema in that file) and
  one row per account, created by an administrator -- there is no
  self-signup, since every non-public role here is scoped staff access,
  not a public account.
- ``SUPABASE_URL`` / ``SUPABASE_ANON_KEY`` available via Streamlit secrets
  (``.streamlit/secrets.toml`` locally, the Streamlit Cloud secrets manager
  when hosted) or plain environment variables.
"""

from __future__ import annotations

from dataclasses import dataclass

from dengue.platform.rbac import Principal, Role
from dengue.platform.secrets import get_secret
from dengue.utils.logging import get_logger

log = get_logger(__name__)


class AuthError(Exception):
    """Sign-in or profile-lookup failure. The message is safe to show a user directly."""


def _client():
    from supabase import create_client

    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise AuthError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY in "
            ".streamlit/secrets.toml (local) or the Streamlit Cloud secrets manager "
            "(hosted) -- see supabase/schema.sql for the rest of the setup."
        )
    return create_client(url, key)


@dataclass(frozen=True)
class Session:
    """An authenticated Supabase session, plus the Principal it resolves to."""

    user_id: str
    email: str
    access_token: str
    principal: Principal


def sign_in(email: str, password: str) -> Session:
    """Authenticate against Supabase and load the account's Principal.

    Raises :class:`AuthError` with a message safe to render directly in the
    login form on any failure: bad credentials, no matching profile row, an
    account with an invalid scope, or an unconfigured Supabase project.
    """
    if not email or not password:
        raise AuthError("Enter both an email and a password.")

    client = _client()
    try:
        result = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:
        log.warning("auth: sign-in failed for %s (%s)", email, exc)
        raise AuthError("Incorrect email or password.") from exc

    user = result.user
    if user is None or result.session is None:
        raise AuthError("Incorrect email or password.")

    principal = _load_principal(client, user.id, user.email or email)
    log.info("auth: %s signed in as %s", user.email or email, principal.role.value)
    return Session(
        user_id=user.id,
        email=user.email or email,
        access_token=result.session.access_token,
        principal=principal,
    )


def _load_principal(client, user_id: str, email: str) -> Principal:
    response = client.table("profiles").select("*").eq("id", user_id).limit(1).execute()
    rows = response.data or []
    if not rows:
        raise AuthError(
            f"No access profile is set up for {email}. Ask an administrator to "
            "create one (see supabase/schema.sql) before this account can log in."
        )
    row = rows[0]
    # `active` defaults true at the database level (see
    # supabase/account_management.sql) -- .get(..., True) only matters for a
    # project that hasn't run that migration yet, where the column doesn't
    # exist in the row at all.
    if not row.get("active", True):
        raise AuthError(
            f"Account {email} has been deactivated. Ask an administrator to "
            "reactivate it if this is unexpected."
        )

    try:
        role = Role(row["role"])
    except ValueError as exc:
        raise AuthError(f"Account {email} has an unrecognised role {row.get('role')!r}.") from exc

    districts = tuple(row.get("districts") or ())
    try:
        return Principal(
            role,
            row.get("display_name") or email,
            districts=districts,
            facility=row.get("facility") or "",
        )
    except ValueError as exc:
        # Principal.__post_init__ raises on a scoped-role account with no
        # districts, or an unknown district slug -- surface that as a
        # configuration problem rather than silently granting nationwide scope.
        raise AuthError(f"Account {email} is misconfigured: {exc}") from exc

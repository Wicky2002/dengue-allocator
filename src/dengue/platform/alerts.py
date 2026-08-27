"""Public email alerts: subscribe from the app, send from the weekly refresh.

Two halves, run in two different places, sharing one table
(``public.alert_subscriptions`` -- schema in ``supabase/schema.sql``):

- :func:`save_subscription` runs inside the Streamlit app (``app/portals.py``,
  the "Get alerts for your district" expander), using the public anon key.
  RLS grants that key insert-only access -- no read, update, or delete -- so
  a submitted address can never be enumerated or edited from the client.
- :func:`send_due_alerts` runs from the weekly GitHub Actions refresh
  (``.github/workflows/refresh-data.yml``), after ``make pipeline-real``
  regenerates ``district_risk.parquet``, using the service-role key (which
  bypasses RLS -- the same privilege the ``profiles`` table's own seeding
  already relies on). It is the one place in this codebase that computes
  from an artifact *and* has a side effect other than writing a file: the
  "never compute at request time" rule is about the interactive app, not an
  offline scheduled job with no user waiting on it.

What this can't do without one more piece of config
-----------------------------------------------------
Sending an actual email needs ``RESEND_API_KEY`` (a free account at
resend.com is enough to get one). Without it, :func:`send_due_alerts` logs a
warning and returns 0 -- subscriptions are still collected for real, they
just have nowhere to be delivered yet. That mirrors how the rest of this
platform degrades: a missing piece of config shows up as a stated gap, not a
crash or a silently fabricated success count.
"""

from __future__ import annotations

import argparse

import pandas as pd

from dengue import config
from dengue.platform.risk import RiskLevel, assess_all
from dengue.platform.secrets import get_secret
from dengue.utils.logging import get_logger

log = get_logger(__name__)

#: Below this, an "outbreak only" subscriber hears nothing.
OUTBREAK_THRESHOLD = RiskLevel.HIGH

#: Sender identity for Resend. Overridable via the ALERT_FROM_EMAIL secret
#: once a real domain is verified -- resend.dev's sandbox address works
#: unverified, but (per Resend's own sandbox restriction) can only actually
#: deliver to the account's own verified address, not to arbitrary
#: subscribers. That restriction lives on Resend's side, not in this code.
DEFAULT_FROM = "DengueSentinel <onboarding@resend.dev>"


class AlertError(Exception):
    """Subscription failure. The message is safe to show a user directly."""


def _anon_client():
    from supabase import create_client

    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise AlertError(
            "Alerts aren't configured yet. Set SUPABASE_URL and SUPABASE_ANON_KEY "
            "-- see supabase/schema.sql."
        )
    return create_client(url, key)


def _service_client():
    from supabase import create_client

    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise AlertError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set to send alerts "
            "(the service-role key, not the anon key -- it needs to read every "
            "subscriber's row, which RLS deliberately hides from the anon key)."
        )
    return create_client(url, key)


def save_subscription(
    email: str,
    districts: list[str],
    *,
    weekly_summary: bool = True,
    outbreak_only: bool = False,
) -> None:
    """Insert one subscription row. Raises :class:`AlertError` on any failure.

    Goes through the ``subscribe_to_alerts`` SECURITY DEFINER function (see
    ``supabase/schema.sql``) rather than a plain table insert -- a bare
    anon-key insert against an RLS INSERT policy has been observed failing
    with a false "violates row-level security policy" on some Supabase
    projects even when the policy is provably correct, which the function
    sidesteps by not depending on anon-role RLS resolution at all.

    Deliberately just an insert, never an upsert: there is no update path
    for a subscriber, so changing your preferences means subscribing again.
    :func:`fetch_active_subscriptions` takes the most recent row per email,
    so the newest submission wins.
    """
    email = (email or "").strip()
    if not email or "@" not in email:
        raise AlertError("Enter a valid email address.")
    if not districts:
        raise AlertError("Choose at least one district.")

    client = _anon_client()
    try:
        client.rpc(
            "subscribe_to_alerts",
            {
                "p_email": email,
                "p_districts": districts,
                "p_weekly_summary": weekly_summary,
                "p_outbreak_only": outbreak_only,
            },
        ).execute()
    except Exception as exc:
        log.warning("alerts: subscription insert failed for %s (%s)", email, exc)
        raise AlertError(
            "Could not save your subscription. Please try again shortly."
        ) from exc


def fetch_active_subscriptions() -> pd.DataFrame:
    """The latest subscription row per email, via the service-role key.

    Returns
    -------
    pandas.DataFrame
        Columns ``email``, ``districts`` (list[str]), ``weekly_summary``,
        ``outbreak_only``. Empty if the table has no rows or isn't reachable.
    """
    client = _service_client()
    response = client.table("alert_subscriptions").select("*").order("created_at").execute()
    rows = response.data or []
    if not rows:
        return pd.DataFrame(columns=["email", "districts", "weekly_summary", "outbreak_only"])

    frame = pd.DataFrame(rows)
    # `order("created_at")` is ascending, so the last row per email (via
    # keep="last") is the most recent submission -- exactly the "resubmitting
    # supersedes" semantics the insert-only table needs.
    return frame.drop_duplicates(subset="email", keep="last").reset_index(drop=True)


def _send_email(*, to: str, subject: str, html: str) -> bool:
    """POST one email via Resend's REST API. Returns whether it was sent."""
    api_key = get_secret("RESEND_API_KEY")
    if not api_key:
        log.warning("alerts: RESEND_API_KEY not set -- skipping send to %s", to)
        return False

    import httpx

    from_addr = get_secret("ALERT_FROM_EMAIL") or DEFAULT_FROM
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"from": from_addr, "to": [to], "subject": subject, "html": html},
            timeout=15.0,
        )
        response.raise_for_status()
        return True
    except Exception as exc:
        log.error("alerts: send to %s failed: %s", to, exc)
        return False


def _render_email(district_names: list[str], assessment_by_name: dict) -> str:
    """Plain, dependency-free HTML -- one row per subscribed district."""
    rows = []
    for name in district_names:
        a = assessment_by_name.get(name)
        if a is None:
            continue
        rows.append(
            f"<tr><td>{name}</td><td>{a.risk_level.label}</td>"
            f"<td>{a.forecast_median:.0f} cases</td>"
            f"<td>{a.change_pct:+.0f}% vs recent weeks</td></tr>"
        )
    table = "<table cellpadding='6'>" + "".join(rows) + "</table>"
    return (
        "<p>Your DengueSentinel update for this week:</p>"
        f"{table}"
        "<p style='color:#666;font-size:12px'>You're receiving this because you "
        "subscribed at the DengueSentinel public portal. Real WER/Open-Meteo data, "
        "refreshed weekly -- see the National administrator portal's Data sources "
        "for full provenance.</p>"
    )


def send_due_alerts(district_risk: pd.DataFrame, *, horizon_weeks: int = 2) -> int:
    """Send every subscriber their due alert. Returns how many were sent.

    "Due" means: a ``weekly_summary`` subscriber always gets one; an
    ``outbreak_only`` subscriber gets one only if at least one of their
    chosen districts is at :data:`OUTBREAK_THRESHOLD` or above this week.
    """
    subscriptions = fetch_active_subscriptions()
    if subscriptions.empty:
        log.info("alerts: no subscriptions to send")
        return 0

    assessments = assess_all(district_risk, horizon_weeks=horizon_weeks, audience="public")
    by_name = {a.district_name: a for a in assessments}

    sent = 0
    for _, sub in subscriptions.iterrows():
        district_ids = list(sub["districts"] or [])
        names = [
            config.get_district(d).name if d in config.DISTRICT_BY_ID else d
            for d in district_ids
        ]
        chosen = [by_name[n] for n in names if n in by_name]
        if not chosen:
            continue

        is_outbreak = any(a.risk_level.rank >= OUTBREAK_THRESHOLD.rank for a in chosen)
        due = bool(sub.get("weekly_summary")) or (bool(sub.get("outbreak_only")) and is_outbreak)
        if not due:
            continue

        subject = (
            "Dengue outbreak warning for your district"
            if is_outbreak and sub.get("outbreak_only")
            else "Your weekly DengueSentinel update"
        )
        html = _render_email(names, by_name)
        if _send_email(to=sub["email"], subject=subject, html=html):
            sent += 1

    log.info("alerts: sent %d of %d subscriptions", sent, len(subscriptions))
    return sent


def main(argv: list[str] | None = None) -> int:
    """Send this week's alerts. Reads ``artifacts/district_risk.parquet``."""
    parser = argparse.ArgumentParser(description="Send due DengueSentinel email alerts.")
    parser.add_argument(
        "--horizon", type=int, default=min(config.HORIZONS), help="Forecast horizon to alert on."
    )
    args = parser.parse_args(argv)

    path = config.ARTIFACTS_DIR / "district_risk.parquet"
    if not path.exists():
        log.warning("alerts: no district_risk.parquet at %s -- run the pipeline first", path)
        return 0

    district_risk = pd.read_parquet(path)
    try:
        return send_due_alerts(district_risk, horizon_weeks=args.horizon)
    except AlertError as exc:
        # A scheduled job with no one watching it run should degrade the
        # same way the interactive app does: a missing secret is a stated
        # gap in the log, not a failed CI run that pages someone at 3am.
        log.warning("alerts: %s", exc)
        return 0


if __name__ == "__main__":
    main()

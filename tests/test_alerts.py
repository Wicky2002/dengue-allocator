"""Tests for dengue.platform.alerts -- no real Supabase or Resend calls.

Every Supabase/Resend touchpoint is monkeypatched at the module's own private
client functions (``_anon_client``, ``_service_client``, ``_send_email``), the
same boundary the real code calls through -- so these tests exercise the
actual validation, dedup, and "who is due an alert" logic, not a reimplementation
of it.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dengue import config
from dengue.platform.alerts import (
    AlertError,
    fetch_active_subscriptions,
    save_subscription,
    send_due_alerts,
)


def _fake_district_risk() -> pd.DataFrame:
    ids = list(config.DISTRICT_IDS[:6])
    return pd.DataFrame(
        {
            "district_id": ids,
            "horizon": 2,
            "q0.1": [10, 20, 5, 2, 1, 0],
            "q0.5": [400, 200, 50, 20, 5, 1],
            "q0.9": [800, 400, 90, 40, 12, 4],
            "incidence_per_100k": [20.0, 9.0, 4.0, 1.0, 0.4, 0.1],
            "change_vs_recent_pct": [45.0, 10.0, -5.0, 0.0, 2.0, 0.0],
            "target_week": pd.Period("2026-08-03", freq=config.WEEK_FREQ),
        }
    )


# ---------------------------------------------------------------------
# save_subscription
# ---------------------------------------------------------------------


def test_save_subscription_rejects_missing_email():
    with pytest.raises(AlertError, match="valid email"):
        save_subscription("", [config.DISTRICT_IDS[0]])


def test_save_subscription_rejects_no_districts():
    with pytest.raises(AlertError, match="district"):
        save_subscription("a@example.com", [])


def test_save_subscription_inserts_expected_row(monkeypatch):
    calls = []

    class FakeRpc:
        def execute(self):
            return None

    class FakeClient:
        def rpc(self, name, params):
            assert name == "subscribe_to_alerts"
            calls.append(params)
            return FakeRpc()

    monkeypatch.setattr("dengue.platform.alerts._anon_client", lambda: FakeClient())

    save_subscription(
        "  a@example.com  ",
        ["colombo"],
        weekly_summary=False,
        outbreak_only=True,
    )

    assert calls == [
        {
            "p_email": "a@example.com",
            "p_districts": ["colombo"],
            "p_weekly_summary": False,
            "p_outbreak_only": True,
        }
    ]


def test_save_subscription_wraps_client_errors(monkeypatch):
    class FailingClient:
        def rpc(self, name, params):
            raise RuntimeError("network down")

    monkeypatch.setattr("dengue.platform.alerts._anon_client", lambda: FailingClient())

    with pytest.raises(AlertError, match="Could not save"):
        save_subscription("a@example.com", ["colombo"])


# ---------------------------------------------------------------------
# fetch_active_subscriptions
# ---------------------------------------------------------------------


def test_fetch_active_subscriptions_keeps_latest_per_email(monkeypatch):
    rows = [
        {
            "email": "a@example.com",
            "districts": ["colombo"],
            "weekly_summary": True,
            "outbreak_only": False,
            "created_at": "2026-01-01T00:00:00Z",
        },
        {
            "email": "a@example.com",
            "districts": ["gampaha"],
            "weekly_summary": False,
            "outbreak_only": True,
            "created_at": "2026-02-01T00:00:00Z",
        },
        {
            "email": "b@example.com",
            "districts": ["mannar"],
            "weekly_summary": True,
            "outbreak_only": False,
            "created_at": "2026-01-15T00:00:00Z",
        },
    ]

    class FakeResponse:
        data = rows

    class FakeQuery:
        def select(self, _):
            return self

        def order(self, _):
            return self

        def execute(self):
            return FakeResponse()

    class FakeClient:
        def table(self, name):
            assert name == "alert_subscriptions"
            return FakeQuery()

    monkeypatch.setattr("dengue.platform.alerts._service_client", lambda: FakeClient())

    result = fetch_active_subscriptions()
    assert sorted(result["email"]) == ["a@example.com", "b@example.com"]
    a_row = result[result["email"] == "a@example.com"].iloc[0]
    assert a_row["districts"] == ["gampaha"]  # the later of the two rows, not the first
    assert bool(a_row["outbreak_only"]) is True


def test_fetch_active_subscriptions_empty_table(monkeypatch):
    class FakeResponse:
        data = []

    class FakeQuery:
        def select(self, _):
            return self

        def order(self, _):
            return self

        def execute(self):
            return FakeResponse()

    class FakeClient:
        def table(self, name):
            return FakeQuery()

    monkeypatch.setattr("dengue.platform.alerts._service_client", lambda: FakeClient())

    result = fetch_active_subscriptions()
    assert result.empty


# ---------------------------------------------------------------------
# send_due_alerts
# ---------------------------------------------------------------------


def test_send_due_alerts_sends_weekly_and_gates_outbreak_only(monkeypatch):
    district_risk = _fake_district_risk()
    names = {d: config.get_district(d).name for d in district_risk["district_id"]}
    high_risk_name = names[district_risk.iloc[0]["district_id"]]  # incidence 20.0 -> severe
    low_risk_name = names[district_risk.iloc[-1]["district_id"]]  # incidence 0.1 -> low
    high_risk_id = district_risk.iloc[0]["district_id"]
    low_risk_id = district_risk.iloc[-1]["district_id"]

    subs = pd.DataFrame(
        [
            # Weekly subscriber to a low-risk district -- still due every week.
            {
                "email": "weekly@example.com",
                "districts": [low_risk_id],
                "weekly_summary": True,
                "outbreak_only": False,
            },
            # Outbreak-only subscriber to the same low-risk district -- not due.
            {
                "email": "quiet@example.com",
                "districts": [low_risk_id],
                "weekly_summary": False,
                "outbreak_only": True,
            },
            # Outbreak-only subscriber to the high-risk district -- due.
            {
                "email": "urgent@example.com",
                "districts": [high_risk_id],
                "weekly_summary": False,
                "outbreak_only": True,
            },
        ]
    )
    monkeypatch.setattr("dengue.platform.alerts.fetch_active_subscriptions", lambda: subs)

    sent_to = []
    monkeypatch.setattr(
        "dengue.platform.alerts._send_email",
        lambda *, to, subject, html: sent_to.append((to, subject)) or True,
    )

    sent = send_due_alerts(district_risk, horizon_weeks=2)

    assert sent == 2
    recipients = {to for to, _ in sent_to}
    assert recipients == {"weekly@example.com", "urgent@example.com"}
    assert high_risk_name and low_risk_name  # sanity: names actually resolved


def test_send_due_alerts_skips_unknown_districts(monkeypatch):
    district_risk = _fake_district_risk()
    subs = pd.DataFrame(
        [
            {
                "email": "ghost@example.com",
                "districts": ["not_a_real_district"],
                "weekly_summary": True,
                "outbreak_only": False,
            }
        ]
    )
    monkeypatch.setattr("dengue.platform.alerts.fetch_active_subscriptions", lambda: subs)
    monkeypatch.setattr(
        "dengue.platform.alerts._send_email", lambda **_: pytest.fail("should not be called")
    )

    assert send_due_alerts(district_risk, horizon_weeks=2) == 0


def test_send_due_alerts_no_subscriptions(monkeypatch):
    monkeypatch.setattr(
        "dengue.platform.alerts.fetch_active_subscriptions",
        lambda: pd.DataFrame(columns=["email", "districts", "weekly_summary", "outbreak_only"]),
    )
    assert send_due_alerts(_fake_district_risk(), horizon_weeks=2) == 0


# ---------------------------------------------------------------------
# _send_email
# ---------------------------------------------------------------------


def test_send_email_skips_without_api_key(monkeypatch):
    from dengue.platform.alerts import _send_email

    monkeypatch.setattr("dengue.platform.alerts.get_secret", lambda name: None)
    assert _send_email(to="a@example.com", subject="hi", html="<p>hi</p>") is False

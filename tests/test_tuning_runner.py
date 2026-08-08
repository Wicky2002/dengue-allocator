"""Runner-level tests: persistence helpers (fast) and one real end-to-end
CLI invocation (slow -- the first real use of the `slow` marker, see the
Makefile's `test` target).
"""

from __future__ import annotations

import json

import pytest

from dengue.tuning.runner import _write_entry, load_tuned_params, main


def test_load_tuned_params_returns_none_for_a_missing_file(tmp_path):
    assert load_tuned_params("lgbm_quantile", path=tmp_path / "missing.json") is None


def test_load_tuned_params_returns_none_for_malformed_json(tmp_path):
    path = tmp_path / "tuned.json"
    path.write_text("{not valid json", encoding="utf-8")
    assert load_tuned_params("lgbm_quantile", path=path) is None


def test_load_tuned_params_returns_none_for_an_absent_model_key(tmp_path):
    path = tmp_path / "tuned.json"
    path.write_text(json.dumps({"other_model": {"params": {}}}), encoding="utf-8")
    assert load_tuned_params("lgbm_quantile", path=path) is None


def test_write_entry_then_load_round_trips(tmp_path):
    path = tmp_path / "tuned.json"
    _write_entry("lgbm_quantile", {"params": {"n_estimators": 77}}, path=path)

    loaded = load_tuned_params("lgbm_quantile", path=path)
    assert loaded == {"params": {"n_estimators": 77}}


def test_write_entry_merges_rather_than_clobbers_other_models(tmp_path):
    path = tmp_path / "tuned.json"
    _write_entry("lgbm_quantile", {"params": {"n_estimators": 77}}, path=path)
    _write_entry("ensemble", {"weights": {"w_naive": 1.0}}, path=path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(payload) == {"lgbm_quantile", "ensemble"}
    assert payload["lgbm_quantile"]["params"]["n_estimators"] == 77


@pytest.mark.slow
def test_tuning_runner_end_to_end_writes_a_confirmed_result(tmp_path):
    """Tiny population/generations, synthetic panel, `tmp_path` output --
    exercises the full CLI wiring (LGBM search, val/test confirmation,
    ensemble search) without the ~30 min budget of a real `make tune`."""
    out_path = tmp_path / "tuned_hyperparams.json"

    main(
        [
            "--synthetic",
            "--n-weeks",
            "150",
            "--population",
            "3",
            "--generations",
            "2",
            "--elitism",
            "1",
            "--tournament-size",
            "2",
            "--search-origins",
            "2",
            "--search-stride",
            "4",
            "--max-minutes",
            "2",
            "--ensemble-population",
            "6",
            "--ensemble-generations",
            "2",
            "--out",
            str(out_path),
        ]
    )

    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))

    assert "lgbm_quantile" in payload
    lgbm_entry = payload["lgbm_quantile"]
    assert "params" in lgbm_entry
    assert set(lgbm_entry["confirmation"]) == {"val", "test"}
    for fold_scores in lgbm_entry["confirmation"].values():
        assert "pinball_mean" in fold_scores

    assert "ensemble" in payload
    weights = payload["ensemble"]["weights"]
    assert set(weights) == {"w_naive", "w_sarima", "w_lgbm"}
    assert sum(weights.values()) == pytest.approx(1.0)

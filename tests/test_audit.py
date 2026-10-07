from __future__ import annotations

import pandas as pd

from averted.audit import run_audit
from averted.causal.data import LogSpec, prepare


def test_prepare_drops_due_rows_and_unobserved_outcomes(tiny):
    fr = prepare(tiny.log)
    assert len(fr) == int((tiny.log["y"].notna() & ~tiny.log["due"]).sum())
    assert not set(fr.T.tolist()) - {0, 1}


def test_audit_report_structure(tiny):
    rep = run_audit(tiny.log, n_folds=3, with_sensitivity=False)
    assert set(rep["estimates"]) == {"naive", "regression", "ipw", "aipw"}
    assert rep["verdict"]["level"] in {"green", "yellow", "red"}
    assert rep["data"]["rows_analyzed"] + rep["data"]["rows_excluded_due"] == rep["data"]["rows_with_outcome"]
    ov = rep["overlap"]
    assert abs(sum(ov["hist_treated"]) - ov["n_treated"]) <= 1
    assert "subgroups" in rep and rep["subgroups"]["cat"]


def test_audit_runs_on_a_log_with_other_column_names(tiny):
    """실제 로그처럼 열 이름이 다를 때 LogSpec 으로 매핑하면 같은 코드가 돈다."""
    renamed = tiny.log.rename(columns={"asset": "설비", "week": "주", "treated": "점검", "y": "고장"}).copy()
    spec = LogSpec(unit="설비", time="주", treatment="점검", outcome="고장", prior_outcome=None)
    rep = run_audit(renamed, spec=spec, n_folds=3, with_sensitivity=False)
    assert rep["estimates"]["aipw"]["averted"] == rep["estimates"]["aipw"]["averted"]


def test_missing_columns_are_reported_clearly(tiny):
    broken = tiny.log.drop(columns=["cmp"])
    try:
        run_audit(broken)
    except ValueError as e:
        assert "cmp" in str(e)
    else:
        raise AssertionError("열이 없으면 ValueError 여야 한다")


def test_treatment_must_be_binary(tiny):
    bad = tiny.log.copy()
    bad.loc[bad.index[:5], "treated"] = 3
    try:
        prepare(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("처치가 0/1 이 아니면 거부해야 한다")


def test_pandas_frame_is_not_mutated(tiny):
    before = tiny.log.copy()
    run_audit(tiny.log, n_folds=3, with_sensitivity=False)
    pd.testing.assert_frame_equal(before, tiny.log)

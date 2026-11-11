"""Tests for the parts where a silent bug would change the conclusion."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from muashir import build, eventstudy, score


def test_leave_one_out_market_excludes_own_return():
    idx = pd.date_range("2024-01-01", periods=3)
    cols = [f"T{i}" for i in range(12)]
    ret = pd.DataFrame(0.01, index=idx, columns=cols)
    ret["T0"] = 0.50                                   # an outlier must not leak into its own benchmark
    mkt = eventstudy.leave_one_out_market(ret)
    assert mkt["T0"].iloc[0] == pytest.approx(0.01)
    assert mkt["T1"].iloc[0] == pytest.approx((0.50 + 0.01 * 10) / 11)


def test_leave_one_out_market_needs_enough_members():
    ret = pd.DataFrame(0.01, index=pd.date_range("2024-01-01", periods=2), columns=list("ABCDE"))
    assert eventstudy.leave_one_out_market(ret).isna().all().all()


def test_market_model_recovers_alpha_and_beta():
    rng = np.random.default_rng(0)
    rm = rng.normal(0, 0.01, 220)
    ri = 0.0005 + 1.3 * rm + rng.normal(0, 0.0005, 220)
    alpha, beta, _ = eventstudy.market_model(ri, rm)
    assert beta == pytest.approx(1.3, abs=0.02)
    assert alpha == pytest.approx(0.0005, abs=0.0002)


def test_market_model_refuses_short_history():
    assert eventstudy.market_model(np.zeros(50), np.zeros(50)) is None


def test_percentile_uses_only_earlier_announcements():
    n = 100
    ev = pd.DataFrame({"day0": pd.date_range("2020-01-01", periods=n, freq="D"), "x": np.arange(n, dtype=float)})
    base = score.trailing_percentile(ev, "x")
    # changing a later value must not change any earlier percentile
    ev2 = ev.copy()
    ev2.loc[n - 1, "x"] = -1e9
    changed = score.trailing_percentile(ev2, "x")
    pd.testing.assert_series_equal(base.iloc[: n - 1], changed.iloc[: n - 1])
    # an ever-rising series is always above everything before it
    assert base.dropna().eq(100.0).all()
    assert base.iloc[: score.MIN_REFERENCE].isna().all()


def test_same_day_announcements_do_not_reference_each_other():
    days = pd.to_datetime(["2020-01-01"] * 70 + ["2020-06-01"] * 2)
    ev = pd.DataFrame({"day0": days, "x": [0.0] * 70 + [5.0, 9.0]})
    p = score.trailing_percentile(ev, "x")
    assert p.iloc[70] == 100.0 and p.iloc[71] == 100.0   # 9.0 is not ranked against the same-day 5.0


def test_split_mismatch_is_corrected_only_near_the_split():
    ev = pd.DataFrame({
        "announced_at": pd.to_datetime(["2022-02-20", "2022-05-10", "2022-08-04"]).tz_localize("Asia/Riyadh"),
        "eps_estimate": [0.65, 0.67, 0.68],
        "eps_reported": [0.67, 1.10, 1.09],            # 2nd is a 1.6x share-count mismatch; 3rd is a real beat far from the split
    })
    splits = pd.DataFrame({"date": pd.to_datetime(["2022-05-09"]), "stock_splits": [1.6]})
    out = build.fix_split_mismatch(ev, splits)
    assert out["eps_split_fixed"].tolist() == [0, 1, 0]
    assert out["eps_reported"].iloc[1] == pytest.approx(1.10 / 1.6)
    assert out["eps_source"].iloc[1] == 1.10
    assert out["eps_reported"].iloc[2] == 1.09


def test_lag_requires_a_real_quarter_gap():
    ev = pd.DataFrame({
        "ticker": ["A"] * 3,
        "day0": pd.to_datetime(["2020-01-01", "2020-04-01", "2021-06-01"]),   # third is 14 months later
        "eps_reported": [1.0, 2.0, 3.0],
    })
    lag1 = score._lag(ev, 1, 50, 135)
    assert np.isnan(lag1.iloc[0]) and lag1.iloc[1] == 1.0 and np.isnan(lag1.iloc[2])

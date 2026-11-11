"""Point-in-time Muashir score.

Every input is known at the announcement (prices are taken two sessions before
it), and every percentile is taken against announcements that came strictly
earlier, so the score for an event never uses information from its own future.

The seven components mirror the criteria of the original Muashir site. Two of
them had to be replaced by a measurable proxy because the free source has no
quarterly revenue history and "geopolitical independence" was a judgement call:

    site criterion               component here
    --------------------------   ------------------------------------------------
    net income growth (YoY)      yoy          change in EPS vs same quarter last year / price
    quarter-on-quarter trend     qoq          change in EPS vs previous quarter / price
    revenue growth               surprise     EPS minus analyst estimate / price   (proxy)
    earnings quality             consistency  share of last 4 quarters with YoY growth
    P/E                          earn_yield   trailing-12-month EPS / price
    dividend yield               div_yield    dividends paid in last 365 days / price
    geopolitical independence    low_beta     minus the market beta                (proxy)

Weights are equal and fixed in advance; nothing is fitted to returns.
"""
from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd

COMPONENTS = ["yoy", "qoq", "surprise", "consistency", "earn_yield", "div_yield", "low_beta"]
REFERENCE_DAYS = 730
MIN_REFERENCE = 60
MIN_COMPONENTS = 4


def _lag(ev: pd.DataFrame, k: int, min_gap: int, max_gap: int) -> pd.Series:
    """EPS k announcements back, only if it really is k quarters back."""
    g = ev.groupby("ticker")
    eps = g["eps_reported"].shift(k)
    gap = (ev["day0"] - g["day0"].shift(k)).dt.days
    return eps.where(gap.between(min_gap, max_gap))


def build_features(con: sqlite3.Connection, info: pd.DataFrame) -> pd.DataFrame:
    ev = pd.read_sql("SELECT event_id, ticker, eps_estimate, eps_reported FROM events", con)
    ev = ev.merge(info, on="event_id", how="inner").sort_values(["ticker", "day0"]).reset_index(drop=True)
    price = ev["price_ref"]

    lag1 = _lag(ev, 1, 50, 135)
    lag4 = _lag(ev, 4, 300, 430)
    ev["yoy"] = (ev["eps_reported"] - lag4) / price
    ev["qoq"] = (ev["eps_reported"] - lag1) / price
    ev["surprise"] = (ev["eps_reported"] - ev["eps_estimate"]) / price

    improved = (ev["eps_reported"] > lag4).where(lag4.notna()).astype(float)
    ev["consistency"] = (
        improved.groupby(ev["ticker"]).rolling(4, min_periods=4).mean().reset_index(level=0, drop=True)
    )

    g = ev.groupby("ticker")
    ttm = g["eps_reported"].rolling(4, min_periods=4).sum().reset_index(level=0, drop=True)
    span = (ev["day0"] - g["day0"].shift(3)).dt.days
    ev["earn_yield"] = ttm.where(span.between(240, 330)) / price

    div = pd.read_sql("SELECT ticker, date, dividends FROM prices WHERE dividends > 0", con, parse_dates=["date"])
    div_by_ticker = {t: d.set_index("date")["dividends"] for t, d in div.groupby("ticker")}
    paid = []
    for r in ev.itertuples(index=False):
        d = div_by_ticker.get(r.ticker)
        if d is None:
            paid.append(0.0)
            continue
        paid.append(float(d[(d.index < r.day0) & (d.index >= r.day0 - pd.Timedelta(days=365))].sum()))
    ev["div_yield"] = np.array(paid) / price

    ev["low_beta"] = -ev["beta"]
    return ev


def trailing_percentile(ev: pd.DataFrame, col: str) -> pd.Series:
    """Percentile (0-100) of each value among announcements in the prior two years."""
    out = pd.Series(np.nan, index=ev.index)
    days = ev["day0"].to_numpy()
    vals = ev[col].to_numpy(dtype=float)
    order = np.argsort(days, kind="stable")
    days_s, vals_s = days[order], vals[order]
    for j, i in enumerate(order):
        if np.isnan(vals[i]):
            continue
        start = np.searchsorted(days_s, days[i] - np.timedelta64(REFERENCE_DAYS, "D"), side="left")
        end = np.searchsorted(days_s, days[i], side="left")       # strictly earlier days only
        ref = vals_s[start:end]
        ref = ref[~np.isnan(ref)]
        if len(ref) < MIN_REFERENCE:
            continue
        out.iloc[i] = 100.0 * ((ref < vals[i]).sum() + 0.5 * (ref == vals[i]).sum()) / len(ref)
    return out


def add_score(ev: pd.DataFrame) -> pd.DataFrame:
    ev = ev.copy()
    pct_cols = []
    for c in COMPONENTS:
        ev[f"p_{c}"] = trailing_percentile(ev, c)
        pct_cols.append(f"p_{c}")
    n = ev[pct_cols].notna().sum(axis=1)
    ev["n_components"] = n
    ev["score"] = ev[pct_cols].mean(axis=1).where(n >= MIN_COMPONENTS)
    return ev

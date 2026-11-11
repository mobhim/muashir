"""Event study: abnormal returns around each earnings announcement.

Market benchmark
    The TASI index history is not available from the free source, so the market
    return is an equal-weighted average of the *other* stocks in the universe
    (leave-one-out, so a stock never benchmarks against itself).

Abnormal return
    Market model: AR_t = r_it - (alpha_i + beta_i * r_mt), with alpha/beta
    estimated on trading days [-250, -31] before the event. Two alternatives
    are kept as robustness checks because the choice matters for long windows:
    market-adjusted (r_it - r_mt) and beta-adjusted without alpha
    (r_it - beta_i * r_mt). Subtracting last year's alpha penalises stocks that
    have been doing well, which is exactly what a high score selects.
"""
from __future__ import annotations

import logging
import sqlite3

import numpy as np
import pandas as pd

from . import config

log = logging.getLogger("muashir.eventstudy")


def load_returns(con: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame]:
    px = pd.read_sql("SELECT ticker, date, close, ret FROM prices", con, parse_dates=["date"])
    ret = px.pivot(index="date", columns="ticker", values="ret").sort_index()
    close = px.pivot(index="date", columns="ticker", values="close").sort_index()
    # the trading calendar = days on which enough stocks actually traded
    live = ret.notna().sum(axis=1) > config.MIN_PROXY_MEMBERS
    return ret[live], close[live].ffill()


def leave_one_out_market(ret: pd.DataFrame) -> pd.DataFrame:
    """Equal-weighted mean return of all other stocks, per stock per day."""
    total = ret.sum(axis=1, skipna=True)
    count = ret.notna().sum(axis=1)
    own = ret.fillna(0.0)
    own_present = ret.notna().astype(int)
    others_n = (-own_present).add(count, axis=0)
    mkt = (-own).add(total, axis=0) / others_n.where(others_n >= config.MIN_PROXY_MEMBERS)
    return mkt


def market_model(ri: np.ndarray, rm: np.ndarray) -> tuple[float, float, float] | None:
    ok = ~(np.isnan(ri) | np.isnan(rm))
    if ok.sum() < config.MIN_ESTIMATION_OBS:
        return None
    x, y = rm[ok], ri[ok]
    beta = np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)
    alpha = y.mean() - beta * x.mean()
    resid_sd = np.std(y - (alpha + beta * x), ddof=2)
    return float(alpha), float(beta), float(resid_sd)


def run(con: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns (per-event info, per-event-per-window abnormal returns, daily AR paths)."""
    ret, close = load_returns(con)
    mkt = leave_one_out_market(ret)
    cal = ret.index
    events = pd.read_sql("SELECT event_id, ticker, react_date FROM events", con, parse_dates=["react_date"])

    lo = min(config.ESTIMATION_WINDOW[0], min(w[0] for w in config.WINDOWS.values()))
    hi = max(w[1] for w in config.WINDOWS.values())
    path_lo, path_hi = config.WINDOWS["pre"][0], hi

    info_rows, win_rows, path_rows = [], [], []
    for ev in events.itertuples(index=False):
        pos = cal.searchsorted(ev.react_date)        # first trading day >= react_date
        if pos >= len(cal) or (cal[pos] - ev.react_date).days > 7 or pos + lo < 0:
            continue
        ri_all = ret[ev.ticker].to_numpy()
        rm_all = mkt[ev.ticker].to_numpy()
        e0, e1 = pos + config.ESTIMATION_WINDOW[0], pos + config.ESTIMATION_WINDOW[1] + 1
        mm = market_model(ri_all[e0:e1], rm_all[e0:e1])
        if mm is None:
            continue
        alpha, beta, resid_sd = mm
        info_rows.append({
            "event_id": ev.event_id, "day0": cal[pos], "alpha": alpha, "beta": beta, "resid_sd": resid_sd,
            "price_ref": close[ev.ticker].iat[pos - 2],   # last price clearly before the news
        })

        for name, (a, b) in config.WINDOWS.items():
            s, e = pos + a, pos + b + 1
            if e > len(cal):
                continue                                  # window not complete yet
            ri, rm = ri_all[s:e], rm_all[s:e]
            ok = ~(np.isnan(ri) | np.isnan(rm))
            if ok.mean() < 0.8:
                continue
            ar = ri[ok] - (alpha + beta * rm[ok])
            win_rows.append({
                "event_id": ev.event_id, "window": name, "n_days": int(ok.sum()),
                "car_mm": float(ar.sum()),
                "car_ma": float((ri[ok] - rm[ok]).sum()),
                "car_beta": float((ri[ok] - beta * rm[ok]).sum()),   # beta-adjusted, no alpha

                "raw_ret": float(np.prod(1 + ri[ok]) - 1),
                "mkt_ret": float(np.prod(1 + rm[ok]) - 1),
                "mkt_part": float((beta * rm[ok]).sum()),  # share of the move explained by the market
            })

        s, e = pos + path_lo, pos + path_hi + 1
        if e <= len(cal):
            ar = ri_all[s:e] - (alpha + beta * rm_all[s:e])
            for k, v in zip(range(path_lo, path_hi + 1), ar):
                path_rows.append((ev.event_id, k, v))

    info = pd.DataFrame(info_rows)
    wins = pd.DataFrame(win_rows)
    paths = pd.DataFrame(path_rows, columns=["event_id", "rel_day", "ar"])
    log.info("event study: %d of %d events usable, %d window rows", len(info), len(events), len(wins))
    return info, wins, paths

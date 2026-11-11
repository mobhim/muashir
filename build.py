"""Clean the raw files and load them into SQLite (companies, prices, events)."""
from __future__ import annotations

import logging
import sqlite3

import numpy as np
import pandas as pd

from . import config
from .fetch import load_universe

log = logging.getLogger("muashir.build")

MAX_ABS_DAILY_RETURN = 0.31   # Tadawul limit is 10% (30% on listing days); beyond this is a data error
SPLIT_FIX_WINDOW_DAYS = 45
SPLIT_FIX_MIN_RATIO = 1.2
SPLIT_FIX_TOLERANCE = 0.12

DDL = """
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS prices;
DROP TABLE IF EXISTS events;
CREATE TABLE companies (
    ticker    TEXT PRIMARY KEY,
    name_ar   TEXT NOT NULL,
    sector_ar TEXT NOT NULL
);
CREATE TABLE prices (
    ticker       TEXT NOT NULL REFERENCES companies(ticker),
    date         TEXT NOT NULL,
    close        REAL NOT NULL,
    adj_close    REAL NOT NULL,
    volume       REAL,
    dividends    REAL NOT NULL DEFAULT 0,
    stock_splits REAL NOT NULL DEFAULT 0,
    ret          REAL,
    PRIMARY KEY (ticker, date)
);
CREATE TABLE events (
    event_id        INTEGER PRIMARY KEY,
    ticker          TEXT NOT NULL REFERENCES companies(ticker),
    announced_at    TEXT NOT NULL,   -- Riyadh local time, hour precision (as given by source)
    react_date      TEXT NOT NULL,   -- first calendar date on which the market could react
    eps_estimate    REAL,
    eps_reported    REAL NOT NULL,   -- after split correction, see eps_split_fixed
    eps_source      REAL NOT NULL,   -- exactly as downloaded
    eps_split_fixed INTEGER NOT NULL DEFAULT 0,
    UNIQUE (ticker, react_date)
);
CREATE INDEX idx_events_ticker ON events(ticker, announced_at);
"""


def clean_prices(ticker: str) -> pd.DataFrame:
    p = pd.read_csv(config.RAW_DIR / f"{ticker}_prices.csv", parse_dates=["date"])
    p = p[(p["close"] > 0) & (p["adj_close"] > 0)].drop_duplicates("date").sort_values("date")
    p["ret"] = p["adj_close"].pct_change()
    bad = p["ret"].abs() > MAX_ABS_DAILY_RETURN
    if bad.any():
        log.warning("%s: %d daily returns beyond %.0f%% set to missing", ticker, bad.sum(), MAX_ABS_DAILY_RETURN * 100)
        p.loc[bad, "ret"] = np.nan
    p.insert(0, "ticker", ticker)
    return p[["ticker", "date", "close", "adj_close", "volume", "dividends", "stock_splits", "ret"]]


def fix_split_mismatch(ev: pd.DataFrame, splits: pd.DataFrame) -> pd.DataFrame:
    """Undo a known source defect.

    Around a bonus-share issue the source sometimes reports EPS on the old share
    count while the estimate (and every other quarter) is on the new one, which
    looks like a +50-60% "surprise". If reported/estimate matches the split ratio
    within tolerance for an announcement near the split, divide it out.
    """
    ev = ev.copy()
    ev["eps_source"] = ev["eps_reported"]
    ev["eps_split_fixed"] = 0
    for _, s in splits.iterrows():
        ratio = s["stock_splits"]
        if ratio < SPLIT_FIX_MIN_RATIO:
            continue
        near = (ev["announced_at"].dt.tz_localize(None) - s["date"]).abs() <= pd.Timedelta(days=SPLIT_FIX_WINDOW_DAYS)
        rel = ev["eps_reported"] / ev["eps_estimate"]
        hit = near & (ev["eps_estimate"] > 0) & ((rel / ratio - 1).abs() < SPLIT_FIX_TOLERANCE) & (ev["eps_split_fixed"] == 0)
        ev.loc[hit, "eps_reported"] = ev.loc[hit, "eps_reported"] / ratio
        ev.loc[hit, "eps_split_fixed"] = 1
    return ev


def clean_events(ticker: str, prices: pd.DataFrame) -> pd.DataFrame:
    path = config.RAW_DIR / f"{ticker}_earnings.csv"
    if not path.exists():
        return pd.DataFrame()
    ev = pd.read_csv(path)
    ev = ev[ev["eps_reported"].notna()].copy()
    if ev.empty:
        return ev
    ev["announced_at"] = pd.to_datetime(ev["announced_at"], utc=True).dt.tz_convert(config.RIYADH_TZ)
    ev = ev.sort_values("announced_at")
    ev = fix_split_mismatch(ev, prices.loc[prices["stock_splits"] > 0, ["date", "stock_splits"]])

    local = ev["announced_at"].dt.tz_localize(None)
    after_close = local.dt.hour >= config.MARKET_CLOSE_HOUR
    ev["react_date"] = local.dt.normalize() + pd.to_timedelta(after_close.astype(int), unit="D")
    ev = ev.drop_duplicates("react_date", keep="last")
    ev.insert(0, "ticker", ticker)
    return ev[["ticker", "announced_at", "react_date", "eps_estimate", "eps_reported", "eps_source", "eps_split_fixed"]]


def run() -> dict:
    uni = load_universe()
    price_frames, event_frames, skipped = [], [], []
    for ticker in uni["ticker"]:
        if not (config.RAW_DIR / f"{ticker}_prices.csv").exists():
            skipped.append(ticker)
            continue
        p = clean_prices(ticker)
        e = clean_events(ticker, p)
        if e.empty:
            skipped.append(ticker)
            continue
        price_frames.append(p)
        event_frames.append(e)

    prices = pd.concat(price_frames, ignore_index=True)
    events = pd.concat(event_frames, ignore_index=True).sort_values(["react_date", "ticker"]).reset_index(drop=True)
    events.insert(0, "event_id", np.arange(1, len(events) + 1))
    companies = uni[~uni["ticker"].isin(skipped)]

    prices["date"] = prices["date"].dt.strftime("%Y-%m-%d")
    events["announced_at"] = events["announced_at"].dt.strftime("%Y-%m-%d %H:%M")
    events["react_date"] = events["react_date"].dt.strftime("%Y-%m-%d")

    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(config.DB_PATH) as con:
        con.executescript(DDL)
        companies.to_sql("companies", con, if_exists="append", index=False)
        prices.to_sql("prices", con, if_exists="append", index=False)
        events.to_sql("events", con, if_exists="append", index=False)

    summary = {
        "companies": int(len(companies)),
        "skipped_tickers": skipped,
        "price_rows": int(len(prices)),
        "events": int(len(events)),
        "events_split_fixed": int(events["eps_split_fixed"].sum()),
    }
    log.info("build: %s", summary)
    return summary

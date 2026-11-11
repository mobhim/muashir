"""Download raw data from Yahoo Finance and cache it untouched in data/raw.

Raw files are never edited; all cleaning happens in later stages so that any
result can be traced back to exactly what the source returned.
"""
from __future__ import annotations

import argparse
import logging
import time
import warnings
from datetime import datetime, timezone
from io import StringIO

import pandas as pd
import yfinance as yf

from . import config

log = logging.getLogger("muashir.fetch")
warnings.filterwarnings("ignore", category=FutureWarning)


def load_universe() -> pd.DataFrame:
    uni = pd.read_csv(config.UNIVERSE_CSV, dtype={"ticker": str})
    if uni["ticker"].duplicated().any():
        raise ValueError("duplicate tickers in universe.csv")
    return uni


def _retry(fn, attempts: int = 4, wait: float = 3.0):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # network errors from Yahoo are heterogeneous
            last = exc
            log.warning("attempt %d failed: %s", i + 1, repr(exc)[:160])
            time.sleep(wait * (i + 1))
    raise last


def fetch_prices(ticker: str) -> pd.DataFrame:
    t = yf.Ticker(f"{ticker}.SR")
    df = _retry(lambda: t.history(start=config.PRICE_START, auto_adjust=False, actions=True))
    if df.empty:
        raise ValueError("no price rows")
    df = df.rename_axis("date").reset_index()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    return df[["date", "open", "high", "low", "close", "adj_close", "volume", "dividends", "stock_splits"]]


def _scrape_earnings(t: yf.Ticker) -> pd.DataFrame:
    """Parse Yahoo's earnings calendar directly.

    yfinance localises "1 AM EST" stamps to America/New_York, which raises on the
    ambiguous hour when US clocks go back. The page already states EST/EDT, so we
    apply the fixed offset instead.
    """
    url = f"https://finance.yahoo.com/calendar/earnings?symbol={t.ticker}&offset=0&size=100"
    html = t._data.cache_get(url).text
    df = pd.read_html(StringIO(html), na_values=["-"])[0]
    df = df.rename(columns={"Surprise (%)": "Surprise(%)"}).dropna(subset=["Earnings Date"])
    parts = df["Earnings Date"].str.rsplit(" ", n=1, expand=True)
    naive = pd.to_datetime(parts[0], format="%B %d, %Y at %I %p")
    offset = parts[1].map({"EST": 5, "EDT": 4})
    if offset.isna().any():
        raise ValueError(f"unexpected timezone labels: {sorted(parts[1].unique())}")
    df.index = (naive + pd.to_timedelta(offset, unit="h")).dt.tz_localize("UTC")
    return df[["EPS Estimate", "Reported EPS", "Surprise(%)"]]


def fetch_earnings(ticker: str) -> pd.DataFrame:
    t = yf.Ticker(f"{ticker}.SR")
    try:
        df = _retry(lambda: t.get_earnings_dates(limit=60), attempts=2)
    except Exception as exc:
        log.warning("%s: yfinance parser failed (%s); using direct scrape", ticker, type(exc).__name__)
        df = _retry(lambda: _scrape_earnings(t))
    if df is None or df.empty:
        raise ValueError("no earnings rows")
    df = df.rename_axis("announced_at").reset_index()
    df = df.rename(columns={
        "EPS Estimate": "eps_estimate",
        "Reported EPS": "eps_reported",
        "Surprise(%)": "surprise_pct",
    })
    # keep the original timestamp with its UTC offset; conversion happens in the build stage
    df["announced_at"] = pd.to_datetime(df["announced_at"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return df[["announced_at", "eps_estimate", "eps_reported", "surprise_pct"]]


def run(refresh: bool = False) -> pd.DataFrame:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    uni = load_universe()
    rows = []
    for ticker in uni["ticker"]:
        status = {"ticker": ticker, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        for kind, fn in (("prices", fetch_prices), ("earnings", fetch_earnings)):
            path = config.RAW_DIR / f"{ticker}_{kind}.csv"
            if path.exists() and not refresh:
                status[kind] = "cached"
                continue
            try:
                df = fn(ticker)
                df.to_csv(path, index=False)
                status[kind] = f"ok:{len(df)}"
            except Exception as exc:
                status[kind] = f"FAILED:{repr(exc)[:80]}"
                log.error("%s %s failed: %s", ticker, kind, exc)
        log.info("%s", status)
        rows.append(status)
    manifest = pd.DataFrame(rows)
    manifest.to_csv(config.RAW_DIR / "_manifest.csv", index=False)
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true", help="re-download even if cached")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    m = run(refresh=args.refresh)
    print(m.to_string(index=False))

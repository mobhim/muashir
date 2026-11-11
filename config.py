"""Paths and study parameters. Every tunable number of the study lives here."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "muashir.db"
REPORT_DIR = ROOT / "reports"
FIG_DIR = REPORT_DIR / "figures"

UNIVERSE_CSV = CONFIG_DIR / "universe.csv"

RIYADH_TZ = "Asia/Riyadh"
MARKET_CLOSE_HOUR = 15  # Tadawul closes 15:00 Riyadh; later announcements trade next session

PRICE_START = "2014-01-01"
STUDY_START = "2016-01-01"  # first event date used in tests

# Event-study windows, in trading days relative to the first session that can react (day 0)
ESTIMATION_WINDOW = (-250, -31)   # market-model alpha/beta
MIN_ESTIMATION_OBS = 120
# The source gives announcement times to the hour and many are placeholders, so the
# true reaction day is only known to +/- 1 session. The reaction window therefore
# spans [-1, +1], and the drift windows start at +3 so that no part of the
# immediate reaction can leak into what we call "predictable" drift.
WINDOWS = {
    "pre": (-20, -2),        # run-up before the announcement
    "reaction": (-1, 1),     # immediate reaction
    "drift_20": (3, 22),     # tradable: enter at close of day +2
    "drift_60": (3, 62),
}
PRIMARY_WINDOW = "drift_60"

# Minimum number of other stocks needed to build the market proxy on a given day
MIN_PROXY_MEMBERS = 10

WINSOR = (0.01, 0.99)
BOOTSTRAP_REPS = 2000
SEED = 20261111

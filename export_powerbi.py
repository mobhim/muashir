"""Export a star schema for Power BI as UTF-8 CSV files in powerbi/data.

    dim_company ─┐
    dim_date ────┼── fact_event ──┬── fact_abnormal_return ── dim_window
    dim_bucket ──┘                └── fact_car_path

Power BI has no built-in SQLite connector, so CSV keeps the report free of
driver installs. The files are rebuilt on every pipeline run.
"""
from __future__ import annotations

import sqlite3

import pandas as pd

from . import config
from .analysis import winsorize
from .score import COMPONENTS

OUT_DIR = config.ROOT / "powerbi" / "data"

WINDOW_LABELS = {
    "pre": (1, "قبل الإعلان (−20 إلى −2)"),
    "reaction": (2, "ردة الفعل (−1 إلى +1)"),
    "drift_20": (3, "بعد الإعلان (+3 إلى +22)"),
    "drift_60": (4, "بعد الإعلان (+3 إلى +62)"),
}
BUCKET_LABELS = {1: "1 · الأدنى درجة", 2: "2", 3: "3 · الوسط", 4: "4", 5: "5 · الأعلى درجة"}


def write(con: sqlite3.Connection, df: pd.DataFrame, wins: pd.DataFrame, paths: pd.DataFrame) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample_ids = set(df["event_id"])

    companies = pd.read_sql("SELECT ticker, name_ar, sector_ar FROM companies", con)
    companies = companies[companies["ticker"].isin(df["ticker"].unique())]

    ev_cols = ["event_id", "ticker", "day0", "season", "year", "bucket", "score", "n_components",
               "eps_reported", "eps_estimate", "beta", "alpha", "price_ref"]
    events = df[ev_cols + [f"p_{c}" for c in COMPONENTS]].copy()
    events = events.rename(columns={"day0": "date"})
    events["date"] = events["date"].dt.strftime("%Y-%m-%d")

    ar = wins[wins["event_id"].isin(sample_ids)][
        ["event_id", "window", "car_mm", "car_beta", "car_ma", "raw_ret", "mkt_part"]
    ].copy()
    # same 1%/99% clipping per window as the statistical tests, so dashboard means match the report
    for col in ("car_mm", "car_beta"):
        ar[f"{col}_w"] = ar.groupby("window")[col].transform(winsorize)

    path = paths[paths["event_id"].isin(sample_ids)].copy()
    path["ar"] = path["ar"].clip(-0.1, 0.1).fillna(0.0).round(6)   # as in the report's path figure

    days = pd.date_range(df["day0"].min().normalize(), df["day0"].max().normalize(), freq="D")
    dim_date = pd.DataFrame({
        "date": days.strftime("%Y-%m-%d"), "year": days.year, "quarter": days.quarter,
        "season": days.to_period("Q").astype(str), "month": days.month,
    })
    dim_window = pd.DataFrame([{"window": k, "window_order": o, "window_label": l} for k, (o, l) in WINDOW_LABELS.items()])
    dim_bucket = pd.DataFrame([{"bucket": k, "bucket_label": v} for k, v in BUCKET_LABELS.items()])

    tables = {
        "dim_company": companies, "dim_date": dim_date, "dim_window": dim_window, "dim_bucket": dim_bucket,
        "fact_event": events, "fact_abnormal_return": ar, "fact_car_path": path,
    }
    for name, t in tables.items():
        t.to_csv(OUT_DIR / f"{name}.csv", index=False, encoding="utf-8-sig", float_format="%.6f")
    return {name: len(t) for name, t in tables.items()}

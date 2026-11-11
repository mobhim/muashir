"""Write site/data.js: everything the website shows, taken from the study outputs.

The file is a script (`window.MUASHIR = {...}`) rather than JSON so the site
also works when opened straight from the folder, where fetch() is blocked.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date

import numpy as np
import pandas as pd

from . import config
from .analysis import N_BUCKETS, winsorize
from .score import COMPONENTS

OUT = config.ROOT / "site" / "data.js"


def _r(x, nd: int = 5):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    return round(float(x), nd)


def _spread(sp: dict) -> dict:
    return {"mean": _r(sp["mean"]), "t": _r(sp["t"], 2), "lo": _r(sp["ci_low"]), "hi": _r(sp["ci_high"])}


def write(con: sqlite3.Connection, df: pd.DataFrame, wins: pd.DataFrame, paths: pd.DataFrame, results: dict) -> int:
    ids = set(df["event_id"])
    w = wins[wins["event_id"].isin(ids)].copy()
    for col in ("car_mm", "car_beta"):
        w[f"{col}_w"] = w.groupby("window")[col].transform(winsorize)
    w = w.merge(df[["event_id", "bucket", "ticker"]], on="event_id")

    def by_bucket(window: str, col: str) -> list:
        s = w[w["window"] == window].groupby("bucket")[col].mean()
        return [_r(s.get(b)) for b in range(1, N_BUCKETS + 1)]

    p = paths[paths["event_id"].isin(ids)].merge(df[["event_id", "bucket"]], on="event_id")
    p["ar"] = p["ar"].clip(-0.1, 0.1).fillna(0.0)
    cum = p.groupby(["bucket", "rel_day"])["ar"].mean().unstack(0).sort_index().cumsum()

    companies = pd.read_sql("SELECT ticker, name_ar, sector_ar FROM companies", con)
    wide = w.pivot(index="event_id", columns="window", values="car_mm")
    wide_w = w.pivot(index="event_id", columns="window", values="car_mm_w")
    ev = df.merge(wide[["reaction", "drift_60"]].reset_index(), on="event_id", how="left")
    ev = ev.merge(wide_w[["reaction", "drift_60"]].rename(columns=lambda c: c + "_w").reset_index(), on="event_id", how="left")
    comp_rows = []
    for c in companies.itertuples(index=False):
        e = ev[ev["ticker"] == c.ticker].sort_values("day0")
        if e.empty:
            continue
        comp_rows.append({
            "t": c.ticker, "name": c.name_ar, "sector": c.sector_ar, "n": int(len(e)),
            "score": _r(e["score"].mean(), 1), "beta": _r(e["beta"].mean(), 2),
            "react": _r(e["reaction_w"].mean()), "drift": _r(e["drift_60_w"].mean()),
            "up": _r((e["reaction"] > 0).mean(), 3),
            "comp": [_r(e[f"p_{k}"].mean(), 1) for k in COMPONENTS],
            "events": [[d.strftime("%Y-%m-%d"), _r(s, 1), int(b), _r(a), _r(dr), _r(eps, 2), _r(est, 2)]
                       for d, s, b, a, dr, eps, est in zip(e["day0"], e["score"], e["bucket"], e["reaction"],
                                                            e["drift_60"], e["eps_reported"], e["eps_estimate"])],
        })
    comp_rows.sort(key=lambda r: (r["sector"], r["name"]))

    win = results["windows"]
    rob = results["robustness"]
    data = {
        "generated": date.today().isoformat(),
        "sample": results["sample"],
        "windows": {k: {"spread": _spread(v["spread"]), "ic": _r(v["ic"]["mean"], 3), "ic_t": _r(v["ic"]["t"], 2)}
                    for k, v in win.items()},
        "buckets": {
            "n": [int(x) for x in win["reaction"]["buckets"]["n"]],
            "score": [_r(x, 1) for x in win["reaction"]["buckets"]["mean_score"]],
            "reaction": by_bucket("reaction", "car_mm_w"),
            "drift": by_bucket("drift_60", "car_mm_w"),
            "drift_beta": by_bucket("drift_60", "car_beta_w"),
        },
        "path": {"days": [int(d) for d in cum.index],
                 "buckets": {str(b): [_r(x) for x in cum[b]] for b in range(1, N_BUCKETS + 1)}},
        "measures": {k: _spread(rob[k]) for k in ("market_adjusted", "beta_adjusted", "raw_return")},
        "robust": {k: _spread(rob[k]) for k in ("excluding_2020", "first_half", "second_half")},
        "prior_alpha": {k: _r(v) if k != "days" else int(v) for k, v in results["prior_alpha"].items()},
        "seasons": [{"s": k, "v": _r(v)} for k, v in win[config.PRIMARY_WINDOW]["spread"]["by_season"].items()],
        "components": [{"id": c, "react": _r(results["components"][c]["reaction"]["mean"], 3),
                        "react_t": _r(results["components"][c]["reaction"]["t"], 2),
                        "drift": _r(results["components"][c][config.PRIMARY_WINDOW]["mean"], 3),
                        "drift_t": _r(results["components"][c][config.PRIMARY_WINDOW]["t"], 2)} for c in COMPONENTS],
        "regression": {k: {"coef": _r(v["coef"], 3), "t": _r(v["t"], 2), "p": _r(v["p"], 3), "n": v["n"]}
                       for k, v in results["regression"].items()},
        "decomposition": {k: _r(v, 4) if k != "n" else int(v) for k, v in results["decomposition"].items()},
        "companies": comp_rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("window.MUASHIR = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    return OUT.stat().st_size

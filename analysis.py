"""Statistical tests of the score against post-announcement abnormal returns.

Announcements cluster in reporting seasons and stocks move together, so events
are not independent. Every test therefore treats the reporting season (calendar
quarter of the announcement) as the unit of independence: seasonal averages with
a t-test (Fama-MacBeth style), a season-block bootstrap, and season-clustered
regression errors.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from . import config
from .score import COMPONENTS

MIN_SEASON_EVENTS = 15
N_BUCKETS = 5


def assemble(features: pd.DataFrame, wins: pd.DataFrame) -> pd.DataFrame:
    wide = wins.pivot(index="event_id", columns="window", values=["car_mm", "car_ma", "car_beta", "raw_ret", "mkt_part"])
    wide.columns = [f"{a}_{b}" for a, b in wide.columns]
    df = features.merge(wide.reset_index(), on="event_id", how="left")
    df = df[(df["day0"] >= config.STUDY_START) & df["score"].notna()].copy()
    df["season"] = df["day0"].dt.to_period("Q").astype(str)
    df["year"] = df["day0"].dt.year
    sizes = df.groupby("season")["event_id"].transform("size")
    df = df[sizes >= MIN_SEASON_EVENTS].copy()
    # sort into five groups inside each season: a clean "best vs worst reports of the season" comparison
    df["bucket"] = df.groupby("season")["score"].transform(
        lambda s: pd.qcut(s.rank(method="first"), N_BUCKETS, labels=False) + 1
    )
    return df.reset_index(drop=True)


def winsorize(s: pd.Series) -> pd.Series:
    lo, hi = s.quantile(config.WINSOR[0]), s.quantile(config.WINSOR[1])
    return s.clip(lo, hi)


def _t(series: pd.Series) -> dict:
    s = series.dropna()
    n = len(s)
    mean = s.mean()
    se = s.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    return {"mean": float(mean), "t": float(mean / se) if se and se > 0 else np.nan, "n": int(n)}


def seasonal_ic(df: pd.DataFrame, x: str, y: str) -> dict:
    """Mean of per-season Spearman correlations between x and y."""
    d = df[[x, y, "season"]].dropna()
    ics = d.groupby("season").apply(
        lambda g: g[x].corr(g[y], method="spearman") if len(g) >= 10 else np.nan
    )
    out = _t(ics)
    out["pooled"] = float(d[x].corr(d[y], method="spearman"))
    out["n_events"] = int(len(d))
    out["by_season"] = ics.dropna()
    return out


def bucket_table(df: pd.DataFrame, y: str) -> pd.DataFrame:
    d = df[["bucket", y, "score"]].dropna()
    d[y] = winsorize(d[y])
    t = d.groupby("bucket").agg(n=(y, "size"), mean_score=("score", "mean"), mean_car=(y, "mean"),
                                median_car=(y, "median"), hit_rate=(y, lambda s: (s > 0).mean()))
    return t


def spread_test(df: pd.DataFrame, y: str, rng: np.random.Generator) -> dict:
    """Top-minus-bottom bucket mean abnormal return, with season-level inference."""
    d = df[["bucket", "season", y]].dropna().copy()
    d[y] = winsorize(d[y])
    top, bot = d[d["bucket"] == N_BUCKETS], d[d["bucket"] == 1]
    per_season = top.groupby("season")[y].mean() - bot.groupby("season")[y].mean()
    out = _t(per_season)
    out["pooled_spread"] = float(top[y].mean() - bot[y].mean())
    out["by_season"] = per_season.dropna()

    seasons = d["season"].unique()
    groups = {s: g for s, g in d.groupby("season")}
    boots = np.empty(config.BOOTSTRAP_REPS)
    for b in range(config.BOOTSTRAP_REPS):
        pick = rng.choice(seasons, size=len(seasons), replace=True)
        s = pd.concat([groups[p] for p in pick], ignore_index=True)
        boots[b] = s.loc[s["bucket"] == N_BUCKETS, y].mean() - s.loc[s["bucket"] == 1, y].mean()
    out["ci_low"], out["ci_high"] = (float(v) for v in np.percentile(boots, [2.5, 97.5]))
    out["boot_p"] = float(2 * min((boots <= 0).mean(), (boots >= 0).mean()))
    return out


def regression(df: pd.DataFrame, y: str, controls: bool) -> dict:
    cols = ["score", "season", y] + (["car_mm_pre", "beta"] if controls else [])
    d = df[cols].dropna().copy()
    d["y"] = winsorize(d[y]) * 100                 # in percent
    d["score10"] = d["score"] / 10                 # effect of a 10-point higher score
    formula = "y ~ score10" + (" + car_mm_pre + beta" if controls else "")
    fit = smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["season"])[0]})
    return {"coef": float(fit.params["score10"]), "t": float(fit.tvalues["score10"]),
            "p": float(fit.pvalues["score10"]), "n": int(fit.nobs), "r2": float(fit.rsquared)}


def decomposition(df: pd.DataFrame) -> dict:
    """How much of the move around results is the market, how much is the company."""
    d = df[["car_mm_reaction", "mkt_part_reaction"]].dropna()
    comp, mkt = d["car_mm_reaction"].abs(), d["mkt_part_reaction"].abs()
    share = comp / (comp + mkt)
    return {
        "n": int(len(d)),
        "median_company_share": float(share.median()),
        "company_dominates": float((comp > mkt).mean()),
        "median_abs_company_move": float(comp.median()),
        "median_abs_market_move": float(mkt.median()),
    }


def run(df: pd.DataFrame) -> dict:
    rng = np.random.default_rng(config.SEED)
    res: dict = {"sample": {
        "events": int(len(df)), "companies": int(df["ticker"].nunique()), "seasons": int(df["season"].nunique()),
        "first": str(df["day0"].min().date()), "last": str(df["day0"].max().date()),
    }}
    res["windows"] = {}
    for w in config.WINDOWS:
        y = f"car_mm_{w}"
        res["windows"][w] = {
            "ic": seasonal_ic(df, "score", y),
            "spread": spread_test(df, y, rng),
            "buckets": bucket_table(df, y),
        }
    p = config.PRIMARY_WINDOW
    yp = f"car_mm_{p}"
    res["regression"] = {"simple": regression(df, yp, False), "controls": regression(df, yp, True)}
    res["components"] = {
        c: {w: {k: v for k, v in seasonal_ic(df, f"p_{c}", f"car_mm_{w}").items() if k != "by_season"}
            for w in ("reaction", p)}
        for c in COMPONENTS
    }
    res["robustness"] = {
        "market_adjusted": spread_test(df, f"car_ma_{p}", rng),
        "beta_adjusted": spread_test(df, f"car_beta_{p}", rng),
        "raw_return": spread_test(df, f"raw_ret_{p}", rng),
        "excluding_2020": spread_test(df[df["year"] != 2020], yp, rng),
        "first_half": spread_test(df[df["day0"] < df["day0"].median()], yp, rng),
        "second_half": spread_test(df[df["day0"] >= df["day0"].median()], yp, rng),
    }
    res["decomposition"] = decomposition(df)
    # Were high-score stocks already outperforming before the news? Expressed over the
    # same number of days as the primary window so it is directly comparable to the spread.
    a, b = config.WINDOWS[p]
    days = b - a + 1
    prior = df.groupby("bucket")["alpha"].mean() * days
    res["prior_alpha"] = {"top": float(prior[N_BUCKETS]), "bottom": float(prior[1]),
                          "spread": float(prior[N_BUCKETS] - prior[1]), "days": days}
    return res

"""Run the whole study: fetch -> build -> event study -> score -> tests -> report.

    python -m muashir.pipeline            # uses cached raw data if present
    python -m muashir.pipeline --refresh  # re-download everything first
"""
from __future__ import annotations

import argparse
import logging
import sqlite3

from . import analysis, build, config, eventstudy, export_powerbi, export_site, fetch, report, score


def main(refresh: bool = False, skip_fetch: bool = False) -> dict:
    if not skip_fetch:
        fetch.run(refresh=refresh)
    build_summary = build.run()
    with sqlite3.connect(config.DB_PATH) as con:
        info, wins, paths = eventstudy.run(con)
        features = score.add_score(score.build_features(con, info))
        df = analysis.assemble(features, wins)
        # persist the analytical tables so they can be queried from SQL / Power BI
        out = features.copy()
        out["day0"] = out["day0"].dt.strftime("%Y-%m-%d")
        out.to_sql("event_features", con, if_exists="replace", index=False)
        wins.to_sql("abnormal_returns", con, if_exists="replace", index=False)
        sample = df[["event_id", "season", "bucket"]]
        sample.to_sql("study_sample", con, if_exists="replace", index=False)
        logging.getLogger("muashir.pipeline").info("power bi export: %s", export_powerbi.write(con, df, wins, paths))
        results = analysis.run(df)
        size = export_site.write(con, df, wins, paths, results)
        logging.getLogger("muashir.pipeline").info("site data: %d KB", size // 1024)
    report.write(df, paths, results, build_summary)
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--skip-fetch", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    main(refresh=a.refresh, skip_fetch=a.skip_fetch)

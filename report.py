"""Figures, results.json and the Arabic report. All numbers come from `results`."""
from __future__ import annotations

import json
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config
from .analysis import N_BUCKETS, winsorize
from .score import COMPONENTS

INK, MUTED, GOLD, RED, GRID = "#1b1b1b", "#8a8a8a", "#b8892b", "#a33a3a", "#e6e2d8"
WINDOW_AR = {
    "pre": "قبل الإعلان (من −20 إلى −2)",
    "reaction": "ردة الفعل (من −1 إلى +1)",
    "drift_20": "بعد الإعلان (من +3 إلى +22)",
    "drift_60": "بعد الإعلان (من +3 إلى +62)",
}
COMPONENT_AR = {
    "yoy": "نمو ربحية السهم السنوي", "qoq": "التغير عن الربع السابق", "surprise": "المفاجأة عن توقعات المحللين",
    "consistency": "استمرارية النمو", "earn_yield": "عائد الأرباح (عكس مكرر الربحية)",
    "div_yield": "عائد التوزيعات", "low_beta": "انخفاض الحساسية للسوق",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.axisbelow": True, "xtick.color": INK, "ytick.color": INK,
    "figure.dpi": 150, "savefig.bbox": "tight", "axes.titleweight": "bold", "axes.titlesize": 11,
})


def _pct(x: float, digits: int = 2) -> str:
    return "—" if x is None or np.isnan(x) else f"{x * 100:+.{digits}f}%"


def _num(x: float, digits: int = 2) -> str:
    return "—" if x is None or np.isnan(x) else f"{x:.{digits}f}"


def fig_buckets(results: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8), sharey=False, constrained_layout=True)
    for ax, w, title in zip(axes, ("reaction", config.PRIMARY_WINDOW),
                            ("Immediate reaction, days -1 to +1", "After the news, days +3 to +62")):
        t = results["windows"][w]["buckets"]
        colors = [RED] + [MUTED] * (N_BUCKETS - 2) + [GOLD]
        ax.bar(t.index.astype(int), t["mean_car"] * 100, color=colors, width=0.7)
        ax.axhline(0, color=INK, linewidth=0.8)
        ax.set_title(title)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Mean abnormal return, %")
    fig.supxlabel("Score group within the reporting season (1 = lowest, 5 = highest)", fontsize=10)
    fig.savefig(config.FIG_DIR / "01_buckets.png")
    plt.close(fig)


def fig_paths(df: pd.DataFrame, paths: pd.DataFrame) -> None:
    p = paths.merge(df[["event_id", "bucket"]], on="event_id")
    p = p[p["bucket"].isin([1, 3, N_BUCKETS])].copy()
    p["ar"] = p["ar"].clip(-0.1, 0.1).fillna(0.0)
    mean = p.groupby(["bucket", "rel_day"])["ar"].mean().unstack(0).sort_index().cumsum() * 100
    fig, ax = plt.subplots(figsize=(8, 3.8))
    for b, color, label in ((N_BUCKETS, GOLD, "Highest scores"), (3, MUTED, "Middle"), (1, RED, "Lowest scores")):
        ax.plot(mean.index, mean[b], color=color, linewidth=2, label=label)
    ax.axvspan(-1, 1, color=GRID, alpha=0.9, linewidth=0)
    ax.axhline(0, color=INK, linewidth=0.8)
    ax.set_title("Cumulative abnormal return around the announcement")
    ax.set_xlabel("Trading days relative to the announcement (shaded = reaction window)")
    ax.set_ylabel("Cumulative abnormal return, %")
    ax.legend(frameon=False, loc="upper left")
    fig.savefig(config.FIG_DIR / "02_paths.png")
    plt.close(fig)


def fig_seasons(results: dict) -> None:
    s = results["windows"][config.PRIMARY_WINDOW]["spread"]["by_season"] * 100
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ax.bar(range(len(s)), s.values, color=[GOLD if v >= 0 else RED for v in s.values], width=0.75)
    ax.axhline(0, color=INK, linewidth=0.8)
    step = max(1, len(s) // 12)
    ax.set_xticks(range(0, len(s), step))
    ax.set_xticklabels(s.index[::step], rotation=45, ha="right")
    ax.set_title("Top-minus-bottom group, each reporting season (days +3 to +62)")
    ax.set_ylabel("Abnormal return spread, %")
    ax.grid(axis="x", visible=False)
    fig.savefig(config.FIG_DIR / "03_seasons.png")
    plt.close(fig)


def fig_components(results: dict) -> None:
    labels = {"yoy": "EPS growth YoY", "qoq": "EPS change QoQ", "surprise": "Analyst surprise",
              "consistency": "Growth consistency", "earn_yield": "Earnings yield", "div_yield": "Dividend yield",
              "low_beta": "Low market beta"}
    comp = results["components"]
    y = np.arange(len(COMPONENTS))
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.barh(y + 0.19, [comp[c]["reaction"]["mean"] for c in COMPONENTS], height=0.36, color=MUTED, label="Reaction (-1 to +1)")
    ax.barh(y - 0.19, [comp[c][config.PRIMARY_WINDOW]["mean"] for c in COMPONENTS], height=0.36, color=GOLD, label="After (+3 to +62)")
    ax.axvline(0, color=INK, linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([labels[c] for c in COMPONENTS])
    ax.invert_yaxis()
    ax.set_title("Which component carries information? (mean seasonal rank correlation)")
    ax.set_xlabel("Rank correlation with abnormal return")
    ax.legend(frameon=False)
    ax.grid(axis="y", visible=False)
    fig.savefig(config.FIG_DIR / "04_components.png")
    plt.close(fig)


def _jsonable(o):
    if isinstance(o, dict):
        return {k: _jsonable(v) for k, v in o.items()}
    if isinstance(o, pd.DataFrame):
        return o.reset_index().to_dict("records")
    if isinstance(o, pd.Series):
        return {str(k): float(v) for k, v in o.items()}
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


def _significant(sp: dict) -> bool:
    return abs(sp["t"]) >= 2 and (sp["ci_low"] > 0 or sp["ci_high"] < 0)


def _verdict(results: dict) -> list[str]:
    react = results["windows"]["reaction"]["spread"]
    drift = results["windows"][config.PRIMARY_WINDOW]["spread"]
    lines = []
    if _significant(react) and react["mean"] > 0:
        lines.append(
            f"**الدرجة تلتقط ما يحرّك السعر عند الإعلان.** الشركات الأعلى درجة تفوقت على الأدنى درجة بمتوسط "
            f"{_pct(react['mean'])} خلال ثلاثة أيام حول الإعلان، والفرق ذو دلالة إحصائية (t = {_num(react['t'])})."
        )
    else:
        lines.append(
            f"**الدرجة لا تفسّر ردة الفعل عند الإعلان بشكل موثوق.** الفرق بين الأعلى والأدنى درجة "
            f"{_pct(react['mean'])} (t = {_num(react['t'])})."
        )
    if _significant(drift):
        direction = "استمرت في التفوق" if drift["mean"] > 0 else "تراجعت مقارنة بالأدنى درجة"
        lines.append(
            f"**الدرجة تتنبأ بالأداء بعد الإعلان.** الشركات الأعلى درجة {direction} بمتوسط {_pct(drift['mean'])} "
            f"على مدى 60 يوم تداول تبدأ بعد الإعلان بثلاثة أيام (t = {_num(drift['t'])}، "
            f"فترة الثقة 95%: من {_pct(drift['ci_low'])} إلى {_pct(drift['ci_high'])})."
        )
    else:
        lines.append(
            f"**الدرجة لا تتنبأ بالأداء بعد الإعلان.** الفرق بين الأعلى والأدنى درجة على مدى 60 يوم تداول بعد الإعلان "
            f"{_pct(drift['mean'])} (t = {_num(drift['t'])}، فترة الثقة 95%: من {_pct(drift['ci_low'])} إلى "
            f"{_pct(drift['ci_high'])})، وهذا لا يختلف إحصائياً عن الصفر. بمعنى أن السوق يسعّر محتوى النتائج "
            f"خلال أيام الإعلان، ولا يبقى منه ما يكفي لبناء قرار شراء لاحق على الدرجة وحدها."
        )
    alt = {k: results["robustness"][k] for k in ("market_adjusted", "beta_adjusted", "raw_return")}
    disagree = [k for k, sp in alt.items() if _significant(sp) != _significant(drift)]
    if disagree:
        vals = "، ".join(f"{_pct(alt[k]['mean'])} (t = {_num(alt[k]['t'])})" for k in alt)
        pa = results["prior_alpha"]
        text = (
            f"**لكن الجواب يتغير حسب طريقة القياس.** نموذج السوق يطرح من كل سهم تفوقه في السنة السابقة (ألفا). "
            f"بدون هذا الطرح، بالمقاييس الثلاثة البديلة (ناقص السوق، ناقص بيتا × السوق، العائد الخام)، الفرق على التوالي: {vals}. "
            f"والشركات الأعلى درجة كانت متفوقة أصلاً قبل الإعلان: فرق ألفا السابقة بينها وبين الأدنى درجة يعادل "
            f"{_pct(pa['spread'])} على {pa['days']} يوم."
        )
        alt_mean = float(np.mean([sp["mean"] for sp in alt.values()]))
        if alt_mean > 0 and pa["spread"] >= 0.5 * alt_mean:
            text += (
                " **التفسير:** الدرجة تميّز الشركات التي يستمر تفوقها بعد الإعلان بنفس وتيرته قبله تقريباً، "
                "لكن الإعلان نفسه لا يضيف تفوقاً جديداً بعد أيامه الأولى."
            )
        else:
            text += " التفوق السابق لا يفسّر الفرق كله، فالدليل على التنبؤ بعد الإعلان قائم لكنه غير ثابت عبر المقاييس."
        lines.append(text)
    return lines


def write(df: pd.DataFrame, paths: pd.DataFrame, results: dict, build_summary: dict) -> None:
    config.FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig_buckets(results)
    fig_paths(df, paths)
    fig_seasons(results)
    fig_components(results)

    payload = {"generated": date.today().isoformat(), "build": build_summary, **_jsonable(results)}
    (config.REPORT_DIR / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    s, dec, reg = results["sample"], results["decomposition"], results["regression"]
    L: list[str] = []
    L += ["# مؤشّر: هل درجة النتائج الربعية تتنبأ بأداء السهم؟", ""]
    L += [f"تقرير مولّد آلياً بتاريخ {date.today().isoformat()} من `python -m muashir.pipeline`. كل رقم هنا محسوب من قاعدة البيانات `data/muashir.db`.", ""]
    L += ["## الخلاصة", ""]
    L += [f"- {line}" for line in _verdict(results)]
    L += [
        f"- **حركة السهم حول النتائج أغلبها من الشركة نفسها.** في {dec['company_dominates'] * 100:.0f}% من الإعلانات كان الجزء الخاص "
        f"بالشركة أكبر من الجزء الذي يفسّره السوق، ووسيط حصة الشركة من الحركة {dec['median_company_share'] * 100:.0f}%.",
        "",
    ]
    L += ["## العينة", ""]
    L += [f"- {s['events']:,} إعلان نتائج ربعية لـ {s['companies']} شركة مدرجة في السوق السعودي، على {s['seasons']} موسم نتائج.",
          f"- من {s['first']} إلى {s['last']}.",
          f"- المصدر Yahoo Finance: الأسعار المعدّلة، وتواريخ الإعلان، وربحية السهم الفعلية والمتوقعة.",
          f"- صُحّحت {build_summary['events_split_fixed']} قراءة لربحية السهم كانت محسوبة على عدد الأسهم قبل منحة أسهم.", ""]

    L += ["## النتيجة حسب النافذة الزمنية", "",
          "الفرق = متوسط العائد غير الطبيعي لأعلى خُمس في الدرجة ناقص أدنى خُمس، داخل كل موسم نتائج.", "",
          "| النافذة | الفرق | t | فترة الثقة 95% | معامل الارتباط الرتبي | t |",
          "|---|---|---|---|---|---|"]
    for w in config.WINDOWS:
        sp, ic = results["windows"][w]["spread"], results["windows"][w]["ic"]
        L.append(f"| {WINDOW_AR[w]} | {_pct(sp['mean'])} | {_num(sp['t'])} | {_pct(sp['ci_low'])} إلى {_pct(sp['ci_high'])} | {_num(ic['mean'], 3)} | {_num(ic['t'])} |")
    L += ["", "![العائد حسب مجموعة الدرجة](figures/01_buckets.png)", "", "![المسار التراكمي](figures/02_paths.png)", ""]

    t = results["windows"][config.PRIMARY_WINDOW]["buckets"]
    L += [f"### مجموعات الدرجة، {WINDOW_AR[config.PRIMARY_WINDOW]}", "",
          "| المجموعة | عدد الإعلانات | متوسط الدرجة | متوسط العائد غير الطبيعي | الوسيط | نسبة الإعلانات الموجبة |", "|---|---|---|---|---|---|"]
    for b, r in t.iterrows():
        L.append(f"| {int(b)} | {int(r['n'])} | {r['mean_score']:.1f} | {_pct(r['mean_car'])} | {_pct(r['median_car'])} | {r['hit_rate'] * 100:.0f}% |")
    L += ["", "![الفرق في كل موسم](figures/03_seasons.png)", ""]

    L += ["## الانحدار", "",
          f"المتغير التابع: العائد غير الطبيعي {WINDOW_AR[config.PRIMARY_WINDOW]} بالنسبة المئوية. المعامل = أثر ارتفاع الدرجة 10 نقاط. الأخطاء المعيارية مجمّعة حسب موسم النتائج.", "",
          "| النموذج | المعامل | t | p | عدد المشاهدات | R² |", "|---|---|---|---|---|---|",
          f"| الدرجة فقط | {_num(reg['simple']['coef'], 3)} | {_num(reg['simple']['t'])} | {_num(reg['simple']['p'], 3)} | {reg['simple']['n']} | {_num(reg['simple']['r2'], 4)} |",
          f"| مع ضبط الصعود السابق للإعلان والبيتا | {_num(reg['controls']['coef'], 3)} | {_num(reg['controls']['t'])} | {_num(reg['controls']['p'], 3)} | {reg['controls']['n']} | {_num(reg['controls']['r2'], 4)} |", ""]

    L += ["## أي مكوّن يحمل المعلومة؟", "",
          "متوسط معامل الارتباط الرتبي الموسمي بين كل مكوّن والعائد غير الطبيعي.", "",
          f"| المكوّن | ردة الفعل | t | {WINDOW_AR[config.PRIMARY_WINDOW]} | t |", "|---|---|---|---|---|"]
    for c in COMPONENTS:
        a, b = results["components"][c]["reaction"], results["components"][c][config.PRIMARY_WINDOW]
        L.append(f"| {COMPONENT_AR[c]} | {_num(a['mean'], 3)} | {_num(a['t'])} | {_num(b['mean'], 3)} | {_num(b['t'])} |")
    L += ["", "![المكونات](figures/04_components.png)", ""]

    L += ["## اختبارات المتانة", "", f"الفرق بين أعلى وأدنى خُمس، {WINDOW_AR[config.PRIMARY_WINDOW]}.", "",
          "| الاختبار | الفرق | t | فترة الثقة 95% |", "|---|---|---|---|"]
    names = {"market_adjusted": "عائد السهم ناقص عائد السوق", "beta_adjusted": "عائد السهم ناقص بيتا × عائد السوق (بدون ألفا)",
             "raw_return": "العائد الخام بدون أي تعديل", "excluding_2020": "باستبعاد سنة 2020",
             "first_half": "النصف الأول من الفترة", "second_half": "النصف الثاني من الفترة"}
    for k, label in names.items():
        sp = results["robustness"][k]
        L.append(f"| {label} | {_pct(sp['mean'])} | {_num(sp['t'])} | {_pct(sp['ci_low'])} إلى {_pct(sp['ci_high'])} |")
    L += [""]

    L += ["## أداء أم أوضاع؟", "",
          f"في نافذة ردة الفعل، وسيط حركة السهم الخاصة بالشركة {dec['median_abs_company_move'] * 100:.2f}% مقابل "
          f"{dec['median_abs_market_move'] * 100:.2f}% للجزء الذي يفسّره السوق ({dec['n']:,} إعلان).", ""]

    L += ["## المنهجية باختصار", "",
          "- **العائد غير الطبيعي:** عائد السهم ناقص ما يتوقعه نموذج السوق (ألفا وبيتا مقدّرتان على الأيام من −250 إلى −31 قبل الإعلان).",
          "- **مؤشر السوق:** متوسط متساوي الأوزان لعوائد بقية شركات العينة، لأن تاريخ مؤشر تاسي غير متاح من المصدر المجاني.",
          "- **الدرجة:** متوسط سبعة مكونات، كل مكوّن محوّل إلى ترتيب مئوي مقارنة بإعلانات السنتين السابقتين فقط. الأوزان متساوية ومحددة مسبقاً، ولم تُضبط على العوائد.",
          "- **الدلالة الإحصائية:** موسم النتائج هو وحدة الاستقلال: اختبار t على الفروق الموسمية، وإعادة معاينة بالمواسم، وأخطاء مجمّعة في الانحدار.",
          f"- **القيم المتطرفة:** العوائد مقصوصة عند المئين {int(config.WINSOR[0] * 100)} و{int(config.WINSOR[1] * 100)}.", ""]

    L += ["## حدود الدراسة", "",
          "- **تاريخ الإعلان دقيق ليوم واحد تقريباً.** أوقات الإعلان في المصدر تقريبية، لذلك نافذة ردة الفعل ثلاثة أيام ونوافذ ما بعد الإعلان تبدأ من اليوم الثالث.",
          "- **مكوّنان بديلان.** لا يتوفر تاريخ ربعي للإيرادات، فاستُخدمت المفاجأة عن توقعات المحللين بدل نمو الإيرادات، وبيتا السوق بدل الاستقلال الجيوسياسي.",
          "- **انحياز البقاء.** العينة شركات كبيرة مدرجة اليوم، والشركات التي شُطبت غير موجودة.",
          "- **تغطية غير متساوية.** بعض الشركات لها عدد قليل من الإعلانات في المصدر.",
          "- **لا تكاليف تداول.** الأرقام قبل العمولات وفروق الأسعار.",
          "- **ليست توصية استثمارية.** هذه دراسة إحصائية لبيانات تاريخية.", ""]
    (config.REPORT_DIR / "REPORT.md").write_text("\n".join(L), encoding="utf-8")

"""Generate the Power BI project (PBIP) for Muashir: semantic model (TMDL) + report (PBIR).

    python powerbi/generate_pbip.py

The project is plain text so it can be versioned and regenerated. Open
powerbi/Muashir.pbip in Power BI Desktop and press Refresh.
"""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
MODEL = HERE / "Muashir.SemanticModel"
REPORT = HERE / "Muashir.Report"

INK, PANEL, GOLD, CREAM, MUTED, RED, GREEN = "#050505", "#111111", "#C9A227", "#F3EAD3", "#8C8676", "#C0504D", "#5E9E6E"

# ───────────────────────────── semantic model ─────────────────────────────

TABLES = {
    "dim_company": [("ticker", "string"), ("name_ar", "string"), ("sector_ar", "string")],
    "dim_date": [("date", "dateTime"), ("year", "int64"), ("quarter", "int64"), ("season", "string"), ("month", "int64")],
    "dim_window": [("window", "string"), ("window_order", "int64"), ("window_label", "string")],
    "dim_bucket": [("bucket", "int64"), ("bucket_label", "string")],
    "fact_event": [
        ("event_id", "int64"), ("ticker", "string"), ("date", "dateTime"), ("season", "string"), ("year", "int64"),
        ("bucket", "int64"), ("score", "double"), ("n_components", "int64"), ("eps_reported", "double"),
        ("eps_estimate", "double"), ("beta", "double"), ("alpha", "double"), ("price_ref", "double"),
        ("p_yoy", "double"), ("p_qoq", "double"), ("p_surprise", "double"), ("p_consistency", "double"),
        ("p_earn_yield", "double"), ("p_div_yield", "double"), ("p_low_beta", "double"),
    ],
    "fact_abnormal_return": [
        ("event_id", "int64"), ("window", "string"), ("car_mm", "double"), ("car_beta", "double"), ("car_ma", "double"),
        ("raw_ret", "double"), ("mkt_part", "double"), ("car_mm_w", "double"), ("car_beta_w", "double"),
    ],
    "fact_car_path": [("event_id", "int64"), ("rel_day", "int64"), ("ar", "double")],
}
M_TYPES = {"string": "type text", "int64": "Int64.Type", "double": "type number", "dateTime": "type date"}
SORT_BY = {("dim_window", "window_label"): "window_order", ("dim_bucket", "bucket_label"): "bucket"}
VISIBLE = {  # everything else is hidden from the field list
    "dim_company": {"name_ar", "sector_ar", "ticker"}, "dim_date": {"date", "year", "season"},
    "dim_window": {"window_label"}, "dim_bucket": {"bucket_label"},
    "fact_event": {"score"}, "fact_abnormal_return": set(), "fact_car_path": {"rel_day"},
}
RELATIONSHIPS = [
    ("fact_event", "ticker", "dim_company", "ticker"),
    ("fact_event", "date", "dim_date", "date"),
    ("fact_event", "bucket", "dim_bucket", "bucket"),
    ("fact_abnormal_return", "event_id", "fact_event", "event_id"),
    ("fact_abnormal_return", "window", "dim_window", "window"),
    ("fact_car_path", "event_id", "fact_event", "event_id"),
]

PCT = "+0.00%;-0.00%;0.00%"
MEASURES = {
    "fact_event": [
        ("عدد الإعلانات", "COUNTROWS(fact_event)", "#,0"),
        ("عدد الشركات", "DISTINCTCOUNT(fact_event[ticker])", "0"),
        ("عدد المواسم", "DISTINCTCOUNT(fact_event[season])", "0"),
        ("متوسط الدرجة", "AVERAGE(fact_event[score])", "0.0"),
        ("متوسط البيتا", "AVERAGE(fact_event[beta])", "0.00"),
    ],
    "fact_abnormal_return": [
        ("متوسط العائد غير الطبيعي", "AVERAGE(fact_abnormal_return[car_mm_w])", PCT),
        ("متوسط العائد المعدّل بالبيتا", "AVERAGE(fact_abnormal_return[car_beta_w])", PCT),
        ("نسبة الإعلانات الموجبة",
         "DIVIDE(COUNTROWS(FILTER(fact_abnormal_return, fact_abnormal_return[car_mm_w] > 0)), COUNTROWS(fact_abnormal_return))", "0%"),
        ("العائد عند الإعلان", 'CALCULATE([متوسط العائد غير الطبيعي], dim_window[window] = "reaction")', PCT),
        ("العائد بعد الإعلان 60 يوم", 'CALCULATE([متوسط العائد غير الطبيعي], dim_window[window] = "drift_60")', PCT),
        ("العائد بعد الإعلان 60 يوم (بيتا)", 'CALCULATE([متوسط العائد المعدّل بالبيتا], dim_window[window] = "drift_60")', PCT),
        ("العائد قبل الإعلان", 'CALCULATE([متوسط العائد غير الطبيعي], dim_window[window] = "pre")', PCT),
        ("فرق الأعلى والأدنى",
         "CALCULATE([متوسط العائد غير الطبيعي], dim_bucket[bucket] = 5) - CALCULATE([متوسط العائد غير الطبيعي], dim_bucket[bucket] = 1)", PCT),
        ("فرق الأعلى والأدنى (متوسط المواسم)", "AVERAGEX(VALUES(fact_event[season]), [فرق الأعلى والأدنى])", PCT),
        ("الفرق عند الإعلان", 'CALCULATE([فرق الأعلى والأدنى (متوسط المواسم)], dim_window[window] = "reaction")', PCT),
        ("الفرق بعد الإعلان 60 يوم", 'CALCULATE([فرق الأعلى والأدنى (متوسط المواسم)], dim_window[window] = "drift_60")', PCT),
        ("الفرق بعد الإعلان 60 يوم (بيتا)",
         'CALCULATE(AVERAGEX(VALUES(fact_event[season]), CALCULATE([متوسط العائد المعدّل بالبيتا], dim_bucket[bucket] = 5) - '
         'CALCULATE([متوسط العائد المعدّل بالبيتا], dim_bucket[bucket] = 1)), dim_window[window] = "drift_60")', PCT),
    ],
    "fact_car_path": [
        ("العائد التراكمي",
         "VAR d = MAX(fact_car_path[rel_day]) RETURN SUMX(FILTER(ALL(fact_car_path[rel_day]), fact_car_path[rel_day] <= d), "
         "CALCULATE(AVERAGE(fact_car_path[ar])))", PCT),
    ],
}


def tid() -> str:
    return str(uuid.uuid4())


def table_tmdl(name: str, cols: list) -> str:
    out = [f"table {name}", f"\tlineageTag: {tid()}", ""]
    for mname, expr, fmt in MEASURES.get(name, []):
        out += [f"\tmeasure '{mname}' = {expr}", f"\t\tformatString: {fmt}", f"\t\tlineageTag: {tid()}", ""]
    for col, typ in cols:
        out += [f"\tcolumn {col}", f"\t\tdataType: {typ}"]
        if typ == "dateTime":
            out += ["\t\tformatString: yyyy-mm-dd"]
        if col not in VISIBLE[name]:
            out += ["\t\tisHidden"]
        out += [f"\t\tlineageTag: {tid()}", "\t\tsummarizeBy: none", f"\t\tsourceColumn: {col}"]
        if (name, col) in SORT_BY:
            out += [f"\t\tsortByColumn: {SORT_BY[(name, col)]}"]
        out += [""]
    types = ", ".join('{"%s", %s}' % (c, M_TYPES[t]) for c, t in cols)
    out += [
        f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =",
        "\t\t\t\tlet",
        f'\t\t\t\t    Source = Csv.Document(File.Contents(DataFolder & "\\{name}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "\t\t\t\t    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f'\t\t\t\t    Typed = Table.TransformColumnTypes(Promoted, {{{types}}}, "en-US")',
        "\t\t\t\tin", "\t\t\t\t    Typed", "",
    ]
    return "\n".join(out)


def write_model() -> None:
    d = MODEL / "definition"
    (d / "tables").mkdir(parents=True)
    (MODEL / "definition.pbism").write_text(json.dumps({"version": "4.0", "settings": {}}, indent=2), encoding="utf-8")
    (d / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1567\n", encoding="utf-8")
    model = ["model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
             "\tsourceQueryCulture: en-US", "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
             "annotation __PBI_TimeIntelligenceEnabled = 0", ""]
    model += [f"ref table {t}" for t in TABLES] + ["", "ref expression DataFolder", ""]
    (d / "model.tmdl").write_text("\n".join(model), encoding="utf-8")
    (d / "expressions.tmdl").write_text(
        f'expression DataFolder = "{DATA}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
        f"\tlineageTag: {tid()}\n\n\tannotation PBI_ResultType = Text\n", encoding="utf-8")
    rel = []
    for ft, fc, tt, tc in RELATIONSHIPS:
        rel += [f"relationship {tid()}", f"\tfromColumn: {ft}.{fc}", f"\ttoColumn: {tt}.{tc}", ""]
    (d / "relationships.tmdl").write_text("\n".join(rel), encoding="utf-8")
    for name, cols in TABLES.items():
        (d / "tables" / f"{name}.tmdl").write_text(table_tmdl(name, cols), encoding="utf-8")


# ───────────────────────────────── report ─────────────────────────────────

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"


def lit(v) -> dict:
    if isinstance(v, bool):
        return {"expr": {"Literal": {"Value": "true" if v else "false"}}}
    if isinstance(v, (int, float)):
        return {"expr": {"Literal": {"Value": f"{v}D"}}}
    return {"expr": {"Literal": {"Value": "'" + str(v).replace("'", "''") + "'"}}}


def color(hex_: str) -> dict:
    return {"solid": {"color": lit(hex_)}}


def col(table: str, name: str) -> dict:
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}},
            "queryRef": f"{table}.{name}", "nativeQueryRef": name}


def mea(table: str, name: str) -> dict:
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}},
            "queryRef": f"{table}.{name}", "nativeQueryRef": name}


def container(title: str | None) -> dict:
    objs = {
        "background": [{"properties": {"show": lit(True), "color": color(PANEL), "transparency": lit(0)}}],
        "border": [{"properties": {"show": lit(False)}}],
        "visualHeader": [{"properties": {"show": lit(False)}}],
    }
    if title:
        objs["title"] = [{"properties": {"show": lit(True), "text": lit(title), "fontColor": color(CREAM),
                                         "fontSize": lit(11), "alignment": lit("right")}}]
    else:
        objs["title"] = [{"properties": {"show": lit(False)}}]
    return objs


def visual(name: str, vtype: str, pos: tuple, query: dict | None, title: str | None = None, objects: dict | None = None) -> tuple:
    x, y, w, h = pos
    v = {"visualType": vtype, "visualContainerObjects": container(title), "drillFilterOtherVisuals": True}
    if query:
        v["query"] = {"queryState": {role: {"projections": projs} for role, projs in query.items()}}
    if objects:
        v["objects"] = objects
    return name, {"$schema": f"{SCHEMA}/visualContainer/1.0.0/schema.json", "name": name,
                  "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": 0}, "visual": v}


def textbox(name: str, pos: tuple, text: str, size: int, colour: str, bold: bool = False) -> tuple:
    style = {"fontSize": f"{size}pt", "color": colour}
    if bold:
        style["fontWeight"] = "bold"
    objs = {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": text, "textStyle": style}], "horizontalTextAlignment": "right"}]}}]}
    n, v = visual(name, "textbox", pos, None, None, objs)
    v["visual"]["visualContainerObjects"]["background"] = [{"properties": {"show": lit(False)}}]
    return n, v


def card(name: str, pos: tuple, table: str, measure: str, title: str) -> tuple:
    objs = {
        "labels": [{"properties": {"color": color(GOLD), "fontSize": lit(26)}}],
        "categoryLabels": [{"properties": {"show": lit(False)}}],
    }
    return visual(name, "card", pos, {"Values": [mea(table, measure)]}, title, objs)


AXIS = {"labelColor": color(MUTED), "showAxisTitle": lit(False), "gridlineColor": color("#222222")}


def page_summary() -> list:
    v = [
        textbox("title", (640, 20, 600, 50), "مؤشّر · دراسة إعلانات النتائج", 22, CREAM, True),
        textbox("subtitle", (440, 66, 800, 34), "هل الشركات الأعلى درجة عند إعلان نتائجها يتفوق سهمها؟ السوق السعودي 2016–2026", 11, MUTED),
        card("c_events", (980, 110, 260, 110), "fact_event", "عدد الإعلانات", "إعلان نتائج"),
        card("c_companies", (700, 110, 260, 110), "fact_event", "عدد الشركات", "شركة"),
        card("c_react", (420, 110, 260, 110), "fact_abnormal_return", "الفرق عند الإعلان", "فرق الأعلى والأدنى درجة عند الإعلان"),
        card("c_drift", (140, 110, 260, 110), "fact_abnormal_return", "الفرق بعد الإعلان 60 يوم", "الفرق في 60 يوم بعد الإعلان"),
        visual("bar_react", "clusteredColumnChart", (660, 240, 580, 220),
               {"Category": [col("dim_bucket", "bucket_label")], "Y": [mea("fact_abnormal_return", "العائد عند الإعلان")]},
               "العائد غير الطبيعي عند الإعلان حسب مجموعة الدرجة",
               {"dataPoint": [{"properties": {"fill": color(GOLD)}}], "categoryAxis": [{"properties": AXIS}],
                "valueAxis": [{"properties": AXIS}], "legend": [{"properties": {"show": lit(False)}}]}),
        visual("bar_drift", "clusteredColumnChart", (140, 240, 500, 220),
               {"Category": [col("dim_bucket", "bucket_label")],
                "Y": [mea("fact_abnormal_return", "العائد بعد الإعلان 60 يوم"), mea("fact_abnormal_return", "العائد بعد الإعلان 60 يوم (بيتا)")]},
               "العائد في 60 يوم بعد الإعلان: نموذج السوق مقابل المعدّل بالبيتا",
               {"categoryAxis": [{"properties": AXIS}], "valueAxis": [{"properties": AXIS}],
                "legend": [{"properties": {"show": lit(True), "labelColor": color(MUTED), "position": lit("Top")}}]}),
        visual("line_path", "lineChart", (140, 480, 1100, 220),
               {"Category": [col("fact_car_path", "rel_day")], "Series": [col("dim_bucket", "bucket_label")],
                "Y": [mea("fact_car_path", "العائد التراكمي")]},
               "العائد غير الطبيعي التراكمي حول الإعلان (اليوم 0 = الإعلان)",
               {"categoryAxis": [{"properties": {**AXIS, "axisType": lit("Continuous")}}], "valueAxis": [{"properties": AXIS}],
                "legend": [{"properties": {"show": lit(True), "labelColor": color(MUTED), "position": lit("Top")}}]}),
        visual("s_sector", "slicer", (20, 110, 110, 290), {"Values": [col("dim_company", "sector_ar")]}, "القطاع",
               {"header": [{"properties": {"show": lit(False)}}], "items": [{"properties": {"fontColor": color(CREAM), "textSize": lit(9)}}]}),
        visual("s_year", "slicer", (20, 410, 110, 290), {"Values": [col("dim_date", "year")]}, "السنة",
               {"header": [{"properties": {"show": lit(False)}}], "items": [{"properties": {"fontColor": color(CREAM), "textSize": lit(9)}}],
                "data": [{"properties": {"mode": lit("Basic")}}]}),
    ]
    return v


def page_companies() -> list:
    grid = {
        "columnHeaders": [{"properties": {"fontColor": color(GOLD), "backColor": color(PANEL), "fontSize": lit(10)}}],
        "values": [{"properties": {"fontColor": color(CREAM), "backColor": color(PANEL), "fontColorAlternate": color(CREAM),
                                   "backColorAlternate": color("#181818"), "fontSize": lit(10)}}],
        "grid": [{"properties": {"gridVertical": lit(False), "gridHorizontalColor": color("#222222"), "rowPadding": lit(4)}}],
        "total": [{"properties": {"fontColor": color(GOLD), "backColor": color(PANEL)}}],
    }
    return [
        textbox("title2", (640, 20, 600, 50), "مؤشّر · الشركات والقطاعات", 22, CREAM, True),
        textbox("subtitle2", (440, 66, 800, 34), "متوسطات كل شركة على كل إعلاناتها في العينة", 11, MUTED),
        visual("tbl", "tableEx", (420, 110, 820, 590),
               {"Values": [col("dim_company", "name_ar"), col("dim_company", "sector_ar"), mea("fact_event", "عدد الإعلانات"),
                           mea("fact_event", "متوسط الدرجة"), mea("fact_event", "متوسط البيتا"),
                           mea("fact_abnormal_return", "العائد عند الإعلان"), mea("fact_abnormal_return", "العائد بعد الإعلان 60 يوم")]},
               "الشركات", grid),
        visual("bar_sector", "clusteredBarChart", (20, 110, 380, 290),
               {"Category": [col("dim_company", "sector_ar")], "Y": [mea("fact_event", "متوسط الدرجة")]},
               "متوسط الدرجة حسب القطاع",
               {"dataPoint": [{"properties": {"fill": color(GOLD)}}], "categoryAxis": [{"properties": AXIS}],
                "valueAxis": [{"properties": AXIS}], "legend": [{"properties": {"show": lit(False)}}]}),
        visual("bar_window", "clusteredColumnChart", (20, 410, 380, 290),
               {"Category": [col("dim_window", "window_label")], "Y": [mea("fact_abnormal_return", "فرق الأعلى والأدنى (متوسط المواسم)")]},
               "فرق الأعلى والأدنى درجة حسب النافذة",
               {"dataPoint": [{"properties": {"fill": color(GOLD)}}], "categoryAxis": [{"properties": AXIS}],
                "valueAxis": [{"properties": AXIS}], "legend": [{"properties": {"show": lit(False)}}]}),
    ]


THEME = {
    "name": "Muashir",
    "dataColors": [GOLD, MUTED, CREAM, RED, GREEN, "#7A6A3A", "#B9B2A0", "#5A5A5A"],
    "background": INK, "foreground": CREAM, "tableAccent": GOLD,
    "good": GREEN, "neutral": MUTED, "bad": RED,
    "textClasses": {
        "label": {"color": MUTED, "fontFace": "Segoe UI"},
        "callout": {"color": GOLD, "fontFace": "Segoe UI Semibold"},
        "title": {"color": CREAM, "fontFace": "Segoe UI Semibold"},
        "header": {"color": CREAM, "fontFace": "Segoe UI Semibold"},
    },
    "visualStyles": {"page": {"*": {
        "background": [{"color": {"solid": {"color": INK}}, "transparency": 0}],
        "outspace": [{"color": {"solid": {"color": INK}}, "transparency": 0}],
    }}},
}


def write_report() -> None:
    d = REPORT / "definition"
    (d / "pages").mkdir(parents=True)
    (REPORT / "definition.pbir").write_text(json.dumps(
        {"version": "4.0", "datasetReference": {"byPath": {"path": "../Muashir.SemanticModel"}}}, indent=2), encoding="utf-8")
    res = REPORT / "StaticResources" / "RegisteredResources"
    res.mkdir(parents=True)
    (res / "Muashir.json").write_text(json.dumps(THEME, ensure_ascii=False, indent=2), encoding="utf-8")

    (d / "version.json").write_text(json.dumps(
        {"$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, indent=2), encoding="utf-8")
    (d / "report.json").write_text(json.dumps({
        "$schema": f"{SCHEMA}/report/1.0.0/schema.json",
        "themeCollection": {"customTheme": {"name": "Muashir.json", "reportVersionAtImport": "5.59", "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": "Muashir.json", "path": "Muashir.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    pages = [("summary", "الخلاصة", page_summary()), ("companies", "الشركات", page_companies())]
    (d / "pages" / "pages.json").write_text(json.dumps({
        "$schema": f"{SCHEMA}/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p[0] for p in pages], "activePageName": pages[0][0]}, indent=2), encoding="utf-8")
    for pname, display, visuals in pages:
        pd_ = d / "pages" / pname
        (pd_ / "visuals").mkdir(parents=True)
        (pd_ / "page.json").write_text(json.dumps({
            "$schema": f"{SCHEMA}/page/1.0.0/schema.json", "name": pname, "displayName": display,
            "displayOption": "FitToPage", "height": 720, "width": 1280,
            "objects": {"background": [{"properties": {"color": color(INK), "transparency": lit(0)}}],
                        "outspace": [{"properties": {"color": color(INK), "transparency": lit(0)}}]},
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        for i, (vname, vjson) in enumerate(visuals):
            vjson["position"]["z"] = i * 1000
            vjson["position"]["tabOrder"] = i * 1000
            vd = pd_ / "visuals" / vname
            vd.mkdir()
            (vd / "visual.json").write_text(json.dumps(vjson, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    for p in (MODEL, REPORT):
        if p.exists():
            shutil.rmtree(p)
    write_model()
    write_report()
    (HERE / "Muashir.pbip").write_text(json.dumps({
        "version": "1.0", "artifacts": [{"report": {"path": "Muashir.Report"}}],
        "settings": {"enableAutoRecovery": True}}, indent=2), encoding="utf-8")
    print("written:", HERE / "Muashir.pbip")


if __name__ == "__main__":
    main()

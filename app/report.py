"""PDF export of the National overview -- the "Download report" button.

Built entirely from the ``district_risk`` artifact and the same
:mod:`dengue.platform.risk` functions ``national_overview()`` already calls,
so generating a report is page-load-cheap formatting of numbers the pipeline
already produced -- not a second compute path alongside it, and not a reason
to relax the "never compute at request time" rule the rest of the app
follows.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from dengue import config
from dengue.platform.risk import assess_all, classify, national_summary

DISTRICT_NAMES = {d.district_id: d.name for d in config.DISTRICTS}

#: Same hex values as theme.py's RiskLevel colours -- duplicated rather than
#: imported because reportlab needs its own colors.HexColor wrapper, not a
#: raw string, at every use site.
_RISK_FILL = {
    "low": colors.HexColor("#0f766e"),
    "moderate": colors.HexColor("#ca8a04"),
    "high": colors.HexColor("#ea580c"),
    "severe": colors.HexColor("#b91c1c"),
}

_INK_SECONDARY = colors.HexColor("#52514e")
_BRAND_BLUE = colors.HexColor("#1c5cab")
_HAIRLINE = colors.HexColor("#e1e0d9")
_PAGE_TINT = colors.HexColor("#eeece2")


def build_report_pdf(
    district_risk: pd.DataFrame,
    *,
    horizon: int,
    role_label: str,
    scope_label: str,
    is_synthetic: bool,
    pipeline_meta_row: pd.Series | None,
) -> bytes:
    """Render a PDF summary of the National overview for the given horizon.

    Parameters mirror what ``national_overview()`` already has in scope --
    this recomputes only the same risk classification and KPI aggregation
    that function calls, not a forecast or an allocation.

    Returns
    -------
    bytes
        A complete PDF file, ready for ``st.download_button``.
    """
    frame = district_risk[district_risk["horizon"] == horizon].copy()
    frame["risk_level"] = frame["incidence_per_100k"].apply(lambda v: classify(float(v or 0)).value)
    frame["district"] = frame["district_id"].map(DISTRICT_NAMES).fillna(frame["district_id"])

    assessments = assess_all(district_risk, horizon_weeks=horizon, audience="public")
    summary = national_summary(assessments)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="DengueSentinel National Overview Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], textColor=_BRAND_BLUE)
    meta_style = ParagraphStyle("ReportMeta", parent=styles["Normal"], textColor=_INK_SECONDARY)
    caveat_style = ParagraphStyle(
        "ReportCaveat",
        parent=styles["Normal"],
        textColor=colors.HexColor("#8a1414"),
        backColor=colors.HexColor("#fbe8e8"),
        borderPadding=8,
        spaceAfter=4,
    )
    confirm_style = ParagraphStyle(
        "ReportConfirm",
        parent=styles["Normal"],
        textColor=colors.HexColor("#0c5c1f"),
        backColor=colors.HexColor("#e6f4e8"),
        borderPadding=8,
        spaceAfter=4,
    )

    story: list = []
    story.append(Paragraph("DengueSentinel — National Overview Report", title_style))
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    story.append(
        Paragraph(
            f"Generated {generated} &middot; Viewing as <b>{role_label}</b> &middot; "
            f"Scope: {scope_label} &middot; {horizon} weeks ahead",
            meta_style,
        )
    )
    story.append(Spacer(1, 10))

    # Same provenance caveat as the live dashboard's banner -- a report that
    # drops this the moment it leaves the browser would be exactly the
    # failure mode the whole provenance-tier system exists to prevent.
    if is_synthetic:
        story.append(
            Paragraph(
                "<b>Simulated data.</b> This report was generated from the synthetic panel "
                "— realistic dynamics, but not observations. Do not read any figure "
                "below as real epidemiology.",
                caveat_style,
            )
        )
    elif pipeline_meta_row is not None:
        row = pipeline_meta_row
        story.append(
            Paragraph(
                f"<b>Real data.</b> Panel: {int(row['panel_rows']):,} rows, "
                f"{int(row['n_districts'])} districts, {row['panel_start']} "
                f"→ {row['panel_end']}. Sourced from the Epidemiology Unit WER "
                "reports and Open-Meteo.",
                confirm_style,
            )
        )
    story.append(Spacer(1, 16))

    kpi_rows = [
        ["Districts forecast", f"{summary['n_districts']} of 25"],
        ["High risk or above", f"{summary['n_severe'] + summary['n_high']} districts"],
        ["Forecast cases (nationwide)", f"{summary['total_forecast_cases']:,.0f}"],
        ["Highest risk district", f"{summary['worst_district']} ({summary['worst_level']})"],
    ]
    kpi_table = Table(kpi_rows, colWidths=[7 * cm, 7 * cm])
    kpi_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), _INK_SECONDARY),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, _HAIRLINE),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 18))

    story.append(
        Paragraph("Every district, ranked by incidence per 100,000 per week", styles["Heading2"])
    )
    story.append(Spacer(1, 4))

    ranked = frame.sort_values("incidence_per_100k", ascending=False)
    header = ["District", "Risk", "Forecast cases", "Per 100,000/week"]
    table_rows = [header]
    row_colours: list[colors.Color] = []
    for _, row in ranked.iterrows():
        risk_level = str(row["risk_level"])
        table_rows.append(
            [
                str(row["district"]),
                risk_level.title(),
                f"{row.get('q0.5', 0):,.0f}",
                f"{row['incidence_per_100k']:.1f}",
            ]
        )
        row_colours.append(_RISK_FILL.get(risk_level, colors.black))

    district_table = Table(table_rows, colWidths=[5 * cm, 3 * cm, 4 * cm, 4 * cm], repeatRows=1)
    style_cmds = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), _PAGE_TINT),
        ("GRID", (0, 0), (-1, -1), 0.4, _HAIRLINE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
    ]
    for i, colour in enumerate(row_colours, start=1):
        style_cmds.append(("TEXTCOLOR", (1, i), (1, i), colour))
        style_cmds.append(("FONTNAME", (1, i), (1, i), "Helvetica-Bold"))
    district_table.setStyle(TableStyle(style_cmds))
    story.append(district_table)

    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "Boundaries: OCHA/HDX (CC-BY-IGO) &middot; Facilities: OpenStreetMap "
            "contributors (ODbL) &middot; Weather: Open-Meteo/ERA5 (CC-BY) &middot; Bed "
            "density: World Bank (CC-BY) &middot; Cases: colmozzie (CC0) / Epidemiology "
            "Unit, Sri Lanka. Generated by DengueSentinel from cached pipeline artifacts "
            "only — nothing was refit or re-solved to produce this report.",
            meta_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()

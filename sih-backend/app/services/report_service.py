from pathlib import Path
from tempfile import NamedTemporaryFile
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


def _display(value: Any) -> str:
    if value in (None, "", "null", "None"):
        return "Not detected"
    return str(value)


def generate_compliance_report(result: dict) -> str:
    scan_id = result.get("scan_id", "unknown")
    filename = result.get("filename", "unknown")
    status = result.get("status", "UNKNOWN")

    declarations = result.get("declarations", [])
    violations = result.get("violations", [])

    temp_file = NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
    )
    temp_file.close()

    pdf_path = temp_file.name

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=6 * mm,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=10 * mm,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
    )

    normal_style = ParagraphStyle(
        "NormalReport",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
    )

    story = []

    # -------------------------------------------------
    # HEADER
    # -------------------------------------------------

    story.append(
        Paragraph(
            "NEXORA",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "LEGAL METROLOGY COMPLIANCE REPORT",
            subtitle_style,
        )
    )

    # -------------------------------------------------
    # STATUS
    # -------------------------------------------------

    status_text = {
        "PASS": "COMPLIANT",
        "FAIL": "NON-COMPLIANT",
        "REVIEW": "MANUAL REVIEW REQUIRED",
    }.get(status, status)

    status_table = Table(
        [
            [
                Paragraph(
                    "<b>FINAL STATUS</b>",
                    normal_style,
                ),
                Paragraph(
                    f"<b>{status_text}</b>",
                    normal_style,
                ),
            ]
        ],
        colWidths=[55 * mm, 110 * mm],
    )

    status_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(status_table)
    story.append(Spacer(1, 5 * mm))

    # -------------------------------------------------
    # INSPECTION SUMMARY
    # -------------------------------------------------

    story.append(
        Paragraph(
            "1. Inspection Summary",
            heading_style,
        )
    )

    summary_data = [
        ["Scan ID", _display(scan_id)],
        ["File Name", _display(filename)],
        [
            "Inspection Date",
            datetime.now().strftime("%d %B %Y, %I:%M %p"),
        ],
        ["Result", status_text],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[55 * mm, 110 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(summary_table)

    # -------------------------------------------------
    # DECLARATIONS
    # -------------------------------------------------

    story.append(
        Paragraph(
            "2. Detected Product Declarations",
            heading_style,
        )
    )

    declaration_data = [
        [
            "Field",
            "Detected Value",
            "Confidence",
        ]
    ]

    for item in declarations:
        confidence = item.get("confidence")

        if confidence is None:
            confidence_text = "N/A"
        else:
            confidence_text = f"{confidence * 100:.1f}%"

        declaration_data.append(
            [
                _display(item.get("field")),
                _display(item.get("value")),
                confidence_text,
            ]
        )

    declaration_table = Table(
        declaration_data,
        colWidths=[55 * mm, 80 * mm, 30 * mm],
        repeatRows=1,
    )

    declaration_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(declaration_table)

    # -------------------------------------------------
    # VIOLATIONS
    # -------------------------------------------------

    story.append(
        Paragraph(
            "3. Compliance Violations / Review Items",
            heading_style,
        )
    )

    if not violations:

        story.append(
            Paragraph(
                "No violations were detected by the current Rule Engine.",
                normal_style,
            )
        )

    else:

        violation_data = [
            [
                "Rule",
                "Issue",
                "Expected",
                "Detected",
                "Severity",
            ]
        ]

        for violation in violations:

            rule = violation.get("rule") or violation.get("field")
            issue = violation.get("issue") or violation.get("reason")
            expected = violation.get("expected")
            detected = violation.get("detected")
            severity = violation.get("severity", "MEDIUM")

            violation_data.append(
                [
                    _display(rule),
                    _display(issue),
                    _display(expected),
                    _display(detected),
                    _display(severity),
                ]
            )

        violation_table = Table(
            violation_data,
            colWidths=[
                20 * mm,
                55 * mm,
                35 * mm,
                35 * mm,
                20 * mm,
            ],
            repeatRows=1,
        )

        violation_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#E8EEF5"),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        story.append(violation_table)

    # -------------------------------------------------
    # MESSAGE
    # -------------------------------------------------

    story.append(
        Paragraph(
            "4. Assessment",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            _display(result.get("message")),
            normal_style,
        )
    )

    # -------------------------------------------------
    # DISCLAIMER
    # -------------------------------------------------

    story.append(
        Paragraph(
            "5. Disclaimer",
            heading_style,
        )
    )

    disclaimer = (
        "This report is generated automatically by Nexora based on "
        "the information extracted from the submitted product label "
        "and evaluated by the configured compliance Rule Engine. "
        "A PASS result indicates that no configured violations were "
        "detected from the available information; it should not be "
        "treated as a substitute for an official inspection or legal "
        "determination."
    )

    story.append(
        Paragraph(
            disclaimer,
            normal_style,
        )
    )

    doc.build(story)

    return pdf_path
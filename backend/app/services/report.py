from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.audit import CaseRecord


DISCLAIMER = (
    "AI-assisted screening result. Automated analysis is intended to assist authorized "
    "human review and does not by itself establish fraud, forgery, or identity."
)


def safe_text(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def section(title: str, rows: list[list[str]]) -> Table:
    table = Table(
        [[Paragraph(f"<b>{safe_text(title)}</b>", ParagraphStyle("section", textColor=colors.HexColor("#0B6E69")))]] + rows,
        colWidths=[55 * mm, 125 * mm],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F2EF")),
        ("SPAN", (0, 0), (-1, 0)),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C7D8D4")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def build_screening_report(case: CaseRecord) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm, pageCompression=0)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("report_title", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#123D55"), spaceAfter=5)
    body = styles["BodyText"]
    details = case.details or {}
    ocr = details.get("ocr", {})
    validation = details.get("validation", [])
    tampering = details.get("tampering", {})
    metadata = details.get("metadata", {})
    face = details.get("face_comparison", {})
    risk = details.get("risk", {})
    field_rows = [[safe_text(field.get("name")), safe_text(field.get("value") or "Not detected")] for field in ocr.get("fields", [])]
    validation_rows = [[safe_text(item.get("name")), safe_text(item.get("status")), safe_text(item.get("message"))] for item in validation]
    event_rows = [[safe_text(event.event_type), safe_text(event.module_name), event.timestamp.isoformat(), safe_text(event.status)] for event in case.events]
    story = [
        Paragraph("IDENTITY SCREENING REPORT", title),
        Paragraph("AI-assisted decision-support record · Demonstration Mode", body), Spacer(1, 8),
        section("CASE INFORMATION", [["Case ID", safe_text(case.case_id)], ["Document type", safe_text(case.document_type)], ["Screening timestamp", case.screening_timestamp.isoformat()], ["Status", safe_text(case.screening_status)], ["Mode", "DEMONSTRATION"]]), Spacer(1, 8),
        section("DOCUMENT INTEGRITY", [["SHA-256", safe_text(f"sha256:{case.document_hash}" if case.document_hash else "Not available")], ["Integrity status", "Original bytes hashed server-side"]]), Spacer(1, 8),
        section("OCR EXTRACTION", [["Mode", safe_text(ocr.get("mode", "Not available"))], ["Confidence", safe_text(ocr.get("confidence", "Not checked"))], ["Raw text", "Not reproduced in this report"]] + field_rows), Spacer(1, 8),
        section("DOCUMENT VALIDATION", [["Check", "Status / message"]] + validation_rows), Spacer(1, 8),
        section("METADATA ANALYSIS", [["Status", safe_text(metadata.get("status", "Not available"))], ["Findings", safe_text(", ".join(metadata.get("findings", [])))] ]), Spacer(1, 8),
        section("TAMPER ANALYSIS", [["Risk score", safe_text(tampering.get("risk_score", "Not available"))], ["Assessment", safe_text(tampering.get("assessment", "Not available"))], ["Signals", safe_text(", ".join(tampering.get("indicators", [])))], ["Limitations", safe_text(", ".join(tampering.get("limitations", [])))] ]), Spacer(1, 8),
        section("FACE COMPARISON", [["Status", safe_text(face.get("status", "NOT_AVAILABLE"))], ["Document face", safe_text(face.get("document_face", {}).get("status", "NOT_AVAILABLE"))], ["Presented face", safe_text(face.get("presented_face", {}).get("status", "NOT_AVAILABLE"))], ["Review", "Human review required; no automatic identity decision"]]), Spacer(1, 8),
        section("OVERALL RISK", [["Level", safe_text(risk.get("level", case.risk_level or "Not available"))], ["Score", safe_text(risk.get("score", case.risk_score or "Not available"))], ["Reasons", safe_text("; ".join(risk.get("reasons", [])))] ]), Spacer(1, 8),
        section("AUDIT TRAIL", [["Event", "Module / timestamp / status"]] + [[row[0], f"{row[1]} / {row[2]} / {row[3]}"] for row in event_rows]), Spacer(1, 10),
        Paragraph(f"<b>LIMITATION AND DISCLAIMER</b><br/>{safe_text(DISCLAIMER)}", body),
    ]
    document.build(story)
    return output.getvalue()

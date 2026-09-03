"""PDF generation service for WaterTrack hydration reports."""

import io
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from app.features.goals.repository import SettingsRepository
from app.features.users.models import User
from app.features.waterlogs.repository import WaterLogRepository


class PDFReportService:
    @staticmethod
    def generate_intake_report_pdf(
        db: Session,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> io.BytesIO:
        """Generates a styled, multi-section PDF hydration summary report."""
        # Default to the last 30 days if date range not specified
        today = datetime.now(timezone.utc).date()
        if end_date is None:
            end_date = today
        if start_date is None:
            start_date = end_date - timedelta(days=29)

        # Retrieve user settings & logs
        settings = SettingsRepository.get_or_create(db, user.id)
        daily_goal_ml = float(settings.daily_goal_ml)
        all_logs = WaterLogRepository.get_all_by_user(db, user.id)

        # Filter logs within date range
        filtered_logs = []
        for log in all_logs:
            log_date = log.logged_at.date() if isinstance(log.logged_at, datetime) else log.logged_at
            if start_date <= log_date <= end_date:
                filtered_logs.append(log)

        # Aggregate daily intakes
        num_days = (end_date - start_date).days + 1
        date_range_list = [start_date + timedelta(days=i) for i in range(num_days)]
        
        daily_intake_map = {d: 0.0 for d in date_range_list}
        for log in filtered_logs:
            log_date = log.logged_at.date() if isinstance(log.logged_at, datetime) else log.logged_at
            daily_intake_map[log_date] = daily_intake_map.get(log_date, 0.0) + float(log.amount_ml)

        total_intake_ml = sum(daily_intake_map.values())
        logged_days_count = sum(1 for v in daily_intake_map.values() if v > 0)
        goals_met_count = sum(1 for v in daily_intake_map.values() if v >= daily_goal_ml)
        average_daily_ml = (total_intake_ml / num_days) if num_days > 0 else 0.0
        success_rate = (goals_met_count / num_days * 100.0) if num_days > 0 else 0.0

        # Create in-memory PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom Palette
        primary_color = colors.HexColor("#0284C7")  # Ocean Cyan / Blue
        dark_header = colors.HexColor("#0F172A")   # Slate 900
        muted_text = colors.HexColor("#64748B")    # Slate 500
        bg_card = colors.HexColor("#F8FAFC")       # Slate 50
        border_color = colors.HexColor("#E2E8F0")  # Slate 200

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=primary_color,
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=muted_text,
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=dark_header,
        )
        card_label_style = ParagraphStyle(
            "CardLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=muted_text,
            alignment=1,  # Center
        )
        card_val_style = ParagraphStyle(
            "CardVal",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=dark_header,
            alignment=1,  # Center
        )
        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.white,
            alignment=1,
        )
        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=dark_header,
            alignment=1,
        )

        elements = []

        # Header Title Banner
        header_table = Table(
            [
                [
                    Paragraph("WaterTrack Hydration Summary", title_style),
                    Paragraph(
                        f"Generated: {datetime.now(timezone.utc).strftime('%b %d, %Y %H:%M UTC')}<br/>"
                        f"Period: <b>{start_date.strftime('%b %d, %Y')}</b> to <b>{end_date.strftime('%b %d, %Y')}</b>",
                        ParagraphStyle("RightText", parent=subtitle_style, alignment=2),
                    ),
                ]
            ],
            colWidths=[4.2 * inch, 3.3 * inch],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=12))

        # Section 1: User Profile & Target
        elements.append(Paragraph("User Profile & Daily Target", section_heading))
        elements.append(Spacer(1, 5))

        user_info_data = [
            [
                Paragraph("<b>Name:</b> " + (user.full_name or "N/A"), styles["Normal"]),
                Paragraph("<b>Email:</b> " + user.email, styles["Normal"]),
                Paragraph(f"<b>Weight:</b> {user.weight_kg or 'Not set'} kg", styles["Normal"]),
            ],
            [
                Paragraph(f"<b>Activity Level:</b> {(user.activity_level or 'Moderate').title()}", styles["Normal"]),
                Paragraph(f"<b>Daily Hydration Goal:</b> <b>{int(daily_goal_ml)} ml</b>", styles["Normal"]),
                Paragraph(f"<b>Days Tracked:</b> {logged_days_count} / {num_days} days", styles["Normal"]),
            ],
        ]
        user_info_table = Table(user_info_data, colWidths=[2.5 * inch, 2.7 * inch, 2.3 * inch])
        user_info_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), bg_card),
                    ("BOX", (0, 0), (-1, -1), 1, border_color),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(user_info_table)
        elements.append(Spacer(1, 12))

        # Section 2: Key Metrics KPI Grid
        elements.append(Paragraph("Key Hydration Performance", section_heading))
        elements.append(Spacer(1, 5))

        kpi_data = [
            [
                Paragraph("TOTAL CONSUMPTION", card_label_style),
                Paragraph("DAILY AVERAGE", card_label_style),
                Paragraph("GOAL SUCCESS RATE", card_label_style),
                Paragraph("GOALS COMPLETED", card_label_style),
            ],
            [
                Paragraph(f"<b>{total_intake_ml / 1000.0:.2f} L</b><br/><font size=7 color='#64748B'>({int(total_intake_ml):,} ml)</font>", card_val_style),
                Paragraph(f"<b>{int(average_daily_ml):,} ml</b><br/><font size=7 color='#64748B'>per day</font>", card_val_style),
                Paragraph(f"<font color='{'#16A34A' if success_rate >= 75 else '#D97706'}'><b>{success_rate:.1f}%</b></font><br/><font size=7 color='#64748B'>compliance</font>", card_val_style),
                Paragraph(f"<b>{goals_met_count} / {num_days}</b><br/><font size=7 color='#64748B'>target met days</font>", card_val_style),
            ],
        ]
        kpi_table = Table(kpi_data, colWidths=[1.87 * inch, 1.87 * inch, 1.87 * inch, 1.87 * inch])
        kpi_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), bg_card),
                    ("BOX", (0, 0), (-1, -1), 1, border_color),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(kpi_table)
        elements.append(Spacer(1, 12))

        # Section 3: Daily Log Breakdown Table (Show up to 30 days)
        display_days = min(num_days, 30)
        elements.append(Paragraph(f"Daily Intake Breakdown (Recent {display_days} Days)", section_heading))
        elements.append(Spacer(1, 5))

        table_rows = [
            [
                Paragraph("Date", table_header_style),
                Paragraph("Intake (ml)", table_header_style),
                Paragraph("Daily Goal (ml)", table_header_style),
                Paragraph("% of Goal", table_header_style),
                Paragraph("Status", table_header_style),
            ]
        ]

        # Display descending order by date
        sorted_dates = sorted(date_range_list, reverse=True)[:display_days]
        for d in sorted_dates:
            intake = daily_intake_map[d]
            pct = (intake / daily_goal_ml * 100.0) if daily_goal_ml > 0 else 0.0
            is_met = intake >= daily_goal_ml

            status_text = (
                "<font color='#16A34A'><b>Achieved</b></font>"
                if is_met
                else ("<font color='#D97706'>Below Goal</font>" if intake > 0 else "<font color='#94A3B8'>No Entry</font>")
            )

            table_rows.append(
                [
                    Paragraph(d.strftime("%a, %b %d, %Y"), table_cell_style),
                    Paragraph(f"{int(intake):,} ml", table_cell_style),
                    Paragraph(f"{int(daily_goal_ml):,} ml", table_cell_style),
                    Paragraph(f"{pct:.1f}%", table_cell_style),
                    Paragraph(status_text, table_cell_style),
                ]
            )

        daily_table = Table(
            table_rows,
            colWidths=[1.8 * inch, 1.4 * inch, 1.4 * inch, 1.3 * inch, 1.6 * inch],
        )
        
        # Style table with alternating row backgrounds
        daily_table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        for idx in range(1, len(table_rows)):
            if idx % 2 == 0:
                daily_table_style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#F1F5F9")))
        
        daily_table.setStyle(TableStyle(daily_table_style))
        elements.append(daily_table)
        elements.append(Spacer(1, 12))

        # Hydration Advisory Footer Note
        tip_text = (
            "💡 <b>Hydration Tip:</b> Consistent daily hydration enhances energy, "
            "regulates body temperature, and supports metabolic health. Aim to sip water evenly throughout the day."
        )
        tip_table = Table(
            [[Paragraph(tip_text, ParagraphStyle("TipText", parent=styles["Normal"], fontSize=8, leading=11, textColor=colors.HexColor("#334155")))]],
            colWidths=[7.5 * inch],
        )
        tip_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#BFDBFE")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        elements.append(tip_table)

        # Build PDF into buffer
        doc.build(elements)
        buffer.seek(0)
        return buffer

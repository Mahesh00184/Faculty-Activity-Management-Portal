from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import models
from app.api.auth import get_current_user
from app.services.reports import generate_pdf_report, generate_excel_report
from app.services.audit import log_action

router = APIRouter()

def get_user_faculty(user: models.User, db: Session):
    if user.faculty_profile:
        return user.faculty_profile
    return db.query(models.Faculty).filter(models.Faculty.email == user.email).first()

@router.get("/generate")
def generate_report(
    report_type: str = Query(..., description="faculty, monthly, annual, publications, certificates, activity_type"),
    export_format: str = Query("pdf", description="pdf, excel, json"),
    faculty_id: Optional[int] = None,
    month: Optional[str] = None,
    year: Optional[int] = None,
    activity_type: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Enforce faculty restriction
    if current_user.role == models.RoleEnum.faculty.value:
        my_fac = get_user_faculty(current_user, db)
        faculty_id = my_fac.id if my_fac else -1

    title = "Faculty Activity Report"
    subtitle = "Annual Faculty Review & Accreditations"
    headers = []
    rows = []
    col_widths = None

    if report_type == "faculty":
        title = "Faculty-Wise Activity Report"
        query = db.query(models.Activity).join(models.Faculty)
        if faculty_id:
            query = query.filter(models.Activity.faculty_id == faculty_id)
            fac = db.query(models.Faculty).filter(models.Faculty.id == faculty_id).first()
            if fac:
                subtitle = f"Faculty Member: {fac.name} ({fac.employee_code}) - {fac.designation or ''}"
        activities = query.order_by(models.Faculty.name, models.Activity.created_at.desc()).all()

        headers = ["Faculty Name", "Type", "Organization", "Title", "Month", "Dates", "Status"]
        col_widths = [110, 65, 120, 180, 60, 95, 80]
        for a in activities:
            dates = f"{a.start_date or ''} to {a.end_date or ''}" if a.start_date else "-"
            rows.append([
                a.faculty.name if a.faculty else "N/A",
                a.event_type or "-",
                a.organization or "-",
                a.title or "-",
                a.month or "-",
                dates,
                a.status or "-"
            ])

    elif report_type == "monthly":
        title = f"Monthly Activity Report {f'({month})' if month else ''}"
        query = db.query(models.Activity).join(models.Faculty)
        if month:
            query = query.filter(models.Activity.month.ilike(f"%{month}%"))
            subtitle = f"Month of {month}"
        if faculty_id:
            query = query.filter(models.Activity.faculty_id == faculty_id)
        activities = query.order_by(models.Activity.month, models.Activity.title).all()

        headers = ["Month", "Faculty Name", "Type", "Organization", "Title", "Status"]
        col_widths = [65, 120, 75, 140, 220, 90]
        for a in activities:
            rows.append([
                a.month or "-",
                a.faculty.name if a.faculty else "N/A",
                a.event_type or "-",
                a.organization or "-",
                a.title or "-",
                a.status or "-"
            ])

    elif report_type == "annual":
        title = f"Annual Activity Report {f'({year})' if year else ''}"
        subtitle = "Consolidated Institutional Year-End Report"
        query = db.query(models.Activity).join(models.Faculty)
        if faculty_id:
            query = query.filter(models.Activity.faculty_id == faculty_id)
        activities = query.order_by(models.Activity.created_at.desc()).all()

        headers = ["ID", "Faculty", "Activity Title", "Type", "Organization", "Month", "Status"]
        col_widths = [40, 120, 200, 70, 130, 65, 85]
        for a in activities:
            rows.append([
                f"ACT-{a.id:04d}",
                a.faculty.name if a.faculty else "N/A",
                a.title or "-",
                a.event_type or "-",
                a.organization or "-",
                a.month or "-",
                a.status or "-"
            ])

    elif report_type == "publications":
        title = "Faculty Publication Report"
        subtitle = "Academic Research & Scholarly Contributions"
        query = db.query(models.Publication).join(models.Faculty)
        if faculty_id:
            query = query.filter(models.Publication.faculty_id == faculty_id)
        pubs = query.order_by(models.Publication.created_at.desc()).all()

        headers = ["Faculty Name", "Type", "Title", "Month", "Milestone", "Status", "Details"]
        col_widths = [110, 70, 180, 60, 95, 75, 120]
        for p in pubs:
            rows.append([
                p.faculty.name if p.faculty else "N/A",
                p.publication_type or "Book",
                p.title or "-",
                p.month or "-",
                p.milestone_achieved or "-",
                p.status or "-",
                p.publication_details or "-"
            ])

    elif report_type == "certificates":
        title = "Certificates & Verification Report"
        subtitle = "Accreditation Proofs and Verification Records"
        query = db.query(models.Certificate).join(models.Faculty)
        if faculty_id:
            query = query.filter(models.Certificate.faculty_id == faculty_id)
        certs = query.order_by(models.Certificate.uploaded_at.desc()).all()

        headers = ["Certificate Title", "Faculty Member", "Related Item", "Uploaded Date", "Link/File"]
        col_widths = [180, 140, 140, 100, 150]
        for c in certs:
            item = "-"
            if c.activity:
                item = f"Activity: {c.activity.title[:25]}..."
            elif c.publication:
                item = f"Pub: {c.publication.title[:25]}..."
            rows.append([
                c.title or "-",
                c.faculty.name if c.faculty else "N/A",
                item,
                c.uploaded_at.strftime("%Y-%m-%d") if c.uploaded_at else "-",
                c.file_name or c.certificate_link or "-"
            ])

    elif report_type == "activity_type":
        title = f"Activity-Type Report {f'({activity_type})' if activity_type else ''}"
        subtitle = "Distribution and Categorization of Faculty Engagements"
        query = db.query(models.Activity).join(models.Faculty)
        if activity_type:
            query = query.filter(models.Activity.event_type.ilike(f"%{activity_type}%"))
        if faculty_id:
            query = query.filter(models.Activity.faculty_id == faculty_id)
        activities = query.order_by(models.Activity.event_type, models.Activity.title).all()

        headers = ["Type", "Faculty Name", "Title", "Organization", "Month", "Status"]
        col_widths = [80, 120, 200, 140, 70, 80]
        for a in activities:
            rows.append([
                a.event_type or "-",
                a.faculty.name if a.faculty else "N/A",
                a.title or "-",
                a.organization or "-",
                a.month or "-",
                a.status or "-"
            ])
    else:
        raise HTTPException(status_code=400, detail="Invalid report_type")

    # Audit log
    log_action(
        db=db,
        action="EXPORT",
        entity="Report",
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"Generated {report_type} report in {export_format.upper()} format"
    )

    if export_format == "json":
        return {
            "title": title,
            "subtitle": subtitle,
            "headers": headers,
            "rows": rows,
            "total_records": len(rows)
        }

    elif export_format == "excel":
        buf = generate_excel_report(title, headers, rows, sheet_name=report_type.capitalize())
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    else: # PDF
        buf = generate_pdf_report(title, subtitle, headers, rows, col_widths)
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

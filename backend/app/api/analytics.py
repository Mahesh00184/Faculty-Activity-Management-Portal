from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from collections import defaultdict

from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.api.auth import get_current_user

router = APIRouter()

def get_user_faculty(user: models.User, db: Session):
    if user.faculty_profile:
        return user.faculty_profile
    return db.query(models.Faculty).filter(models.Faculty.email == user.email).first()

@router.get("/dashboard/admin", response_model=schemas.AdminDashboardStats)
def get_admin_dashboard_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_faculty = db.query(models.Faculty).count()
    total_activities = db.query(models.Activity).count()
    pending_approvals = db.query(models.Activity).filter(
        models.Activity.status.in_([models.StatusEnum.submitted.value, models.StatusEnum.under_review.value, "PENDING"])
    ).count()
    approved_activities = db.query(models.Activity).filter(
        models.Activity.status == models.StatusEnum.approved.value
    ).count()
    publications_count = db.query(models.Publication).count()
    certificates_count = db.query(models.Certificate).count()

    # Recent activities (last 5)
    recent = db.query(models.Activity).order_by(models.Activity.created_at.desc()).limit(5).all()
    recent_list = []
    for r in recent:
        r_dict = schemas.Activity.model_validate(r)
        if r.faculty:
            r_dict.faculty_name = r.faculty.name
        recent_list.append(r_dict)

    # Status distribution
    status_counts = db.query(
        models.Activity.status, func.count(models.Activity.id)
    ).group_by(models.Activity.status).all()
    status_dist = [{"name": s[0] or "Unknown", "value": s[1]} for s in status_counts]

    # Type distribution
    type_counts = db.query(
        models.Activity.event_type, func.count(models.Activity.id)
    ).group_by(models.Activity.event_type).all()
    type_dist = [{"name": t[0] or "Other", "value": t[1]} for t in type_counts]

    # Monthly trends
    month_counts = db.query(
        models.Activity.month, func.count(models.Activity.id)
    ).group_by(models.Activity.month).all()
    month_dist = [{"month": m[0] or "Unspecified", "count": m[1]} for m in month_counts]

    return schemas.AdminDashboardStats(
        total_faculty=total_faculty,
        total_activities=total_activities,
        pending_approvals=pending_approvals,
        approved_activities=approved_activities,
        publications_count=publications_count,
        certificates_count=certificates_count,
        recent_activities=recent_list,
        activity_status_distribution=status_dist,
        activity_type_distribution=type_dist,
        monthly_activity_trends=month_dist
    )

@router.get("/dashboard/faculty", response_model=schemas.FacultyDashboardStats)
def get_faculty_dashboard_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    faculty = get_user_faculty(current_user, db)
    faculty_id = faculty.id if faculty else -1

    query = db.query(models.Activity).filter(models.Activity.faculty_id == faculty_id)
    my_activities_count = query.count()
    drafts_count = query.filter(models.Activity.status == models.StatusEnum.draft.value).count()
    submitted_count = query.filter(models.Activity.status == models.StatusEnum.submitted.value).count()
    under_review_count = query.filter(models.Activity.status.in_([models.StatusEnum.under_review.value, "PENDING"])).count()
    approved_count = query.filter(models.Activity.status == models.StatusEnum.approved.value).count()
    correction_required_count = query.filter(models.Activity.status == models.StatusEnum.correction_required.value).count()
    rejected_count = query.filter(models.Activity.status == models.StatusEnum.rejected.value).count()

    my_publications_count = db.query(models.Publication).filter(models.Publication.faculty_id == faculty_id).count()
    my_certificates_count = db.query(models.Certificate).filter(models.Certificate.faculty_id == faculty_id).count()

    recent = query.order_by(models.Activity.created_at.desc()).limit(5).all()
    recent_list = []
    for r in recent:
        r_dict = schemas.Activity.model_validate(r)
        if faculty:
            r_dict.faculty_name = faculty.name
        recent_list.append(r_dict)

    # Type distribution
    type_counts = db.query(
        models.Activity.event_type, func.count(models.Activity.id)
    ).filter(models.Activity.faculty_id == faculty_id).group_by(models.Activity.event_type).all()
    type_dist = [{"name": t[0] or "Other", "value": t[1]} for t in type_counts]

    # Monthly trends
    month_counts = db.query(
        models.Activity.month, func.count(models.Activity.id)
    ).filter(models.Activity.faculty_id == faculty_id).group_by(models.Activity.month).all()
    month_dist = [{"month": m[0] or "Unspecified", "count": m[1]} for m in month_counts]

    return schemas.FacultyDashboardStats(
        my_activities_count=my_activities_count,
        drafts_count=drafts_count,
        submitted_count=submitted_count,
        under_review_count=under_review_count,
        approved_count=approved_count,
        correction_required_count=correction_required_count,
        rejected_count=rejected_count,
        my_publications_count=my_publications_count,
        my_certificates_count=my_certificates_count,
        recent_activities=recent_list,
        activity_type_distribution=type_dist,
        monthly_activity_trends=month_dist
    )

@router.get("/overview")
def get_analytics_overview(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Monthly activities
    monthly = db.query(
        models.Activity.month, func.count(models.Activity.id)
    ).group_by(models.Activity.month).all()

    # Types
    types = db.query(
        models.Activity.event_type, func.count(models.Activity.id)
    ).group_by(models.Activity.event_type).all()

    # Status
    statuses = db.query(
        models.Activity.status, func.count(models.Activity.id)
    ).group_by(models.Activity.status).all()

    # Publications by type
    pub_types = db.query(
        models.Publication.publication_type, func.count(models.Publication.id)
    ).group_by(models.Publication.publication_type).all()

    # Faculty comparison (top faculty by activity count)
    faculty_acts = db.query(
        models.Faculty.name, func.count(models.Activity.id)
    ).join(models.Activity, models.Faculty.id == models.Activity.faculty_id, isouter=True)\
     .group_by(models.Faculty.name).limit(10).all()

    return {
        "monthly_trend": [{"month": m[0] or "Other", "activities": m[1]} for m in monthly],
        "type_distribution": [{"name": t[0] or "Other", "value": t[1]} for t in types],
        "status_distribution": [{"name": s[0] or "Other", "value": s[1]} for s in statuses],
        "publication_distribution": [{"name": p[0] or "Other", "value": p[1]} for p in pub_types],
        "faculty_comparison": [{"faculty": f[0] or "Unknown", "count": f[1]} for f in faculty_acts]
    }

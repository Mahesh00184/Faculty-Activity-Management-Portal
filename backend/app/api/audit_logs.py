from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.api.auth import get_current_admin

router = APIRouter()

@router.get("/", response_model=List[schemas.AuditLog])
def get_audit_logs(
    action: Optional[str] = None,
    entity: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(models.AuditLog)

    if action:
        query = query.filter(models.AuditLog.action == action.upper())
    if entity:
        query = query.filter(models.AuditLog.entity.ilike(f"%{entity}%"))
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (models.AuditLog.user_email.ilike(s)) |
            (models.AuditLog.details.ilike(s)) |
            (models.AuditLog.action.ilike(s))
        )

    return query.order_by(models.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

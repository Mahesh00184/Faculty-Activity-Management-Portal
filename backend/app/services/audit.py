from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.models import models

def log_action(
    db: Session,
    action: str,
    entity: str,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    details: Optional[str] = None
):
    try:
        log_entry = models.AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Failed to write audit log: {e}")
        db.rollback()

def notify_user(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    link: Optional[str] = None
):
    try:
        notification = models.Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(notification)
        db.commit()
    except Exception as e:
        print(f"Failed to create notification: {e}")
        db.rollback()

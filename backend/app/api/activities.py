from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.api.auth import get_current_user, get_current_admin
from app.services.audit import log_action, notify_user

router = APIRouter()

def get_user_faculty(user: models.User, db: Session) -> Optional[models.Faculty]:
    if user.faculty_profile:
        return user.faculty_profile
    return db.query(models.Faculty).filter(models.Faculty.email == user.email).first()

@router.get("/", response_model=List[schemas.Activity])
def get_activities(
    faculty_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    event_type: Optional[str] = None,
    month: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Activity)
    
    # If faculty user, restrict to their own activities
    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty:
            return []
        query = query.filter(models.Activity.faculty_id == faculty.id)
    elif faculty_id:
        query = query.filter(models.Activity.faculty_id == faculty_id)

    if status_filter:
        query = query.filter(models.Activity.status == status_filter)
    if event_type:
        query = query.filter(models.Activity.event_type.ilike(f"%{event_type}%"))
    if month:
        query = query.filter(models.Activity.month.ilike(f"%{month}%"))
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (models.Activity.title.ilike(s)) |
            (models.Activity.organization.ilike(s)) |
            (models.Activity.event_type.ilike(s)) |
            (models.Activity.notes.ilike(s))
        )

    activities = query.order_by(models.Activity.created_at.desc()).offset(skip).limit(limit).all()
    
    # Populate faculty_name
    result = []
    for act in activities:
        act_dict = schemas.Activity.model_validate(act)
        if act.faculty:
            act_dict.faculty_name = act.faculty.name
        result.append(act_dict)
    return result

@router.get("/{activity_id}", response_model=schemas.Activity)
def get_activity(
    activity_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    act = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty or act.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this activity")
            
    act_dict = schemas.Activity.model_validate(act)
    if act.faculty:
        act_dict.faculty_name = act.faculty.name
    return act_dict

@router.post("/", response_model=schemas.Activity)
def create_activity(
    activity_in: schemas.ActivityCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    faculty_id = activity_in.faculty_id
    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty:
            raise HTTPException(status_code=400, detail="Faculty profile not linked")
        faculty_id = faculty.id
    elif not faculty_id:
        raise HTTPException(status_code=400, detail="faculty_id required for admin creation")

    # Initial status: DRAFT or SUBMITTED
    status_val = activity_in.status or models.StatusEnum.draft.value
    if status_val not in [models.StatusEnum.draft.value, models.StatusEnum.submitted.value]:
        status_val = models.StatusEnum.draft.value

    data = activity_in.model_dump(exclude={"faculty_id", "status"})
    new_act = models.Activity(
        **data,
        faculty_id=faculty_id,
        status=status_val,
        created_at=datetime.utcnow()
    )
    db.add(new_act)
    db.commit()
    db.refresh(new_act)

    log_action(
        db=db,
        action="CREATE",
        entity="Activity",
        entity_id=new_act.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"Created activity: {new_act.title} ({new_act.status})"
    )

    if new_act.status == models.StatusEnum.submitted.value:
        # Notify admin
        admins = db.query(models.User).filter(models.User.role == models.RoleEnum.admin.value).all()
        fac_name = new_act.faculty.name if new_act.faculty else "Faculty"
        for adm in admins:
            notify_user(
                db=db,
                user_id=adm.id,
                title="New Activity Submitted",
                message=f"{fac_name} submitted '{new_act.title}' for review.",
                link="/activities"
            )

    act_dict = schemas.Activity.model_validate(new_act)
    if new_act.faculty:
        act_dict.faculty_name = new_act.faculty.name
    return act_dict

@router.put("/{activity_id}", response_model=schemas.Activity)
def update_activity(
    activity_id: int,
    activity_in: schemas.ActivityUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    act = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty or act.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Faculty can only edit if DRAFT or CORRECTION REQUIRED
        if act.status not in [models.StatusEnum.draft.value, models.StatusEnum.correction_required.value]:
            raise HTTPException(status_code=400, detail="Cannot edit activity once under review or approved")

    update_data = activity_in.model_dump(exclude_unset=True)
    status_update = update_data.pop("status", None)
    
    for k, v in update_data.items():
        setattr(act, k, v)
        
    db.commit()
    db.refresh(act)

    log_action(
        db=db,
        action="UPDATE",
        entity="Activity",
        entity_id=act.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"Updated activity: {act.title}"
    )

    act_dict = schemas.Activity.model_validate(act)
    if act.faculty:
        act_dict.faculty_name = act.faculty.name
    return act_dict

@router.post("/{activity_id}/submit", response_model=schemas.Activity)
def submit_activity(
    activity_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    act = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty or act.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    if act.status not in [models.StatusEnum.draft.value, models.StatusEnum.correction_required.value]:
        raise HTTPException(status_code=400, detail="Activity is already submitted or processed")

    is_resubmit = (act.status == models.StatusEnum.correction_required.value)
    # Submitted goes directly to SUBMITTED or UNDER REVIEW
    act.status = models.StatusEnum.under_review.value if is_resubmit else models.StatusEnum.submitted.value
    db.commit()
    db.refresh(act)

    action_name = "RESUBMIT" if is_resubmit else "SUBMIT"
    log_action(
        db=db,
        action=action_name,
        entity="Activity",
        entity_id=act.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"{action_name} activity: {act.title}"
    )

    # Notify admins
    admins = db.query(models.User).filter(models.User.role == models.RoleEnum.admin.value).all()
    fac_name = act.faculty.name if act.faculty else "Faculty"
    for adm in admins:
        notify_user(
            db=db,
            user_id=adm.id,
            title=f"Activity {'Resubmitted' if is_resubmit else 'Submitted'}",
            message=f"{fac_name} submitted '{act.title}' for review.",
            link="/activities"
        )

    act_dict = schemas.Activity.model_validate(act)
    if act.faculty:
        act_dict.faculty_name = act.faculty.name
    return act_dict

@router.post("/{activity_id}/review", response_model=schemas.Activity)
def review_activity(
    activity_id: int,
    review_in: schemas.ActivityStatusUpdate,
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    act = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    target_status = review_in.status.upper()
    valid_statuses = [
        models.StatusEnum.under_review.value,
        models.StatusEnum.approved.value,
        models.StatusEnum.correction_required.value,
        models.StatusEnum.rejected.value
    ]
    if target_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid review status. Must be one of: {valid_statuses}")

    act.status = target_status
    if review_in.comments is not None:
        act.comments = review_in.comments

    db.commit()
    db.refresh(act)

    action_map = {
        models.StatusEnum.approved.value: "APPROVE",
        models.StatusEnum.correction_required.value: "CORRECTION_REQUIRED",
        models.StatusEnum.rejected.value: "REJECT",
        models.StatusEnum.under_review.value: "UNDER_REVIEW"
    }

    log_action(
        db=db,
        action=action_map.get(target_status, "REVIEW"),
        entity="Activity",
        entity_id=act.id,
        user_id=current_admin.id,
        user_email=current_admin.email,
        details=f"Admin set status to {target_status}. Notes: {review_in.comments or 'None'}"
    )

    # Notify faculty member
    if act.faculty and act.faculty.user_id:
        notify_user(
            db=db,
            user_id=act.faculty.user_id,
            title=f"Activity Status: {target_status}",
            message=f"Your activity '{act.title}' is now {target_status}. {f'Comments: {review_in.comments}' if review_in.comments else ''}",
            link="/activities"
        )

    act_dict = schemas.Activity.model_validate(act)
    if act.faculty:
        act_dict.faculty_name = act.faculty.name
    return act_dict

@router.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    act = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty or act.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Faculty can only delete drafts
        if act.status not in [models.StatusEnum.draft.value, models.StatusEnum.correction_required.value]:
            raise HTTPException(status_code=400, detail="Cannot delete an activity once submitted or approved")

    title = act.title
    db.delete(act)
    db.commit()

    log_action(
        db=db,
        action="DELETE",
        entity="Activity",
        entity_id=activity_id,
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"Deleted activity: {title}"
    )
    return {"message": f"Activity '{title}' deleted successfully"}

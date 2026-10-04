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

@router.get("/", response_model=List[schemas.Publication])
def get_publications(
    faculty_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    pub_type: Optional[str] = None,
    month: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Publication)
    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty:
            return []
        query = query.filter(models.Publication.faculty_id == faculty.id)
    elif faculty_id:
        query = query.filter(models.Publication.faculty_id == faculty_id)

    if status_filter:
        query = query.filter(models.Publication.status == status_filter)
    if pub_type:
        query = query.filter(models.Publication.publication_type.ilike(f"%{pub_type}%"))
    if month:
        query = query.filter(models.Publication.month.ilike(f"%{month}%"))
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (models.Publication.title.ilike(s)) |
            (models.Publication.publication_details.ilike(s)) |
            (models.Publication.milestone_achieved.ilike(s)) |
            (models.Publication.notes.ilike(s))
        )

    pubs = query.order_by(models.Publication.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for p in pubs:
        p_dict = schemas.Publication.model_validate(p)
        if p.faculty:
            p_dict.faculty_name = p.faculty.name
        result.append(p_dict)
    return result

@router.get("/{pub_id}", response_model=schemas.Publication)
def get_publication(
    pub_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")

    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty or pub.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    p_dict = schemas.Publication.model_validate(pub)
    if pub.faculty:
        p_dict.faculty_name = pub.faculty.name
    return p_dict

@router.post("/", response_model=schemas.Publication)
def create_publication(
    pub_in: schemas.PublicationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    faculty_id = pub_in.faculty_id
    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty:
            raise HTTPException(status_code=400, detail="Faculty profile not linked")
        faculty_id = faculty.id
    elif not faculty_id:
        raise HTTPException(status_code=400, detail="faculty_id required for admin creation")

    status_val = pub_in.status or models.StatusEnum.draft.value
    if status_val not in [models.StatusEnum.draft.value, models.StatusEnum.submitted.value]:
        status_val = models.StatusEnum.draft.value

    data = pub_in.model_dump(exclude={"faculty_id", "status"})
    new_pub = models.Publication(
        **data,
        faculty_id=faculty_id,
        status=status_val,
        created_at=datetime.utcnow()
    )
    db.add(new_pub)
    db.commit()
    db.refresh(new_pub)

    log_action(
        db=db,
        action="CREATE",
        entity="Publication",
        entity_id=new_pub.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"Created publication: {new_pub.title} ({new_pub.status})"
    )

    if new_pub.status == models.StatusEnum.submitted.value:
        admins = db.query(models.User).filter(models.User.role == models.RoleEnum.admin.value).all()
        fac_name = new_pub.faculty.name if new_pub.faculty else "Faculty"
        for adm in admins:
            notify_user(
                db=db,
                user_id=adm.id,
                title="New Publication Submitted",
                message=f"{fac_name} submitted publication '{new_pub.title}' for review.",
                link="/publications"
            )

    p_dict = schemas.Publication.model_validate(new_pub)
    if new_pub.faculty:
        p_dict.faculty_name = new_pub.faculty.name
    return p_dict

@router.put("/{pub_id}", response_model=schemas.Publication)
def update_publication(
    pub_id: int,
    pub_in: schemas.PublicationUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")

    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty or pub.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if pub.status not in [models.StatusEnum.draft.value, models.StatusEnum.correction_required.value]:
            raise HTTPException(status_code=400, detail="Cannot edit publication once under review or approved")

    update_data = pub_in.model_dump(exclude_unset=True)
    update_data.pop("status", None)

    for k, v in update_data.items():
        setattr(pub, k, v)

    db.commit()
    db.refresh(pub)

    log_action(
        db=db,
        action="UPDATE",
        entity="Publication",
        entity_id=pub.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"Updated publication: {pub.title}"
    )

    p_dict = schemas.Publication.model_validate(pub)
    if pub.faculty:
        p_dict.faculty_name = pub.faculty.name
    return p_dict

@router.post("/{pub_id}/submit", response_model=schemas.Publication)
def submit_publication(
    pub_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")

    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty or pub.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    if pub.status not in [models.StatusEnum.draft.value, models.StatusEnum.correction_required.value]:
        raise HTTPException(status_code=400, detail="Publication already submitted or approved")

    is_resubmit = (pub.status == models.StatusEnum.correction_required.value)
    pub.status = models.StatusEnum.under_review.value if is_resubmit else models.StatusEnum.submitted.value
    db.commit()
    db.refresh(pub)

    action_name = "RESUBMIT" if is_resubmit else "SUBMIT"
    log_action(
        db=db,
        action=action_name,
        entity="Publication",
        entity_id=pub.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"{action_name} publication: {pub.title}"
    )

    admins = db.query(models.User).filter(models.User.role == models.RoleEnum.admin.value).all()
    fac_name = pub.faculty.name if pub.faculty else "Faculty"
    for adm in admins:
        notify_user(
            db=db,
            user_id=adm.id,
            title=f"Publication {'Resubmitted' if is_resubmit else 'Submitted'}",
            message=f"{fac_name} submitted '{pub.title}' for review.",
            link="/publications"
        )

    p_dict = schemas.Publication.model_validate(pub)
    if pub.faculty:
        p_dict.faculty_name = pub.faculty.name
    return p_dict

@router.post("/{pub_id}/review", response_model=schemas.Publication)
def review_publication(
    pub_id: int,
    review_in: schemas.PublicationStatusUpdate,
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")

    target_status = review_in.status.upper()
    valid_statuses = [
        models.StatusEnum.under_review.value,
        models.StatusEnum.approved.value,
        models.StatusEnum.correction_required.value,
        models.StatusEnum.rejected.value
    ]
    if target_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid review status. Must be one of: {valid_statuses}")

    pub.status = target_status
    if review_in.comments is not None:
        pub.comments = review_in.comments

    db.commit()
    db.refresh(pub)

    action_map = {
        models.StatusEnum.approved.value: "APPROVE",
        models.StatusEnum.correction_required.value: "CORRECTION_REQUIRED",
        models.StatusEnum.rejected.value: "REJECT",
        models.StatusEnum.under_review.value: "UNDER_REVIEW"
    }

    log_action(
        db=db,
        action=action_map.get(target_status, "REVIEW"),
        entity="Publication",
        entity_id=pub.id,
        user_id=current_admin.id,
        user_email=current_admin.email,
        details=f"Admin set status to {target_status}. Notes: {review_in.comments or 'None'}"
    )

    if pub.faculty and pub.faculty.user_id:
        notify_user(
            db=db,
            user_id=pub.faculty.user_id,
            title=f"Publication Status: {target_status}",
            message=f"Your publication '{pub.title}' is now {target_status}. {f'Comments: {review_in.comments}' if review_in.comments else ''}",
            link="/publications"
        )

    p_dict = schemas.Publication.model_validate(pub)
    if pub.faculty:
        p_dict.faculty_name = pub.faculty.name
    return p_dict

@router.delete("/{pub_id}")
def delete_publication(
    pub_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")

    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty or pub.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if pub.status not in [models.StatusEnum.draft.value, models.StatusEnum.correction_required.value]:
            raise HTTPException(status_code=400, detail="Cannot delete publication once submitted or approved")

    title = pub.title
    db.delete(pub)
    db.commit()

    log_action(
        db=db,
        action="DELETE",
        entity="Publication",
        entity_id=pub_id,
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"Deleted publication: {title}"
    )
    return {"message": f"Publication '{title}' deleted successfully"}

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.api.auth import get_current_user, get_current_admin
from app.auth.auth import get_password_hash
from app.services.audit import log_action

router = APIRouter()

@router.get("/", response_model=List[schemas.Faculty])
def get_all_faculty(
    search: Optional[str] = None,
    designation: Optional[str] = None,
    specialization: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Faculty)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (models.Faculty.name.ilike(s)) |
            (models.Faculty.employee_code.ilike(s)) |
            (models.Faculty.email.ilike(s)) |
            (models.Faculty.specialization.ilike(s))
        )
    if designation:
        query = query.filter(models.Faculty.designation == designation)
    if specialization:
        query = query.filter(models.Faculty.specialization.ilike(f"%{specialization}%"))
        
    faculty_list = query.offset(skip).limit(limit).all()
    
    # Enrich with counts
    result = []
    for f in faculty_list:
        act_count = db.query(models.Activity).filter(models.Activity.faculty_id == f.id).count()
        pub_count = db.query(models.Publication).filter(models.Publication.faculty_id == f.id).count()
        f_dict = schemas.Faculty.model_validate(f)
        f_dict.activities_count = act_count
        f_dict.publications_count = pub_count
        result.append(f_dict)
    return result

@router.get("/profile", response_model=schemas.FacultyDetail)
def get_my_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    faculty = db.query(models.Faculty).filter(models.Faculty.user_id == current_user.id).first()
    if not faculty and current_user.email:
        faculty = db.query(models.Faculty).filter(models.Faculty.email == current_user.email).first()
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty profile not found for current user"
        )
    return faculty

@router.put("/profile", response_model=schemas.Faculty)
def update_my_profile(
    profile_data: schemas.FacultyUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    faculty = db.query(models.Faculty).filter(models.Faculty.user_id == current_user.id).first()
    if not faculty and current_user.email:
        faculty = db.query(models.Faculty).filter(models.Faculty.email == current_user.email).first()
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty profile not found"
        )
        
    update_dict = profile_data.model_dump(exclude_unset=True)
    # Faculty cannot change their own employee code
    update_dict.pop("employee_code", None)
    
    for key, value in update_dict.items():
        setattr(faculty, key, value)
        
    db.commit()
    db.refresh(faculty)
    
    log_action(
        db=db,
        action="UPDATE",
        entity="Faculty",
        entity_id=faculty.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details="Updated own faculty profile"
    )
    return faculty

@router.get("/{faculty_id}", response_model=schemas.FacultyDetail)
def get_faculty_by_id(
    faculty_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    faculty = db.query(models.Faculty).filter(models.Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    return faculty

@router.post("/", response_model=schemas.Faculty)
def create_faculty(
    faculty_in: schemas.FacultyCreate,
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # Check if employee code already exists
    existing = db.query(models.Faculty).filter(models.Faculty.employee_code == faculty_in.employee_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Faculty with this Employee Code already exists")

    # If email provided, create or link user account
    user_id = None
    if faculty_in.email:
        existing_user = db.query(models.User).filter(models.User.email == faculty_in.email).first()
        if existing_user:
            user_id = existing_user.id
        else:
            new_user = models.User(
                email=faculty_in.email,
                hashed_password=get_password_hash(faculty_in.password or "faculty123"),
                role=models.RoleEnum.faculty.value,
                is_active=True
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_id = new_user.id

    faculty_data = faculty_in.model_dump(exclude={"password"})
    new_faculty = models.Faculty(**faculty_data, user_id=user_id)
    db.add(new_faculty)
    db.commit()
    db.refresh(new_faculty)

    log_action(
        db=db,
        action="CREATE",
        entity="Faculty",
        entity_id=new_faculty.id,
        user_id=current_admin.id,
        user_email=current_admin.email,
        details=f"Created faculty {new_faculty.name} ({new_faculty.employee_code})"
    )
    return new_faculty

@router.put("/{faculty_id}", response_model=schemas.Faculty)
def update_faculty(
    faculty_id: int,
    faculty_in: schemas.FacultyUpdate,
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    faculty = db.query(models.Faculty).filter(models.Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")

    update_dict = faculty_in.model_dump(exclude_unset=True)
    if "employee_code" in update_dict and update_dict["employee_code"] != faculty.employee_code:
        dup = db.query(models.Faculty).filter(models.Faculty.employee_code == update_dict["employee_code"]).first()
        if dup:
            raise HTTPException(status_code=400, detail="Employee code already taken")

    for k, v in update_dict.items():
        setattr(faculty, k, v)

    db.commit()
    db.refresh(faculty)

    log_action(
        db=db,
        action="UPDATE",
        entity="Faculty",
        entity_id=faculty.id,
        user_id=current_admin.id,
        user_email=current_admin.email,
        details=f"Admin updated faculty {faculty.name}"
    )
    return faculty

@router.delete("/{faculty_id}")
def delete_faculty(
    faculty_id: int,
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    faculty = db.query(models.Faculty).filter(models.Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")

    name = faculty.name
    db.delete(faculty)
    db.commit()

    log_action(
        db=db,
        action="DELETE",
        entity="Faculty",
        entity_id=faculty_id,
        user_id=current_admin.id,
        user_email=current_admin.email,
        details=f"Deleted faculty member {name} (ID: {faculty_id})"
    )
    return {"message": f"Faculty member {name} deleted successfully"}

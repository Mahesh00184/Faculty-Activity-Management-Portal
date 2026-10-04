from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
from datetime import datetime

from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.api.auth import get_current_user
from app.services.audit import log_action

router = APIRouter()

# Safe upload directory
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "certificates"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_user_faculty(user: models.User, db: Session) -> Optional[models.Faculty]:
    if user.faculty_profile:
        return user.faculty_profile
    return db.query(models.Faculty).filter(models.Faculty.email == user.email).first()

@router.get("/", response_model=List[schemas.Certificate])
def get_certificates(
    faculty_id: Optional[int] = None,
    activity_id: Optional[int] = None,
    publication_id: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Certificate)
    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty:
            return []
        query = query.filter(models.Certificate.faculty_id == faculty.id)
    elif faculty_id:
        query = query.filter(models.Certificate.faculty_id == faculty_id)

    if activity_id:
        query = query.filter(models.Certificate.activity_id == activity_id)
    if publication_id:
        query = query.filter(models.Certificate.publication_id == publication_id)

    return query.order_by(models.Certificate.uploaded_at.desc()).all()

@router.post("/upload", response_model=schemas.Certificate)
async def upload_certificate(
    title: str = Form(...),
    activity_id: Optional[int] = Form(None),
    publication_id: Optional[int] = Form(None),
    certificate_link: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    faculty = get_user_faculty(current_user, db)
    faculty_id = faculty.id if faculty else 1

    file_name = None
    file_path = None
    if file and file.filename:
        # Sanitize filename with uuid prefix
        ext = os.path.splitext(file.filename)[1]
        safe_name = f"{uuid.uuid4().hex[:12]}_{os.path.basename(file.filename)}"
        target_path = os.path.join(UPLOAD_DIR, safe_name)
        
        # Save file to uploads folder
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_name = file.filename
        file_path = safe_name # relative filename stored safely

    # Check that at least a file or link is provided
    if not file_name and not certificate_link:
        raise HTTPException(status_code=400, detail="Must provide either a certificate file or a certificate link")

    cert = models.Certificate(
        faculty_id=faculty_id,
        activity_id=activity_id,
        publication_id=publication_id,
        title=title,
        file_name=file_name,
        file_path=file_path,
        certificate_link=certificate_link,
        uploaded_at=datetime.utcnow()
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)

    # If linked to activity or publication, also update their certificate_link if empty
    if activity_id and (certificate_link or file_path):
        act = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
        if act and not act.certificate_link:
            act.certificate_link = certificate_link or f"/api/certificates/download/{cert.id}"
            db.commit()

    if publication_id and (certificate_link or file_path):
        pub = db.query(models.Publication).filter(models.Publication.id == publication_id).first()
        if pub and not pub.certificate_link:
            pub.certificate_link = certificate_link or f"/api/certificates/download/{cert.id}"
            db.commit()

    log_action(
        db=db,
        action="CREATE",
        entity="Certificate",
        entity_id=cert.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"Uploaded certificate: {title}"
    )

    return cert

@router.get("/download/{cert_id}")
def download_certificate(
    cert_id: int,
    db: Session = Depends(get_db)
):
    cert = db.query(models.Certificate).filter(models.Certificate.id == cert_id).first()
    if not cert or not cert.file_path:
        raise HTTPException(status_code=404, detail="Certificate file not found")

    full_path = os.path.join(UPLOAD_DIR, os.path.basename(cert.file_path))
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File on disk not found")

    return FileResponse(
        path=full_path,
        filename=cert.file_name or "certificate",
        media_type="application/octet-stream"
    )

@router.delete("/{cert_id}")
def delete_certificate(
    cert_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cert = db.query(models.Certificate).filter(models.Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if current_user.role == models.RoleEnum.faculty.value:
        faculty = get_user_faculty(current_user, db)
        if not faculty or cert.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    # Remove file from disk if exists
    if cert.file_path:
        full_path = os.path.join(UPLOAD_DIR, os.path.basename(cert.file_path))
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except Exception:
                pass

    title = cert.title
    db.delete(cert)
    db.commit()

    log_action(
        db=db,
        action="DELETE",
        entity="Certificate",
        entity_id=cert_id,
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"Deleted certificate: {title}"
    )
    return {"message": f"Certificate '{title}' deleted successfully"}

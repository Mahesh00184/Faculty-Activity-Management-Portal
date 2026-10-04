from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from jose import JWTError, jwt

from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.auth.auth import (
    verify_password,
    create_access_token,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)
from app.services.audit import log_action

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

def get_current_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role != models.RoleEnum.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privilege required"
        )
    return current_user

def get_current_faculty_user(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == models.RoleEnum.faculty.value:
        faculty = db.query(models.Faculty).filter(models.Faculty.user_id == current_user.id).first()
        if not faculty:
            # Fallback by email match
            faculty = db.query(models.Faculty).filter(models.Faculty.email == current_user.email).first()
        return current_user, faculty
    return current_user, None

@router.post("/login", response_model=schemas.Token)
async def login(request: Request, db: Session = Depends(get_db)):
    # Supports JSON login body and form data
    email = None
    password = None
    
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email") or body.get("username")
        password = body.get("password")
    else:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")
        
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )
        
    user = db.query(models.User).filter(models.User.email == email.strip().lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        log_action(
            db=db,
            action="LOGIN_FAILED",
            entity="User",
            user_email=email,
            details=f"Failed login attempt for {email}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    faculty_id = None
    faculty_name = None
    if user.faculty_profile:
        faculty_id = user.faculty_profile.id
        faculty_name = user.faculty_profile.name
    elif user.role == "faculty":
        fac = db.query(models.Faculty).filter(models.Faculty.email == user.email).first()
        if fac:
            faculty_id = fac.id
            faculty_name = fac.name

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_payload = {
        "sub": user.email,
        "role": user.role,
        "user_id": user.id,
        "faculty_id": faculty_id,
        "name": faculty_name or ("Administrator" if user.role == "admin" else "Faculty")
    }
    access_token = create_access_token(data=token_payload, expires_delta=access_token_expires)
    
    log_action(
        db=db,
        action="LOGIN",
        entity="User",
        entity_id=user.id,
        user_id=user.id,
        user_email=user.email,
        details=f"Successful login as {user.role}"
    )

    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        email=user.email,
        faculty_id=faculty_id,
        name=faculty_name or ("Administrator" if user.role == "admin" else "Faculty")
    )

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Refresh user to load faculty_profile
    db.refresh(current_user)
    return current_user

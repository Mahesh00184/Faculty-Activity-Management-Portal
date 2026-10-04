from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    faculty = "faculty"

class StatusEnum(str, Enum):
    draft = "DRAFT"
    submitted = "SUBMITTED"
    under_review = "UNDER REVIEW"
    correction_required = "CORRECTION REQUIRED"
    approved = "APPROVED"
    rejected = "REJECTED"

# --- Auth & User ---
class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    email: str
    faculty_id: Optional[int] = None
    name: Optional[str] = None

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    role: Optional[str] = RoleEnum.faculty.value

# --- Certificate ---
class CertificateBase(BaseModel):
    title: str
    activity_id: Optional[int] = None
    publication_id: Optional[int] = None
    certificate_link: Optional[str] = None

class CertificateCreate(CertificateBase):
    faculty_id: Optional[int] = None

class Certificate(CertificateBase):
    id: int
    faculty_id: int
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

# --- Activity ---
class ActivityBase(BaseModel):
    event_type: str
    organization: str
    title: str
    month: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    certificate_link: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = StatusEnum.draft.value

class ActivityCreate(ActivityBase):
    faculty_id: Optional[int] = None

class ActivityUpdate(BaseModel):
    event_type: Optional[str] = None
    organization: Optional[str] = None
    title: Optional[str] = None
    month: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    certificate_link: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class ActivityStatusUpdate(BaseModel):
    status: str
    comments: Optional[str] = None

class Activity(ActivityBase):
    id: int
    faculty_id: int
    faculty_name: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime
    certificates: List[Certificate] = []

    class Config:
        from_attributes = True

# --- Publication ---
class PublicationBase(BaseModel):
    publication_type: str = "Book"
    publication_details: Optional[str] = None
    title: str
    month: Optional[str] = None
    date_of_publication: Optional[date] = None
    milestone_achieved: Optional[str] = None
    certificate_link: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = StatusEnum.draft.value

class PublicationCreate(PublicationBase):
    faculty_id: Optional[int] = None

class PublicationUpdate(BaseModel):
    publication_type: Optional[str] = None
    publication_details: Optional[str] = None
    title: Optional[str] = None
    month: Optional[str] = None
    date_of_publication: Optional[date] = None
    milestone_achieved: Optional[str] = None
    certificate_link: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class PublicationStatusUpdate(BaseModel):
    status: str
    comments: Optional[str] = None

class Publication(PublicationBase):
    id: int
    faculty_id: int
    faculty_name: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime
    certificates: List[Certificate] = []

    class Config:
        from_attributes = True

# --- Faculty ---
class FacultyBase(BaseModel):
    name: str
    employee_code: str
    designation: Optional[str] = None
    phd_status: Optional[str] = None
    specialization: Optional[str] = None
    date_of_joining: Optional[date] = None
    experience: Optional[str] = None
    au_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class FacultyCreate(FacultyBase):
    password: Optional[str] = "faculty123"

class FacultyUpdate(BaseModel):
    name: Optional[str] = None
    employee_code: Optional[str] = None
    designation: Optional[str] = None
    phd_status: Optional[str] = None
    specialization: Optional[str] = None
    date_of_joining: Optional[date] = None
    experience: Optional[str] = None
    au_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class Faculty(FacultyBase):
    id: int
    user_id: Optional[int] = None
    activities_count: Optional[int] = 0
    publications_count: Optional[int] = 0

    class Config:
        from_attributes = True

class FacultyDetail(Faculty):
    activities: List[Activity] = []
    publications: List[Publication] = []
    certificates: List[Certificate] = []

    class Config:
        from_attributes = True

# --- User Detail ---
class User(UserBase):
    id: int
    role: str
    is_active: bool
    faculty_profile: Optional[Faculty] = None

    class Config:
        from_attributes = True

# --- Notifications ---
class Notification(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Audit Logs ---
class AuditLog(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    entity: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Dashboard & Stats ---
class AdminDashboardStats(BaseModel):
    total_faculty: int
    total_activities: int
    pending_approvals: int
    approved_activities: int
    publications_count: int
    certificates_count: int
    recent_activities: List[Activity]
    activity_status_distribution: List[Dict[str, Any]]
    activity_type_distribution: List[Dict[str, Any]]
    monthly_activity_trends: List[Dict[str, Any]]

class FacultyDashboardStats(BaseModel):
    my_activities_count: int
    drafts_count: int
    submitted_count: int
    under_review_count: int
    approved_count: int
    correction_required_count: int
    rejected_count: int
    my_publications_count: int
    my_certificates_count: int
    recent_activities: List[Activity]
    activity_type_distribution: List[Dict[str, Any]]
    monthly_activity_trends: List[Dict[str, Any]]

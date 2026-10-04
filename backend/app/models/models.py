from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime, Text, Enum
from sqlalchemy.orm import relationship
import enum
import datetime
from app.database import Base

class RoleEnum(str, enum.Enum):
    admin = "admin"
    faculty = "faculty"

class StatusEnum(str, enum.Enum):
    draft = "DRAFT"
    submitted = "SUBMITTED"
    under_review = "UNDER REVIEW"
    correction_required = "CORRECTION REQUIRED"
    approved = "APPROVED"
    rejected = "REJECTED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default=RoleEnum.faculty.value)
    is_active = Column(Boolean, default=True)
    
    faculty_profile = relationship("Faculty", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Faculty(Base):
    __tablename__ = "faculty"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, index=True)
    employee_code = Column(String, unique=True, index=True)
    designation = Column(String, nullable=True)
    phd_status = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    date_of_joining = Column(Date, nullable=True)
    experience = Column(String, nullable=True)
    au_id = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    user = relationship("User", back_populates="faculty_profile")
    activities = relationship("Activity", back_populates="faculty", cascade="all, delete-orphan")
    publications = relationship("Publication", back_populates="faculty", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="faculty", cascade="all, delete-orphan")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"))
    event_type = Column(String) # Flexible: MOOC, STTP, Webinar, Workshop, FDP, Acted as Resource Person, etc.
    organization = Column(String)
    title = Column(String)
    month = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    certificate_link = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String, default=StatusEnum.draft.value)
    comments = Column(Text, nullable=True) # Reason for Correction Required or Rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    faculty = relationship("Faculty", back_populates="activities")
    certificates = relationship("Certificate", back_populates="activity")

class Publication(Base):
    __tablename__ = "publications"
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"))
    publication_type = Column(String) # e.g. Book, Journal, Conference, Book Chapter, Patent, etc.
    publication_details = Column(Text, nullable=True)
    title = Column(String)
    status = Column(String, default=StatusEnum.draft.value)
    month = Column(String, nullable=True)
    date_of_publication = Column(Date, nullable=True)
    milestone_achieved = Column(String, nullable=True) # e.g. "Book Published"
    certificate_link = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    comments = Column(Text, nullable=True) # Reason for Correction Required or Rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    faculty = relationship("Faculty", back_populates="publications")
    certificates = relationship("Certificate", back_populates="publication")

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"))
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    publication_id = Column(Integer, ForeignKey("publications.id"), nullable=True)
    title = Column(String)
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    certificate_link = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    faculty = relationship("Faculty", back_populates="certificates")
    activity = relationship("Activity", back_populates="certificates")
    publication = relationship("Publication", back_populates="certificates")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    link = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String, nullable=True)
    action = Column(String) # LOGIN, CREATE, UPDATE, DELETE, SUBMIT, APPROVE, CORRECTION_REQUIRED, REJECT, RESUBMIT, IMPORT, EXPORT
    entity = Column(String) # Activity, Publication, Faculty, Certificate, System
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

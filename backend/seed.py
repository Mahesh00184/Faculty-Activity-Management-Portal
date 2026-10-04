import requests
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import models
from app.auth.auth import get_password_hash

def seed_database():
    print("Seeding database...")
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if users already exist
    admin_user = db.query(models.User).filter(models.User.email == "admin@facultyportal.local").first()
    if not admin_user:
        admin_user = models.User(
            email="admin@facultyportal.local",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin_user)
    
    faculty_user = db.query(models.User).filter(models.User.email == "faculty@facultyportal.local").first()
    if not faculty_user:
        faculty_user = models.User(
            email="faculty@facultyportal.local",
            hashed_password=get_password_hash("faculty123"),
            role="faculty",
            is_active=True
        )
        db.add(faculty_user)
        db.commit()
        db.refresh(faculty_user)
        
        # Create faculty profile
        faculty_profile = models.Faculty(
            user_id=faculty_user.id,
            name="Dr. A. Hemalatha",
            employee_code="RGU1234",
            designation="Professor",
            phd_status="Completed",
            specialization="Artificial Intelligence",
            phone="1234567890"
        )
        db.add(faculty_profile)
        db.commit()
        db.refresh(faculty_profile)
        
        # Add activities for this faculty
        activities = [
            models.Activity(
                faculty_id=faculty_profile.id,
                event_type="MOOC",
                organization="Coursera",
                title="Python for Data Science",
                month="June",
                status="APPROVED"
            ),
            models.Activity(
                faculty_id=faculty_profile.id,
                event_type="FDP",
                organization="AICTE",
                title="AI for Educators 5.0",
                month="August",
                status="APPROVED"
            ),
            models.Activity(
                faculty_id=faculty_profile.id,
                event_type="Workshop",
                organization="IEEE",
                title="Machine Learning Fundamentals",
                month="September",
                status="UNDER REVIEW"
            )
        ]
        db.add_all(activities)
        db.commit()
    
    print("Database seeded successfully with users and initial data.")
    print("Admin: admin@facultyportal.local / admin123")
    print("Faculty: faculty@facultyportal.local / faculty123")
    
if __name__ == "__main__":
    seed_database()

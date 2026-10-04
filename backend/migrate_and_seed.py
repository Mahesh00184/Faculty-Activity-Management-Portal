import sqlite3
import datetime
from app.database import engine, SessionLocal, Base
from app.models import models
from app.auth.auth import get_password_hash

def run_migration_and_seed():
    print("Checking and migrating database...")
    # 1. Safely alter existing tables if new columns are missing
    with engine.connect() as conn:
        # Check activities columns
        result = conn.exec_driver_sql("PRAGMA table_info(activities)").fetchall()
        existing_activity_cols = [r[1] for r in result]
        if "comments" not in existing_activity_cols:
            print("Adding comments column to activities...")
            conn.exec_driver_sql("ALTER TABLE activities ADD COLUMN comments TEXT")
        
        # Check faculty columns
        result = conn.exec_driver_sql("PRAGMA table_info(faculty)").fetchall()
        existing_faculty_cols = [r[1] for r in result]
        if "email" not in existing_faculty_cols:
            print("Adding email column to faculty...")
            conn.exec_driver_sql("ALTER TABLE faculty ADD COLUMN email VARCHAR")
        conn.commit()

    # 2. Create any missing tables (publications, certificates, notifications, audit_logs)
    Base.metadata.create_all(bind=engine)
    print("Tables verified/created.")

    # 3. Seed accounts
    db = SessionLocal()
    try:
        # Check Admin
        admin_user = db.query(models.User).filter(models.User.email == "admin@rgu.ac.in").first()
        if not admin_user:
            print("Creating default admin account: admin@rgu.ac.in / admin123")
            admin_user = models.User(
                email="admin@rgu.ac.in",
                hashed_password=get_password_hash("admin123"),
                role=models.RoleEnum.admin.value,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        # Check Faculty User
        faculty_user = db.query(models.User).filter(models.User.email == "faculty@rgu.ac.in").first()
        if not faculty_user:
            print("Creating default faculty account: faculty@rgu.ac.in / faculty123")
            faculty_user = models.User(
                email="faculty@rgu.ac.in",
                hashed_password=get_password_hash("faculty123"),
                role=models.RoleEnum.faculty.value,
                is_active=True
            )
            db.add(faculty_user)
            db.commit()
            db.refresh(faculty_user)

        # Check Faculty Profile for Dr. A. Hemalatha (faculty id 1)
        faculty_profile = db.query(models.Faculty).filter(models.Faculty.id == 1).first()
        if not faculty_profile:
            faculty_profile = db.query(models.Faculty).filter(models.Faculty.employee_code == "RGU1234").first()
        
        if not faculty_profile:
            print("Creating Faculty Profile for Dr. A. Hemalatha...")
            faculty_profile = models.Faculty(
                id=1,
                user_id=faculty_user.id,
                name="Dr. A. Hemalatha",
                employee_code="RGU1234",
                designation="Professor",
                phd_status="Completed",
                specialization="Artificial Intelligence",
                experience="12 Years",
                au_id="AU-RGU-104",
                phone="9876543210",
                email="faculty@rgu.ac.in",
                date_of_joining=datetime.date(2018, 7, 1)
            )
            db.add(faculty_profile)
            db.commit()
            db.refresh(faculty_profile)
        else:
            if not faculty_profile.user_id:
                faculty_profile.user_id = faculty_user.id
                faculty_profile.email = "faculty@rgu.ac.in"
                db.commit()

        # Seed sample publication if none exist
        pub_count = db.query(models.Publication).count()
        if pub_count == 0:
            print("Seeding sample publication...")
            pub = models.Publication(
                faculty_id=faculty_profile.id,
                publication_type="Book",
                publication_details="Published by Springer Nature, ISBN: 978-3-030-12345-6",
                title="Deep Learning Frameworks for Intelligent Medical Diagnostics",
                month="July",
                date_of_publication=datetime.date(2026, 7, 15),
                milestone_achieved="Book Published",
                notes="Co-authored with international research team",
                status="APPROVED"
            )
            db.add(pub)
            db.commit()

        # Seed sample notifications if none exist
        notif_count = db.query(models.Notification).count()
        if notif_count == 0:
            print("Seeding sample notifications...")
            n1 = models.Notification(
                user_id=faculty_user.id,
                title="Activity Approved",
                message="Your activity 'Python for Data Science' has been approved by the Admin.",
                is_read=False,
                link="/activities"
            )
            n2 = models.Notification(
                user_id=admin_user.id,
                title="New Submission For Review",
                message="Dr. A. Hemalatha submitted a Workshop activity for review.",
                is_read=False,
                link="/activities"
            )
            db.add_all([n1, n2])
            db.commit()

        # Seed sample audit log
        audit_count = db.query(models.AuditLog).count()
        if audit_count == 0:
            print("Seeding initial audit logs...")
            a1 = models.AuditLog(
                user_id=admin_user.id,
                user_email=admin_user.email,
                action="SYSTEM_INIT",
                entity="System",
                entity_id=1,
                details="Portal initialized with development admin and faculty profiles."
            )
            db.add(a1)
            db.commit()

        print("Migration and seed completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration_and_seed()

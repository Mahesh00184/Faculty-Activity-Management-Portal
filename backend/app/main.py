from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import engine
from app.models import models
from app.api import (
    auth,
    faculty,
    activities,
    publications,
    certificates,
    reports,
    analytics,
    notifications,
    audit_logs,
    excel_io
)

# Ensure database tables exist
models.Base.metadata.create_all(bind=engine)

# Ensure uploads directory exists
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(os.path.join(UPLOAD_DIR, "certificates"), exist_ok=True)

app = FastAPI(
    title="Faculty Activity Management Portal API",
    description="Production-grade API for Faculty Activity, Publication, and Accreditation Tracking",
    version="1.0.0"
)

# CORS configuration
const_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
origins = []
for origin in const_origins.split(","):
    cleaned = origin.strip()
    if cleaned:
        origins.append(cleaned)
        if cleaned.endswith("/"):
            origins.append(cleaned.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(faculty.router, prefix="/api/faculty", tags=["Faculty"])
app.include_router(activities.router, prefix="/api/activities", tags=["Activities"])
app.include_router(publications.router, prefix="/api/publications", tags=["Publications"])
app.include_router(certificates.router, prefix="/api/certificates", tags=["Certificates"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics & Dashboard"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(audit_logs.router, prefix="/api/audit-logs", tags=["Audit Logs"])
app.include_router(excel_io.router, prefix="/api/excel", tags=["Excel Import/Export"])

@app.get("/")
def read_root():
    return {
        "message": "Faculty Activity Management Portal API is running",
        "docs_url": "/docs",
        "status": "online"
    }

@app.on_event("startup")
def startup_event():
    # Run safe check and seed
    try:
        from migrate_and_seed import run_migration_and_seed
        run_migration_and_seed()
    except Exception as e:
        print(f"Startup migration/seed notice: {e}")

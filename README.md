# Faculty Activity Management Portal

A professional, modern full-stack web application designed for a college faculty/admin user to manage activities, publications, and certificates.

## Architecture & Technology Stack
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
- **Database**: SQLite (Development) / PostgreSQL (Production ready)

## Features
- **Faculty Dashboard**: Modern responsive UI with statistics and activity overview.
- **Activity Tracking**: Manage MOOCs, FDPs, Workshops, etc.
- **REST API**: Robust FastAPI implementation with SQLAlchemy ORM.

## Setup Instructions

### 1. Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # On Windows
pip install -r requirements.txt # (or install dependencies listed in setup)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend will run at `http://localhost:5173`

### 3. Demo Data
To seed initial data to the database, run:
```bash
cd backend
.\venv\Scripts\activate
python seed.py
```

## Future Scope (Phases Remaining)
The foundation architecture supports all required phases. Further development will include extending endpoints for Publications, Certificate Google Drive Integration, Excel Import/Export via Pandas/OpenPyxl, and PDF generation with ReportLab.

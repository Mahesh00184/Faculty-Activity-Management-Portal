# Faculty Activity Management Portal — Deployment Guide

This guide provides step-by-step instructions for deploying the Faculty Activity Management Portal to production using **Render** (FastAPI backend) and **Vercel** (React + Vite frontend).

---

## Architecture Overview

- **Frontend**: React + TypeScript + Vite + Tailwind CSS (Hosted on Vercel)
- **Backend**: FastAPI + SQLAlchemy + SQLite (Hosted on Render Web Service)
- **Database**: SQLite (`sql_app.db`)

---

## ⚠️ Important Database & Hosting Persistence Warnings

### 1. Local SQLite Database (`sql_app.db`) & GitHub Exclusion
> [!IMPORTANT]
> **The local SQLite database (`sql_app.db`) is excluded from GitHub.**
> Therefore, deploying the backend to Render will **NOT** automatically include your local development database or its existing local records.
> 
> - **Do NOT** commit the local SQLite database file to GitHub.
> - The Render service will have its **own independent database file** created at runtime on Render.
> - Free Render filesystem storage is ephemeral and is not suitable for reliable long-term SQLite persistence. When the free service restarts, sleeps from inactivity, or redeploys, non-persisted local SQLite file writes will reset.
> - For a true production deployment with permanent persistent data, a managed database like **PostgreSQL** should be used. (The application codebase is already equipped to connect to PostgreSQL simply by configuring `DATABASE_URL=postgresql://user:password@host:port/dbname`).

### 2. Local Certificate File Storage
> [!WARNING]
> - Certificate uploads are saved locally in the `backend/uploads/certificates/` directory.
> - Files uploaded to a free cloud instance's local filesystem may not persist across restarts or redeployments.
> - For permanent file persistence in production, attach persistent volume storage or migrate to an S3-compatible cloud object store. The current local functionality is fully preserved for local and staging workflows.

---

## Step-by-Step Deployment Instructions

### PART A — Push Project to GitHub

1. Confirm that local database files (`sql_app.db`, `*.db`), `.env` files, `node_modules/`, `venv/`, and `dist/` are in `.gitignore`. Do NOT commit `sql_app.db`.
2. Initialize git and commit your project (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Prepare Faculty Activity Management Portal for deployment"
   ```
3. Create a new repository on [GitHub](https://github.com/new).
4. Add remote and push your code:
   ```bash
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git
   git branch -M main
   git push -u origin main
   ```

---

### PART B — Deploy Backend to Render

1. Log in to your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.
4. Configure the service settings:
   - **Name**: `faculty-portal-backend`
   - **Region**: Choose the region closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Configure Environment Variables under **Advanced**:
   - `DATABASE_URL`: `sqlite:///./sql_app.db`
     *(Note: This creates an independent SQLite instance on Render; it does not import your local records)*
   - `SECRET_KEY`: *Click "Generate" or provide a secure random 32+ character string*
   - `CORS_ORIGINS`: `http://localhost:5173` *(Temporary until Vercel URL is created)*
6. Health Check Path:
   - Under **Health Check Path**, enter: `/health`
7. Click **Create Web Service**.
8. Wait for the build and deployment to complete. Note down your Render backend URL:
   - Example placeholder: `https://YOUR-RENDER-BACKEND-URL.onrender.com`
9. Verify health check by visiting:
   ```
   https://YOUR-RENDER-BACKEND-URL.onrender.com/health
   ```
   Expected response:
   ```json
   { "status": "ok" }
   ```

---

### PART C — Deploy Frontend to Vercel

1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** → **Project**.
3. Select and import your GitHub repository.
4. Configure the project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend` *(Click Edit and select the `frontend` folder)*
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Configure Environment Variables:
   - Name: `VITE_API_URL`
   - Value: `https://YOUR-RENDER-BACKEND-URL.onrender.com/api`
   *(Replace `YOUR-RENDER-BACKEND-URL` with your actual Render service domain from Part B. Ensure it includes `/api` at the end).*
6. Click **Deploy**.
7. Vercel will build and assign a production URL (e.g. `https://YOUR-VERCEL-URL.vercel.app`).
8. Single Page Application (SPA) routing is pre-configured via `frontend/vercel.json` so direct routes like `/login`, `/dashboard`, `/activities`, `/faculty`, `/reports`, `/analytics` load properly.

---

### PART D — Update Render CORS

1. Return to your [Render Dashboard](https://dashboard.render.com).
2. Select your `faculty-portal-backend` service.
3. Navigate to **Environment**.
4. Update the `CORS_ORIGINS` environment variable to include your Vercel URL:
   ```
   CORS_ORIGINS=http://localhost:5173,https://YOUR-VERCEL-URL.vercel.app
   ```
   *(Replace `https://YOUR-VERCEL-URL.vercel.app` with the exact URL generated by Vercel in Part C. Both local development and Vercel production will now be permitted).*
5. Click **Save Changes**. Render will automatically restart the service.

---

## Verification Checklist

- [ ] Backend `/health` returns `{"status": "ok"}`
- [ ] Vercel frontend loads login page at `/login`
- [ ] User authentication succeeds via API calls to Render
- [ ] Protected routes (`/dashboard`, `/activities`, `/publications`, `/certificates`, etc.) navigate without 404 on page refresh
- [ ] CORS headers allow requests from the Vercel production domain

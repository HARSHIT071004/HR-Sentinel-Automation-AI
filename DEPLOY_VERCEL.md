# Deploy HR Sentinel AI to Vercel

This guide covers deploying the full-stack HR Sentinel AI (FastAPI + React) on Vercel.

---

## Prerequisites

- A [Vercel](https://vercel.com) account (free tier works)
- A **PostgreSQL** database – required because Vercel's serverless environment is **ephemeral** (SQLite won't persist). Use one of:
  - [Neon](https://neon.tech) (free serverless Postgres)
  - [Supabase](https://supabase.com) (free Postgres)
  - [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres) (built-in, but requires Pro plan)
- An **OpenRouter** (or OpenAI) API key for AI features
- Your project pushed to a **GitHub** repository

---

## 1. Prepare Environment Variables

Set these in the **Vercel dashboard → Your Project → Settings → Environment Variables**:

| Variable | Value | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/dbname` | Replace with your Postgres connection string from Neon/Supabase |
| `JWT_SECRET_KEY` | `<random-64-char-string>` | Generate: `openssl rand -hex 32` or use a password manager |
| `OPENAI_API_KEY` | `sk-or-v1-...` | Your OpenRouter or OpenAI API key |
| `CORS_ORIGINS` | `["https://your-app.vercel.app"]` | Replace with your actual Vercel domain |
| `APP_NAME` | `HR Sentinel AI` | |
| `APP_VERSION` | `1.0.0` | |
| `DEBUG` | `false` | |

> **Note**: `FILE_UPLOAD` uses a local `./uploads` directory by default. For production, switch to cloud storage (e.g., Vercel Blob, AWS S3). See [Cloud Storage for Uploads](#5-cloud-storage-for-uploads) below.

---

## 2. Deploy on Vercel

### Option A: Vercel CLI (recommended for full control)

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from project root
vercel --prod
```

### Option B: Vercel Git Import

1. Push your repo to GitHub.
2. Go to [vercel.com/new](https://vercel.com/new).
3. Import your GitHub repository.
4. Vercel will auto-detect the settings from `vercel.json`.
5. Add the environment variables from step 1.
6. Click **Deploy**.

---

## 3. Files Created for Vercel

### `api/index.py` – Serverless entry point

Vercel Python functions look for handlers in the `api/` directory. This file imports your FastAPI `app` from `backend/app/main.py`.

```python
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.main import app

handler = app
```

### `pyproject.toml` – Entrypoint declaration

Tells Vercel's framework detection where the FastAPI entrypoint lives, so it doesn't need to guess.

```toml
[tool.vercel]
entrypoint = "api/index.py"
```

### `vercel.json` – Project configuration

```json
{
  "buildCommand": "cd dashboard && npm install && npm run build",
  "outputDirectory": "dashboard/dist",
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index" },
    { "source": "/((?!api/).*)", "destination": "/index.html" }
  ],
  "functions": {
    "api/index.py": {
      "runtime": "@vercel/python@3.12",
      "memory": 512,
      "maxDuration": 30
    }
  }
}
```

---

## 4. Architecture on Vercel

```
User Request
     │
     ▼
  Vercel CDN
     │
     ├── /api/*  ──►  Python Serverless Function (FastAPI)
     │                     │
     │                     ▼
     │               PostgreSQL (Neon/Supabase)
     │
     └── /*  ──►  Static Files (React SPA from dashboard/dist)
                       │
                       ▼
                 SPA Fallback to index.html
```

---

## 5. Cloud Storage for Uploads

The default `UPLOAD_DIR=./uploads` is **writable but ephemeral** on Vercel – files will be lost after a cold start.

**Recommended**: Use Vercel Blob for persistence:

1. Add `@vercel/blob` to the backend:
   ```
   pip install @vercel/blob
   ```
2. Add `BLOB_READ_WRITE_TOKEN` to Vercel environment variables.
3. Update upload logic in `backend/app/services/` to use `@vercel/blob` instead of local disk.

Alternatively, use AWS S3 or Cloudinary.

---

## 6. Database Setup (Neon – recommended free tier)

1. Go to [neon.tech](https://neon.tech) and create a free account.
2. Create a project → copy the **connection string**.
3. It looks like:
   ```
   postgresql+asyncpg://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb
   ```
4. Set this as `DATABASE_URL` in Vercel environment variables.

---

## 7. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| 500 errors on API calls | Missing `DATABASE_URL` | Ensure Postgres env var is set |
| "no such table" errors | Tables not created | Vercel cold start should auto-create via `lifespan` in `main.py` – or run a migration script manually |
| CORS errors in browser | `CORS_ORIGINS` doesn't match domain | Set it to `["https://your-app.vercel.app"]` |
| Uploads disappear after deploy | Ephemeral filesystem | Switch to Vercel Blob or S3 |
| 504 Gateway Timeout | Function exceeds 30s limit | Check for long-running queries; increase `maxDuration` (up to 300s on Pro) |

---

## 8. Post-Deployment Checks

- [ ] Hit `https://your-app.vercel.app/` – should show the landing page
- [ ] `https://your-app.vercel.app/api/v1/health` – should return `{"status": "ok"}`
- [ ] `https://your-app.vercel.app/docs` – should load Swagger UI
- [ ] Upload a test attendance file and verify data appears on the dashboard
- [ ] Test login with default credentials (check backend seed script)

---

## 9. Alternative: Backend-only on Vercel + Frontend elsewhere

If you prefer to host only the API on Vercel and the frontend on a separate platform (e.g., Netlify, Cloudflare Pages):

1. Deploy the frontend as a static site (`dashboard/`).
2. Set `VITE_API_URL` during frontend build to the backend URL (e.g., `https://your-api.vercel.app/api/v1`).
3. Deploy only the `api/` directory and `backend/` folder to Vercel.

---

## Useful Links

- [Vercel Python Runtime Docs](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Neon Serverless Postgres](https://neon.tech)
- [Vercel Blob Storage](https://vercel.com/docs/storage/vercel-blob)
- [Vercel Environment Variables](https://vercel.com/docs/projects/environment-variables)

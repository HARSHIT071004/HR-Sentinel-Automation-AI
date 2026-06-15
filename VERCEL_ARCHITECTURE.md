# Vercel Deployment Architecture

## How the current setup works (root-folder deploy)

The files in this repo are configured to deploy **frontend + backend as a single Vercel project** from the root folder:

```
vercel build      # builds frontend from dashboard/, detects Python backend
     │
     ▼
  Vercel CDN
     │
     ├── /api/*  ──►  Python Serverless Function (FastAPI from api/index.py)
     │
     └── /*  ──►  Static SPA files (dashboard/dist/index.html)
```

When you import the repo or run `vercel --prod`, Vercel:
1. Builds the **React frontend** (`dashboard/`) into static files
2. Deploys `api/index.py` as a **Python serverless function** handling `/api/*`
3. Rewrites all other routes to `index.html` (SPA fallback)

---

## Option A: Single deploy from root (✅ current setup)

**One project, one domain** (e.g., `hr-sentinel.vercel.app`).

| Pro | Con |
|---|---|
| Simple – one deploy, one domain | Function cold starts affect API |
| Frontend & API always in sync | Scaling is coupled |
| No CORS issues (same origin) | 30s function timeout (free tier) |

---

## Option B: Separate deploys

**Two projects, two domains** (e.g., `dashboard.vercel.app` + `api.vercel.app`).

| Pro | Con |
|---|---|
| Scale independently | Need CORS config |
| Different runtimes/limits per project | Two deploys to manage |
| Isolate failures | Slightly higher latency (cross-origin) |

**To split**: deploy `dashboard/` as a Vite project, and `backend/` + `api/` as a FastAPI project separately.

---

## Recommendation

**Start with Option A** (current setup). It's simpler and works well. Switch to Option B only if you need independent scaling or hit the 30s function limit.

Either way, you need a remote PostgreSQL database (Neon/Supabase) – SQLite won't work on Vercel.

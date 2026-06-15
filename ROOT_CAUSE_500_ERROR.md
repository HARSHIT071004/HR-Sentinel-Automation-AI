# Root Cause: 500 Error on Vercel

## The Problem

Login returns 500 (POST `/api/v1/auth/login`). The function crashes at **import time** — before any request logic runs. This means every endpoint, including login, fails with 500 because the Python process never finishes loading.

## The Import Chain

```
api/index.py
  → from app.main import app
    → from app.api.router import api_router
      → from app.api.v1 import auth, employees, departments, attendance, dashboard, health, ai, copilot
        → attendance.py → AttendanceService
          → attendance_service.py → ingest_attendance_records, delete_attendance_embeddings
            → attendance_ingestion.py → vector_store
              → vector_store.py → import numpy as np   ← CRASH
```

The `router.py` imports **all** V1 route modules at module load time. The `attendance` module triggers a chain that ends with `vector_store.py` trying to `import numpy as np`.

## Why numpy is Missing

- `numpy` (and `faiss`) were removed from `requirements.txt` because these native C++ libraries **crash on Vercel's Lambda ARM architecture** (incompatible binaries).
- Without numpy, every import of `vector_store.py` or `ai_client.py` fails with `ModuleNotFoundError: No module named 'numpy'`.
- This kills the entire Python process before FastAPI can serve any endpoint — including login.

## The Fix

Two files were changed to use **lazy imports** instead of top-level imports:

### 1. `backend/app/core/vector_store.py`

Wrapped `import numpy` and `import faiss` in a `try/except ModuleNotFoundError`. When missing:
- `HAS_VECTOR_STORE = False` flag is set
- All vector operations (`add`, `search`, `delete`, `save`, `load`) become no-ops
- Methods return empty results instead of crashing

### 2. `backend/app/core/ai_client.py`

Replaced top-level `import numpy as np` with a **lazy import inside the function** that uses it (`_hash_embedding`). When numpy is absent, a pure-Python fallback using `random.Random` generates the deterministic embedding vector.

## Result

The app loads successfully without numpy. Vector search (FAISS) and OpenAI embeddings degrade gracefully — they simply won't work on Vercel, but login, CRUD, and database operations function normally.

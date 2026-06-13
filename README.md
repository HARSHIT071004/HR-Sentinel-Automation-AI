# HR Sentinel AI — Workforce Intelligence Platform

AI-powered attendance management with real-time dashboards, risk scoring, behavior analysis, and RAG document chat.

---

## Features

- **Upload** Excel/CSV files — auto-creates employee profiles
- **Dashboard** — real-time stats: total employees, present, late, missing punches
- **Employees** — directory with per-employee AI risk scoring
- **AI Insights** — risk scores (0–100) + behavior analysis with LLM reasoning
- **Delete** files — cascading cleanup removes records, employees, and AI data
- **RAG Copilot** — chat with HR policies via FAISS vector search
- **90-day analysis** — AI looks back up to 90 days for trend detection

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+

### 1. Backend Setup
```bash
cd backend
pip install -r ..\requirements.txt
```

### 2. Environment
Create `backend\.env`:
```env
OPENAI_API_KEY=sk-or-v1-...    # Get free at https://openrouter.ai/keys
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openrouter/free
```

Without `.env`, the AI falls back to rule-based scoring — everything else still works.

### 3. Seed Database (first time only)
```bash
cd backend
python seed.py
# Creates: admin@aegis.com / admin123
#          hr@aegis.com   / hr123
```

### 4. Start Backend
```bash
cd backend
python -m uvicorn app.main:app --port 8080
```

### 5. Frontend Setup
```bash
cd dashboard
npm install
npm run dev
```

### 6. Login
```
http://localhost:5173
Email: hr@aegis.com
Pass:  hr123
```

### 7. Generate Test Data (optional)
```bash
cd backend
python generate_excel.py
# Creates attendance_50_employees.xlsx (50 employees, 5 days)
```

---

## Uploading Files

| Format | Column Headers (any case/spacing work) |
|--------|----------------------------------------|
| `.xlsx` | `Employee ID`, `Name`, `Date`, `Time`, `Status` |
| `.xls` | Same as above |
| `.csv` | Same as above |

Accepted header variations: `employee_id`, `Emp ID`, `Employee Code`, `employee name`, `Full Name`, etc.

---

## Architecture

```
Frontend (React/Vite :5173)
    │ proxy /api → :8080
    ▼
Backend (FastAPI :8080)
    ├── API Routes  ───  Services  ───  Repositories
    └── SQLite DB (hr_sentinel.db)
    └── FAISS Vector Store (RAG)
    └── OpenRouter AI (free model)
```

### Project Layout

```
HR-Sentinel-Automation-AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/       # Routes (auth, employees, attendance, ai, copilot...)
│   │   ├── core/          # Config, AI client, security, vector store
│   │   ├── models/        # SQLAlchemy models
│   │   ├── repositories/  # Database queries
│   │   ├── schemas/       # Pydantic response models
│   │   ├── services/      # Business logic (attendance, AI, copilot...)
│   │   └── utils/         # Document ingestion, types
│   ├── seed.py
│   ├── generate_excel.py
│   └── ingest_documents.py  # Populate FAISS with HR policies
├── dashboard/
│   └── src/
│       ├── pages/         # Dashboard, Employees, Attendance, AI Insights
│       ├── stores/        # Zustand auth store
│       ├── api/           # Axios client with JWT interceptor
│       └── components/    # UI components
├── requirements.txt
├── .gitignore
└── README.md
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Login |
| `/api/v1/employees` | GET | List employees (paginated) |
| `/api/v1/dashboard/stats` | GET | Dashboard statistics |
| `/api/v1/dashboard/feed` | GET | Today's attendance feed |
| `/api/v1/attendance/upload` | POST | Upload Excel/CSV |
| `/api/v1/attendance/files` | GET | List uploaded files |
| `/api/v1/attendance/files/{id}` | DELETE | Delete file + cascade cleanup |
| `/api/v1/ai/risk/{employee_id}` | GET | AI risk score |
| `/api/v1/ai/behavior/{employee_id}` | GET | AI behavior analysis |
| `/api/v1/copilot/chat` | POST | RAG chat with HR policies |

---

## RAG Copilot

The copilot uses FAISS vector search to answer HR policy questions:

```bash
# Populate FAISS with default policies
cd backend
python ingest_documents.py
```

Then chat via the API or frontend (when added):
```bash
curl -X POST http://localhost:5173/api/v1/copilot/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the attendance policy about late arrivals?"}'
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI, SQLAlchemy 2.0, SQLite |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| AI | OpenRouter (free model), rule-based fallback |
| RAG | FAISS, keyword + vector search |
| Auth | JWT (python-jose), bcrypt |
| State | Zustand, TanStack React Query |

---

## Contributing

1. Fork the repo
2. Create a feature branch
3. Run `pip install -r requirements.txt` and `npm install`
4. Start both servers
5. Make changes, verify with `python seed.py` and a test upload

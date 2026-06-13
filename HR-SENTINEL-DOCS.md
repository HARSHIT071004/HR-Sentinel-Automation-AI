# HR Sentinel AI — Workforce Intelligence Platform

## Overview

HR Sentinel AI is an end-to-end **attendance management & workforce intelligence platform**. It ingests raw attendance data (Excel/CSV), automatically profiles employees, computes real-time dashboard metrics, and runs **AI-powered risk scoring & behavior analysis** — all through a modern web UI.

---

## How Data Flows

```
User Uploads File (Excel/CSV)
         |
         v
  Backend Parser (attendance.py)
    - Supports: .xlsx, .xls, .csv
    - Normalises column headers: "Employee ID" → "employee_id"
         |
         v
  consolidate_attendance() (attendance_service.py)
    - Groups IN/OUT punches per employee per day
    - Flags late arrivals (after 11:00 AM)
    - Detects missing punches
    - Deduplicates via SHA-256 hash
         |
         v
  process_upload()
    - Creates EmployeeProfile records (auto)
    - Upserts DailyRecord rows
    - Computes MonthlySummary (late counts, strike levels)
    - Generates WarningLog entries for escalations
         |
         v
  Frontend (React + Vite)
    - Dashboard: real-time stats
    - Employees: directory with risk scores
    - Attendance: upload history & delete
    - AI Insights: risk scoring & behavior analysis
```

---

## Column Header Support

Any of these formats work automatically:

| Field | Accepted Headers |
|-------|-----------------|
| Employee ID | `employee_id`, `Employee ID`, `Emp ID`, `emp_id`, `Employee Code`, `EmployeeID` |
| Name | `name`, `Name`, `Employee Name`, `Emp Name`, `employee_name`, `Full Name` |
| Date | `date`, `Date` |
| Time | `time`, `Time` |
| Status | `status`, `Status`, `punch_status` (IN/OUT) |

Extra columns like `Department` are ignored — they don't break anything.

---

## Features by Section

### 1. Dashboard (`/`)
- **Stats cards**: Total Employees, Present Today, Late Today, Missing Punches
- **Attendance Feed**: per-employee today's check-in/out, status (Present/Late/Absent), strike count
- **Strike Distribution**: how many employees are on Strike 1/2/3
- **AI Insights Panel**: late count, warnings issued, attendance rate %

### 2. Employees (`/employees`)
- Lists all employees auto-created from uploads
- Shows: Name, ID, Department, Designation, Email
- **Risk Score** button — click to get AI-powered risk assessment per employee
- After file delete: employees with 0 attendance records are auto-removed

### 3. Attendance (`/attendance`)
- Upload .xlsx / .xls / .csv files
- View upload history (file name, rows, records created, status)
- **Delete** removes the file + cascades:
  - DailyRecord rows deleted
  - MonthlySummary recalculated (empty ones deleted)
  - RiskScore / AIWarning / WarningLog cleaned up
  - EmployeeProfiles with 0 remaining records deleted
  - Dashboard resets to 0

### 4. AI Insights (`/ai`)
- **Risk Score**: selects employee → returns score (0–100), level (LOW/MEDIUM/HIGH/CRITICAL), reasoning + recommendations
- **Behavior Analysis**: detailed pattern analysis, anomalies, trends, potential causes
- Powered by **OpenRouter free model** (`openrouter/free`) — real LLM reasoning, not rule-based

---

## How the 90-Day Analysis Works

The AI service (`ai_service.py`) computes features from the **last 90 days** of attendance data:

```
_compute_features(employee_id, days=90)
         |
         v
  For each employee:
    - total_days:   # of days with records
    - late_count:   # of days flagged late
    - late_pct:     late_count / total_days * 100
    - avg_checkin:  average check-in time
    - max_streak:   longest consecutive late streak
    - checkin_trend: declining / improving / stable
      (compares recent 14 days vs older period)
    - dow_pattern:  which weekdays have most lateness
    - monthly_history: breakdown by month
```

These features are sent to the LLM (via OpenRouter) which generates **contextual risk scores** and **behavior summaries** with real reasoning, not templates.

### What "90 Days" Means for You

- If you upload **5 days** of data → AI analyses those 5 days (highest available within the 90-day window)
- If you upload **90 days** → AI analyses the full 90-day trend
- The `cutoff_date` slides: `date.today() - 90 days`, so old data beyond 90 days is ignored
- **Upload more data = better AI insights** (more patterns, stronger trend detection)

---

## How It Helps HR & Employees

### For HR Managers

| Need | How HR Sentinel Helps |
|------|----------------------|
| **Track attendance** | Upload Excel/CSV → instant dashboard |
| **Identify late employees** | Dashboard shows Late Today count |
| **Escalate issues** | Strike system: Strike 1 (friendly) → Strike 2 (formal) → Strike 3 (final warning + HR meeting) |
| **AI-powered insights** | Risk scores identify who needs attention |
| **Behavior analysis** | Understand patterns (e.g., "always late on Mondays") |
| **Clean up data** | Delete outdated uploads — cascading cleanup |
| **No manual entry** | Auto-creates employee profiles from upload data |
| **Free AI** | Uses OpenRouter's free models — no API costs |

### For Employees

| Need | How HR Sentinel Helps |
|------|----------------------|
| **Know your status** | Dashboard shows attendance feed per employee |
| **Transparent scoring** | AI risk scores are explainable with reasoning |
| **Fair warnings** | Escalation system is automatic and consistent |
| **Data-driven** | All decisions based on uploaded attendance records |

---

## Technical Architecture

```
┌─────────────────────────────────────────────────┐
│                 Frontend (React + Vite)          │
│  Port 5173  │  Proxy: /api → localhost:8080     │
│  Pages: Dashboard, Employees, Attendance, AI     │
│  State: Zustand (auth) + React Query (data)     │
└────────────────────────┬────────────────────────┘
                         │ HTTP / JSON
                         ▼
┌─────────────────────────────────────────────────┐
│          Backend (FastAPI + Uvicorn)             │
│               Port 8080                          │
│                                                   │
│  ┌─────────────┐  ┌──────────────┐               │
│  │  API Routes  │  │  Services    │               │
│  │  /auth       │  │  Attendance  │               │
│  │  /employees  │  │  AI          │               │
│  │  /dashboard  │  │  Employee    │               │
│  │  /attendance │  │  Dashboard   │               │
│  │  /ai         │  │  Auth        │               │
│  └──────┬──────┘  └──────┬───────┘               │
│         │                │                        │
│         ▼                ▼                        │
│  ┌──────────────────────────────────────────┐    │
│  │           Repositories (SQLAlchemy)       │    │
│  └──────────────────┬───────────────────────┘    │
│                     │                             │
│                     ▼                             │
│  ┌──────────────────────────────────────────┐    │
│  │        SQLite (hr_sentinel.db)            │    │
│  │  Tables: users, employee_profiles,        │    │
│  │  daily_records, monthly_summaries,        │    │
│  │  upload_logs, warning_logs, risk_scores,  │    │
│  │  ai_warnings, ai_reports, ai_usage_logs   │    │
│  └──────────────────────────────────────────┘    │
└───────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│          OpenRouter AI (Free Model)              │
│  Model: openrouter/free                          │
│  Used for: risk scoring, behavior analysis,      │
│  warning generation, executive reports           │
└─────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Start backend
cd backend
python -m uvicorn app.main:app --port 8080

# 2. Start frontend
cd dashboard
npm run dev

# 3. Login
# URL: http://localhost:5173
# Email: hr@aegis.com
# Pass:  hr123

# 4. Generate test data
cd backend
python generate_excel.py
# Creates: attendance_50_employees.xlsx

# 5. Upload in UI
# Go to Attendance tab → upload file
# Check Dashboard, Employees, AI Insights
```

---

## Database Seeding

```bash
cd backend
python seed.py
# Creates: admin@aegis.com, hr@aegis.com
# + 4 departments (Engineering, Product, Design, Marketing, HR)
# NO fake attendance data — upload real files to populate
```

---

## Key Design Decisions

1. **Cascade delete**: Removing a file removes its records, AI data, and orphaned employees
2. **Dedup by hash**: Same file content (same records) rejected with 409 Conflict
3. **Column header normalisation**: Any common format works — no need to rename columns
4. **LLM fallback**: If OpenRouter is unavailable, rule-based scoring kicks in
5. **Real LLM reasoning**: Uses `openrouter/free` model — free, no API key costs beyond free tier
6. **Pagination**: Employee list defaults to 20 per page; dashboard shows aggregate totals

---

## Future Scope

- CSV export of reports
- Department filters on dashboard
- Email notifications for warnings
- PDF report generation
- Multi-tenant support
- Role-based access controls per department

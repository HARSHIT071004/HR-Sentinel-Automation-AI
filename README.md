# Growify: AI-Powered Attendance & Warning System

Growify is an enterprise-grade automated HR solution that orchestrates biometric attendance logs, identifies late arrivals, and triggers AI-powered warning escalations via Gmail and Google Calendar.

---

## 🚀 Quick Start

### 1. Database Setup (PostgreSQL 15+)
```bash
psql -U your_user -d your_db -f schema.sql
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```
> **Note**: The core logic uses only Python standard library. The `requirements.txt` lists optional packages for extending the project beyond n8n.

### 3. Dashboard Setup (React/Vite)
```bash
cd dashboard
npm install
npm run dev
```
The dashboard will be available at `http://localhost:5173`.

### 4. Automation Setup (n8n)
1. Import `workflow.json` into your [n8n](https://n8n.io/) instance.
2. Configure your credentials in n8n:
   - **PostgreSQL** — for database operations.
   - **OpenAI** — for AI-generated warning emails.
   - **Gmail** — for sending emails.
   - **Google Calendar** — for scheduling meetings.
3. Ensure `logic.py` is accessible from the n8n server's working directory.

### 5. Running Logic Standalone (Optional)
```bash
python logic.py data.json            # File path
cat data.json | python logic.py      # Stdin pipe
```

### 6. Running Tests
```bash
python test_logic.py
```

---

## 🧠 Core Logic (`logic.py`)

All attendance processing lives in a single Python file — the **single source of truth**.

### Attendance Consolidation
1. **Grouping**: All biometric punches are grouped by `(Employee ID, Date)`.
2. **Flattening**: The **earliest "IN"** punch → `check_in`, the **latest "OUT"** → `check_out`.
3. **Late Detection**: `check_in` after **11:00 AM IST** → `late_flag = true`.
4. **Missing Punches**: Missing "IN" or "OUT" → `missing_punch = true`.
5. **Idempotency**: **SHA-256 hash** of sorted input → `file_hash`. The `upload_log` table rejects duplicates.

### The "Strike" Escalation System
Rolling monthly strike count per employee:
- **Strike 1 — Friendly**: Supportive reminder email (OpenAI, warm tone).
- **Strike 2 — Formal**: Serious warning referencing repeated violations (OpenAI, firm tone).
- **Strike 3 — Critical**: Final warning + **Mandatory HR Meeting** at 5:00 PM via Google Calendar.

---

## 📂 Complete Project Map

```
Growify/
├── logic.py              # Core attendance logic (Python)
├── test_logic.py         # Verification suite for logic.py
├── workflow.json         # n8n automation workflow
├── schema.sql            # PostgreSQL database schema
├── prompts.md            # AI prompt templates
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── dashboard/            # React frontend
    ├── src/
    │   ├── App.tsx        # Main dashboard component
    │   ├── index.css      # Design system & styling
    │   └── main.tsx       # React entry point
    ├── index.html         # HTML shell
    ├── package.json       # Node.js dependencies
    ├── tsconfig.json      # TypeScript configuration
    └── vite.config.ts     # Vite bundler configuration
```

### File-by-File Breakdown

| File | Role | What It Does |
|---|---|---|
| **`logic.py`** | 🧠 Core Engine | Groups biometric punches by employee+date, picks earliest IN / latest OUT, flags late arrivals (>11 AM), detects missing punches, generates SHA-256 hash for duplicate upload prevention. Accepts JSON via stdin or file path. |
| **`test_logic.py`** | ✅ Test Suite | Validates `logic.py` against 4 test cases: on-time employee, late arrival, missing punch, and multi-punch deduplication with field name variations. |
| **`workflow.json`** | 🔄 Orchestrator | n8n workflow with 12 nodes: Webhook trigger → Excel parser → Python Execute Command (`logic.py`) → PostgreSQL upsert → Late check → Strike lookup → OpenAI email generation → Gmail dispatch → Calendar scheduling → Warning log. |
| **`schema.sql`** | 🗄️ Database | PostgreSQL schema with 4 tables (`daily_records`, `monthly_summary`, `upload_log`, `warning_log`), indexes for fast lookups, auto-update triggers, and a `v_dashboard_today` view for the frontend. |
| **`prompts.md`** | 💬 AI Templates | Three prompt templates (Strike 1/2/3) with system + user prompt pairs, strict JSON output format, tone directives, and guardrails against hallucination. |
| **`requirements.txt`** | 📦 Dependencies | Python package list. Core logic needs only stdlib; optional packages listed for extending beyond n8n (psycopg2, openai, fastapi). |
| **`dashboard/src/App.tsx`** | 🖥️ Dashboard UI | React component showing live attendance feed (employee table with status/strikes), stat cards (total employees, late count, AI warnings, escalations), AI insights panel, and active alerts sidebar. |
| **`dashboard/src/index.css`** | 🎨 Styling | CSS design system with dark theme, glassmorphism effects, CSS variables for colors, and responsive grid layout. |

---

## 🔧 Tech Stack

| Layer              | Technology                    |
|--------------------|-------------------------------|
| **Orchestration**  | n8n (Workflow Automation)     |
| **Logic**          | Python (`logic.py`)           |
| **AI**             | OpenAI GPT-4o                 |
| **Database**       | PostgreSQL 15+                |
| **Frontend**       | React 18, Vite 6, TypeScript  |
| **Email**          | Gmail API                     |
| **Calendar**       | Google Calendar API           |

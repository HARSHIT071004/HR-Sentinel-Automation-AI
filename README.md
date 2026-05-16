# HR Sentinel Automation AI

HR Sentinel Automation AI is an enterprise-grade automated HR system that processes biometric attendance logs, detects late arrivals and missing punches, and triggers AI-powered escalation workflows via Gmail and Google Calendar. The system combines Python-based rule processing, workflow automation, AI-generated communication, and a real-time dashboard.

---

## Quick Start

### 1. Database Setup (PostgreSQL 15+)
```bash
psql -U your_user -d your_db -f schema.sql
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

> Note: The core logic uses only Python standard library. The requirements file includes optional dependencies for extended integrations beyond n8n.

### 3. Dashboard Setup (React / Vite)
```bash
cd dashboard
npm install
npm run dev
```

The dashboard will be available at:
```
http://localhost:5173
```

### 4. Automation Setup (n8n)
1. Import `workflow.json` into your n8n instance  
2. Configure credentials:
   - PostgreSQL for database operations  
   - OpenAI for AI-generated warning emails  
   - Gmail for sending notifications  
   - Google Calendar for scheduling HR meetings  
3. Ensure `logic.py` is accessible from the n8n execution environment  

### 5. Running Logic Standalone (Optional)
```bash
python logic.py data.json
cat data.json | python logic.py
```

### 6. Running Tests
```bash
python test_logic.py
```

---

## Core Logic (logic.py)

All attendance processing is handled in a single Python module, which acts as the system’s core decision engine.

### Attendance Processing Pipeline
1. Group attendance logs by Employee ID and Date  
2. Extract earliest IN as check-in and latest OUT as check-out  
3. Flag late arrivals if check-in is after 11:00 AM IST  
4. Detect missing IN or OUT punches  
5. Prevent duplicate processing using SHA-256 hashing  

---

### Strike Escalation System
The system maintains a rolling monthly strike count per employee:

- Strike 1: Friendly reminder email generated using AI  
- Strike 2: Formal warning email with escalation context  
- Strike 3: Critical escalation and mandatory HR meeting scheduled via Google Calendar  

---

## Project Structure

```
HR-Sentinel-Automation-AI/
├── logic.py
├── test_logic.py
├── workflow.json
├── schema.sql
├── prompts.md
├── requirements.txt
├── README.md
└── dashboard/
    ├── src/
    │   ├── App.tsx
    │   ├── index.css
    │   └── main.tsx
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
```

---

## File Responsibilities

| File | Role | Description |
|------|------|-------------|
| logic.py | Core Engine | Processes biometric attendance logs and detects anomalies |
| test_logic.py | Test Suite | Validates attendance logic across multiple scenarios |
| workflow.json | Automation Orchestrator | n8n workflow integrating Python, PostgreSQL, OpenAI, Gmail, and Google Calendar |
| schema.sql | Database Layer | Defines schema, indexes, triggers, and dashboard views |
| prompts.md | AI Layer | Structured prompts for HR escalation email generation |
| requirements.txt | Dependencies | Optional Python libraries for extended integrations |
| dashboard/src/App.tsx | Frontend UI | Displays attendance status, strikes, and AI insights |
| dashboard/src/index.css | UI System | Styling and layout system |

---

## Tech Stack

| Layer | Technology |
|------|------------|
| Orchestration | n8n Workflow Automation |
| Core Logic | Python |
| AI Layer | OpenAI GPT-4o |
| Database | PostgreSQL 15+ |
| Frontend | React 18, Vite, TypeScript |
| Email Service | Gmail API |
| Scheduling | Google Calendar API |
```

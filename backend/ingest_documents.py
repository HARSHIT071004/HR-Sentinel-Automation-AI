import sys
sys.path.insert(0, '.')

import numpy as np
from app.core.vector_store import vector_store


POLICIES = [
    {
        "id": "attendance_policy",
        "title": "Attendance Policy",
        "content": """# Attendance Policy

## Working Hours
Standard working hours are 9:00 AM to 6:00 PM IST, Monday through Friday.

## Check-in Policy
All employees must check in by 11:00 AM IST. Check-ins after 11:00 AM are considered late arrivals.

## Check-out Policy
All employees must check out when leaving for the day. Missing check-outs will be flagged as missing punches.

## Late Arrival Policy
- Late arrivals are tracked monthly
- Strike 1: Friendly reminder email
- Strike 2: Formal warning email
- Strike 3: Final warning + mandatory HR meeting

## Leave Policy
Leave requests must be submitted at least 24 hours in advance through the HR portal.

## Remote Work Policy
Remote work must be pre-approved by the manager. Remote days still require check-in by 11:00 AM.

## Overtime Policy
Overtime must be pre-approved. Overtime hours are tracked separately.""",
    },
    {
        "id": "leave_policy",
        "title": "Leave Policy",
        "content": """# Leave Policy

## Annual Leave
Employees are entitled to 20 days of annual leave per year.

## Sick Leave
Employees are entitled to 10 days of sick leave per year. Medical certificate required for 3+ consecutive days.

## Personal Leave
Employees are entitled to 5 days of personal leave per year.

## Public Holidays
Company observes national public holidays as per government notification.

## Leave Request Process
1. Submit request through HR portal
2. Manager approval required
3. HR notification for leaves > 3 days

## Leave Carry Forward
Maximum 5 days of annual leave can be carried forward to next year.""",
    },
    {
        "id": "escalation_policy",
        "title": "Escalation Policy",
        "content": """# Escalation Policy

## Strike System
The company uses a 3-strike system for attendance violations.

## Strike 1 - Friendly Warning
- Triggered on first late arrival in a month
- AI-generated friendly reminder email
- No formal action required

## Strike 2 - Formal Warning
- Triggered on second late arrival in a month
- AI-generated formal warning email
- Manager is notified
- Employee must acknowledge warning

## Strike 3 - Final Warning
- Triggered on third late arrival in a month
- AI-generated final warning email
- Mandatory HR meeting scheduled
- Attendance improvement plan required

## Monthly Reset
Strike counts reset at the beginning of each month.

## Appeals
Employees can appeal warnings through the HR department within 5 business days.""",
    },
    {
        "id": "conduct_policy",
        "title": "Code of Conduct",
        "content": """# Code of Conduct

## Professional Behavior
All employees are expected to maintain professional behavior at all times.

## Anti-Harassment Policy
The company has zero tolerance for harassment of any kind.

## Confidentiality
Employee attendance data is confidential and must be handled according to data protection policies.

## Dress Code
Business casual attire is required on all working days.

## Communication
All official communications should be through company email. Personal email should not be used for work-related matters.""",
    },
    {
        "id": "compensation_policy",
        "title": "Compensation Policy",
        "content": """# Compensation Policy

## Salary Structure
Salaries are reviewed annually based on performance and market rates.

## Performance Bonuses
Performance bonuses are awarded quarterly based on individual and team performance.

## Overtime Compensation
Overtime hours are compensated at 1.5x the regular hourly rate.

## Benefits
- Health insurance for employee and dependents
- Provident fund contributions
- Annual performance bonus
- Paid sick leave

## Salary Payment
Salaries are credited on the last working day of each month.""",
    },
]


def ingest_documents():
    print("Starting document ingestion into FAISS...")

    for policy in POLICIES:
        print(f"Ingesting: {policy['title']}")

        sections = policy["content"].split("\n## ")
        texts = []
        metadatas = []

        for i, section in enumerate(sections):
            if section.strip():
                texts.append(section.strip())
                metadatas.append({
                    "document_id": policy["id"],
                    "title": policy["title"],
                    "section_index": i,
                    "doc_type": "policy",
                })

        if texts:
            # Use random embeddings as fallback (will be replaced with real embeddings when API credits are added)
            np.random.seed(42 + len(texts))
            embeddings = np.random.randn(len(texts), 1536).astype(np.float32).tolist()

            vector_store.add_documents(
                collection="policies",
                texts=texts,
                metadatas=metadatas,
                embeddings=embeddings,
            )
            print(f"  Added {len(texts)} chunks")

    print(f"\nIngestion complete. Total documents in FAISS: {vector_store.get_store('policies').count()}")
    print("Note: Using random embeddings. Add OpenAI API credits for real semantic search.")


if __name__ == "__main__":
    ingest_documents()

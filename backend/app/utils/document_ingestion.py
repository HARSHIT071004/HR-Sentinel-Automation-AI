import re
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.chroma_client import chroma_service
from app.models.ai import AIUsageLog


class DocumentIngestion:
    def __init__(self, db: AsyncSession):
        self.db = db

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(".")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)
                if break_point > chunk_size * 0.5:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1

            if chunk.strip():
                chunks.append(chunk.strip())

            start = end - overlap

        return chunks

    def chunk_by_headers(self, text: str) -> list[dict]:
        sections = []
        current_header = "General"
        current_content = []

        for line in text.split("\n"):
            if re.match(r"^#{1,3}\s+", line):
                if current_content:
                    sections.append({
                        "header": current_header,
                        "content": "\n".join(current_content).strip(),
                    })
                current_header = re.sub(r"^#{1,3}\s+", "", line).strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections.append({
                "header": current_header,
                "content": "\n".join(current_content).strip(),
            })

        return sections

    async def ingest_document(
        self,
        collection_name: str,
        document_id: str,
        title: str,
        content: str,
        doc_type: str = "policy",
        metadata: dict | None = None,
    ) -> dict:
        sections = self.chunk_by_headers(content)

        documents = []
        metadatas = []
        ids = []

        for section in sections:
            chunks = self.chunk_text(section["content"])
            for i, chunk in enumerate(chunks):
                doc_id = f"{document_id}_{section['header']}_{i}"
                documents.append(chunk)
                metadatas.append({
                    "document_id": document_id,
                    "title": title,
                    "header": section["header"],
                    "doc_type": doc_type,
                    "chunk_index": i,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    **(metadata or {}),
                })
                ids.append(doc_id)

        if documents:
            chroma_service.add_documents(
                collection_name=collection_name,
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

        return {
            "document_id": document_id,
            "title": title,
            "chunks_created": len(documents),
            "sections": len(sections),
        }

    async def ingest_employee_summary(self, employee_id: str, name: str, summary: str) -> dict:
        return await self.ingest_document(
            collection_name="employee_summaries",
            document_id=f"emp_{employee_id}",
            title=f"Employee Summary: {name}",
            content=summary,
            doc_type="employee_summary",
            metadata={"employee_id": employee_id, "employee_name": name},
        )

    async def ingest_department_report(self, department_id: str, department_name: str, report: str) -> dict:
        return await self.ingest_document(
            collection_name="department_reports",
            document_id=f"dept_{department_id}",
            title=f"Department Report: {department_name}",
            content=report,
            doc_type="department_report",
            metadata={"department_id": department_id, "department_name": department_name},
        )


def get_default_policies() -> list[dict]:
    return [
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
    ]

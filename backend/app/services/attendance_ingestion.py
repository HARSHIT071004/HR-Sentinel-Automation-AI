import uuid
import logging
from datetime import datetime, timezone
from app.core.vector_store import vector_store
from app.core.ai_client import ai_client

logger = logging.getLogger(__name__)


def _build_record_texts(records: list[dict]) -> list[str]:
    texts = []
    for r in records:
        check_in = r.get("check_in", "-")
        check_out = r.get("check_out", "-")
        status = (
            "Late" if r.get("late_flag")
            else ("Missing punch" if r.get("missing_punch") else "Present")
        )
        texts.append(
            f"Employee {r['employee_id']} ({r['name']}) — Date: {r['date']}, "
            f"Check-in: {check_in}, Check-out: {check_out}, Status: {status}, "
            f"Punches: {r.get('raw_punch_count', 1)}"
        )
    return texts


def _build_summary_texts(records: list[dict]) -> list[str]:
    employee_records: dict[str, list[dict]] = {}
    for r in records:
        employee_records.setdefault(r["employee_id"], []).append(r)

    summaries = []
    for eid, recs in employee_records.items():
        name = recs[0]["name"]
        total = len(recs)
        late = sum(1 for r in recs if r.get("late_flag"))
        missing = sum(1 for r in recs if r.get("missing_punch"))
        month = recs[0].get("month_year", "unknown")
        dates = ", ".join(r["date"] for r in recs)
        summaries.append(
            f"Attendance Summary for {eid} ({name}) — Month: {month}, "
            f"Total days: {total}, Late arrivals: {late}, Missing punches: {missing}. "
            f"Dates: {dates}"
        )
    return summaries


async def ingest_attendance_records(records: list[dict], upload_id: uuid.UUID | None = None) -> int:
    if not records:
        return 0

    record_texts = _build_record_texts(records)
    summary_texts = _build_summary_texts(records)
    all_texts = record_texts + summary_texts

    metadatas = []
    for i, t in enumerate(all_texts):
        meta = {
            "text": t,
            "doc_type": "attendance",
            "upload_id": str(upload_id) if upload_id else "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        # Extract employee_id from the text
        for r in records:
            if r["employee_id"] in t:
                meta["employee_id"] = r["employee_id"]
                meta["employee_name"] = r.get("name", "")
                break
        metadatas.append(meta)

    embeddings = await ai_client.embed_batch(all_texts)
    vector_store.add_documents("attendance", all_texts, metadatas, embeddings)

    logger.info(f"Ingested {len(all_texts)} attendance chunks into FAISS (upload={upload_id})")
    return len(all_texts)


async def delete_attendance_embeddings(upload_id: uuid.UUID) -> int:
    return vector_store.delete_documents("attendance", "upload_id", str(upload_id))

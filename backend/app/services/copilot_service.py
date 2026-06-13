import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.core.ai_client import ai_client
from app.core.vector_store import vector_store
from app.models.chat import ChatConversation, ChatMessage
from app.models.ai import AIUsageLog
from app.models.attendance import MonthlySummary, DailyRecord
from app.utils.injection_protection import injection_protection


COPILOT_SYSTEM = """You are an AI HR Assistant for AegisHR. You help HR managers with workforce intelligence.

RULES:
1. Answer ONLY based on the provided context
2. If context is insufficient, say "I don't have enough information to answer that question"
3. Be helpful and professional
4. Never fabricate information
5. For data queries, provide specific numbers and names
6. For policy queries, cite the specific policy section"""


async def vector_search(collection: str, query: str, top_k: int = 5) -> list[dict]:
    """Vector search against a FAISS collection."""
    try:
        store = vector_store.get_store(collection)
        if store.count() == 0:
            return []
        query_embedding = await ai_client.embed(query)
        return store.search(query_embedding, top_k=top_k)
    except Exception:
        return []


async def query_summary_stats(db: AsyncSession) -> str:
    """Build a plain-text summary of current attendance data."""

    today = datetime.now(timezone.utc).date()
    current_month = today.strftime("%Y-%m")

    # Monthly summaries
    result = await db.execute(
        select(MonthlySummary).where(MonthlySummary.month_year == current_month)
    )
    summaries = list(result.scalars().all())

    if not summaries:
        return "No attendance data available for the current month."

    total_employees = len(summaries)
    total_late = sum(s.late_count for s in summaries)
    employees_with_warnings = [s for s in summaries if s.warning_level > 0]

    lines = [
        f"Current Month ({current_month}) Attendance Summary:",
        f"- Total employees with records: {total_employees}",
        f"- Total late arrivals: {total_late}",
        f"- Employees with active warnings: {len(employees_with_warnings)}",
    ]

    for s in summaries:
        lines.append(
            f"  {s.name} ({s.employee_id}): {s.late_count} late arrivals, "
            f"warning level {s.warning_level}, last late: {s.last_late_date or 'N/A'}"
        )

    return "\n".join(lines)


async def query_today_stats(db: AsyncSession) -> str:
    """Build a summary of today's attendance."""
    today = datetime.now(timezone.utc).date()

    result = await db.execute(
        select(DailyRecord).where(DailyRecord.date == today)
    )
    records = list(result.scalars().all())

    if not records:
        return "No attendance records for today."

    total = len(records)
    late = sum(1 for r in records if r.late_flag)
    missing = sum(1 for r in records if r.missing_punch)
    present = total - late - missing

    lines = [
        f"Today ({today.isoformat()}) Attendance:",
        f"- Total employees: {total}",
        f"- Present: {present}",
        f"- Late: {late}",
        f"- Missing punches: {missing}",
        "",
        "Individual records:",
    ]

    for r in records[:50]:  # cap at 50 to avoid huge context
        lines.append(
            f"  {r.name} ({r.employee_id}): "
            f"check-in {r.check_in}, check-out {r.check_out}, "
            f"{'LATE' if r.late_flag else ''}{' MISSING PUNCH' if r.missing_punch else ''}"
        )

    return "\n".join(lines)


class RAGCopilot:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_query(self, user_id: str, message: str, conversation_id: str | None = None) -> dict:
        sanitized_message = message.strip()

        injection_check = injection_protection.detect_injection(sanitized_message)
        if injection_check["detected"]:
            return {
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "response": "I'm sorry, but I cannot process that request. Please ask a valid HR-related question.",
                "sources": [],
            }

        # Gather context from multiple sources
        context_parts = []
        sources = []

        today_stats = await query_today_stats(self.db)
        if "No attendance records" not in today_stats:
            context_parts.append(today_stats)

        month_stats = await query_summary_stats(self.db)
        if "No attendance data" not in month_stats:
            context_parts.append(month_stats)

        # Vector search on FAISS collections
        for collection in ("attendance", "policies"):
            try:
                results = await vector_search(collection, sanitized_message, top_k=5)
                for r in results:
                    text = r.get("text", "")
                    if text:
                        context_parts.append(text)
                    sources.append({
                        "title": r.get("title", r.get("doc_type", collection)),
                        "snippet": (text or "")[:200],
                        "source": collection,
                    })
            except Exception:
                continue

        context = "\n\n".join(context_parts) if context_parts else "No relevant context found."

        user_prompt = f"""Based on the following context, answer the user's question.

CONTEXT:
{context}

RULES:
- Answer based only on the provided context
- If context is insufficient, say "I don't have enough information to answer that question"
- Give specific names, numbers, and dates when available
- Be helpful and professional

QUESTION: {sanitized_message}

ANSWER:"""

        result = await ai_client.generate(
            system_prompt=COPILOT_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        log = AIUsageLog(
            feature="copilot",
            model=result.get("model", "unknown"),
            prompt_tokens=result.get("prompt_tokens", 0),
            completion_tokens=result.get("completion_tokens", 0),
            total_tokens=result.get("total_tokens", 0),
            cost_usd=result.get("cost_usd", 0.0),
            latency_ms=result.get("latency_ms", 0),
            status="error" if result.get("error") else "success",
            error_message=result.get("error"),
        )
        self.db.add(log)
        await self.db.flush()

        response_text = result.get("content", "I'm sorry, I couldn't process your request. Please try again.")

        # Find or create conversation
        if conversation_id:
            conv_result = await self.db.execute(
                select(ChatConversation).where(ChatConversation.id == uuid.UUID(conversation_id))
            )
            conversation = conv_result.scalar_one_or_none()
        else:
            conversation = None

        if not conversation:
            conversation = ChatConversation(
                user_id=uuid.UUID(user_id),
                title=sanitized_message[:100],
            )
            self.db.add(conversation)
            await self.db.flush()
            conversation_id = str(conversation.id)
        else:
            conversation_id = str(conversation.id)

        user_msg = ChatMessage(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        self.db.add(user_msg)

        assistant_msg = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            sources=sources,
            tokens_used=result.get("total_tokens", 0),
            cost_usd=result.get("cost_usd", 0.0),
        )
        self.db.add(assistant_msg)
        await self.db.flush()

        return {
            "conversation_id": conversation_id,
            "response": response_text,
            "sources": sources,
        }

    async def get_conversations(self, user_id: str, skip: int = 0, limit: int = 20) -> list[dict]:
        result = await self.db.execute(
            select(ChatConversation)
            .where(ChatConversation.user_id == uuid.UUID(user_id))
            .order_by(ChatConversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        conversations = list(result.scalars().all())
        return [
            {
                "id": str(c.id),
                "title": c.title,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in conversations
        ]

    async def get_conversation(self, conversation_id: str) -> dict | None:
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(ChatConversation)
            .options(selectinload(ChatConversation.messages))
            .where(ChatConversation.id == uuid.UUID(conversation_id))
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return None

        return {
            "id": str(conversation.id),
            "title": conversation.title,
            "created_at": conversation.created_at,
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "sources": m.sources,
                    "created_at": m.created_at,
                }
                for m in conversation.messages
            ],
        }

    async def delete_conversation(self, conversation_id: str) -> bool:
        result = await self.db.execute(
            select(ChatConversation).where(ChatConversation.id == uuid.UUID(conversation_id))
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return False
        await self.db.delete(conversation)
        await self.db.flush()
        return True

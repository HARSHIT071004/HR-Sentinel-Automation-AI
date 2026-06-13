import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.ai_client import ai_client
from app.core.vector_store import vector_store
from app.models.chat import ChatConversation, ChatMessage
from app.models.ai import AIUsageLog
from app.models.attendance import MonthlySummary
from app.utils.injection_protection import injection_protection


COPILOT_SYSTEM = """You are an AI HR Assistant for AegisHR. You help HR managers with workforce intelligence.

RULES:
1. Answer ONLY based on the provided context
2. If context is insufficient, say "I don't have enough information to answer that question"
3. Be helpful and professional
4. Never fabricate information
5. For data queries, provide specific numbers and names
6. For policy queries, cite the specific policy section"""


def keyword_search(query: str, top_k: int = 5) -> list[dict]:
    """Simple keyword-based search using FAISS metadata."""
    try:
        store = vector_store.get_store("policies")
        if store.count() == 0:
            return []

        # Simple keyword matching on metadata text
        query_lower = query.lower()
        results = []
        for meta in store.metadata:
            text = meta.get("text", "").lower()
            # Calculate relevance score based on keyword overlap
            query_words = set(query_lower.split())
            text_words = set(text.split())
            overlap = len(query_words.intersection(text_words))
            if overlap > 0:
                results.append({**meta, "score": overlap / len(query_words)})

        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:top_k]
    except Exception as e:
        logger.warning(f"Keyword search failed: {e}")
        return []


class RAGCopilot:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def classify_intent(self, message: str) -> dict:
        system = """Classify the intent of this HR question. Return ONLY a JSON object.

INTENTS:
- "policy": About company rules, leave policy, attendance policy, HR procedures
- "data": About specific employees, numbers, statistics, attendance records
- "analysis": Requests analysis, trends, comparisons, risk assessments
- "action": Wants to perform an action (generate report, send email)
- "general": General HR question not fitting above categories

Return: {"intent": "<intent>", "confidence": <0.0-1.0>}"""

        result = await ai_client.generate_json(
            system_prompt=system,
            user_prompt=f"Classify this question: {message}",
            temperature=0.1,
        )

        if result.get("data"):
            return result["data"]

        message_lower = message.lower()
        if any(w in message_lower for w in ["policy", "rule", "procedure", "leave"]):
            return {"intent": "policy", "confidence": 0.7}
        elif any(w in message_lower for w in ["who", "how many", "employee", "late", "strike"]):
            return {"intent": "data", "confidence": 0.7}
        elif any(w in message_lower for w in ["trend", "analyze", "compare", "risk"]):
            return {"intent": "analysis", "confidence": 0.7}
        elif any(w in message_lower for w in ["generate", "report", "send"]):
            return {"intent": "action", "confidence": 0.7}
        else:
            return {"intent": "general", "confidence": 0.5}

    async def query_database(self, intent: dict, message: str) -> str:
        intent_type = intent.get("intent", "general")

        if intent_type in ("data", "analysis"):
            current_month = datetime.now().strftime("%Y-%m")
            result = await self.db.execute(
                select(MonthlySummary).where(MonthlySummary.month_year == current_month)
            )
            summaries = list(result.scalars().all())

            if not summaries:
                return "No attendance data available for the current month."

            context_parts = []
            for s in summaries:
                context_parts.append(f"- {s.name} ({s.employee_id}): {s.late_count} late arrivals, warning level {s.warning_level}")

            return "Current month attendance violations:\n" + "\n".join(context_parts)

        return ""

    async def process_query(self, user_id: str, message: str, conversation_id: str | None = None) -> dict:
        sanitized_message = injection_protection.sanitize_input(message)

        injection_check = injection_protection.detect_injection(message)
        if injection_check["detected"]:
            return {
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "response": "I'm sorry, but I cannot process that request. Please ask a valid HR-related question.",
                "sources": [],
            }

        intent = await self.classify_intent(sanitized_message)

        context = ""
        sources = []

        if intent["intent"] in ("data", "analysis"):
            db_context = await self.query_database(intent, sanitized_message)
            if db_context:
                context = db_context

        # Search FAISS for relevant documents using keyword matching
        faiss_results = keyword_search(sanitized_message, top_k=3)
        for r in faiss_results:
            context += f"\n\n{r.get('text', '')}"
            sources.append({
                "title": r.get("title", "Document"),
                "content": r.get("text", "")[:200],
                "score": r.get("score", 0),
            })

        user_prompt = f"""Based on the following context, answer the user's question.

CONTEXT:
{context if context else "No relevant context found."}

RULES:
- Answer based only on the provided context
- If context is insufficient, say "I don't have enough information to answer that question"
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

        if sources:
            response_text += "\n\nSources:\n" + "\n".join([f"[{i+1}] {s['title']}" for i, s in enumerate(sources)])

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

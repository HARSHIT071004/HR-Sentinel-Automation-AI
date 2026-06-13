from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ChatConversationResponse, ChatConversationDetail
from app.services.copilot_service import RAGCopilot
from app.core.deps import require_role, get_current_user
from app.models.user import User

router = APIRouter(prefix="/copilot", tags=["HR Copilot"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = RAGCopilot(db)
    result = await service.process_query(
        user_id=str(current_user.id),
        message=data.message,
        conversation_id=data.conversation_id,
    )
    return result


@router.get("/conversations", response_model=list[ChatConversationResponse])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = RAGCopilot(db)
    return await service.get_conversations(str(current_user.id), skip=skip, limit=limit)


@router.get("/conversations/{conversation_id}", response_model=ChatConversationDetail)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = RAGCopilot(db)
    result = await service.get_conversation(conversation_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"])),
):
    service = RAGCopilot(db)
    deleted = await service.delete_conversation(conversation_id)
    if not deleted:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted", "success": True}

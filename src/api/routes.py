from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.schemas import RawEvent, UserContextResponse
from src.services.queue import RedisQueue
from src.services.retrieval import ContextService
from src.db.session import get_async_db
from src.api.security import validate_api_key

router = APIRouter()
queue_service = RedisQueue()


@router.post("/ingest", dependencies=[Depends(validate_api_key)])
async def ingest_event(event: RawEvent):
    try:
        await queue_service.push(event)
        return {"status": "queued", "user": event.distinct_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/context/user/{user_id}",
    response_model=UserContextResponse,
    dependencies=[Depends(validate_api_key)],
)
async def get_context(user_id: str, db: AsyncSession = Depends(get_async_db)):
    service = ContextService(db)
    return await service.get_user_context(user_id)

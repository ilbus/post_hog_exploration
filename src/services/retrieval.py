from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from src.db.models import EventModel
from src.core.schemas import UserContextResponse, UserActivity


class ContextService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _format_time_ago(self, dt: datetime) -> str:
        if not dt:
            return "Unknown"
        diff = datetime.now() - dt
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minutes ago" if minutes < 60 else f"{int(minutes / 60)}h ago"

    async def get_user_context(
        self, user_id: str, limit: int = 10
    ) -> UserContextResponse:
        query = (
            select(EventModel)
            .where(EventModel.user_id == user_id)
            .order_by(EventModel.created_at.desc())
            .limit(limit)
        )

        query_result = await self.db.execute(query)

        events = query_result.scalars().all()

        if not events:
            return UserContextResponse(
                user_id=user_id, summary="No events found", user_activity=[]
            )

        history = [
            UserActivity(
                time_ago=self._format_time_ago(e.created_at),
                action=e.semantic_label,
                session_id=e.session_id,
            )
            for e in events
        ]

        summary = "User is active."
        actions = [e.semantic_label.lower() for e in events]
        if any("upgrade" in a for a in actions):
            summary = "User showing Purchase Intent."

        return UserContextResponse(
            user_id=user_id, summary=summary, user_activity=history
        )
